#!/usr/bin/env python3
"""
Ensure standard family event album structure exists in Immich.

Default templates (per year):
- Family - Events - {year}
- Family - Events - {year} - Birthdays
- Family - Events - {year} - Holidays
- Family - Events - {year} - School
- Family - Events - {year} - Trips

Optional env overrides in .env.immich-api:
- EVENT_ALBUM_TEMPLATES=Comma-separated templates with {year}
- EVENT_ALBUM_YEARS=Comma-separated years (e.g. 2026,2027)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env.immich-api"

DEFAULT_TEMPLATES = [
    "Family - Events - {year}",
    "Family - Events - {year} - Birthdays",
    "Family - Events - {year} - Holidays",
    "Family - Events - {year} - School",
    "Family - Events - {year} - Trips",
]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


class ImmichClient:
    def __init__(self, base_url: str, api_key: str):
        self.base = base_url.rstrip("/")
        self.headers = {
            "x-api-key": api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def call(self, method: str, path: str, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode()
        req = request.Request(self.base + path, method=method, headers=self.headers, data=data)
        try:
            with request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            raise RuntimeError(f"HTTP {e.code} {path}: {body[:400]}") from e



def parse_years(raw: str | None) -> list[int]:
    if raw:
        years: list[int] = []
        for item in raw.split(","):
            s = item.strip()
            if not s:
                continue
            if s.isdigit():
                years.append(int(s))
        if years:
            return sorted(set(years))

    y = datetime.utcnow().year
    return [y, y + 1]


def parse_templates(raw: str | None) -> list[str]:
    if raw:
        templates = [x.strip() for x in raw.split(",") if x.strip()]
        if templates:
            return templates
    return DEFAULT_TEMPLATES


def main() -> int:
    env = load_env(ENV_FILE)
    immich_url = os.environ.get("IMMICH_URL") or env.get("IMMICH_URL")
    api_key = os.environ.get("IMMICH_API_KEY") or env.get("IMMICH_API_KEY")

    if not immich_url or not api_key:
        print("[FAIL] IMMICH_URL and IMMICH_API_KEY are required in .env.immich-api")
        return 2

    years = parse_years(env.get("EVENT_ALBUM_YEARS"))
    templates = parse_templates(env.get("EVENT_ALBUM_TEMPLATES"))
    desired_names = [tpl.replace("{year}", str(y)) for y in years for tpl in templates]

    client = ImmichClient(immich_url, api_key)
    existing = client.call("GET", "/api/albums") or []
    existing_names = {(a.get("albumName") or "").strip(): a.get("id") for a in existing}

    created = []
    skipped = []
    for name in desired_names:
        if name in existing_names:
            skipped.append(name)
            continue
        created_album = client.call("POST", "/api/albums", {"albumName": name})
        created.append(created_album.get("albumName") or name)

    print("[INFO] Event album bootstrap years:", ", ".join(str(y) for y in years))
    print(f"[INFO] Templates used: {len(templates)}")
    print(f"[INFO] Already existed: {len(skipped)}")
    print(f"[OK] Created: {len(created)}")
    if created:
        for n in created:
            print(f"  - {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
