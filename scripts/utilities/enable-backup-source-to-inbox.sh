#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

MOUNT_SCRIPT="$ROOT_DIR/scripts/utilities/mount-backup-share.sh"
REGISTER_SCRIPT="$ROOT_DIR/scripts/utilities/register-backup-library.py"
ROUTER_SCRIPT="$ROOT_DIR/scripts/utilities/route_new_assets_to_inbox.py"

echo "[STEP] Mount backup SMB share"
"$MOUNT_SCRIPT"

echo "[STEP] Restart Immich server container to apply bind mounts from docker-compose"
cd "$ROOT_DIR"
docker compose up -d immich-server

echo "[STEP] Register/update backup external library and queue scan"
python3 "$REGISTER_SCRIPT"

echo "[STEP] Run inbox router once to place newly discovered assets in Family - Inbox Review"
python3 "$ROUTER_SCRIPT"

echo "[OK] Backup source enablement flow complete"
