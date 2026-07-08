# Benchmark Minimum Sample Policy

Minimum sample sizes for reliable benchmark results.

| Metric | Minimum Samples | Reason |
|:------:|:---------------:|--------|
| AUROC | 50 positives + 50 negatives | Bootstrap CI is reliable |
| Per-family AUROC | 20 per class | Smaller = wide CI |
| Hemolysis detection | 30 hemolytic + 30 selective | Moderate statistical power |
| Precision@k | k <= 10% of set | Small-k precision is noisy |

## Rules
- Benchmarks with fewer than minimum samples should be labeled `informational`.
- Informational benchmarks must not be used for regression gates.
- The benchmark gate should skip metrics that don't meet minimums.
- Document sample sizes alongside all benchmark results.
