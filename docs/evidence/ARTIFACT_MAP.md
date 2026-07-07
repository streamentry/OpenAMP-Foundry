# Artifact Documentation Map

Groups pipeline artifacts by category. Each entry links to the relevant
schema, documentation, and validation rules.

---

## Inputs

| Artifact | Format | Schema | Documentation |
|----------|--------|--------|---------------|
| Candidate CSV | CSV | `schemas/panel_csv.schema.json` | `docs/engineering/ARCHITECTURE.md` |
| Reference CSV | CSV | — | `docs/engineering/ARCHITECTURE.md` |
| Config YAML | YAML | — | `configs/pipeline.yaml` |

## Intermediate Outputs

| Artifact | Format | Schema | Documentation |
|----------|--------|--------|---------------|
| Scored candidates (ranked) | JSONL | — | `docs/evidence/EVIDENCE_CERTIFICATE.md` |
| Evidence certificates | JSON | `schemas/candidate.schema.json` | `docs/evidence/EVIDENCE_CERTIFICATE.md` |
| Run manifest | JSON | `schemas/run_manifest.schema.json` | `docs/engineering/RUN_MANIFEST_STANDARD.md` |
| Batch report | JSON | `schemas/batch_report.schema.json` | `docs/engineering/ARCHITECTURE.md` |

## Benchmark Outputs

| Artifact | Format | Documentation |
|----------|--------|---------------|
| Benchmark results | JSON | `docs/evidence/METRICS_CURRENT.md` |
| Cross-dataset results | JSON | `docs/evidence/BENCHMARK_GOVERNANCE.md` |
| Simulation ablation | JSON | `docs/evidence/SIMULATION_BENCHMARK.md` |
| Simulation baselines | JSON | `docs/evidence/SIMULATION_BENCHMARK.md` |
| Gate verdict | JSON | `docs/evidence/SIMULATION_BENCHMARK.md` |

## Lab and Review Artifacts

| Artifact | Format | Schema | Documentation |
|----------|--------|--------|---------------|
| Lab batch pack | ZIP | — | `docs/review/LAB_PARTNER_ONBOARDING.md` |
| Lab results | JSON | `schemas/lab_result.schema.json` | `docs/review/WET_LAB_HANDOFF.md` |
| Pass/fail verdict | JSON | — | `configs/wave1_pass_fail.yaml` |
| Negative result archive | CSV | — | `docs/evidence/NEGATIVE_RESULT_ARCHIVE.md` |
| Review request | JSON | — | `docs/review/EXPERT_REVIEW_PACK.md` |
| Decision log | JSON | `schemas/decision_log.schema.json` | `docs/trust/DATA_GOVERNANCE.md` |

## Release Artifacts

| Artifact | Format | Documentation |
|----------|--------|---------------|
| Full reproducibility report | JSON + MD | `docs/review/RELEASE_DRY_RUN_GUIDE.md` |
| Publication pack | MD | `docs/review/PUBLICATION_PACK.md` |
| Metrics snapshot | JSON | `docs/evidence/METRICS_CURRENT.md` |

## Planned (not yet implemented)

| Artifact | Status |
|----------|--------|
| Calibration intake report | Implemented |
| Recalibration gate verdict | Implemented |
| Weight update proposal | Implemented |
| Batch-2 selection manifest | Implemented |
| Model card | Planned |
| Dataset card | Planned |
