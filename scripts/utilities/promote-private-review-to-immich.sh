#!/usr/bin/env bash
set -euo pipefail

# Promote approved private-review photos into the shared Immich sync target.
# Safe-by-default: copy mode + dry-run unless explicitly changed.

ENV_FILE="/root/immich-app/.env.immich-api"
env_get() {
  local key="$1"
  local default="${2:-}"
  if [[ ! -f "$ENV_FILE" ]]; then
    printf '%s' "$default"
    return
  fi
  local line
  line=$(grep -E "^${key}=" "$ENV_FILE" | head -n 1 || true)
  if [[ -z "$line" ]]; then
    printf '%s' "$default"
  else
    printf '%s' "${line#*=}"
  fi
}

APPROVED_DIR="$(env_get PRIVATE_REVIEW_APPROVED_DIR '/root/nextcloud/data/ortiq01/files/PrivateReview/Approved')"
TARGET_ROOT="$(env_get PRIVATE_REVIEW_PROMOTION_TARGET '/shared/nextcloud-photos/private-approved')"
PROMOTION_MODE="$(env_get PRIVATE_REVIEW_PROMOTION_MODE 'copy')"   # copy|move
DRY_RUN="$(env_get PRIVATE_REVIEW_PROMOTION_DRY_RUN 'false')"      # true|false

print() { printf '%s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
ok() { printf '[OK] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*"; }

if [[ ! -d "$APPROVED_DIR" ]]; then
  warn "Approved folder not found: $APPROVED_DIR"
  warn "Set PRIVATE_REVIEW_APPROVED_DIR in .env.immich-api when ready."
  exit 0
fi

mkdir -p "$TARGET_ROOT"

RSYNC_FLAGS=("-a" "--human-readable" "--info=stats2,progress2")
if [[ "$DRY_RUN" == "true" ]]; then
  RSYNC_FLAGS+=("--dry-run")
fi

print "Promoting approved private-review assets"
print "  approved_dir: $APPROVED_DIR"
print "  target_root : $TARGET_ROOT"
print "  mode        : $PROMOTION_MODE"
print "  dry_run     : $DRY_RUN"

# Keep directory structure and avoid duplicate overwrites.
RSYNC_FLAGS+=("--ignore-existing")

if [[ "$PROMOTION_MODE" == "copy" ]]; then
  rsync "${RSYNC_FLAGS[@]}" "$APPROVED_DIR/" "$TARGET_ROOT/"
  ok "Promotion copy completed."
elif [[ "$PROMOTION_MODE" == "move" ]]; then
  # Move only after successful transfer.
  rsync "${RSYNC_FLAGS[@]}" --remove-source-files "$APPROVED_DIR/" "$TARGET_ROOT/"
  # Remove empty directories left behind.
  find "$APPROVED_DIR" -type d -empty -delete || true
  ok "Promotion move completed."
else
  fail "Invalid PRIVATE_REVIEW_PROMOTION_MODE: $PROMOTION_MODE (expected copy|move)"
  exit 2
fi

ok "Approved assets are now in Nextcloud->Immich intake path."
