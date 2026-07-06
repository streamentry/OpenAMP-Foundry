# Documentation Maintenance

## Purpose

This document defines how OpenAMP Foundry keeps documentation useful as the project grows.

Doc drift is not cosmetic. In this repo, stale documentation can become a scientific or safety failure.

## Core rule

**If behavior, metrics, safety posture, or claim boundaries change, the relevant source-of-truth document must change in the same PR.**

## Why docs matter here

OpenAMP is not only code.

It is a coordinated system of:

- safety policy;
- claim discipline;
- benchmark evidence;
- candidate certificates;
- calibration rules;
- agent instructions;
- human onboarding;
- collaboration boundaries;
- future wet-lab-facing artifacts.

If docs drift, humans and agents act on stale assumptions.

## Document classes

### Class 1 — Source-of-truth docs

These docs define current project truth.

| Doc | Owns |
|---|---|
| `README.md` | Primary entrypoint and repo map. |
| `MISSION.md` | Mission and claim boundaries. |
| `VISION.md` | Long-term vision. |
| `GOAL.md` | Milestones and kill rules. |
| `SAFETY.md` | Safety policy. |
| `RESPONSIBLE_USE.md` | Allowed/disallowed use. |
| `MODEL_RELEASE_POLICY.md` | Artifact release boundaries. |
| `docs/evidence/METRICS_CURRENT.md` | Current benchmark metrics. |
| `docs/evidence/DECISION_RULES.md` | Gates and thresholds. |
| `docs/CALIBRATION_POLICY.md` | Recalibration gate policy. |
| `docs/PROJECT_INDEX.md` | Navigation hub. |

These must be kept current.

### Class 2 — Operating docs

These docs tell people and agents how to work.

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `docs/getting-started/AGENT_ONBOARDING.md`
- `docs/getting-started/HUMAN_ONBOARDING.md`
- `docs/operations/HIGH_LEVERAGE_TASKS.md`
- `docs/getting-started/MAINTAINER_GUIDE.md`

If a workflow changes, these may need updates.

### Class 3 — Technical reference docs

These explain systems and artifacts.

- `docs/engineering/ARCHITECTURE.md`
- `docs/evidence/BENCHMARKING.md`
- `docs/evidence/BENCHMARK_GOVERNANCE.md`
- `docs/evidence/EVIDENCE_CERTIFICATE.md`
- `docs/VIRTUAL_ASSAY_SCOPE.md`
- `docs/evidence/SIMULATION_BENCHMARK.md`

If code behavior changes, these may need updates.

### Class 4 — Collaboration docs

These help outsiders safely evaluate or reuse the project.

- `docs/review/COLLABORATION_PLAYBOOK.md`
- `docs/review/WET_LAB_HANDOFF.md`
- `docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md`
- `docs/ADOPTION_STRATEGY.md`
- `docs/OPEN_BIOTECH_STACK.md`
- `docs/PROOF_LADDER.md`

If external-facing language changes, these need review.

## Update triggers

### Metrics change

Update:

- `docs/evidence/METRICS_CURRENT.md`
- `outputs/metrics_snapshot.json` if generated
- `docs/evidence/BENCHMARKING.md` if benchmark meaning changed
- `docs/research/ROADMAP.md` or `docs/50_LOOP_PLAN.md` if milestone changed

### Benchmark added or changed

Update:

- `docs/evidence/BENCHMARKING.md`
- `docs/evidence/BENCHMARK_GOVERNANCE.md` if governance status changes
- `docs/evidence/METRICS_CURRENT.md` after result exists
- Makefile target where appropriate
- tests for benchmark behavior

### Scorer or ranking behavior changed

Update:

- `docs/engineering/ARCHITECTURE.md`
- `docs/evidence/METRICS_CURRENT.md` if metrics changed
- `docs/evidence/DECISION_RULES.md` if gates changed
- `docs/evidence/EVIDENCE_CERTIFICATE.md` if certificate semantics changed
- `README.md` if user workflow changed

### Safety or release boundary changed

Update:

- `SAFETY.md`
- `RESPONSIBLE_USE.md`
- `MODEL_RELEASE_POLICY.md`
- `CONTRIBUTING.md`
- `docs/getting-started/MAINTAINER_GUIDE.md`
- `docs/review/COLLABORATION_PLAYBOOK.md`

Human safety review required.

### Agent workflow changed

Update:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/getting-started/AGENT_ONBOARDING.md`
- `docs/operations/HIGH_LEVERAGE_TASKS.md`
- `docs/PROJECT_INDEX.md`

### New important doc added

Update:

- `README.md` repo map if top-level or core doc;
- `docs/PROJECT_INDEX.md` always;
- `CLAUDE.md` if agents should read it;
- `CONTRIBUTING.md` if contributors should read it.

## Staleness markers

Use explicit status markers when appropriate:

```md
**Status:** current | experimental | deprecated | historical | template
**Last reviewed:** YYYY-MM-DD
**Source of truth:** file/path
```

A stale doc should say it is stale.

## Deprecated docs

Do not delete major docs casually.

When deprecating:

1. Add a banner at the top.
2. Point to the replacement.
3. Explain why it is deprecated.
4. Keep it if old links may exist.
5. Remove only after maintainers agree it is safe.

## Cross-linking rule

Docs should not be isolated.

Important docs should link to:

- the project index;
- proof ladder when claims are involved;
- safety policy when release risk is involved;
- benchmark governance when metrics are involved;
- collaboration playbook when external partners are involved.

## Doc review checklist

Before merging documentation changes, ask:

- Does this strengthen or weaken claim discipline?
- Does this conflict with safety policy?
- Does this duplicate a source-of-truth doc?
- Does this create a stale metric risk?
- Does this help a real role: agent, engineer, scientist, lab, reviewer, funder?
- Does this make next action clearer?
- Does this avoid unsafe operational biological detail?

## Good docs in this repo

Good docs are:

- role-specific;
- exact about evidence level;
- clear about what is not proven;
- linked to source-of-truth files;
- useful to a future contributor;
- safe by default;
- resistant to hype.

## Bad docs in this repo

Bad docs are:

- impressive but unverifiable;
- full of stale metrics;
- ambiguous about claim level;
- redundant without adding clarity;
- unsafe or operationally biological;
- written for attention rather than action;
- impossible for agents to apply.

## Documentation north star

A fresh serious contributor should be able to answer:

1. What is this project?
2. What is it not?
3. What is currently true?
4. What is still unproven?
5. What is safe to work on?
6. What is the next highest-leverage task?
7. What evidence is required before stronger claims?

If the docs do not answer these, improve them.
