# Benchmark Slice Registry

Registry of benchmark slices used in per-family analysis.

| Slice | Criteria | Count | Description |
|-------|----------|:-----:|-------------|
| highly_cationic | charge >= 4.0 | 73 | High positive charge |
| moderately_cationic | charge 2.0-3.9 | 115 | Moderate positive charge |
| cysteine_rich | >= 2 Cys | 153 | Disulfide-stabilized |
| low_charge | charge < 2.0 | 118 | Low or neutral charge |
| short | length <= 12 | 21 | Short sequences |
| proline_rich | Pro >= 15% | 20 | Proline-rich |

## Rules
- Slices must be mutually exclusive.
- Every benchmark candidate should belong to exactly one slice.
- Slice definitions should be documented in the benchmark card.
- New slices should be added when new candidate classes are identified.
