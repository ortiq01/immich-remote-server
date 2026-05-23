#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY_SCRIPT="$ROOT_DIR/scripts/utilities/enable_family_timeline.py"
ENV_FILE="$ROOT_DIR/.env.immich-api"
FAMILY_ENV_FILE="$ROOT_DIR/.env.family-timeline"

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "[ERROR] Missing $PY_SCRIPT"
  exit 1
fi

echo "Family timeline setup wizard"
echo "This must be run ONCE per user account using that user's API key."
echo ""

# Optional non-interactive mode via .env.family-timeline
# Expected keys per member:
#   FAMILY_MEMBER_1_EMAIL=...
#   FAMILY_MEMBER_1_API_KEY=...
#   FAMILY_MEMBER_1_EXCLUDE_SHARED_WITH_EMAILS=admin@example.com,other@example.com
#   FAMILY_MEMBER_2_EMAIL=...
#   FAMILY_MEMBER_2_API_KEY=...
#   ...
if [[ -f "$FAMILY_ENV_FILE" ]]; then
  echo "[INFO] Found $FAMILY_ENV_FILE"
  ran_any=false
  for i in $(seq 1 20); do
    email_var="FAMILY_MEMBER_${i}_EMAIL"
    key_var="FAMILY_MEMBER_${i}_API_KEY"
    exclude_var="FAMILY_MEMBER_${i}_EXCLUDE_SHARED_WITH_EMAILS"

    email="$(grep -E "^${email_var}=" "$FAMILY_ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^ *//;s/ *$//')"
    api_key="$(grep -E "^${key_var}=" "$FAMILY_ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^ *//;s/ *$//')"
    exclude_emails="$(grep -E "^${exclude_var}=" "$FAMILY_ENV_FILE" | head -1 | cut -d= -f2- | sed 's/^ *//;s/ *$//')"

    [[ -z "$email" ]] && continue
    [[ "$email" =~ ^# ]] && continue

    if [[ -z "$api_key" || "$api_key" == "REPLACE_ME" ]]; then
      echo "[WARN] $key_var empty for $email, skipping"
      continue
    fi

    ran_any=true
    echo "[INFO] Applying family timeline settings for $email from env file ..."
    cmd=(python3 "$PY_SCRIPT" --env-file "$ENV_FILE" --api-key "$api_key")
    if [[ -n "$exclude_emails" ]]; then
      echo "[INFO] Outbound exclusion(s) for $email: $exclude_emails"
      cmd+=(--exclude-shared-with-emails "$exclude_emails")
    fi

    if "${cmd[@]}"; then
      echo "[OK] Completed for $email"
    else
      echo "[WARN] Setup had issues for $email"
    fi
    echo ""
  done

  if [[ "$ran_any" == "true" ]]; then
    echo "[DONE] Processed entries from $FAMILY_ENV_FILE"
    exit 0
  fi

  echo "[INFO] No usable API key entries found in $FAMILY_ENV_FILE, switching to interactive mode."
  echo ""
fi

while true; do
  read -r -p "User email (leave empty to stop): " email
  [[ -z "$email" ]] && break

  echo "Paste API key for $email (input hidden):"
  read -r -s api_key
  echo ""

  if [[ -z "$api_key" ]]; then
    echo "[WARN] No API key entered, skipping $email"
    continue
  fi

  echo "[INFO] Applying family timeline settings for $email ..."
  if python3 "$PY_SCRIPT" --env-file "$ENV_FILE" --api-key "$api_key"; then
    echo "[OK] Completed for $email"
  else
    echo "[WARN] Setup had issues for $email"
  fi
  echo ""
done

echo "[DONE] Wizard finished."
