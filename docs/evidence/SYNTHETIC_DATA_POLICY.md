# Synthetic Data and Toy Fixture Policy

## Purpose

Synthetic data and toy fixtures are essential for testing, demonstration,
and workflow development. They must never be mistaken for real biological
evidence.

## Definitions

| Term | Meaning | Example |
|------|---------|---------|
| **Toy fixture** | Minimal dataset shipped with the repo for demo/testing | `examples/sequences/demo_candidates.csv` |
| **Synthetic data** | Programmatically generated data mimicking real outputs | `examples/lab_results_generator.py` output |
| **Real data** | Data from qualified wet-lab experiments | — (none yet) |

## Labeling Requirements

Every synthetic or toy data file MUST contain a clear label:

- **CSV/JSONL files**: Include a `disclaimer` or `source` field with `SYNTHETIC` or `demo`.
- **JSON files**: Include `"disclaimer": "SYNTHETIC — replace with real data"`.
- **Scripts generating synthetic data**: Output MUST include a disclaimer in every file.

## Allowed Use

- CI/CD testing and regression detection
- Developer onboarding and demonstration
- Workflow prototyping and integration testing
- Benchmark development (when labeled separately from real benchmarks)
- Documentation examples

## Forbidden Use

- Representing synthetic results as biological evidence
- Including synthetic data in publication support packages without clear labeling
- Using toy fixtures to calibrate or tune production scorers
- Claiming proof-ladder advancement based on synthetic data

## Quarantine

Synthetic data files live in `examples/` or `outputs/` (git-ignored).
They are never stored in `data/` or `schemas/` to prevent accidental
inclusion in real-data workflows.

## Relationship to Proof Ladder

Synthetic data sits at **Level 0** (unvalidated). It cannot upgrade any
proof-ladder claim. A result demonstrated only on synthetic data must be
described as "demonstrated on synthetic data" with no implication of
biological validity.

## Related Documents

- `docs/evidence/EVIDENCE_CERTIFICATE.md` — certificate schema (disclaimer field)
- `docs/evidence/PROOF_LADDER.md` — evidence level definitions
- `docs/evidence/NEGATIVE_RESULT_ARCHIVE.md` — negative result handling
- `docs/trust/DATA_GOVERNANCE.md` — data licensing and governance
