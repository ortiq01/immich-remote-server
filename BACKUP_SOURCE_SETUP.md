# Backup Share → Immich Inbox Setup (Command Center Handoff)

## Goal
Ingest photos from Windows share `\\192.168.1.107\backup` (Z:) into Immich and route new assets to album **`Family - Inbox Review`**.

---

## Current state (already prepared)
The repository is already pre-wired with automation and config:

- Docker mount targets added in `docker-compose.yml`:
  - `/mnt/backup_107/Fotos` → `/usr/src/app/external/backup/Fotos` (read-only)
  - `/mnt/backup_107/Podcast` → `/usr/src/app/external/backup/Podcast` (read-only)
- Inbox router prefixes updated in `.env.immich-api` to include backup paths.
- Helper files/scripts created:
  - `.env.backup-source`
  - `.env.backup-source.example`
  - `scripts/utilities/mount-backup-share.sh`
  - `scripts/utilities/register-backup-library.py`
  - `scripts/utilities/enable-backup-source-to-inbox.sh`

Only missing piece: valid SMB credentials and host-level mount permissions.

---

## Required inputs from Command Center
Fill these in `/root/immich-app/.env.backup-source`:

- `BACKUP_SMB_USERNAME`
- `BACKUP_SMB_PASSWORD`
- Optional: `BACKUP_SMB_DOMAIN` (if required in your AD/SMB environment)

Defaults are already set for:
- Host: `192.168.1.107`
- Share: `backup`
- Mount point: `/mnt/backup_107`
- Subfolders: `Fotos`, `Podcast`

---

## Setup steps

### 1) Populate backup env
Edit:
- `/root/immich-app/.env.backup-source`

Replace placeholders (`REPLACE_ME`) with real SMB credentials.

### 2) Run full enablement flow
From `/root/immich-app` run:

```bash
./scripts/utilities/enable-backup-source-to-inbox.sh
```

This performs:
1. Mount SMB share on host (`/mnt/backup_107`)
2. Restart Immich server container (to apply docker bind mounts)
3. Register or update external library import paths in Immich
4. Queue a library scan
5. Run inbox router once to push new assets into `Family - Inbox Review`

---

## Verification checklist

### A) SMB mounted and folders visible
```bash
mount | grep /mnt/backup_107
ls -la /mnt/backup_107
ls -la /mnt/backup_107/Fotos
ls -la /mnt/backup_107/Podcast
```

### B) Container sees mounted folders
```bash
docker exec immich_server sh -lc "ls -la /usr/src/app/external/backup && ls -la /usr/src/app/external/backup/Fotos && ls -la /usr/src/app/external/backup/Podcast"
```

### C) Immich library import paths include backup
```bash
python3 /root/immich-app/scripts/utilities/register-backup-library.py
```
Expected: either "Created library" or "Updated library" with both import paths.

### D) Inbox router runs successfully
```bash
python3 /root/immich-app/scripts/utilities/route_new_assets_to_inbox.py
```
Expected: non-error output and assets added (or explicit "No new assets to route").

### E) Final API check (optional)
```bash
python3 - <<'PY'
from pathlib import Path
from urllib import request
import json

env={}
for line in Path('/root/immich-app/.env.immich-api').read_text().splitlines():
    s=line.strip()
    if s and not s.startswith('#') and '=' in s:
        k,v=s.split('=',1); env[k.strip()]=v.strip()
base=env['IMMICH_URL'].rstrip('/')
key=env['IMMICH_API_KEY']
req=request.Request(base+'/api/libraries',headers={'x-api-key':key,'accept':'application/json'})
libs=json.loads(request.urlopen(req,timeout=20).read())
for l in libs:
    print(l.get('name'), l.get('importPaths'))
PY
```

---

## Operational note (persistence)
If host reboots are expected, ensure SMB mount is restored automatically.
Recommended options:
- systemd mount/unit, or
- `/etc/fstab` with secured credentials file and proper mount options.

Current helper script (`mount-backup-share.sh`) can be re-run safely and can be used in boot automation.

---

## Security notes
- Keep `.env.backup-source` permission-restricted (600).
- Credentials are written to `/root/immich-app/.secrets/backup-share.credentials` with mode 600.
- `.env.*` and `.secrets/` are gitignored.

---

## Rollback
If needed to remove backup source:
1. Remove backup mount lines from `docker-compose.yml`
2. Restart container:
```bash
docker compose up -d immich-server
```
3. Update/remove backup import paths from Immich library (via UI/API)
4. Unmount share:
```bash
umount /mnt/backup_107 || true
```

---

## Ownership
Prepared in repo by automation assistant. Command Center only needs to provide SMB credentials and execute one orchestration script.
