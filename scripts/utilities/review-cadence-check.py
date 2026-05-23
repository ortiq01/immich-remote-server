#!/usr/bin/env python3
"""
Review cadence health check for Family - Inbox Review.

Outputs a compact status report and exits non-zero only when API calls fail.
Thresholds are informational and configurable via .env.immich-api:
- REVIEW_CADENCE_ALBUM_NAME
- REVIEW_CADENCE_WARN_COUNT (default: 1500)
- REVIEW_CADENCE_WARN_OLDEST_DAYS (default: 14)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env.immich-api"


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


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None


def is_plausible_media_date(dt: datetime) -> bool:
    # Some assets may report 1970 epoch placeholders. Treat those as unknown.
    return dt.year >= 2000
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def main() -> int:
    env = load_env(ENV_FILE)
    immich_url = os.environ.get("IMMICH_URL") or env.get("IMMICH_URL")
    api_key = os.environ.get("IMMICH_API_KEY") or env.get("IMMICH_API_KEY")

    album_name = env.get("REVIEW_CADENCE_ALBUM_NAME", "Family - Inbox Review")
    warn_count = int(env.get("REVIEW_CADENCE_WARN_COUNT", "1500"))
    warn_oldest_days = int(env.get("REVIEW_CADENCE_WARN_OLDEST_DAYS", "14"))

    if not immich_url or not api_key:
        print("[FAIL] IMMICH_URL and IMMICH_API_KEY are required in .env.immich-api")
        return 2

    client = ImmichClient(immich_url, api_key)

    albums = client.call("GET", "/api/albums") or []
    target = next((a for a in albums if (a.get("albumName") or "").strip() == album_name), None)
    if not target:
        print(f"[WARN] Album not found: {album_name}")
        return 0

    album_id = target.get("id")
    album = client.call("GET", f"/api/albums/{album_id}?withoutAssets=false") or {}
    assets = album.get("assets") or []

    now = datetime.now(timezone.utc)
    oldest = None
    newest = None

    for a in assets:
        ts = parse_iso(a.get("fileCreatedAt") or a.get("createdAt"))
        if not ts:
            continue
        if not is_plausible_media_date(ts):
            continue
        if oldest is None or ts < oldest:
            oldest = ts
        if newest is None or ts > newest:
            newest = ts

    count = len(assets)
    oldest_days = int((now - oldest).total_seconds() // 86400) if oldest else 0

    print(f"[INFO] Album: {album_name}")
    print(f"[INFO] Asset count: {count}")
    if oldest:
        print(f"[INFO] Oldest asset age: {oldest_days} days ({oldest.isoformat()})")
    if newest:
        print(f"[INFO] Newest asset: {newest.isoformat()}")

    status_bits = []
    if count >= warn_count:
        status_bits.append(f"count>=threshold ({count}>={warn_count})")
    if oldest and oldest_days >= warn_oldest_days:
        status_bits.append(f"oldest>=threshold ({oldest_days}>={warn_oldest_days} days)")

    if status_bits:
        print("[WARN] Review cadence behind: " + "; ".join(status_bits))
    else:
        print("[OK] Review cadence looks healthy")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
