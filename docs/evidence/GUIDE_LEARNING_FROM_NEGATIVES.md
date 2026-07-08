# Negative-Result Learning Guide

How to extract value from negative results.

## What Negative Results Teach
- Which candidate classes are overpredicted
- Which safety markers are insufficient
- Which benchmark assumptions need revision
- Where the pipeline needs improvement

## Process
1. Record in the negative result archive.
2. Analyze whether the failure was model error, data error, or genuine negative.
3. Document findings in the decision log.
4. If multiple negatives point to the same issue, prioritize fixing it.

## Rules
- Negative results are calibration data, not failures.
- Never discard a negative result.
- Never change weights based on a single negative result.
