---
name: Immich Development Workflow Rules
description: "Use when: developing or changing Immich automation, runbooks, onboarding flows, sync logic, or utility scripts in this repository."
applyTo: "scripts/**,docs/**,README.md,.github/copilot-instructions.md,.github/instructions/**"
---

# Immich Development Workflow Rules

## Scope

This overlay applies to day-to-day Immich development and operational automation for CT112.

## Core Development Model

- Runtime source: `/root/immich-app`
- Git source: `/root/immich-remote-server`
- Synchronization direction: runtime -> repo only

Never automate repo -> runtime overwrite without explicit operator approval.

## Change Safety Rules

1. Run read-only checks first (`docker compose ps`, logs, status reports).
2. For sync tasks, run:
   - `DRY_RUN=1 scripts/utilities/sync-from-immich-app-safe.sh`
   before any apply-mode run.
3. Keep `DELETE_MISSING=0` unless doing intentional cleanup windows.
4. Exclude runtime-only and secret files from commits:
   - `.env*`, `.secrets/`, `.state/`, `mcp-gateway.env.local`, local logs/reports.

## Duplicate / Ingestion Operations

- Always generate audit reports before removal.
- Require explicit confirmation before any destructive cleanup.
- Preserve family onboarding and timeline workflows unless specifically requested.

## Documentation Requirement

When changing behavior of scripts/automation:

- update relevant runbook/docs in the same change,
- include validation evidence in commit/PR notes,
- keep instructions aligned with the canonical all-server baseline.

## Done Criteria

A task is done when:

1. scripts lint/execute successfully for changed scope,
2. runtime health is unchanged or improved,
3. docs are aligned,
4. repo is pushed cleanly.
