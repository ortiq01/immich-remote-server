#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.backup-source"
SECRETS_DIR="$ROOT_DIR/.secrets"
CREDS_FILE="$SECRETS_DIR/backup-share.credentials"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Missing $ENV_FILE"
  exit 1
fi

env_get() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2-
}

HOST="$(env_get BACKUP_SMB_HOST)"
SHARE="$(env_get BACKUP_SMB_SHARE)"
USER="$(env_get BACKUP_SMB_USERNAME)"
PASS="$(env_get BACKUP_SMB_PASSWORD)"
DOMAIN="$(env_get BACKUP_SMB_DOMAIN)"
VERS="$(env_get BACKUP_SMB_VERSION)"
MOUNT_POINT="$(env_get BACKUP_HOST_MOUNT_POINT)"
PHOTOS_SUBDIR="$(env_get BACKUP_PHOTOS_SUBDIR)"
PODCAST_SUBDIR="$(env_get BACKUP_PODCAST_SUBDIR)"

if [[ -z "$HOST" || -z "$SHARE" || -z "$MOUNT_POINT" ]]; then
  echo "[ERROR] BACKUP_SMB_HOST, BACKUP_SMB_SHARE, BACKUP_HOST_MOUNT_POINT are required"
  exit 1
fi

if [[ "$USER" == "REPLACE_ME" || "$PASS" == "REPLACE_ME" || -z "$USER" || -z "$PASS" ]]; then
  echo "[ERROR] Fill BACKUP_SMB_USERNAME and BACKUP_SMB_PASSWORD in $ENV_FILE"
  exit 1
fi

mkdir -p "$SECRETS_DIR" "$MOUNT_POINT"
chmod 700 "$SECRETS_DIR"

{
  echo "username=$USER"
  echo "password=$PASS"
  [[ -n "$DOMAIN" ]] && echo "domain=$DOMAIN"
} > "$CREDS_FILE"
chmod 600 "$CREDS_FILE"

if mountpoint -q "$MOUNT_POINT"; then
  echo "[INFO] Already mounted: $MOUNT_POINT"
else
  echo "[INFO] Mounting //${HOST}/${SHARE} -> $MOUNT_POINT"
  mount -t cifs "//${HOST}/${SHARE}" "$MOUNT_POINT" -o "credentials=${CREDS_FILE},vers=${VERS},iocharset=utf8,uid=0,gid=0,dir_mode=0755,file_mode=0644"
fi

echo "[INFO] Checking required subfolders"
for d in "$PHOTOS_SUBDIR" "$PODCAST_SUBDIR"; do
  if [[ -d "$MOUNT_POINT/$d" ]]; then
    echo "  [OK] $MOUNT_POINT/$d"
  else
    echo "  [WARN] Missing: $MOUNT_POINT/$d"
  fi
done

echo "[OK] Backup share mount step complete"
