#!/usr/bin/env bash
set -euo pipefail

# One-way, conflict-safe sync from live runtime tree to repo working tree.
# Never writes from repo back into /root/immich-app.
APP_DIR="${APP_DIR:-/root/immich-app}"
REPO_DIR="${REPO_DIR:-/root/immich-remote-server}"
DRY_RUN="${DRY_RUN:-1}"
DELETE_MISSING="${DELETE_MISSING:-0}"

if [[ ! -d "$APP_DIR" || ! -d "$REPO_DIR/.git" ]]; then
  echo "APP_DIR or REPO_DIR invalid" >&2
  exit 1
fi

RSYNC_ARGS=(
  -a
  --exclude=.git/
  --exclude=.env
  --exclude=.env.*
  --exclude=mcp-gateway.env.local
  --exclude=.secrets/
  --exclude=.state/
  --exclude=backups/
  --exclude=reports/
  --exclude=**/__pycache__/
  --exclude=*.local.log
  --exclude=docker-compose.yml.backup
  --exclude=.gitignore
)

if [[ "$DELETE_MISSING" == "1" ]]; then
  RSYNC_ARGS+=(--delete)
  echo "[safe-sync] DELETE_MISSING=1 (repo files absent in runtime may be removed)"
else
  echo "[safe-sync] DELETE_MISSING=0 (repo-only files are preserved)"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  RSYNC_ARGS+=(--dry-run --itemize-changes)
  echo "[safe-sync] DRY_RUN=1 (preview only)"
else
  echo "[safe-sync] DRY_RUN=0 (app -> repo copy)"
fi

rsync "${RSYNC_ARGS[@]}" "$APP_DIR/" "$REPO_DIR/"

echo "[safe-sync] Done"
