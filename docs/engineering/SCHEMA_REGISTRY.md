# Schema Registry

## Purpose

This document is the human-readable registry for OpenAMP Foundry schemas and structured artifacts.

OpenAMP becomes infrastructure when external humans, agents, labs, reviewers, and downstream tools can rely on stable artifact shapes.

## Prime rule

**Every important artifact needs a schema, an owner, a version, and a compatibility story.**

## Registry status

This registry is currently human-maintained.

Future work should add machine-readable schema metadata and automated schema checks.

## Core artifact types

| Artifact type | Purpose | Stability target | Source docs |
|---|---|---|---|
| Candidate evidence certificate | Explains why a candidate was selected, rejected, or reviewed. | High. | [`EVIDENCE_CERTIFICATE.md`](../evidence/EVIDENCE_CERTIFICATE.md) |
| Candidate manifest | Lists panel candidates, roles, hashes, release status, and proof level. | High. | [`WET_LAB_HANDOFF.md`](../review/WET_LAB_HANDOFF.md) |
| Run manifest | Records command, config, inputs, commit, versions, and hashes. | High. | [`RUN_MANIFEST_STANDARD.md`](RUN_MANIFEST_STANDARD.md) |
| Benchmark card | Documents benchmark purpose, data, baselines, metrics, caveats, and status. | High. | [`BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) |
| Dataset card | Documents dataset source, license, labels, preprocessing, bias, and release status. | High. | [`DATA_GOVERNANCE.md`](../trust/DATA_GOVERNANCE.md) |
| Model or adapter card | Documents intended use, not-for list, data, benchmarks, safety, and release status. | High. | [`MODEL_CARD_TEMPLATE.md`](../trust/MODEL_CARD_TEMPLATE.md) |
| External review packet | Bundles candidate, benchmark, safety, or adoption evidence for external review. | Medium-high. | [`EXTERNAL_REVIEW_PACKET.md`](../review/EXTERNAL_REVIEW_PACKET.md) |
| Result summary | Captures qualified outcome summaries at a safe abstraction level. | High. | [`CALIBRATION_POLICY.md`](../evidence/CALIBRATION_POLICY.md) |
| Calibration intake report | Joins predictions with structured result summaries. | High. | [`CALIBRATION_POLICY.md`](../evidence/CALIBRATION_POLICY.md) |
| Recalibration gate verdict | Records whether recalibration may be considered. | High. | [`CALIBRATION_POLICY.md`](../evidence/CALIBRATION_POLICY.md) |
| Disconfirming test record (`DTR-`) | Records one explicit attempt to falsify a computational claim and the resulting follow-up action. | Experimental. | [`DISCONFIRMING_TEST_RECORD_GUIDE.md`](../evidence/DISCONFIRMING_TEST_RECORD_GUIDE.md) |
| Decision record | Records important project decisions. | Medium-high. | [`DECISION_RECORD_TEMPLATE.md`](../operations/DECISION_RECORD_TEMPLATE.md) |

## Required schema metadata

Every schema or structured artifact family should define:

```yaml
artifact_type: stable-name
schema_file: path-or-TBD
current_version: MAJOR.MINOR.PATCH
status: experimental | stable | deprecated
owner: maintainer-role
release_status_field_required: true-or-false
proof_ladder_field_required: true-or-false
backward_compatibility: strict | best-effort | none
last_reviewed: YYYY-MM-DD
```

## Stability levels

### Experimental

Allowed for exploratory modules and draft artifacts.

Must be clearly labeled.

External users should not depend on stability.

### Stable

Required for core artifacts used by external reviewers, agents, or downstream tooling.

Breaking changes require version bump and migration notes.

### Deprecated

Still readable where practical, but not recommended for new use.

Must point to replacement.

## Compatibility rules

Do not silently:

- remove required fields;
- rename fields;
- change enum meaning;
- change proof-ladder semantics;
- change release-status meaning;
- treat restricted data as open;
- convert historical artifacts to stronger claims.

## Schema review checklist

Before adding or changing a schema, ask:

1. Who consumes this artifact?
2. What claim could be made from it?
3. Does it need release status?
4. Does it need proof-ladder level?
5. Does it need provenance fields?
6. Is it safe to publish examples?
7. Does it need backward compatibility?
8. Are docs and examples updated?
9. Does it require human review?

## Agent guidance

Agents may:

- add examples;
- add validators;
- add documentation;
- add optional fields with clear rationale;
- improve error messages.

Agents must not autonomously:

- remove required fields;
- change safety or release semantics;
- change proof-ladder meaning;
- break downstream compatibility;
- migrate restricted artifacts into public examples.

## Final standard

A schema should make OpenAMP easier to reuse without making it easier to misunderstand.
