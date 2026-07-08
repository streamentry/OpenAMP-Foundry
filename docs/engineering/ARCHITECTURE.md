# Architecture

## Purpose

This document describes the OpenAMP Foundry architecture as scientific infrastructure, not only software architecture.

The system is designed to make antimicrobial peptide candidate selection reproducible, auditable, safety-aware, and reviewable.

## Prime rule

**Architecture should make unsupported claims structurally difficult.**

A good architecture does not merely compute scores. It preserves provenance, uncertainty, baselines, release status, and review boundaries.

## Current production architecture

```text
candidate records
  -> loaders
  -> validation
  -> feature extraction
  -> independent scorers
  -> ensemble or configured ranker
  -> novelty checker
  -> safety-risk and feasibility checks
  -> diversity selector
  -> evidence certificates
  -> run manifest
  -> report
```

This is the current dry-lab candidate foundry.

It can support computational nomination and expert-review packaging.

It does not prove biological activity, safety, or clinical value.

## Trust architecture

The technical architecture is surrounded by a trust architecture:

```text
safe scope
  -> deterministic commands
  -> schemas
  -> run manifests
  -> evidence certificates
  -> benchmark cards
  -> proof ladder
  -> release status
  -> external review packets
  -> decision records
```

The trust layer is as important as the scoring layer.

## Longer-range architecture

The mature system should become a wet-lab compression engine:

```text
candidate generation or import
  -> dry-lab validation and ranking
  -> benchmark-challenged proxy models
  -> uncertainty-aware panel construction
  -> qualified external review
  -> structured result summaries
  -> calibration intake
  -> recalibration gate
  -> human decision record
  -> next-round selection
```

The purpose of added layers is not simulation theater.

The purpose is to improve which questions qualified humans choose to test next.

## Package map

| Package | Role |
|---|---|
| `openamp_foundry.data` | Loading and normalizing candidate/reference data. |
| `openamp_foundry.features` | Physicochemical feature extraction. |
| `openamp_foundry.scoring` | Activity-likeness, safety-risk, novelty, feasibility, ensemble, and related scorers. |
| `openamp_foundry.selection` | Ranking, diversity selection, and panel construction guards. |
| `openamp_foundry.evidence` | Evidence certificate generation and validation. |
| `openamp_foundry.reports` | Human-readable and machine-readable reports. |
| `openamp_foundry.benchmark` | Leakage checks, baseline comparisons, ablations, and benchmark scaffolding. |
| `openamp_foundry.generators` | Safe, bounded toy candidate generation. |
| `openamp_foundry.simulation` | Experimental virtual-assay proxy interfaces and ablations. |
| `openamp_foundry.calibration` | Structured result intake, recalibration gates, and proposal generation. |
| `openamp_foundry.active_learning` | Informative next-batch selection under uncertainty. |
| `openamp_foundry.analysis` | Diversity, similarity, structural-class, and audit helpers. |
| `openamp_foundry.qc` | Quality-control checks for pre-synthesis, hemolysis risk, and feasibility. |
| `openamp_foundry.utils` | I/O helpers, hashing, and shared utilities. |

Package behavior must remain aligned with docs under [`docs/PROJECT_INDEX.md`](../PROJECT_INDEX.md).

## Core artifacts

| Artifact | Purpose | Source doc |
|---|---|---|
| Evidence certificate | Explains candidate selection or rejection. | [`EVIDENCE_CERTIFICATE.md`](../evidence/EVIDENCE_CERTIFICATE.md) |
| Run manifest | Records command, inputs, config, commit, hashes, and claim boundaries. | [`RUN_MANIFEST_STANDARD.md`](RUN_MANIFEST_STANDARD.md) |
| Benchmark card | Documents benchmark purpose, data, baselines, and limits. | [`BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) |
| Dataset card | Documents source, license, labels, preprocessing, bias, and release status. | [`DATA_GOVERNANCE.md`](../trust/DATA_GOVERNANCE.md) |
| Model or adapter card | Documents model/adapter scope, benchmarks, limitations, and release status. | [`MODEL_CARD_TEMPLATE.md`](../trust/MODEL_CARD_TEMPLATE.md) |
| Review packet | Packages artifacts for qualified external review. | [`EXTERNAL_REVIEW_PACKET.md`](../review/EXTERNAL_REVIEW_PACKET.md) |
| Decision record | Records important governance decisions. | [`DECISION_RECORD_TEMPLATE.md`](../operations/DECISION_RECORD_TEMPLATE.md) |

## Threat model

The system is designed to reduce these failures:

| Failure | Mitigation |
|---|---|
| Cherry-picking candidates | Predefined selection rules, manifests, and evidence certificates. |
| Rediscovering known references | Novelty audit and nearest-neighbor reporting. |
| Unsafe optimization | Safety policy, release policy, safety-risk penalties, human review. |
| Model self-confirmation | Cheap-baseline comparisons and benchmark governance. |
| Dataset leakage | Leakage checks, dataset cards, split documentation. |
| Overclaiming | Proof ladder, claim review checklist, reviewer onboarding. |
| Simulation theater | Virtual assay scope, simulation benchmark, ranking gates. |
| Unreviewed release | Model release policy, release checklist, CODEOWNERS intent. |
| Agent drift | Agent operating contract, issue labels, human-agent collaboration model. |
| Artifact drift | Schema registry and artifact versioning policy. |

## Data flow

1. Load candidate records.
2. Normalize and validate records.
3. Reject invalid inputs with explicit errors.
4. Compute dry-lab features.
5. Score independently.
6. Apply configured ranking and safety-aware tradeoffs.
7. Audit novelty and similarity.
8. Select diverse candidates or panel roles.
9. Write structured outputs.
10. Generate evidence certificates.
11. Generate run manifest.
12. Generate human-readable report.
13. Validate artifacts where schemas exist.
14. Map claims to proof-ladder level.

## Result-learning flow

When qualified result summaries exist:

1. Ingest structured result summaries.
2. Join results to prior predictions.
3. Preserve controls, quality flags, and limitations at a safe abstraction level.
4. Generate calibration intake artifact.
5. Run recalibration gate.
6. Record whether recalibration may be considered.
7. Generate proposal if allowed.
8. Require human review and decision record.
9. Apply changes only after review.
10. Preserve rejections as useful evidence.

## Extension points

Future extension points include:

- scorers;
- external predictors;
- virtual-assay proxies;
- dataset loaders;
- benchmark modules;
- report generators;
- evidence-certificate fields;
- review packet generators;
- calibration proposal engines.

Every extension point should answer:

1. What does this component do?
2. What is it not for?
3. Does it need a card?
4. What baseline challenges it?
5. Can it affect ranking?
6. What is its release status?
7. What failure mode is expected?

Use [`ADAPTER_AUTHOR_GUIDE.md`](ADAPTER_AUTHOR_GUIDE.md) for external adapters.

## Adapter policy

Adapters must not silently:

- transmit sequences or sensitive metadata;
- download model artifacts;
- change ranking authority;
- hide unavailable dependencies;
- convert external scores into proof;
- publish restricted outputs.

Default adapter mode should be `off` or `info` until gates support stronger use.

## Schema and compatibility policy

Schemas and structured artifacts should follow:

- [`SCHEMA_REGISTRY.md`](SCHEMA_REGISTRY.md)
- [`ARTIFACT_VERSIONING.md`](ARTIFACT_VERSIONING.md)
- [`RUN_MANIFEST_STANDARD.md`](RUN_MANIFEST_STANDARD.md)

Breaking changes to core artifacts require compatibility review.

## Final standard

OpenAMP architecture is successful when a skeptical reviewer can inspect an artifact and understand how it was produced, what it supports, what it does not support, and what review is still required.
