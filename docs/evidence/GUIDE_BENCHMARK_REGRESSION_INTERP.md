# Benchmark Regression Interpretation Guide

How to interpret a benchmark regression.

## What to Check
1. Is the regression > 0.02 AUROC? (gate threshold)
2. Is the regression in the primary benchmark or a slice?
3. Does the regression affect all classes or just one?
4. Is the change intentional (tradeoff) or accidental (bug)?

## Common Causes
| Cause | Pattern | Action |
|-------|---------|--------|
| Safety penalty increase | AUROC drops, safety improves | Accept tradeoff |
| Feature change | One class regresses | Isolate the class |
| Data change | Cross-dataset validation | Update benchmark |
| Bug | Unexpected drop everywhere | Fix and revert |

## Response
- Acceptable regression (< 0.02): Document and proceed.
- Unacceptable regression (> 0.02): Investigate and fix.
- Deliberate tradeoff: Document the rationale in the decision log.
