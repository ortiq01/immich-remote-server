#!/usr/bin/env bash
# Launch the Immich photo dashboard.
# Usage: ./run-dashboard.sh [port]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/scripts/utilities/dashboard"
LOG="$SCRIPT_DIR/scripts/utilities/dashboard.local.log"
PORT="${1:-8088}"

export DASHBOARD_PORT="$PORT"
export DASHBOARD_BIND="0.0.0.0"

echo "[INFO] Starting dashboard on http://0.0.0.0:$PORT"
echo "[INFO] Log: $LOG"
echo "[INFO] Press Ctrl-C to stop."

exec python3 "$DASHBOARD_DIR/server.py" 2>&1 | tee -a "$LOG"
