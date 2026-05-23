# Tomorrow Breadcrumbs (2026-05-24)

A short restart plan so work can continue quickly.

## 1) First 5-minute health snapshot

Run:

```bash
cd /root/immich-remote-server
python3 scripts/utilities/onboarding_status_report.py
python3 scripts/utilities/review-cadence-check.py
python3 scripts/utilities/audit_duplicates.py
```

Check:
- Onboarding still healthy (`API keys working`, `shared albums`)
- Review backlog trend for `Family - Inbox Review`
- Duplicate audit report refreshed in `reports/`

## 2) Face/Explore progress check

In Immich Admin > Jobs:
- Verify `faceDetection` and `facialRecognition` are progressing
- Retry failed jobs if failed counts remain non-zero

In user accounts:
- Validate if face clusters start appearing in `Verkennen`

## 3) Duplicate cleanup plan (safe mode)

Do **not** delete directly.

- Use latest duplicate report (`reports/duplicates-audit-*.json`)
- Focus first on mixed-source groups (`/upload/` + `/external/backup/`)
- Produce a `safe delete candidates` list for review
- Only after approval: move selected duplicates to trash in small batches

## 4) Device onboarding close-out

Use `ONBOARDING_RUNBOOK.md` quick checklist with family members and mark final device-level completion.

## 5) Optional polish

- Tune backup library exclusions for thumbnail/cache folders if needed
- Commit and push only reviewed changes

## Notes

- Repo sync policy remains runtime -> repo only (`docs/SYNC_POLICY.md`).
- Keep secrets/runtime artifacts out of git (`.env*`, backups, reports, logs).
