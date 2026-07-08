# Review Packet Diff Report

Reports differences between review packet versions.

## Format
```diff
+ Added: SEED-020_VAR_004 (new candidate)
- Removed: SEED-015_VAR_002 (deprioritized)
~ Changed: LIMITATIONS_OVERVIEW.md (updated simulation section)
```

## When to Generate
- When a review packet is updated after initial review.
- When new candidates are added to the panel.
- When benchmark results change significantly.
- Before sending the final packet to reviewers.

## Rules
- Changes should be highlighted, not hidden.
- Reviewers should be notified of significant changes.
- The diff should be included in the review packet cover note.
- If changes are extensive, consider a new review cycle.
