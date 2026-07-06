# Models Directory

## Purpose

This directory is for model and adapter metadata, not for unrestricted release of trained weights or sensitive artifacts.

No trained model weights are shipped in this starter repository by default.

Future model artifacts must follow:

- [`../MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md)
- [`../docs/MODEL_CARD_TEMPLATE.md`](../docs/MODEL_CARD_TEMPLATE.md)
- [`../docs/ARTIFACT_VERSIONING.md`](../docs/ARTIFACT_VERSIONING.md)
- [`../SAFETY.md`](../SAFETY.md)

## Default rule

Do not commit high-capability generator weights, sensitive predictor artifacts, restricted checkpoints, or candidate-generating systems without explicit release review.

## Recommended layout

```text
models/
  README.md
  manifests/           # model cards and version metadata
  adapters/            # adapter cards and metadata
  local/               # ignored local-only weights or caches
  deprecated/          # metadata for deprecated artifacts, no sensitive weights
```

## What may be committed

Usually safe to commit:

- model cards;
- adapter cards;
- metadata-only manifests;
- toy baseline parameters;
- transparent heuristic scorer descriptions;
- small test fixtures that do not increase sensitive capability;
- deprecation records.

Requires release review before commit:

- trained weights;
- generator artifacts;
- external predictor packages;
- high-throughput candidate-generation tools;
- checkpoints trained on restricted or sensitive data;
- artifacts that affect candidate release or ranking authority;
- artifacts that could be misread as proof of biological activity.

## Model card requirement

Every nontrivial model, scorer, simulator, predictor, generator, or external adapter should have a card before release or ranking authority.

A card should define:

- intended use;
- not-for list;
- inputs and outputs;
- training or calibration data;
- benchmark and cheap-baseline comparison;
- safety assessment;
- release decision;
- known limitations;
- failure behavior;
- review record.

Use [`../docs/MODEL_CARD_TEMPLATE.md`](../docs/MODEL_CARD_TEMPLATE.md).

## Release status labels

Use exact labels:

| Label | Meaning |
|---|---|
| `open` | Public release approved. |
| `staged` | Release in phases after review. |
| `metadata-only` | Card/summary public, raw artifact withheld. |
| `restricted` | Shared only with approved reviewers/partners. |
| `internal` | Kept local/private. |
| `do-not-release` | Release rejected. |

## External adapter rules

External adapters must:

- document whether they call a remote service;
- avoid silent network calls;
- fail closed if unavailable;
- return uncertainty or error status;
- document version and scope;
- avoid ranking authority unless benchmark gates support it;
- preserve sequence privacy expectations.

## Final standard

The models directory should make model release status and limitations clearer.

It should never become a place where sensitive weights or high-capability artifacts appear without review.
