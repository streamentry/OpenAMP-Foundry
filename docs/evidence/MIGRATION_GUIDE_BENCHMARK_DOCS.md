# Migration Guide: Benchmark Docs

When a benchmark changes or a new benchmark is added:

1. Update `docs/evidence/BENCHMARKING.md` with the new benchmark entry.
2. Update `docs/evidence/METRICS_CURRENT.md` with new results.
3. Add a Makefile target for the benchmark if needed.
4. Run the benchmark to verify it works.
5. Update the phony list in the Makefile if needed.
