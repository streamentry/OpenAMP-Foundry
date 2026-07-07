# Scenario Playbook: Benchmark Regression

**Scenario:** A benchmark AUROC drops by more than 0.02.

## Steps

1. Verify the regression is real (not a fluke) by running the benchmark twice.
2. Check what changed since the last passing run (`git log --oneline`).
3. Isolate the change that caused the regression using `git bisect` if needed.
4. If the regression is caused by a deliberate tradeoff (e.g., safety penalty increase), document the tradeoff.
5. If the regression is unintended, fix or revert the change.
6. Update `docs/evidence/METRICS_CURRENT.md` with the new value.
7. Run `make bench-gate` to verify the fix.
