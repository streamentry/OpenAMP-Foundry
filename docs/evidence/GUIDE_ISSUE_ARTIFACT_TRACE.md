# Issue-to-Artifact Trace Field

How issues trace to their resulting artifacts.

## Format
Issues should include a `## Artifacts` section when resolved:
```markdown
## Artifacts
- PR: #NNN
- Doc: docs/evidence/EXAMPLE.md
- Script: scripts/example.py
- Test: tests/test_example.py
```

## Rules
- Every closed issue should trace to at least one artifact.
- Artifacts can be PRs, docs, scripts, tests, or configs.
- The trace helps future contributors understand why something exists.
- If an issue doesn't produce artifacts (investigation only), note that.
