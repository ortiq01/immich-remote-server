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
DB_DIR="$BACKUP_ROOT/db-dumps"
LATEST_DUMP="$(ls -1t "$DB_DIR"/immich-db-*.sql.gz 2>/dev/null | head -1 || true)"

if [[ -z "$LATEST_DUMP" || ! -f "$LATEST_DUMP" ]]; then
  echo "[ERROR] No DB dump found in $DB_DIR"
  exit 1
fi

echo "[INFO] Recovery drill using dump: $LATEST_DUMP"
if ! gunzip -t "$LATEST_DUMP"; then
  echo "[ERROR] Backup file is corrupt: $LATEST_DUMP"
  exit 1
fi

TMP_NAME="immich_restore_drill_$$"
cleanup() {
  docker rm -f "$TMP_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[STEP] Starting temporary PostgreSQL container"
docker run -d \
  --name "$TMP_NAME" \
  -e POSTGRES_PASSWORD=drill \
  -e POSTGRES_USER=immich \
  -e POSTGRES_DB=immich \
  postgres:14 >/dev/null

for _ in $(seq 1 30); do
  if docker exec "$TMP_NAME" pg_isready -U immich -d postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! docker exec "$TMP_NAME" pg_isready -U immich -d postgres >/dev/null 2>&1; then
  echo "[ERROR] Temporary PostgreSQL did not become ready"
  exit 1
fi

echo "[STEP] Ensuring target database exists"
if ! docker exec "$TMP_NAME" psql -U immich -d postgres -tAc "select 1 from pg_database where datname='immich';" | grep -q 1; then
  docker exec "$TMP_NAME" psql -U immich -d postgres -c "create database immich;" >/dev/null
fi

echo "[STEP] Restoring dump into temporary PostgreSQL"
gunzip -c "$LATEST_DUMP" | docker exec -i "$TMP_NAME" psql -U immich -d immich >/dev/null

TABLE_COUNT="$(docker exec "$TMP_NAME" psql -U immich -d immich -tAc "select count(*) from information_schema.tables where table_schema='public';" | tr -d '[:space:]')"
if [[ -z "$TABLE_COUNT" || "$TABLE_COUNT" == "0" ]]; then
  echo "[ERROR] Restore drill failed (public table count=$TABLE_COUNT)"
  exit 1
fi

echo "[OK] Recovery drill passed (public table count=$TABLE_COUNT)"