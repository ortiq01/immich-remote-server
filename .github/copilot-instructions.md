# AI Agent Instructions: Immich Remote Server (CT112)

**Version:** 1.0
**Last Updated:** 2026-05-23
**Last Verified:** 2026-05-23
**Scope:** canonical

## Canonical Alignment (All-Server Baseline)

This repository follows the same baseline instruction model used across your servers:

- Primary baseline authority: `/root/mcp-server-prox/.github/copilot-instructions.md`
- Canonical policy reference: `/root/mcp-server-prox/ai-instructions/CANONICAL_INSTRUCTION_POLICY.md`

Interpretation rule for this repo:

1. This file governs Immich repo runtime behavior.
2. If baseline policy conflicts with local assumptions, baseline guardrails win.
3. Immich-specific overlays in `.github/instructions/*.instructions.md` refine behavior for this repo.

## Big Picture

This repository tracks runtime-safe operations and development workflows for Immich on:

- Host/container: `CT112`
- IP: `192.168.1.109`
- Runtime source tree: `/root/immich-app`
- Git working tree: `/root/immich-remote-server`

Immich services are Docker Compose based and currently include:

- `immich-server` (`2283`)
- `immich-machine-learning`
- `immich_postgres`
- `immich_redis`

## Non-Negotiable Guardrails (Inherited Across Servers)

1. **MCP-first mindset** when MCP capability exists; use direct CLI only when needed.
2. **Read-first diagnostics** before any write/delete operations.
3. **No destructive ops without explicit confirmation** (mass delete, DB wipes, forced cleanup).
4. **Never commit secrets** (`.env*`, tokens, local env files, private keys).
5. **Prefer small, reversible changes** with clear verification.
6. **Use `runs-on: self-hosted`** for workflows that must access the homelab LAN.

## Immich-Specific Operating Rules

1. Keep runtime and repo synchronized using one-way safe sync:
   - `scripts/utilities/sync-from-immich-app-safe.sh`
2. Default sync mode must preserve repo-only files:
   - `DELETE_MISSING=0`
3. Run preview before applying:
   - `DRY_RUN=1` first, then `DRY_RUN=0` only after review.
4. Keep duplicate handling non-destructive by default:
   - generate candidate reports first, delete only with explicit approval.
5. Preserve external library safety:
   - maintain read-only external mounts where intended.

## Required Validation for Changes

Before closing any Immich task, verify:

1. `docker compose ps` shows healthy/expected services.
2. No secret files are staged (`git status --short`).
3. If sync/ingestion logic changed, run a dry-run sync and relevant utility checks.
4. Commit message is conventional (`feat:`, `fix:`, `docs:`, `chore:`).

## Instruction Overlays (Use by Scope)

- `.github/instructions/docker-compose.instructions.md`
- `.github/instructions/environment.instructions.md`
- `.github/instructions/immich-features.instructions.md`
- `.github/instructions/immich-development.instructions.md`

Use overlays when `applyTo` matches files being modified.

## Quick Operational Commands

- Onboarding snapshot: `python3 scripts/utilities/onboarding_status_report.py`
- Review cadence: `python3 scripts/utilities/review-cadence-check.py`
- Event albums: `python3 scripts/utilities/ensure-event-albums.py`
- Duplicate audit: `python3 scripts/utilities/audit_duplicates.py`
- Safe sync preview: `DRY_RUN=1 scripts/utilities/sync-from-immich-app-safe.sh`

## Completion Standard

A change is complete only when:

- behavior is validated,
- no secret leakage risk exists,
- commit is pushed,
- and the working tree is clean.
