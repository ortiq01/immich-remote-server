#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import request, error

ENV_FILE = "/root/immich-app/.env.immich-api"


def load_env(path: str) -> dict:
    env = {}
    p = Path(path)
    if not p.exists():
        return env
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def env_get(name: str, file_env: dict, default: str | None = None) -> str | None:
    return os.environ.get(name) or file_env.get(name) or default


class ImmichClient:
    def __init__(self, base_url: str, api_key: str):
        self.base = base_url.rstrip("/")
        self.key = api_key

    def request_json(self, method: str, path: str, payload: dict | None = None):
        data = None
        headers = {
            "x-api-key": self.key,
            "accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["content-type"] = "application/json"

        req = request.Request(f"{self.base}{path}", data=data, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} {path}: {body[:400]}") from e


def ensure_album(client: ImmichClient, album_name: str) -> str:
    albums = client.request_json("GET", "/api/albums") or []
    for a in albums:
        if a.get("albumName") == album_name:
            return a["id"]

    created = client.request_json("POST", "/api/albums", {"albumName": album_name})
    if not created or not created.get("id"):
        raise RuntimeError("Failed to create target album")
    print(f"[INFO] Created album '{album_name}'")
    return created["id"]


def get_libraries(client: ImmichClient) -> list[dict]:
    return client.request_json("GET", "/api/libraries") or []


def resolve_library_ids_by_path_prefixes(client: ImmichClient, prefixes: list[str]) -> list[str]:
    if not prefixes:
        return []
    ids: list[str] = []
    libs = get_libraries(client)
    for lib in libs:
        lib_id = lib.get("id")
        import_paths = lib.get("importPaths") or []
        if not lib_id:
            continue
        matches = False
        for prefix in prefixes:
            for path in import_paths:
                normalized = path.rstrip("/")
                if prefix.startswith(normalized + "/") or prefix == (normalized + "/") or prefix == normalized:
                    matches = True
                    break
            if matches:
                break
        if matches:
            ids.append(lib_id)
    # preserve order, de-dup
    seen = set()
    deduped = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            deduped.append(i)
    return deduped


def search_new_assets(client: ImmichClient, updated_after: str | None, library_id: str | None = None):
    page = 1
    assets: list[dict] = []
    while True:
        payload = {
            "isNotInAlbum": True,
            "withDeleted": False,
            "size": 1000,
            "page": page,
            "order": "desc",
        }
        if updated_after:
            payload["updatedAfter"] = updated_after
        if library_id:
            payload["libraryId"] = library_id
        res = client.request_json("POST", "/api/search/metadata", payload) or {}
        items = ((res.get("assets") or {}).get("items") or [])
        if not items:
            break
        assets.extend(items)

        next_page = (res.get("assets") or {}).get("nextPage")
        if not next_page:
            break
        try:
            page = int(next_page)
        except ValueError:
            page += 1

    return assets


def add_assets_to_album(client: ImmichClient, album_id: str, asset_ids: list[str]):
    if not asset_ids:
        return 0
    added = 0
    chunk_size = 500
    for i in range(0, len(asset_ids), chunk_size):
        chunk = asset_ids[i:i + chunk_size]
        payload = {"albumIds": [album_id], "assetIds": chunk}
        client.request_json("PUT", "/api/albums/assets", payload)
        added += len(chunk)
    return added


def read_state(path: Path, default_since: str) -> str:
    if not path.exists():
        return default_since
    value = path.read_text().strip()
    return value or default_since


def write_state(path: Path, value: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n")


def should_run_reconcile(reconcile_state_file: Path, interval_hours: int) -> bool:
    if interval_hours <= 0:
        return False
    if not reconcile_state_file.exists():
        return True
    try:
        last = datetime.fromisoformat(reconcile_state_file.read_text().strip().replace("Z", "+00:00"))
    except Exception:
        return True
    now = datetime.now(timezone.utc)
    return (now - last) >= timedelta(hours=interval_hours)


def filter_by_prefix_if_configured(client: ImmichClient, assets: list[dict], prefixes: list[str]) -> list[str]:
    def get_path_and_id(item: dict) -> tuple[str, str | None]:
        return (item.get("originalPath") or "", item.get("id"))

    if not prefixes:
        return [aid for _, aid in map(get_path_and_id, assets) if aid]

    filtered: list[str] = []
    for item in assets:
        p, aid = get_path_and_id(item)
        if aid and any(p.startswith(prefix) for prefix in prefixes):
            filtered.append(aid)
    return filtered


def main():
    file_env = load_env(ENV_FILE)
    immich_url = env_get("IMMICH_URL", file_env)
    api_key = env_get("IMMICH_API_KEY", file_env)
    album_name = env_get("INBOX_ALBUM_NAME", file_env, "Family - Inbox Review")
    state_file = Path(env_get("INBOX_ROUTER_STATE_FILE", file_env, "/root/immich-app/.state/immich-inbox-router.last_updated_after"))
    lookback_hours = int(env_get("INBOX_ROUTER_LOOKBACK_HOURS", file_env, "168"))
    reconcile_hours = int(env_get("INBOX_ROUTER_FORCE_RECONCILE_EVERY_HOURS", file_env, "24"))
    use_library_filter = (env_get("INBOX_ROUTER_USE_LIBRARY_FILTER", file_env, "true") or "true").lower() in {"1", "true", "yes", "y"}
    manual_library_ids_raw = env_get("INBOX_ROUTER_LIBRARY_IDS", file_env, "") or ""
    manual_library_ids = [v.strip() for v in manual_library_ids_raw.split(",") if v.strip()]
    raw_prefixes = env_get("INBOX_ROUTER_PATH_PREFIXES", file_env, "") or ""
    prefixes = [p.strip() for p in raw_prefixes.split(",") if p.strip()]

    if not immich_url or not api_key:
        print("[FAIL] IMMICH_URL and IMMICH_API_KEY are required in .env.immich-api", file=sys.stderr)
        sys.exit(2)

    client = ImmichClient(immich_url, api_key)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    default_since = (now - timedelta(hours=lookback_hours)).isoformat().replace("+00:00", "Z")
    # Backward compatibility: if a previous default state file exists, keep using it.
    legacy_state = Path("/root/immich-app/.state/immich-inbox-router.last_created_after")
    if not state_file.exists() and legacy_state.exists() and state_file != legacy_state:
        state_file = legacy_state

    since = read_state(state_file, default_since)
    reconcile_state_file = Path(str(state_file) + ".reconcile")
    reconcile_now = should_run_reconcile(reconcile_state_file, reconcile_hours)

    print(f"[INFO] Target album: {album_name}")
    if reconcile_now:
        print(f"[INFO] Running full reconcile (interval {reconcile_hours}h)")
    else:
        print(f"[INFO] Searching updatedAfter: {since}")
    if prefixes:
        print(f"[INFO] Restricting to path prefixes: {', '.join(prefixes)}")

    album_id = ensure_album(client, album_name)
    library_ids: list[str] = []
    if manual_library_ids:
        library_ids = manual_library_ids
    elif use_library_filter:
        library_ids = resolve_library_ids_by_path_prefixes(client, prefixes)

    if library_ids:
        print(f"[INFO] Using library filter IDs: {', '.join(library_ids)}")
        assets = []
        for lib_id in library_ids:
            assets.extend(search_new_assets(client, None if reconcile_now else since, library_id=lib_id))
    else:
        assets = search_new_assets(client, None if reconcile_now else since)

    print(f"[INFO] Candidate assets: {len(assets)}")

    # If library scoping is active, path filtering is already implied by library import path.
    if library_ids:
        ids = [a.get("id") for a in assets if a.get("id")]
    else:
        ids = filter_by_prefix_if_configured(client, assets, prefixes)
    print(f"[INFO] Assets after path filter: {len(ids)}")

    if not ids:
        write_state(state_file, now.isoformat().replace("+00:00", "Z"))
        print("[OK] No new assets to route.")
        return

    added = add_assets_to_album(client, album_id, ids)
    write_state(state_file, now.isoformat().replace("+00:00", "Z"))
    if reconcile_now:
        write_state(reconcile_state_file, now.isoformat().replace("+00:00", "Z"))
    print(f"[OK] Added {added} assets to '{album_name}'.")


if __name__ == "__main__":
    main()
