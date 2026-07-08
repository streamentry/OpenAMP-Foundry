# Calibration Rollback Artifact Template

Template for documenting calibration rollbacks.

```markdown
# Calibration Rollback Record

## Date
YYYY-MM-DD

## Reason
Why the rollback was necessary.

## Previous State
- Weights before rollback: [weights]
- Gate verdict: [passed/failed]

## Current State
- Weights after rollback: [weights]
- Benchmarks affected: [list]

## Verification
- [ ] `make bench-gate` passes
- [ ] `make full-reproducibility-report` succeeds
- [ ] Rollback logged in decision log

## Related
- Link to decision log entry.
- Link to original calibration proposal.
```
