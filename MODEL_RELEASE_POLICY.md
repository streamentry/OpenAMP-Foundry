# Model and Artifact Release Policy

## Purpose

This policy defines how OpenAMP Foundry releases models, scorers, predictors, generators, adapters, candidate panels, benchmark artifacts, and other capability-relevant outputs.

OpenAMP is open by default for infrastructure.

It is reviewed by default for sensitive biological capability.

## Prime rule

**Do not call an artifact open source if it cannot be safely released without review.**

Use precise language:

- open source;
- open infrastructure;
- staged release;
- restricted release;
- metadata-only release;
- controlled access;
- responsible open science;
- do not release.

## Open by default

The following are intended to be open:

- data loaders;
- benchmark code;
- schemas;
- validators;
- transparent baseline scorers;
- evidence certificate tooling;
- safety filters;
- documentation;
- toy/demo data;
- review packet formats;
- pre-registration templates;
- non-sensitive benchmark cards;
- non-sensitive issue and PR templates.

## Review before release

The following require release review:

- model weights;
- generator artifacts;
- external predictor integrations;
- non-toy candidate panels;
- generated candidate lists;
- non-toy biological datasets;
- partner result summaries;
- wet-lab-facing summaries;
- high-throughput output artifacts;
- artifacts that could be misread as biological proof;
- artifacts that could materially increase misuse capability.

## Restricted, delayed, or withheld by default

The following are not released by default:

- high-throughput generator weights;
- objective functions that could optimize harmful biological properties;
- unscreened top candidate lists;
- model checkpoints trained on sensitive or restricted data;
- restricted partner data;
- artifacts that include unsafe operational detail;
- tooling that materially increases misuse capability.

## Release decision categories

| Decision | Meaning |
|---|---|
| Open release | Artifact can be public as-is. |
| Staged release | Release in phases after review or redaction. |
| Metadata-only release | Publish card/summary, not raw artifact. |
| Restricted release | Share only with approved reviewers or partners. |
| Internal only | Keep local/private until evidence or safety changes. |
| Do not release | Release is inappropriate. |

## Required release review fields

Before releasing any sensitive model or artifact, record:

```yaml
artifact_id: stable-id
artifact_type: model | scorer | generator | adapter | candidate_panel | dataset | result_summary | other
version: version-or-date
created_at: YYYY-MM-DD
intended_use: text
not_for: list
release_decision: open | staged | metadata-only | restricted | internal | do-not-release
safety_review_required: true-or-false
safety_reviewer: role-or-name
proof_ladder_limit: level-or-null
data_sources: list
license_status: text
known_limitations: list
misuse_risks: list
mitigations: list
review_date: YYYY-MM-DD
```

## Release review questions

Before releasing any model, candidate batch, dataset, or sensitive artifact, answer:

1. What is the intended use?
2. What is the artifact explicitly not for?
3. Could this artifact be used to increase biological harm?
4. Does it include or enable unsafe optimization?
5. Does it publish unscreened candidates?
6. Does it depend on restricted data?
7. Can it be used responsibly without domain expertise?
8. Are limitations and proof level clear?
9. Does it include safety filters by default?
10. Is staged, restricted, metadata-only, or no release safer?
11. Should an external domain or safety expert review it first?
12. Is the decision recorded in a review packet or release note?

## Model card requirement

Every nontrivial model, scorer, simulator, predictor, generator, or adapter should have a card before release or ranking authority.

Use `docs/MODEL_CARD_TEMPLATE.md`.

A model card must include:

- intended use;
- not-for list;
- inputs and outputs;
- training or calibration data;
- benchmark and baseline comparison;
- safety assessment;
- release decision;
- known limitations;
- failure behavior;
- review record.

## Candidate release requirement

Generated candidate lists are not automatically public artifacts.

Before releasing candidate panels, require:

- candidate manifest;
- evidence certificates;
- proof-ladder level;
- novelty audit;
- safety-risk review;
- baseline comparison;
- release status;
- external review packet if partner-facing;
- safety review if non-toy.

## External adapter requirement

External adapters must:

- clearly state whether they run locally or call a third-party service;
- not silently transmit sequences or sensitive metadata;
- fail closed when unavailable;
- return uncertainty or error status;
- document version and scope;
- include a model/adapter card;
- avoid ranking authority unless benchmark gates support it.

## Dataset release requirement

Non-toy datasets require:

- dataset card;
- license status;
- redistribution status;
- citation requirements;
- label definitions;
- known biases;
- intended use;
- safety-release status.

Use `docs/DATA_GOVERNANCE.md`.

## Labeling

Do not call restricted model artifacts “open source.”

Use accurate labels:

- “open infrastructure” for code/schemas/validators;
- “responsible release” for staged artifacts;
- “metadata-only release” for cards without raw artifacts;
- “restricted release” for approved-reviewer access;
- “not released” when release is unsafe or premature.

## Review outcomes

Allowed outcomes:

- approve open release;
- approve staged release;
- approve metadata-only release;
- approve restricted review release;
- require more evidence;
- require safety review;
- reject release;
- deprecate artifact;
- archive internally.

## Final standard

OpenAMP should be maximally open where openness creates public infrastructure and deliberately conservative where release would create avoidable biological, scientific, or reputational risk.
