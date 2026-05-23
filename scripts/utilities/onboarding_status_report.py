#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PRIMARY = ROOT_DIR / ".env.immich-api"
DEFAULT_ENV_FAMILY = ROOT_DIR / ".env.family-timeline"
FALLBACK_ENV_PRIMARY = Path('/root/immich-app/.env.immich-api')
FALLBACK_ENV_FAMILY = Path('/root/immich-app/.env.family-timeline')
REPORT_DIR = ROOT_DIR / "reports"


def pick_env(primary: Path, fallback: Path) -> Path:
    return primary if primary.exists() else fallback


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        out[k.strip()] = v.strip()
    return out


class ImmichClient:
    def __init__(self, base: str, api_key: str):
        self.base = base.rstrip('/')
        self.api_key = api_key

    def call(self, method: str, path: str, body: dict | None = None, api_key: str | None = None):
        payload = None if body is None else json.dumps(body).encode()
        key = api_key or self.api_key
        req = request.Request(
            self.base + path,
            method=method,
            data=payload,
            headers={
                'x-api-key': key,
                'accept': 'application/json',
                'content-type': 'application/json',
            },
        )
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None


def family_members(fenv: dict[str, str]) -> list[dict[str, str]]:
    members: list[dict[str, str]] = []
    for i in range(1, 21):
        email = fenv.get(f'FAMILY_MEMBER_{i}_EMAIL', '').strip()
        key = fenv.get(f'FAMILY_MEMBER_{i}_API_KEY', '').strip()
        if not email:
            continue
        members.append({'slot': str(i), 'email': email, 'apiKeyPresent': 'yes' if bool(key) else 'no', 'apiKey': key})
    return members


def main() -> int:
    env_primary = pick_env(DEFAULT_ENV_PRIMARY, FALLBACK_ENV_PRIMARY)
    env_family = pick_env(DEFAULT_ENV_FAMILY, FALLBACK_ENV_FAMILY)

    penv = load_env(env_primary)
    fenv = load_env(env_family)

    base = penv.get('IMMICH_URL', '').rstrip('/')
    admin_key = penv.get('IMMICH_API_KEY', '')
    if not base or not admin_key:
        print('[FAIL] Missing IMMICH_URL/IMMICH_API_KEY')
        return 2

    cli = ImmichClient(base, admin_key)
    users = cli.call('GET', '/api/users') or []
    by_email = {(u.get('email') or '').lower(): u for u in users}

    members = family_members(fenv)
    rows = []
    summary = {
        'membersTotal': len(members),
        'accountsPresent': 0,
        'apiKeysPresent': 0,
        'apiKeysWorking': 0,
        'timelineInboundComplete': 0,
        'sharedAlbumsHealthy': 0,
    }

    for m in members:
        email = m['email']
        api_key = m['apiKey']
        exists = email.lower() in by_email
        if exists:
            summary['accountsPresent'] += 1
        if api_key:
            summary['apiKeysPresent'] += 1

        row = {
            'email': email,
            'accountExists': exists,
            'apiKeyPresent': bool(api_key),
            'apiKeyWorking': False,
            'ownedAlbums': None,
            'sharedAlbums': None,
            'peopleCount': None,
            'partnersOutbound': None,
            'partnersInbound': None,
            'partnersInboundTimeline': None,
            'status': 'needs-check',
            'notes': [],
        }

        if not api_key:
            row['status'] = 'blocked'
            row['notes'].append('Missing API key in .env.family-timeline')
            rows.append(row)
            continue

        try:
            me = cli.call('GET', '/api/users/me', api_key=api_key)
            _ = me.get('email')
            row['apiKeyWorking'] = True
            summary['apiKeysWorking'] += 1

            people = cli.call('GET', '/api/people', api_key=api_key)
            p = people if isinstance(people, list) else (people.get('people') if isinstance(people, dict) else [])
            owned = cli.call('GET', '/api/albums', api_key=api_key) or []
            shared = cli.call('GET', '/api/albums?shared=true', api_key=api_key) or []
            out = cli.call('GET', '/api/partners?direction=shared-by', api_key=api_key) or []
            inn = cli.call('GET', '/api/partners?direction=shared-with', api_key=api_key) or []
            in_tl = sum(1 for x in inn if x.get('inTimeline'))

            row['peopleCount'] = len(p)
            row['ownedAlbums'] = len(owned)
            row['sharedAlbums'] = len(shared)
            row['partnersOutbound'] = len(out)
            row['partnersInbound'] = len(inn)
            row['partnersInboundTimeline'] = in_tl

            if in_tl == len(inn):
                summary['timelineInboundComplete'] += 1
            if len(shared) >= 2:
                summary['sharedAlbumsHealthy'] += 1

            # Determine status
            if len(shared) < 2:
                row['notes'].append('Very low shared album visibility (<2)')
            if in_tl < len(inn):
                row['notes'].append('Not all inbound partner shares are in timeline')
            if row['peopleCount'] == 0:
                row['notes'].append('No people index yet (expected for non-owners in current setup)')

            row['status'] = 'ok' if not row['notes'] else 'attention'

        except Exception as exc:
            row['status'] = 'blocked'
            row['notes'].append(f'API key test failed: {str(exc)[:140]}')

        rows.append(row)

    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORT_DIR / f'onboarding-status-{ts}.json'

    payload = {
        'generatedAt': ts,
        'immichUrl': base,
        'envPrimary': str(env_primary),
        'envFamily': str(env_family),
        'summary': summary,
        'rows': rows,
        'manualDeviceChecklist': [
            'Install Immich app on each family phone/tablet',
            'Login with personal account',
            'Enable Background Backup (Wi-Fi + charging preferred)',
            'Confirm first backup batch appears in timeline',
            'Validate shared albums are visible',
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2))

    print(f"[INFO] Members in family env: {summary['membersTotal']}")
    print(f"[INFO] Accounts present: {summary['accountsPresent']}")
    print(f"[INFO] API keys present: {summary['apiKeysPresent']}")
    print(f"[INFO] API keys working: {summary['apiKeysWorking']}")
    print(f"[INFO] Inbound timeline complete: {summary['timelineInboundComplete']}/{summary['membersTotal']}")
    print(f"[INFO] Shared albums healthy (>=2): {summary['sharedAlbumsHealthy']}/{summary['membersTotal']}")
    print(f"[OK] Report: {out_path}")

    for r in rows:
        notes = '; '.join(r['notes']) if r['notes'] else '-'
        print(f" - {r['email']} status={r['status']} shared={r['sharedAlbums']} timeline={r['partnersInboundTimeline']}/{r['partnersInbound']} people={r['peopleCount']} notes={notes}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
