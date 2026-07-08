# Cheap Baseline Explanation

A cheap baseline is a simple heuristic that any new method must beat.

## Examples in This Project
| Baseline | What It Tests | Current Performance |
|----------|---------------|:------------------:|
| Charge density | How much of AUROC is charge-driven | AUROC 0.8166 (beats ensemble) |
| Length | Sequence length alone | AUROC 0.5000 (no signal) |
| Selectivity proxy (charge + GRAVY) | Simple selectivity heuristic | Detection AUROC 0.5744 |
| Helix propensity | Chou-Fasman P alpha alone | Detection AUROC 0.6489 |

## Why They Matter
- Without cheap baselines, you can't tell if your complex model is adding value.
- A model that can't beat a cheap baseline is not ready for production.
- Cheap baselines set the minimum bar for acceptance.
