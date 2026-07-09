# Decision Log Index

## Purpose

This index lists all governance decision logs. Each log records a human-reviewed decision about pipeline behavior, release status, calibration, or safety policy.

## Index

| Date | Title | Decision Type | Outcome |
|------|-------|---------------|---------|
| 2026-07-06 | [Initial Recalibration Policy](DECISION_LOG_2026-07-06.md) | policy_approval | approved |

## Adding a new log

1. Create `DECISION_LOG_<YYYY-MM-DD>.md` following [`docs/operations/DECISION_RECORD_TEMPLATE.md`](../docs/operations/DECISION_RECORD_TEMPLATE.md).
2. Add a row to the index above.
3. Update this index when the log is added.

## Validation

Run `make decision-log-index` to regenerate this index from file metadata.
