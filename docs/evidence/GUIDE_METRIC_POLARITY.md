# Metric Polarity Guide

Metric polarity defines whether higher or lower values are better.

## Common Polarity
| Metric | Polarity | Meaning |
|--------|:--------:|---------|
| AUROC | Higher is better | Better discrimination |
| AUPRC | Higher is better | Better precision-recall |
| Recall@k | Higher is better | More positives in top k |
| Disagreement | Lower is better | Better model consensus |
| Charge bias | Lower is better | Less charge-dependence |
| Uncertainty | Lower is better | More confident prediction |
| Hemolysis risk | Lower is better | Less predicted toxicity |

## Importance
Knowing polarity prevents misinterpretation. A low AUROC is bad;
a low disagreement is good. Always check polarity before interpreting a metric.
