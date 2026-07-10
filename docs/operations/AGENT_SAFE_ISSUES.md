# Agent-Safe Issue Examples (D2)

This document shows how to write GitHub issues that are safe for agents to pick up and implement without human clarification.

An agent-safe issue has:
1. A clear, bounded scope (one schema, one test file, one doc).
2. No ambiguity about what "done" means.
3. An explicit statement that the task is dry-lab only and does not touch safety, release, or calibration policy.
4. A test verification step.

## Template

```markdown
## Summary

[One sentence: what schema/test/doc to add and why.]

## Scope

- [ ] `src/openamp_foundry/<module>/<file>.py`
- [ ] `tests/<module>/test_<file>.py` (63 tests)
- [ ] `tests/test_test_count_regression.py` (BASELINE: <N> → <N+63>)

## Acceptance criteria

- All 63 tests pass: `python -m pytest tests/<module>/test_<file>.py -v`
- Schema validates a well-formed record with zero errors.
- Schema rejects at least 5 invalid records with specific error messages.
- `dry_lab_only=True` is enforced.
- `make agent-check` passes.

## Safety classification

- [ ] This task does NOT touch safety policy, calibration policy, release status, or proof-ladder thresholds.
- [ ] This task does NOT introduce real (non-toy) candidate data.
- [ ] This task does NOT modify benchmark thresholds.

## What NOT to do

- Do not add a CLI command (separate issue).
- Do not modify existing schemas (separate issue).
- Do not change any `BASELINE` value other than the one in `tests/test_test_count_regression.py`.
```

## Examples

### Good: well-scoped schema issue

```markdown
## Summary

Add a schema for batch-level rejection summaries (BRS-). Each record summarizes
how many candidates were rejected in a batch and why, linking to NRR- entries.

## Scope

- [ ] `src/openamp_foundry/evidence/batch_rejection_summary.py`
- [ ] `tests/evidence/test_batch_rejection_summary.py` (63 tests)
- [ ] `tests/test_test_count_regression.py` (BASELINE: 8410 → 8473)

## Acceptance criteria

- BRS- prefix validation
- `total_rejected` and `n_with_nrr` consistency check
- `dry_lab_only=True` enforced
- `make agent-check` passes

## Safety classification

- [x] Does not touch safety policy or calibration
- [x] No real candidate data
- [x] No benchmark threshold changes
```

### Bad: unsafe or under-specified issue

```markdown
## Title: Improve the pipeline

Add some improvements to the scoring pipeline. Maybe add a new model.
Test it and make sure it's better.
```

This is unsafe for agents because:
- "Some improvements" is unbounded scope.
- "New model" might touch benchmark thresholds (requires human review).
- "Better" has no measurable criterion.
- No safety classification.

## Agent behavior on receiving an issue

An agent that receives an issue should:
1. Check `AGENT_TASKS.json` to classify the task.
2. If the task is in a `forbidden_zone`, stop and request human review.
3. Verify the issue has a safety classification section.
4. If no safety section exists, treat the issue as requiring human review before proceeding.
