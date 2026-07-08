# Maintainer Runbook: Benchmark Regression Triage

When a benchmark regression is reported:

1. Confirm the regression by re-running the benchmark.
2. Check recent commits for changes that could affect results.
3. Use `git bisect` to find the exact commit if needed.
4. Determine if the regression is acceptable (documented tradeoff) or a bug.
5. If a bug, open an issue and assign priority.
6. If a tradeoff, update METRICS_CURRENT.md and document the reason.
7. Update BENCHMARKING.md if the target needs adjustment.
