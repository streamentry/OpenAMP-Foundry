# Maintainer Review Dashboard

Metrics for tracking review performance.

## Dashboard Metrics
| Metric | Target | Collection |
|--------|:------:|------------|
| Open PRs | < 10 | `gh pr list` |
| PRs awaiting review | < 5 | `gh pr list --review-requested` |
| Median time to review | < 24h | Tracked in review latency ledger |
| Oldest unreviewed PR | < 72h | `gh pr list --sort created` |
| Issues without assignee | < 20 | `gh issue list --no-assignee` |

## How to Use
Run weekly. If any metric exceeds target, investigate bottlenecks.
