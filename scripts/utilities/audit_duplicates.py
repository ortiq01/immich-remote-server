#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env.immich-api"
REPORT_DIR = ROOT_DIR / "reports"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip()
    return out


class ImmichClient:
    def __init__(self, base_url: str, api_key: str):
        self.base = base_url.rstrip("/")
        self.headers = {
            "x-api-key": api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def call(self, method: str, path: str, body: dict | None = None):
        payload = None if body is None else json.dumps(body).encode()
        req = request.Request(self.base + path, method=method, headers=self.headers, data=payload)
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None


def source_bucket(path: str) -> str:
    p = (path or "").lower()
    if "/external/backup/" in p:
        return "external-backup"
    if "/external/nextcloud/" in p:
        return "external-nextcloud"
    if "/upload/" in p:
        return "upload-library"
    return "other"


def heuristic_key(asset: dict):
    return (
        (asset.get("originalFileName") or "").lower(),
        (asset.get("localDateTime") or asset.get("fileCreatedAt") or "")[:19],
        asset.get("width"),
        asset.get("height"),
        asset.get("type"),
    )


def fetch_all_assets(client: ImmichClient) -> list[dict]:
    all_items: list[dict] = []
    page = 1
    size = 1000
    while True:
        payload = {
            "size": size,
            "page": page,
            "order": "desc",
            "withDeleted": False,
        }
        res = client.call("POST", "/api/search/metadata", payload) or {}
        items = ((res.get("assets") or {}).get("items") or [])
        if not items:
            break
        all_items.extend(items)
        next_page = (res.get("assets") or {}).get("nextPage")
        if not next_page:
            break
        try:
            page = int(next_page)
        except Exception:
            page += 1
    return all_items


def main() -> int:
    env = load_env(ENV_FILE)
    base = env.get("IMMICH_URL", "").rstrip("/")
    key = env.get("IMMICH_API_KEY", "")
    if not base or not key:
        print("[FAIL] Missing IMMICH_URL/IMMICH_API_KEY in .env.immich-api")
        return 2

    client = ImmichClient(base, key)
    items = fetch_all_assets(client)

    by_checksum: dict[str, list[dict]] = defaultdict(list)
    by_duplicate_id: dict[str, list[dict]] = defaultdict(list)
    by_heuristic: dict[tuple, list[dict]] = defaultdict(list)
    for a in items:
        checksum = (a.get("checksum") or "").strip()
        if checksum:
            by_checksum[checksum].append(a)
        duplicate_id = (a.get("duplicateId") or "").strip()
        if duplicate_id:
            by_duplicate_id[duplicate_id].append(a)
        h = heuristic_key(a)
        if h[0] and h[1]:
            by_heuristic[h].append(a)

    duplicate_groups = {k: v for k, v in by_checksum.items() if len(v) > 1}
    duplicate_id_groups = {k: v for k, v in by_duplicate_id.items() if len(v) > 1}
    heuristic_groups = [v for v in by_heuristic.values() if len(v) > 1]
    heuristic_groups.sort(key=lambda g: len(g), reverse=True)

    duplicate_assets_total = sum(len(v) for v in duplicate_groups.values())
    duplicate_excess = sum(len(v) - 1 for v in duplicate_groups.values())
    duplicate_id_assets_total = sum(len(v) for v in duplicate_id_groups.values())
    duplicate_id_excess = sum(len(v) - 1 for v in duplicate_id_groups.values())
    heuristic_excess = sum(len(v) - 1 for v in heuristic_groups)

    cross_source_groups = []
    same_source_groups = []
    for checksum, group in duplicate_groups.items():
        buckets = sorted({source_bucket(g.get("originalPath") or "") for g in group})
        rec = {
            "checksum": checksum,
            "count": len(group),
            "buckets": buckets,
            "assets": [
                {
                    "id": g.get("id"),
                    "ownerId": g.get("ownerId"),
                    "libraryId": g.get("libraryId"),
                    "fileCreatedAt": g.get("fileCreatedAt"),
                    "originalFileName": g.get("originalFileName"),
                    "originalPath": g.get("originalPath"),
                    "duplicateId": g.get("duplicateId"),
                }
                for g in group
            ],
        }
        if len(buckets) > 1:
            cross_source_groups.append(rec)
        else:
            same_source_groups.append(rec)

    cross_source_groups.sort(key=lambda x: x["count"], reverse=True)
    same_source_groups.sort(key=lambda x: x["count"], reverse=True)

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"duplicates-audit-{now}.json"

    report = {
        "generatedAt": now,
        "assetCount": len(items),
        "exactChecksumDuplicateGroupCount": len(duplicate_groups),
        "exactChecksumDuplicateAssetsTotal": duplicate_assets_total,
        "exactChecksumDuplicateExcessCount": duplicate_excess,
        "duplicateIdGroupCount": len(duplicate_id_groups),
        "duplicateIdAssetsTotal": duplicate_id_assets_total,
        "duplicateIdExcessCount": duplicate_id_excess,
        "heuristicGroupCount": len(heuristic_groups),
        "heuristicExcessCount": heuristic_excess,
        "crossSourceGroupCount": len(cross_source_groups),
        "sameSourceGroupCount": len(same_source_groups),
        "topCrossSourceGroups": cross_source_groups[:50],
        "topSameSourceGroups": same_source_groups[:50],
        "topHeuristicGroups": [
            {
                "count": len(group),
                "assets": [
                    {
                        "id": g.get("id"),
                        "duplicateId": g.get("duplicateId"),
                        "ownerId": g.get("ownerId"),
                        "libraryId": g.get("libraryId"),
                        "fileCreatedAt": g.get("fileCreatedAt"),
                        "originalFileName": g.get("originalFileName"),
                        "originalPath": g.get("originalPath"),
                    }
                    for g in group[:10]
                ],
            }
            for group in heuristic_groups[:50]
        ],
    }
    report_path.write_text(json.dumps(report, indent=2))

    print(f"[INFO] Assets scanned: {len(items)}")
    print(f"[INFO] Exact-checksum duplicate groups: {len(duplicate_groups)}")
    print(f"[INFO] Exact-checksum duplicate assets total: {duplicate_assets_total}")
    print(f"[INFO] Exact-checksum duplicate excess: {duplicate_excess}")
    print(f"[INFO] duplicateId groups: {len(duplicate_id_groups)}")
    print(f"[INFO] duplicateId assets total: {duplicate_id_assets_total}")
    print(f"[INFO] duplicateId excess: {duplicate_id_excess}")
    print(f"[INFO] Heuristic duplicate groups: {len(heuristic_groups)}")
    print(f"[INFO] Heuristic duplicate excess: {heuristic_excess}")
    print(f"[INFO] Cross-source duplicate groups: {len(cross_source_groups)}")
    print(f"[INFO] Same-source duplicate groups: {len(same_source_groups)}")
    print(f"[OK] Report: {report_path}")

    if cross_source_groups:
        print("[INFO] Top 5 cross-source groups:")
        for grp in cross_source_groups[:5]:
            print(f"  - count={grp['count']} buckets={','.join(grp['buckets'])} checksum={grp['checksum']}")
            for a in grp["assets"][:3]:
                print(f"      · {a['originalPath']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
