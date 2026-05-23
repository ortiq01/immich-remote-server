#!/usr/bin/env python3
import json
from pathlib import Path
from urllib import request, error

IMMICH_ENV = Path('/root/immich-app/.env.immich-api')
BACKUP_ENV = Path('/root/immich-app/.env.backup-source')


def load_env(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip()
    return data


class Immich:
    def __init__(self, base: str, key: str):
        self.base = base.rstrip('/')
        self.headers = {'x-api-key': key, 'accept': 'application/json', 'content-type': 'application/json'}

    def call(self, method: str, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        req = request.Request(self.base + path, method=method, data=data, headers=self.headers)
        try:
            with request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                return resp.status, (json.loads(body) if body else None)
        except error.HTTPError as e:
            raw = e.read().decode('utf-8', 'ignore')
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return e.code, parsed


def main() -> int:
    ienv = load_env(IMMICH_ENV)
    benv = load_env(BACKUP_ENV)

    base = ienv.get('IMMICH_URL', '').strip()
    key = ienv.get('IMMICH_API_KEY', '').strip()
    if not base or not key:
        print('[ERROR] IMMICH_URL and IMMICH_API_KEY required in .env.immich-api')
        return 1

    photos_path = benv.get('BACKUP_CONTAINER_PHOTOS_PATH', '/usr/src/app/external/backup/Fotos').strip()
    podcast_path = benv.get('BACKUP_CONTAINER_PODCAST_PATH', '/usr/src/app/external/backup/Podcast').strip()
    library_name = benv.get('BACKUP_LIBRARY_NAME', 'Backup Share 192.168.1.107').strip()
    owner_email = benv.get('BACKUP_LIBRARY_OWNER_EMAIL', ienv.get('IMMICH_ADMIN_ACCOUNT', '')).strip().lower()

    imm = Immich(base, key)

    c, users = imm.call('GET', '/api/users')
    if c != 200:
        print(f'[ERROR] users fetch failed: {c} {users}')
        return 1
    owner = next((u for u in users if (u.get('email') or '').lower() == owner_email), None)
    if not owner:
        print(f'[ERROR] owner user not found by email: {owner_email}')
        return 1

    c, libraries = imm.call('GET', '/api/libraries')
    if c != 200:
        print(f'[ERROR] libraries fetch failed: {c} {libraries}')
        return 1

    target = next((l for l in libraries if l.get('name') == library_name), None)
    wanted_paths = [p for p in [photos_path, podcast_path] if p]

    if target:
        current = target.get('importPaths') or []
        merged = []
        seen = set()
        for p in current + wanted_paths:
            if p and p not in seen:
                seen.add(p)
                merged.append(p)

        c, d = imm.call('PUT', f"/api/libraries/{target['id']}", {
            'name': target.get('name', library_name),
            'importPaths': merged,
            'exclusionPatterns': target.get('exclusionPatterns') or [
                '**/@eaDir/**',
                '**/._*',
                '**/#recycle/**',
                '**/#snapshot/**',
            ],
        })
        if c not in (200, 201):
            print(f'[ERROR] library update failed: {c} {d}')
            return 1
        lib_id = target['id']
        print(f"[OK] Updated library '{library_name}' with import paths: {merged}")
    else:
        c, d = imm.call('POST', '/api/libraries', {
            'ownerId': owner['id'],
            'name': library_name,
            'importPaths': wanted_paths,
        })
        if c not in (200, 201):
            print(f'[ERROR] library create failed: {c} {d}')
            return 1
        lib_id = d['id']
        print(f"[OK] Created library '{library_name}' ({lib_id}) with import paths: {wanted_paths}")

    c, d = imm.call('POST', f'/api/libraries/{lib_id}/scan')
    if c not in (200, 201, 204):
        print(f'[WARN] Library scan queue failed: {c} {d}')
    else:
        print(f"[OK] Queued scan for library '{library_name}'")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
