# Immich Remote Server Ops

Self-hosted Immich operations repository for server CT112 (`192.168.1.109`).

## Purpose

This repo tracks the operational automation and documentation around the family Immich environment:

- Dashboard proxy UI and workflows
- Backup/recovery scripts and runbooks
- External source ingestion and routing
- Family timeline and album ops helpers

## Tracked

- `docker-compose.yml`
- `scripts/utilities/`
- Runbooks (`*_RUNBOOK.md`, setup docs)
- Safe `.example` env templates

## Not tracked (security/runtime)

- `.env*` secrets
- `.secrets/`
- `backups/`
- `reports/`
- `*.local.log`

## Notes

This repository is intended as operational source control, not as a replacement for running data volumes.
