# Immich Backup & Recovery Runbook

## Goal
Provide a repeatable backup and restore routine for Immich metadata + media with automatic scheduling and a weekly recovery drill.

## What is covered
- **Daily** PostgreSQL dump (metadata, albums, users, links)
- **Daily** config/script archive snapshot
- **Weekly** media snapshot (hard-link incremental via `rsync`)
- **Weekly** recovery drill that restores the latest DB dump into a temporary PostgreSQL container

## Files added
- `scripts/utilities/backup-immich.sh`
- `scripts/utilities/recovery-drill.sh`
- `scripts/utilities/enable-backup-recovery-routine.sh`
- `.env.backup-recovery.example`

## One-time setup

1) Optional: create settings file from template

```bash
cp /root/immich-app/.env.backup-recovery.example /root/immich-app/.env.backup-recovery
```

2) Make sure helper scripts are executable

```bash
chmod +x /root/immich-app/scripts/utilities/backup-immich.sh
chmod +x /root/immich-app/scripts/utilities/recovery-drill.sh
chmod +x /root/immich-app/scripts/utilities/enable-backup-recovery-routine.sh
```

3) Enable cron routine

```bash
/root/immich-app/scripts/utilities/enable-backup-recovery-routine.sh
```

## Schedule (UTC)
- **02:20 daily** → `backup-immich.sh`
- **02:40 Sunday** → `recovery-drill.sh`

Logs:
- `/root/immich-app/scripts/utilities/backup-immich.local.log`
- `/root/immich-app/scripts/utilities/recovery-drill.local.log`

## Manual run commands

```bash
/root/immich-app/scripts/utilities/backup-immich.sh
/root/immich-app/scripts/utilities/recovery-drill.sh
```

## Backup output layout

```text
/root/immich-app/backups/immich/
├── db-dumps/
│   └── immich-db-YYYYMMDDTHHMMSSZ.sql.gz
├── config/
│   └── immich-config-YYYYMMDDTHHMMSSZ.tgz
└── media-snapshots/
    ├── YYYYMMDD/
    └── latest -> YYYYMMDD
```

## Recovery procedure (real incident)

1) Stop Immich app containers:

```bash
cd /root/immich-app
docker compose stop immich-server immich-machine-learning
```

2) Ensure PostgreSQL is running and empty/target DB is prepared.

3) Restore latest DB dump:

```bash
LATEST="$(ls -1t /root/immich-app/backups/immich/db-dumps/immich-db-*.sql.gz | head -1)"
gunzip -c "$LATEST" | docker exec -i immich_postgres psql -U "$(docker exec immich_postgres printenv POSTGRES_USER)" -d "$(docker exec immich_postgres printenv POSTGRES_DB)"
```

4) Restore media snapshot if needed (copy/sync from snapshot back to upload path).

5) Start app containers:

```bash
cd /root/immich-app
docker compose up -d immich-server immich-machine-learning
```

6) Validate:
- login works
- albums load
- random sample assets open correctly

## Retention defaults
- DB + config: 14 days
- media snapshots: 56 days

Adjust in `.env.backup-recovery`.

## Safety notes
- Keep backup destination on reliable storage (prefer separate disk/NAS)
- Test restores regularly (weekly drill already included)
- Keep `.env.backup-recovery` and all `.env.*` files permission-restricted