# Artifact Versioning and Compatibility

## Purpose

This document defines how OpenAMP Foundry versions schemas, certificates, manifests, benchmark cards, review packets, result summaries, and release artifacts.

A project becomes infrastructure only when outsiders can build on its artifacts without fearing silent breakage.

## Prime rule

**Any artifact that external humans, agents, labs, reviewers, or downstream tools may consume needs a version and compatibility story.**

## Artifact classes

| Class | Examples | Compatibility expectation |
|---|---|---|
| Core schemas | candidate certificate, lab result, decision log | Strong backward compatibility. |
| Review artifacts | external review packet, expert review pack, release review | Stable structure, extensible fields. |
| Benchmark artifacts | benchmark cards, metric snapshots, gate outputs | Stable required fields, versioned metrics. |
| Candidate artifacts | manifests, ranked JSONL, panel summaries | Stable IDs and provenance fields. |
| Calibration artifacts | intake reports, gate verdicts, decision logs | Strong auditability and immutability. |
| Demo artifacts | toy examples and tutorial outputs | Can evolve, but should be labeled. |
| Experimental artifacts | simulation outputs, exploratory reports | May change, must be marked experimental. |

## Versioning levels

Use semantic intent, not only package version.

### Major version

Increment when:

- required fields are removed or renamed;
- interpretation changes;
- old consumers may silently misread the artifact;
- proof-ladder or safety meaning changes;
- release status semantics change.

### Minor version

Increment when:

- optional fields are added;
- new enum values are added safely;
- new metadata appears;
- backward-compatible validation rules are added.

### Patch version

Increment when:

- typos are fixed;
- descriptions improve;
- examples change;
- validation error messages improve;
- non-semantic formatting changes.

## Required metadata

Every serious artifact should include:

```yaml
artifact_type: candidate_certificate | candidate_manifest | benchmark_card | review_packet | result_summary | calibration_verdict | decision_log
artifact_version: MAJOR.MINOR.PATCH
created_at: YYYY-MM-DD
created_by: human-or-agent-or-tool
repo_commit: git-sha
pipeline_version: version-or-null
schema_version: version-or-null
release_status: open | staged | restricted | internal | do-not-release
proof_ladder_level: integer-or-null
```

If an artifact cannot include all fields, document why.

## Compatibility promises

### Candidate IDs

Candidate IDs should be stable within a panel or batch.

If a candidate is renamed, provide an alias map.

### Sequence visibility

Some artifacts may include sequence hashes or safe references instead of full sequences.

Consumers must not assume full sequence visibility.

### Evidence certificates

Evidence certificates should remain readable across versions.

If old fields are replaced, provide migration guidance.

### Benchmark cards

Benchmark cards should preserve the meaning of historical results.

If a benchmark changes enough that metrics are not comparable, create a new benchmark ID.

### Calibration decisions

Calibration decision artifacts are historical records.

Do not mutate past decisions to fit new schemas. Add migration wrappers or append new decision records.

## Experimental artifacts

Experimental artifacts must say they are experimental.

They should include:

- status: experimental;
- allowed use;
- forbidden use;
- known instability;
- whether they can affect ranking;
- when they should be deprecated.

Virtual-assay outputs are experimental unless the relevant gate says otherwise.

## Deprecation policy

When deprecating an artifact:

1. Add a `deprecated: true` field where possible.
2. Add `deprecated_at` date.
3. Add `replacement_artifact` if one exists.
4. Explain why the artifact is deprecated.
5. Keep readers or validators for at least one major cycle where practical.
6. Update `docs/PROJECT_INDEX.md` if the artifact was user-facing.

## Migration policy

Migration scripts should:

- never invent missing scientific evidence;
- never strengthen proof-ladder level;
- never convert restricted artifacts into open artifacts;
- preserve original creation time and commit when available;
- record migration time and tool version;
- emit warnings for ambiguous fields.

## Schema registry

The project should eventually maintain a registry of schemas:

```yaml
schemas:
  candidate.schema.json:
    artifact_type: candidate_certificate
    current_version: TBD
    status: stable | experimental | deprecated
    owner: maintainer-role
  lab_result.schema.json:
    artifact_type: result_summary
    current_version: TBD
    status: stable | experimental | deprecated
```

Until automated registry support exists, `docs/PROJECT_INDEX.md` and this document serve as the human registry.

## Breaking-change checklist

Before a breaking artifact change:

- Is the break necessary?
- Can an optional field solve it instead?
- Are downstream users affected?
- Are old artifacts still readable?
- Is migration safe?
- Does the change alter safety or claim meaning?
- Does it require human review?
- Are docs and examples updated?

## Agent guidance

Agents may add optional metadata fields with tests if scope is clear.

Agents must not autonomously:

- remove required fields;
- change proof-ladder meaning;
- alter release-status semantics;
- migrate candidate release status;
- change calibration decision history;
- break schema compatibility.

## Final standard

OpenAMP artifacts should be stable enough that serious outsiders can build workflows around them.

That is one of the differences between a demo repo and infrastructure.
