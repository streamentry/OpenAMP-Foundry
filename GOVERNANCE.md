# Governance

## Purpose

This document defines how OpenAMP Foundry makes decisions as it grows.

OpenAMP is not only a codebase. It is a safety-constrained scientific infrastructure project. Governance must protect the project’s credibility, safety posture, reproducibility, and ability to learn from failure.

## Governance principle

**Decisions should be reviewable by people who do not trust the maintainers.**

Important decisions must leave records.

## Values in priority order

When values conflict, use this order:

1. Safety.
2. Scientific honesty.
3. Reproducibility.
4. External auditability.
5. Contributor experience.
6. Speed.
7. Attention.

Attention is last.

## Project roles

### Maintainers

Maintainers protect repository integrity.

Responsibilities:

- review PRs;
- enforce safety and claim boundaries;
- maintain source-of-truth docs;
- approve releases;
- protect benchmark governance;
- preserve negative results where safe;
- manage issue labels and roadmaps;
- ensure agent work remains reviewable.

### Safety reviewers

Safety reviewers evaluate release and misuse risk.

Required for:

- model or artifact release;
- non-toy candidate publication;
- external-facing biological artifacts;
- release-policy changes;
- safety-policy changes;
- unclear dual-use risk.

### Scientific reviewers

Scientific reviewers evaluate evidence quality.

They may review:

- benchmark design;
- candidate evidence packages;
- novelty claims;
- result interpretation;
- proof-ladder placement;
- pre-registration plans.

### Infrastructure contributors

Infrastructure contributors improve code, tests, docs, schemas, CI, and tooling.

They should optimize for reproducibility and reviewability.

### AI agents

AI agents are infrastructure contributors with stricter boundaries.

They may prepare drafts and implement narrow safe tasks, but may not make final scientific, safety, release, or external-claim decisions.

## Decision classes

### Class A — Routine changes

Examples:

- typo fixes;
- small docs improvements;
- minor bug fixes;
- test improvements;
- low-risk CLI ergonomics.

Review: normal maintainer review.

### Class B — Infrastructure changes

Examples:

- schema changes;
- validators;
- report formats;
- issue templates;
- CI gates;
- artifact versioning.

Review: maintainer review; compatibility note required.

### Class C — Scientific behavior changes

Examples:

- scoring changes;
- ranking behavior;
- benchmark thresholds;
- calibration behavior;
- virtual-assay integration;
- candidate-selection rules.

Review: maintainer plus scientific review. Benchmark and cheap-baseline evidence required.

### Class D — Safety-sensitive changes

Examples:

- release policy;
- safety policy;
- candidate publication;
- model release;
- external partner package;
- non-toy biological data release;
- public claims beyond dry-lab nomination.

Review: safety review required. Do not automerge.

## Decision records

Create a decision record for:

- benchmark threshold changes;
- safety policy changes;
- model release decisions;
- candidate release decisions;
- data release decisions;
- calibration policy changes;
- public claim upgrades;
- external pilot readiness;
- deprecating major artifacts.

Decision records should include:

```yaml
decision_id: stable-id
date: YYYY-MM-DD
decision_class: A | B | C | D
summary: text
options_considered: list
evidence: list
safety_review: required-or-not
scientific_review: required-or-not
decision: text
limitations: list
revisit_condition: text
```

## Release governance

All releases should follow [`docs/trust/RELEASE_CHECKLIST.md`](docs/trust/RELEASE_CHECKLIST.md).

A release should include:

- what changed;
- what evidence supports it;
- what failed;
- what claims are allowed;
- what remains unproven;
- what release decisions were made;
- what should happen next.

## Agent governance

Agent work should follow [`AGENTS.md`](AGENTS.md) and [`docs/getting-started/AGENT_ONBOARDING.md`](docs/getting-started/AGENT_ONBOARDING.md).

Agents may work independently on low-risk issues labeled `agent-safe`.

Agents must not finalize changes labeled:

- `needs-safety-review`;
- `needs-domain-review`;
- `risk-high`;
- `do-not-automerge`;
- `human-required`;
- `needs-maintainer-decision`.

## Conflict resolution

If reviewers disagree:

1. Identify the disputed claim or decision.
2. Map the decision class.
3. Identify what evidence would change the decision.
4. Prefer the safer, weaker, more reversible decision.
5. Record the disagreement if the decision is important.

## Governance anti-patterns

Avoid:

- undocumented threshold changes;
- safety decisions hidden in chat;
- public claims stronger than internal evidence;
- agent-generated broad rewrites without review;
- deleting negative results for optics;
- making releases without limitations;
- allowing one maintainer’s memory to become the process.

## Final standard

Governance should make OpenAMP more trustworthy as it grows.

If growth makes the project harder to audit, governance is failing.
