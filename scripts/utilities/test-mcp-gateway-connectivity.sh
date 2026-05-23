#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-/root/immich-app/mcp-gateway.env.local}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[FAIL] Missing env file: $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

: "${MCP_GATEWAY_HOST:?MCP_GATEWAY_HOST missing}"
: "${MCP_GATEWAY_PORT:?MCP_GATEWAY_PORT missing}"

HOST="$MCP_GATEWAY_HOST"
PORT="$MCP_GATEWAY_PORT"

echo "Testing MCP gateway endpoint: ${HOST}:${PORT}"

if command -v nc >/dev/null 2>&1; then
  if nc -zvw2 "$HOST" "$PORT" >/dev/null 2>&1; then
    echo "[OK] TCP port is reachable"
  else
    echo "[FAIL] TCP port is not reachable"
    exit 2
  fi
else
  echo "[WARN] nc not available; using python socket test"
  python3 - <<PY
import socket, sys
host=${HOST@Q}; port=int(${PORT@Q})
try:
    s=socket.create_connection((host,port),timeout=2)
    s.close()
    print('[OK] TCP port is reachable')
except Exception as e:
    print('[FAIL] TCP port is not reachable:', type(e).__name__, e)
    sys.exit(2)
PY
fi

echo "[INFO] Protocol is raw TCP framed JSON-RPC; connectivity is confirmed."
echo "[INFO] To perform functional RPC calls, use the exact frame format expected by your gateway/client."