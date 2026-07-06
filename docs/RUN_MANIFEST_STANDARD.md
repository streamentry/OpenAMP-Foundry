# Run Manifest Standard

## Purpose

A run manifest records enough information for a future human, AI agent, reviewer, or downstream tool to understand how an OpenAMP artifact was produced.

Reproducibility is not a slogan. It is a set of fields.

## Prime rule

**No important artifact should be trusted without provenance.**

## What a run manifest answers

A run manifest should answer:

- What command ran?
- Which inputs were used?
- Which config was used?
- Which code version produced the output?
- Which package version produced the output?
- Which random seed was used?
- Which schemas were used?
- Which outputs were produced?
- Which hashes identify the inputs and outputs?
- Which claims are allowed from the run?

## Required fields

```yaml
manifest_version: MAJOR.MINOR.PATCH
run_id: stable-id
created_at: YYYY-MM-DDTHH:MM:SSZ
created_by: human | agent | tool
repo_commit: git-sha-or-unknown
package_version: version
command: command-or-workflow-name
working_directory: path-or-null
config_path: path-or-null
config_hash: sha256-or-null
input_artifacts:
  - path: path-or-reference
    artifact_type: candidates | references | config | results | other
    hash: sha256-or-null
    release_status: open | staged | restricted | internal | do-not-release
output_artifacts:
  - path: path-or-reference
    artifact_type: ranked_candidates | report | certificate | manifest | benchmark | other
    hash: sha256-or-null
    schema: path-or-null
random_seed: integer-or-null
proof_ladder_level: integer-or-null
allowed_claims: list
unsupported_claims: list
limitations: list
```

## Recommended fields

```yaml
environment:
  python_version: version
  platform: text
  dependencies_hash: sha256-or-null
  ci_run_id: id-or-null
review:
  human_review_required: true-or-false
  safety_review_required: true-or-false
  scientific_review_required: true-or-false
  release_review_required: true-or-false
notes: list
```

## Manifest classes

### Demo manifest

For toy/demo runs.

Must say demo outputs do not support biological claims.

### Benchmark manifest

For benchmark runs.

Must include benchmark ID, dataset references, split method, and cheap baselines where applicable.

### Candidate-panel manifest

For candidate panel construction.

Must include release status, proof-ladder level, and selection rule.

### Result-intake manifest

For structured result summaries and calibration intake.

Must include result artifact references and gate status where applicable.

### Release manifest

For public releases.

Must include release decisions, safety review status, and claim boundaries.

## Hash policy

Use hashes where practical for:

- input files;
- configs;
- generated reports;
- evidence certificates;
- output manifests;
- dataset snapshots;
- candidate manifests.

If a hash cannot be recorded, the manifest should explain why.

## Claim boundary

A manifest records provenance.

It does not prove biological activity, safety, clinical value, or generalization.

The manifest should explicitly list unsupported claims.

## Agent guidance

Agents should prefer adding or improving manifest fields rather than adding impressive language.

Agents must not invent missing provenance.

If provenance is unavailable, record it as unknown.

## Review checklist

Before a run manifest is treated as review-ready, ask:

1. Can a reviewer identify all inputs?
2. Can a reviewer identify the config?
3. Can a reviewer identify the code version?
4. Can a reviewer reproduce or approximate the command?
5. Are output artifacts listed?
6. Are release statuses present?
7. Are unsupported claims listed?
8. Is human review status clear?

## Final standard

A run manifest should make every important OpenAMP artifact easier to reproduce, reject, or safely reuse.
