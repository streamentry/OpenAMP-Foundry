# Negative-Result Learning Guide

How to learn from negative results.

## What Negative Results Teach Us
- Which candidate classes are overpredicted by the pipeline
- Which safety filters are insufficient
- Which benchmark assumptions are wrong
- Where the pipeline needs improvement

## Process
1. Record the negative result in the negative result archive.
2. Analyze why the result was negative (model error, data error, genuine negative).
3. If the model was wrong, identify what feature or weight contributed to the error.
4. Document the finding in the decision log.
5. If multiple negative results point to the same issue, prioritize fixing it.

## Rules
- Negative results are not failures — they are calibration data.
- Negative results must be preserved (see NEGATIVE_RESULT_ARCHIVE.md).
- Pipeline weights should not be changed based on a single negative result.
