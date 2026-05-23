#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_SCRIPT="$ROOT_DIR/scripts/utilities/backup-immich.sh"
DRILL_SCRIPT="$ROOT_DIR/scripts/utilities/recovery-drill.sh"

if [[ ! -x "$BACKUP_SCRIPT" || ! -x "$DRILL_SCRIPT" ]]; then
  echo "[ERROR] Required scripts are missing or not executable"
  echo "  - $BACKUP_SCRIPT"
  echo "  - $DRILL_SCRIPT"
  exit 1
fi

TMP_CRON="$(mktemp)"
(crontab -l 2>/dev/null || true) | grep -v 'immich-backup-recovery' > "$TMP_CRON"

{
  echo ""
  echo "# immich-backup-recovery"
  echo "20 2 * * * $BACKUP_SCRIPT >> $ROOT_DIR/scripts/utilities/backup-immich.local.log 2>&1 # immich-backup-recovery"
  echo "40 2 * * 0 $DRILL_SCRIPT >> $ROOT_DIR/scripts/utilities/recovery-drill.local.log 2>&1 # immich-backup-recovery"
} >> "$TMP_CRON"

crontab "$TMP_CRON"
rm -f "$TMP_CRON"

echo "[OK] Backup and recovery routine enabled in crontab"
echo "[INFO] Daily backup:    02:20 UTC"
echo "[INFO] Weekly drill:    Sunday 02:40 UTC"