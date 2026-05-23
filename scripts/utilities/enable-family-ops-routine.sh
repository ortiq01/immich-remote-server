#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CADENCE_SCRIPT="$ROOT_DIR/scripts/utilities/review-cadence-check.py"
EVENT_SCRIPT="$ROOT_DIR/scripts/utilities/ensure-event-albums.py"

if [[ ! -f "$CADENCE_SCRIPT" || ! -f "$EVENT_SCRIPT" ]]; then
  echo "[ERROR] Required scripts are missing"
  echo "  - $CADENCE_SCRIPT"
  echo "  - $EVENT_SCRIPT"
  exit 1
fi

chmod +x "$CADENCE_SCRIPT" "$EVENT_SCRIPT"

echo "[STEP] Run event album bootstrap now"
python3 "$EVENT_SCRIPT"

echo "[STEP] Run review cadence check now"
python3 "$CADENCE_SCRIPT"

TMP_CRON="$(mktemp)"
(crontab -l 2>/dev/null || true) | grep -v 'immich-family-ops' > "$TMP_CRON"

{
  echo ""
  echo "# immich-family-ops"
  echo "10 7 * * * /usr/bin/env python3 $CADENCE_SCRIPT >> $ROOT_DIR/scripts/utilities/review-cadence.local.log 2>&1 # immich-family-ops"
  echo "5 6 1 * * /usr/bin/env python3 $EVENT_SCRIPT >> $ROOT_DIR/scripts/utilities/event-albums.local.log 2>&1 # immich-family-ops"
} >> "$TMP_CRON"

crontab "$TMP_CRON"
rm -f "$TMP_CRON"

echo "[OK] Family ops routine enabled"
echo "[INFO] Daily cadence check: 07:10 UTC"
echo "[INFO] Monthly event album bootstrap: day 1 at 06:05 UTC"
