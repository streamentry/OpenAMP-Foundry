# Advisory-to-Blocking Gate Promotion Records

Records of gates being promoted from advisory to blocking.

## Record Format
```json
{
  "gate": "benchmark_regression",
  "promoted_at": "2026-07-08",
  "reason": "Benchmark regression > 0.02 now blocks CI",
  "previous_status": "advisory",
  "new_status": "blocking",
  "decision_log_ref": "DR-2026-07-08-001"
}
```

## Current Gate Statuses
| Gate | Status | Description |
|------|:------:|-------------|
| Benchmark regression | blocking | AUROC drop > 0.02 fails CI |
| Doc link check | advisory | Broken links are reported, don't block |
| Claim check | advisory | Overclaiming language is reported |
| Test suite | blocking | Test failures block CI |

## Rules
- Promoting a gate from advisory to blocking requires a decision log entry.
- Demoting a gate from blocking to advisory requires project lead approval.
- Gate status changes should be announced in release notes.
