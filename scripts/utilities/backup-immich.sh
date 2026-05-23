#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.backup-recovery"

get_env() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 0
  grep -E "^${key}=" "$file" | tail -1 | cut -d= -f2- || true
}

BACKUP_ROOT="$(get_env BACKUP_ROOT "$ENV_FILE")"
BACKUP_ROOT="${BACKUP_ROOT:-$ROOT_DIR/backups/immich}"
RETENTION_DAYS="$(get_env BACKUP_RETENTION_DAYS "$ENV_FILE")"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
MEDIA_RETENTION_DAYS="$(get_env MEDIA_RETENTION_DAYS "$ENV_FILE")"
MEDIA_RETENTION_DAYS="${MEDIA_RETENTION_DAYS:-56}"
MEDIA_SNAPSHOT_DAY_UTC="$(get_env MEDIA_SNAPSHOT_DAY_UTC "$ENV_FILE")"
MEDIA_SNAPSHOT_DAY_UTC="${MEDIA_SNAPSHOT_DAY_UTC:-7}"
MEDIA_SOURCE_OVERRIDE="$(get_env MEDIA_SOURCE_OVERRIDE "$ENV_FILE")"

DB_DIR="$BACKUP_ROOT/db-dumps"
CFG_DIR="$BACKUP_ROOT/config"
MEDIA_DIR="$BACKUP_ROOT/media-snapshots"
mkdir -p "$DB_DIR" "$CFG_DIR" "$MEDIA_DIR"

NOW_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
TODAY_UTC="$(date -u +%Y%m%d)"
DB_DUMP_FILE="$DB_DIR/immich-db-$NOW_UTC.sql.gz"
CFG_ARCHIVE="$CFG_DIR/immich-config-$NOW_UTC.tgz"

echo "[INFO] Starting Immich backup at $NOW_UTC"

if ! docker ps --format '{{.Names}}' | grep -qx 'immich_postgres'; then
  echo "[ERROR] Container immich_postgres is not running"
  exit 1
fi

DB_USER="$(docker exec immich_postgres printenv POSTGRES_USER 2>/dev/null | tr -d '\r')"
DB_NAME="$(docker exec immich_postgres printenv POSTGRES_DB 2>/dev/null | tr -d '\r')"
if [[ -z "$DB_USER" || -z "$DB_NAME" ]]; then
  echo "[ERROR] Could not detect POSTGRES_USER/POSTGRES_DB from immich_postgres"
  exit 1
fi

echo "[STEP] Creating PostgreSQL dump ($DB_NAME)"
docker exec immich_postgres pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges | gzip -9 > "$DB_DUMP_FILE"

if ! gunzip -t "$DB_DUMP_FILE"; then
  echo "[ERROR] Dump integrity check failed: $DB_DUMP_FILE"
  exit 1
fi
echo "[OK] DB dump written: $DB_DUMP_FILE"

echo "[STEP] Archiving config and helper scripts"
tar -czf "$CFG_ARCHIVE" \
  --ignore-failed-read \
  -C "$ROOT_DIR" \
  docker-compose.yml \
  .env.immich-api \
  .env.backup-source \
  .env.backup-recovery \
  .env.immich-api.example \
  .env.backup-source.example \
  .env.backup-recovery.example \
  scripts/utilities/backup-immich.sh \
  scripts/utilities/recovery-drill.sh \
  scripts/utilities/enable-backup-recovery-routine.sh \
  BACKUP_SOURCE_SETUP.md \
  BACKUP_RECOVERY_RUNBOOK.md
echo "[OK] Config archive written: $CFG_ARCHIVE"

MEDIA_SOURCE="$MEDIA_SOURCE_OVERRIDE"
if [[ -z "$MEDIA_SOURCE" ]]; then
  MEDIA_SOURCE="$(docker inspect immich_server --format '{{range .Mounts}}{{if eq .Destination "/usr/src/app/upload"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || true)"
fi

DAY_UTC="$(date -u +%u)"
if [[ "$DAY_UTC" == "$MEDIA_SNAPSHOT_DAY_UTC" ]]; then
  if [[ -z "$MEDIA_SOURCE" || ! -d "$MEDIA_SOURCE" ]]; then
    echo "[WARN] Media snapshot skipped: source path not found (${MEDIA_SOURCE:-unset})"
  elif ! command -v rsync >/dev/null 2>&1; then
    echo "[WARN] Media snapshot skipped: rsync not installed"
  else
    SNAPSHOT_DIR="$MEDIA_DIR/$TODAY_UTC"
    mkdir -p "$SNAPSHOT_DIR"
    LINK_DEST=""
    if [[ -L "$MEDIA_DIR/latest" ]]; then
      LINK_DEST="$(readlink -f "$MEDIA_DIR/latest")"
    fi

    echo "[STEP] Creating weekly media snapshot from $MEDIA_SOURCE"
    if [[ -n "$LINK_DEST" && -d "$LINK_DEST" ]]; then
      rsync -a --delete --link-dest="$LINK_DEST/" "$MEDIA_SOURCE/" "$SNAPSHOT_DIR/"
    else
      rsync -a --delete "$MEDIA_SOURCE/" "$SNAPSHOT_DIR/"
    fi

    ln -sfn "$SNAPSHOT_DIR" "$MEDIA_DIR/latest"
    echo "[OK] Media snapshot written: $SNAPSHOT_DIR"
  fi
else
  echo "[INFO] Media snapshot skipped (today UTC day=$DAY_UTC, scheduled day=$MEDIA_SNAPSHOT_DAY_UTC)"
fi

echo "[STEP] Applying retention policy"
find "$DB_DIR" -type f -name 'immich-db-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete || true
find "$CFG_DIR" -type f -name 'immich-config-*.tgz' -mtime +"$RETENTION_DAYS" -delete || true
find "$MEDIA_DIR" -mindepth 1 -maxdepth 1 -type d -name '20*' -mtime +"$MEDIA_RETENTION_DAYS" -exec rm -rf {} + || true

echo "[OK] Backup routine complete"