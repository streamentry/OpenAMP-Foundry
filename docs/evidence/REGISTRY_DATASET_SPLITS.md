# Dataset Split Registry

Registry of dataset splits used in benchmarks and validation.

| Split | Dataset | Method | Ratio | Seed |
|-------|---------|--------|:-----:|:----:|
| 500-AMP cluster split | known_amps_500.csv | Cluster at 70% similarity | 374/500 clusters | 20260705 |
| Standard benchmark | known_amps.csv + random_background.csv | Random | 95/96 | 1729 |
| Cross-dataset | DRAMP + Swiss-Prot decoys | Source-based | 500/500 | 20260705 |

## Rules
- All splits must be registered here.
- Splits must be reproducible (fixed seed, documented method).
- Split methods must prevent leakage between train and test.
- If a split is updated, increment the version and document the change.
