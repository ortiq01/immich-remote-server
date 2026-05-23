#!/usr/bin/env bash
set -euo pipefail

# Loads local MCP gateway settings from mcp-gateway.env.local
# and exports them for downstream tools.

ENV_FILE="${1:-/root/immich-app/mcp-gateway.env.local}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[FAIL] Missing env file: $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

: "${MCP_GATEWAY_HOST:?MCP_GATEWAY_HOST missing in $ENV_FILE}"
: "${MCP_GATEWAY_PORT:?MCP_GATEWAY_PORT missing in $ENV_FILE}"

echo "[OK] Loaded MCP gateway env from: $ENV_FILE"
echo "[OK] Endpoint: ${MCP_GATEWAY_HOST}:${MCP_GATEWAY_PORT}"

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  echo "[OK] GITHUB_TOKEN present"
else
  echo "[WARN] GITHUB_TOKEN empty"
fi

if [[ -n "${PBS_TOKEN_ID:-}" && -n "${PBS_TOKEN_SECRET:-}" ]]; then
  echo "[OK] PBS tokens present"
else
  echo "[WARN] PBS tokens incomplete/empty"
fi

if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  echo "[OK] CLOUDFLARE_API_TOKEN present"
else
  echo "[WARN] CLOUDFLARE_API_TOKEN empty"
fi
