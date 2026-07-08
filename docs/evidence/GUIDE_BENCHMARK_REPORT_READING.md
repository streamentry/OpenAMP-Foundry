# Benchmark Report Reading Guide

How to read a benchmark report.

## Key Sections
| Section | What to Look For | Action if Concerning |
|---------|------------------|---------------------|
| AUROC | Overall discrimination | Check if > 0.70 |
| Per-family AUROC | Class-specific performance | Investigate weak classes |
| CI width | Precision of estimate | Wider CI = less data |
| Simulation verdict | Module status | Should be NO_IMPROVEMENT |
| Gate verdict | Regression check | Should pass |

## Red Flags
- AUROC drop > 0.02 from baseline.
- Any gate check failing.
- Unexpected simulation IMPROVEMENT.
- CI lower bound below 0.65.
