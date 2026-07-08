# Review Latency Tracking Ledger

Track review latency to identify bottlenecks.

## Metrics
| Metric | Target | How to Measure |
|--------|:------:|----------------|
| Time to first review | < 24h | Time from PR open to first review comment |
| Time to merge | < 72h | Time from PR open to merge |
| Review depth | All issues addressed | Count of review comments resolved |

## Ledger Format
```csv
pr_number,author,reviewer,opened_at,first_review_at,merged_at,comments
#NNN,name,name,datetime,datetime,datetime,N
```

## Rules
- Review latency is tracked monthly.
- If targets are consistently missed, investigate bottlenecks.
- Review latency data is used for process improvement, not blame.
