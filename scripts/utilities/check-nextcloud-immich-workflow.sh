#!/usr/bin/env bash
set -euo pipefail

# Nextcloud -> Immich workflow health check
# Based on workflow mapping provided by operator.

SRC_BASE="/root/nextcloud/data/ortiq01/files"
SRC_PHOTOS="${SRC_BASE}/Photos"
SRC_CAMERA="${SRC_BASE}/Photos/Camera"
SRC_INSTANT="${SRC_BASE}/InstantUpload"
SYNC_TARGET="/shared/nextcloud-photos"
IMMICH_CONTAINER="immich_server"
IMMICH_MOUNT="/usr/src/app/external/nextcloud"

SYNC_SCRIPT="/usr/local/bin/sync-nextcloud-to-immich-final.sh"
SYNC_LOG="/var/log/nextcloud-immich-sync.log"
SYNC_STATE_DIR="/var/log/nextcloud-immich-sync"
LATEST_RUN_JSON="${SYNC_STATE_DIR}/latest-run.json"
LAST_SUCCESS_TS="${SYNC_STATE_DIR}/last-success.timestamp"

print_header() {
  printf "\n=== %s ===\n" "$1"
}

ok() { printf "[OK] %s\n" "$1"; }
warn() { printf "[WARN] %s\n" "$1"; }
fail() { printf "[FAIL] %s\n" "$1"; }

check_dir() {
  local dir="$1"
  local label="$2"
  if [[ -d "$dir" ]]; then
    local count
    count=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
    ok "$label exists: $dir (top-level files: $count)"
  else
    fail "$label missing: $dir"
  fi
}

check_file() {
  local file="$1"
  local label="$2"
  if [[ -e "$file" ]]; then
    ok "$label exists: $file"
  else
    warn "$label missing: $file"
  fi
}

json_get() {
  local file="$1"
  local key="$2"
  python3 - <<PY
import json
from pathlib import Path
p = Path(${file@Q})
if not p.exists():
    print("")
else:
    data = json.loads(p.read_text())
    v = data.get(${key@Q}, "")
    print(v)
PY
}

age_minutes() {
  local file="$1"
  if [[ ! -e "$file" ]]; then
    echo ""
    return
  fi
  python3 - <<PY
from pathlib import Path
import time
p = Path(${file@Q})
age = int((time.time() - p.stat().st_mtime) / 60)
print(age)
PY
}

print_header "Source and target folders"
check_dir "$SRC_PHOTOS" "Nextcloud Photos"
check_dir "$SRC_CAMERA" "Nextcloud Camera"
check_dir "$SRC_INSTANT" "Nextcloud InstantUpload"
check_dir "$SYNC_TARGET" "Shared sync target"

print_header "Sync job artifacts"
check_file "$SYNC_SCRIPT" "Sync script"
check_file "$SYNC_LOG" "Sync log"
check_file "$LATEST_RUN_JSON" "Latest run snapshot"
check_file "$LAST_SUCCESS_TS" "Last success timestamp"

if [[ -f "$LATEST_RUN_JSON" ]]; then
  status=$(json_get "$LATEST_RUN_JSON" "status")
  missing=$(json_get "$LATEST_RUN_JSON" "missing_count")
  copied=$(json_get "$LATEST_RUN_JSON" "copied_count")
  source_count=$(json_get "$LATEST_RUN_JSON" "source_count")
  target_count=$(json_get "$LATEST_RUN_JSON" "target_count")
  msg=$(json_get "$LATEST_RUN_JSON" "message")

  print_header "Latest run summary"
  echo "status: ${status:-unknown}"
  echo "source_count: ${source_count:-n/a}"
  echo "copied_count: ${copied:-n/a}"
  echo "target_count: ${target_count:-n/a}"
  echo "missing_count: ${missing:-n/a}"
  [[ -n "$msg" ]] && echo "message: $msg"

  if [[ "$status" == "success" ]]; then
    ok "Sync status is success"
  elif [[ "$status" == "running" ]]; then
    warn "Sync currently running"
  else
    warn "Sync status is ${status:-unknown}"
  fi

  if [[ -n "${missing:-}" && "${missing}" != "0" ]]; then
    warn "There are missing files reported (missing_count=${missing})"
  fi
fi

if [[ -f "$LAST_SUCCESS_TS" ]]; then
  print_header "Recency"
  age=$(age_minutes "$LAST_SUCCESS_TS")
  if [[ -n "$age" ]]; then
    echo "last_success_file_age_minutes: $age"
    if (( age > 60 )); then
      warn "Last success marker is older than 60 minutes"
    else
      ok "Last success marker is recent"
    fi
  fi
fi

print_header "Immich container mount visibility"
if docker ps --format '{{.Names}}' | grep -q "^${IMMICH_CONTAINER}$"; then
  if docker exec "$IMMICH_CONTAINER" sh -lc "test -d '$IMMICH_MOUNT'"; then
    ok "Immich mount exists in container: $IMMICH_MOUNT"
    sample=$(docker exec "$IMMICH_CONTAINER" sh -lc "ls -1 '$IMMICH_MOUNT' | head -n 5" || true)
    if [[ -n "$sample" ]]; then
      echo "sample files:"
      echo "$sample"
    else
      warn "Mount is reachable but currently appears empty"
    fi
  else
    fail "Immich mount missing in container: $IMMICH_MOUNT"
  fi
else
  fail "Container not running: ${IMMICH_CONTAINER}"
fi

print_header "Suggested actions"
echo "1) If missing_count > 0, inspect: $SYNC_LOG"
echo "2) If target has files but Immich does not show them, trigger library scan in Immich UI"
echo "3) Keep this check in cron/health reports for continuous visibility"
