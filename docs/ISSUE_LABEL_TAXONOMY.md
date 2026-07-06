# Issue Label Taxonomy

## Purpose

This document defines a shared issue-label system for humans and agents working on OpenAMP Foundry.

Labels should make the next safe action obvious.

## Label design principle

A good label answers at least one of these questions:

- Who should work on this?
- How risky is it?
- What evidence is required?
- Does it need human review?
- Does it affect safety, benchmarks, claims, or wet-lab-facing artifacts?

## Recommended labels

### Contributor fit

| Label | Meaning |
|---|---|
| `good-first-task` | Small, clear, low-risk task suitable for a new contributor. |
| `agent-safe` | Suitable for AI agents under normal repo rules. |
| `human-required` | Requires human judgment before completion. |
| `needs-domain-review` | Needs microbiology, peptide, assay, toxicology, or related expertise. |
| `needs-safety-review` | Could affect safety, release, misuse risk, wet-lab-facing materials, or claims. |
| `needs-maintainer-decision` | Requires project direction or governance decision. |

### Work type

| Label | Meaning |
|---|---|
| `docs` | Documentation-only or documentation-primary. |
| `tests` | Test coverage, regression tests, CI checks. |
| `cli` | Command-line interface behavior or ergonomics. |
| `schema` | JSON/YAML schemas or artifact validation. |
| `benchmark` | Benchmark code, metrics, benchmark docs, or gates. |
| `scoring` | Candidate scoring or ranking behavior. |
| `calibration` | Result intake, recalibration gate, weight update, active-learning loop. |
| `simulation` | Virtual assay, proxy model, simulator interface, uncertainty. |
| `safety` | Safety policy, release policy, misuse prevention. |
| `onboarding` | Human or agent onboarding flow. |
| `ecosystem` | External adapters, interoperability, artifact reuse. |

### Risk level

| Label | Meaning |
|---|---|
| `risk-low` | Cannot plausibly affect safety, claims, ranking, or release. |
| `risk-medium` | Could affect interpretation, workflow, or artifact clarity. |
| `risk-high` | Could affect candidate ranking, release, wet-lab-facing artifacts, safety, or public claims. |
| `do-not-automerge` | Human review mandatory. |

### Evidence requirement

| Label | Meaning |
|---|---|
| `needs-test` | Requires test coverage before merge. |
| `needs-benchmark` | Requires benchmark run or benchmark comparison. |
| `needs-baseline` | Requires cheap-baseline comparison. |
| `needs-doc-update` | Behavior changed and docs must be updated. |
| `needs-proof-ladder-check` | Claim language must be mapped to evidence level. |
| `needs-repro-check` | Determinism, hashes, or reproducibility must be verified. |

### Status

| Label | Meaning |
|---|---|
| `triage` | Needs classification or scope. |
| `blocked` | Cannot proceed until a dependency is resolved. |
| `ready` | Clear scope and ready for work. |
| `in-review` | Under review. |
| `wontfix-safety` | Rejected because it violates safety or release policy. |
| `wontfix-evidence` | Rejected because evidence does not justify the claim or feature. |
| `duplicate` | Covered elsewhere. |

## Label combinations

### Safe agent task

Use:

- `agent-safe`
- `good-first-task` or relevant work type
- `risk-low`
- `needs-test` if code changes

Example:

> Improve CLI error when candidate CSV is missing required column.

### Benchmark task

Use:

- `benchmark`
- `needs-baseline`
- `needs-benchmark`
- `needs-doc-update`
- `risk-medium` or `risk-high`

Example:

> Add charge-matched negative-set benchmark for low-charge candidate classes.

### Safety-sensitive task

Use:

- `safety`
- `needs-safety-review`
- `human-required`
- `do-not-automerge`
- `risk-high`

Example:

> Update model release policy for external predictor weights.

### Wet-lab-facing task

Use:

- `wet-lab-facing` if label exists, otherwise `ecosystem` + `needs-domain-review`
- `needs-safety-review`
- `needs-proof-ladder-check`
- `do-not-automerge`

Example:

> Revise external review packet template for qualified lab partner.

## Agent assignment rule

Agents may work on issues labeled `agent-safe` unless another label overrides it.

Do not let agents autonomously complete issues with any of these labels:

- `needs-safety-review`
- `needs-domain-review`
- `human-required`
- `risk-high`
- `do-not-automerge`
- `needs-maintainer-decision`

Agents may prepare drafts or scaffolds for those issues, but human review is mandatory.

## Issue quality checklist

A good issue should include:

- problem statement;
- expected artifact or behavior;
- relevant docs;
- safety impact;
- evidence required;
- commands to run;
- stop condition;
- suggested labels.

## Bad issue patterns

Avoid issues like:

- “make model better”;
- “improve discovery”;
- “add AI magic”;
- “make results more impressive”;
- “publish candidate list”;
- “optimize potency only”;
- “add wet-lab protocol.”

A vague issue invites unsafe or useless work.

## Label governance

Maintainers should review labels quarterly or after major roadmap changes.

Remove labels that do not guide action.

Add labels when repeated review confusion appears.

The label system should reduce coordination cost, not become bureaucracy.
