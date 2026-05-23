# Family Ops Runbook (Cadence + Event Albums)

## Purpose
Keep family photo operations consistent with two lightweight automations:
- Daily review-cadence health check for `Family - Inbox Review`
- Monthly event-album structure bootstrap

## Scripts
- `scripts/utilities/review-cadence-check.py`
- `scripts/utilities/ensure-event-albums.py`
- `scripts/utilities/enable-family-ops-routine.sh`

## One-time activation

```bash
cd /root/immich-app
chmod +x scripts/utilities/enable-family-ops-routine.sh
./scripts/utilities/enable-family-ops-routine.sh
```

## Cron schedule (UTC)
- **07:10 daily** → review cadence check
- **06:05 on day 1 monthly** → event album bootstrap

## Logs
- `scripts/utilities/review-cadence.local.log`
- `scripts/utilities/event-albums.local.log`

## Config knobs (`.env.immich-api`)
- `REVIEW_CADENCE_ALBUM_NAME`
- `REVIEW_CADENCE_WARN_COUNT`
- `REVIEW_CADENCE_WARN_OLDEST_DAYS`
- `EVENT_ALBUM_TEMPLATES`
- `EVENT_ALBUM_YEARS`

## Operational guidance
- If cadence warns repeatedly, schedule a weekly family cleanup session.
- Keep event templates stable year-over-year to reduce clutter.
- Use current+next year auto mode unless you need historical backfill.
