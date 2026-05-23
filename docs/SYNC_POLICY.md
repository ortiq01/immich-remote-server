# Immich Runtime ↔ Repo Sync Policy

This repository is bound to CT112 and follows a **one-way sync policy**:

- Source of truth for runtime files: `/root/immich-app`
- Git working tree: `/root/immich-remote-server`
- Direction: **runtime -> repo only**

## Safety Rules

1. Never copy from repo into `/root/immich-app` automatically.
2. Exclude secrets and runtime-only data from version control:
   - `.env*`, `mcp-gateway.env.local`, `.secrets/`, `.state/`, `backups/`, `reports/`
3. Run preview first:
   - `DRY_RUN=1 scripts/utilities/sync-from-immich-app-safe.sh`
4. Apply only after review:
   - `DRY_RUN=0 scripts/utilities/sync-from-immich-app-safe.sh`

## Commit Flow (safe)

1. Preview sync (`DRY_RUN=1`)
2. Apply sync (`DRY_RUN=0`)
3. `git status`
4. Commit only expected changes
5. Push to `origin/main`
