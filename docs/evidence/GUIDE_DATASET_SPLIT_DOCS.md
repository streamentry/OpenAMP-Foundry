# Dataset Split Documentation Guide

How to document dataset splits used in benchmarks.

## Required Information
- Split method (random, cluster, time-based)
- Split ratio (e.g., 80/20)
- Number of folds (for cross-validation)
- Whether stratification was used
- Random seed used for reproducibility

## Example
```markdown
## Split
- Method: Cluster split at 70% sequence similarity
- Result: 374 independent clusters
- Train: 305 clusters, Test: 69 clusters
- Random seed: 20260705
```
