# Test Taxonomy

## Directory structure

| Directory | Covers |
|-----------|--------|
| `tests/benchmarks/` | Benchmark runners, regression gates, baseline comparisons |
| `tests/calibration/` | Calibration intake, gate, engine, policy version |
| `tests/evidence/` | Evidence certificate generation, schema validation, quality tiers |
| `tests/external/` | External predictor workflows, consensus |
| `tests/features/` | Physicochemical feature extraction |
| `tests/generators/` | Candidate generation |
| `tests/lab/` | Lab handoff, batch pack, result ingestion |
| `tests/novelty/` | Novelty scoring, broad checks |
| `tests/qc/` | Pre-synthesis QC, hemolysis risk |
| `tests/scoring/` | Individual scorer tests (activity, safety, ensemble, etc.) |
| `tests/selection/` | Ranking, diversity, pilot panel |
| `tests/simulation/` | Membrane proxy, structure proxy, external adapter, fail-closed |
| `tests/waves/` | Wave-specific gates, novelty audits |
| `tests/release/` | Reproducibility, manifest verification |
| `tests/active_learning/` | Batch-2 selector, recovery benchmarks |
| Top-level `tests/test_*.py` | Cross-cutting: doc links, claims, CLI, schemas, edge cases |

## Running tests

```bash
make test              # Full suite
make test -k <keyword> # Filter by keyword
make coverage          # Suite with coverage report
```

## Test count baseline

Current baseline: **2427 tests** (Loop 31). The regression gate in `test_test_count_regression.py`
warns if the count drops below 95% of this baseline.
