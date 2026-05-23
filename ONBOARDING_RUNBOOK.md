# Family Onboarding Runbook

## Goal
Onboard all family members and devices in a repeatable way, with API-verifiable checks where possible.

## Automated status report

Use:

```bash
cd /root/immich-remote-server
python3 scripts/utilities/onboarding_status_report.py
```

This writes a JSON report to `reports/onboarding-status-*.json` and prints a summary.

## Manual device checklist (per user)

1. Install Immich app (iOS/Android)
2. Log in with personal account
3. Enable backup (Background + Wi-Fi preferred)
4. Confirm first upload appears in timeline
5. Confirm shared family albums are visible

## What "Done" means

For each family member:
- Account exists in Immich
- API key works
- Inbound partner timeline is fully enabled
- Shared album visibility is healthy (>= 2)
- Device backup tested on at least one device

## Notes

- In current shared model, non-owner users can have `peopleCount=0` in native Explore even with shared albums.
- Use dashboard shared-person workflow for family-level filtering while ownership/indexing remains centralized.
