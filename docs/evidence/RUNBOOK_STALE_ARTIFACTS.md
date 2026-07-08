# Maintainer Runbook: Stale Artifacts

When an artifact is stale:

1. Identify what's stale and why.
2. If it's a benchmark output, regenerate with `make bench-*`.
3. If it's a schema, update it to match current code.
4. If it's a config, update or document the discrepancy.
5. Update references in docs.
6. Add a test to prevent future staleness.
