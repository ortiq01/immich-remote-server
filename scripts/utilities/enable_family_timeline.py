#!/usr/bin/env python3
"""
Enable family-wide partner timeline sharing for the current Immich user.

Run this once PER family account (with that account's API key):
  python3 enable_family_timeline.py --api-key <USER_API_KEY>

What it does for the current user:
1) Creates partner shares from current user -> all other active users.
2) Sets inTimeline=true for all inbound partner shares (shared-with).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import error, request


DEFAULT_ENV = Path(__file__).resolve().parents[2] / ".env.immich-api"


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


class ImmichClient:
    def __init__(self, base_url: str, api_key: str):
        self.base = base_url.rstrip("/")
        self.headers = {
            "x-api-key": api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def call(self, method: str, path: str, body: dict | list | None = None):
        payload = None if body is None else json.dumps(body).encode()
        req = request.Request(self.base + path, method=method, data=payload, headers=self.headers)
        try:
            with request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if raw else None)
        except error.HTTPError as e:
            raw = e.read().decode("utf-8", "ignore")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw
            return e.code, parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Enable family timeline partner sharing for current Immich user")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV), help="Path to env file containing IMMICH_URL")
    parser.add_argument("--immich-url", default=None, help="Override IMMICH_URL")
    parser.add_argument("--api-key", default=None, help="API key for the CURRENT user account")
    parser.add_argument(
        "--exclude-shared-with-emails",
        default="",
        help="Comma-separated emails to EXCLUDE from outbound partner sharing for the current user",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show planned actions without changing anything")
    args = parser.parse_args()

    env = load_env(Path(args.env_file))
    base_url = (args.immich_url or env.get("IMMICH_URL") or "").strip()
    api_key = (args.api_key or os.environ.get("IMMICH_API_KEY") or "").strip()

    if not base_url:
        print("[ERROR] Missing Immich URL. Set --immich-url or IMMICH_URL in env file.")
        return 1
    if not api_key:
        print("[ERROR] Missing API key. Provide --api-key or IMMICH_API_KEY env var.")
        return 1

    excluded_outbound_emails = {
        e.strip().lower()
        for e in (args.exclude_shared_with_emails or "").split(",")
        if e.strip()
    }

    client = ImmichClient(base_url, api_key)

    code, me = client.call("GET", "/api/users/me")
    if code != 200:
        print(f"[ERROR] Could not fetch current user: {code} {me}")
        return 1
    my_id = me["id"]
    my_email = me.get("email")
    print(f"[INFO] Current user: {my_email} ({my_id})")
    if excluded_outbound_emails:
        print("[INFO] Outbound partner exclusions:")
        for e in sorted(excluded_outbound_emails):
            print(f"  - {e}")

    code, users = client.call("GET", "/api/users")
    if code != 200:
        print(f"[ERROR] Could not list users: {code} {users}")
        return 1

    others = [u for u in users if u.get("id") != my_id and (u.get("email") or "")]
    print(f"[INFO] Other users found: {len(others)}")

    code, shared_by = client.call("GET", "/api/partners?direction=shared-by")
    if code != 200:
        print(f"[ERROR] Could not list shared-by partners: {code} {shared_by}")
        return 1

    outbound_ids = {p.get("id") for p in shared_by if p.get("id")}

    created: list[str] = []
    existed: list[str] = []
    skipped_excluded: list[str] = []
    failed_create: list[tuple[str, int]] = []

    for user in others:
        uid = user["id"]
        email = user.get("email", uid)
        email_lc = (email or "").lower()

        if email_lc and email_lc in excluded_outbound_emails:
            skipped_excluded.append(email)
            if args.dry_run:
                print(f"[DRY] Would skip excluded outbound partner share -> {email}")
            continue

        if uid in outbound_ids:
            existed.append(email)
            continue

        if args.dry_run:
            print(f"[DRY] Would create partner share -> {email}")
            continue

        c, d = client.call("POST", "/api/partners", {"sharedWithId": uid})
        if c in (200, 201):
            created.append(email)
        elif c == 400 and "already exists" in str(d).lower():
            existed.append(email)
        else:
            failed_create.append((email, c))
            print(f"[WARN] Create partner failed for {email}: {c} {d}")

    # inbound partner links (other users sharing to me)
    code, shared_with = client.call("GET", "/api/partners?direction=shared-with")
    if code != 200:
        print(f"[ERROR] Could not list shared-with partners: {code} {shared_with}")
        return 1

    enabled: list[str] = []
    already_enabled: list[str] = []
    failed_update: list[tuple[str, int]] = []

    for partner in shared_with:
        shared_by_id = partner.get("id")
        email = partner.get("email") or shared_by_id
        in_timeline = bool(partner.get("inTimeline"))

        if in_timeline:
            already_enabled.append(email)
            continue

        if args.dry_run:
            print(f"[DRY] Would set inTimeline=true for inbound partner {email}")
            continue

        c, d = client.call("PUT", f"/api/partners/{shared_by_id}", {"inTimeline": True})
        if c in (200, 201):
            enabled.append(email)
        else:
            failed_update.append((email, c))
            print(f"[WARN] Update inTimeline failed for {email}: {c} {d}")

    print("\n=== Summary ===")
    print(f"Created outbound shares: {len(created)}")
    if created:
        print("  - " + "\n  - ".join(created))
    print(f"Already had outbound shares: {len(existed)}")
    print(f"Skipped outbound exclusions: {len(skipped_excluded)}")
    if skipped_excluded:
        print("  - " + "\n  - ".join(skipped_excluded))
    print(f"Inbound timeline enabled now: {len(enabled)}")
    if enabled:
        print("  - " + "\n  - ".join(enabled))
    print(f"Inbound already enabled: {len(already_enabled)}")

    if failed_create or failed_update:
        print(f"[WARN] Some operations failed. create={len(failed_create)} update={len(failed_update)}")
        return 2

    print("[OK] Family timeline setup for this user is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
