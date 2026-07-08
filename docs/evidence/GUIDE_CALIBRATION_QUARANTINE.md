# Calibration Input Quarantine Report

Report on calibration inputs that were quarantined.

## Quarantine Reasons
| Reason | Description | Action |
|--------|-------------|--------|
| Low quality | Result quality flag is low or invalid | Exclude from calibration |
| Control failure | Controls did not pass | Regenerate or exclude |
| Missing fields | Required fields absent | Request resubmission |
| Orphan result | No matching prediction | Investigate mismatch |

## Report Format
```json
{
  "total_results": 20,
  "quarantined": 2,
  "reasons": [
    {"candidate_id": "C001", "reason": "control_failure"},
    {"candidate_id": "C002", "reason": "low_quality"}
  ],
  "passed_gate": false
}
```

## Rules
- Quarantined results must not be used for calibration.
- Quarantine reasons should be documented per result.
- If > 50% of results are quarantined, investigate the batch.
