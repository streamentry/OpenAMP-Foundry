# Project Index

## Purpose

This page is the front door for humans and AI agents.

OpenAMP Foundry has many documents because the project is not only code. It is a scientific operating system for honest antimicrobial peptide candidate selection: code, evidence, safety policy, benchmark discipline, calibration, and eventual wet-lab feedback.

Use this index to find the right document for the job without wandering through the repo.

## The shortest accurate description

OpenAMP Foundry is an open, safety-first dry-lab foundry for antimicrobial peptide discovery.

Its current job is to rank, falsify, document, and audit candidate peptides before any lab money is spent.

Its long-term job is harder: become a wet-lab compression engine that helps qualified scientists choose fewer, smarter, safer experiments and learn from every result.

The project never treats computational prediction as biological proof.

## Start here by role

### New engineer

Read in this order:

1. [`README.md`](../README.md) — quickstart and repo map.
2. [`CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution rules and safety checklist.
3. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — system architecture and extension points.
4. [`docs/BENCHMARKING.md`](BENCHMARKING.md) — how evidence is measured.
5. [`docs/AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — useful even for human engineers because it encodes the project workflow.

First useful contribution: fix a small bug, improve a test, add a doc consistency check, or make one CLI path easier to use.

### AI agent

Read in this order:

1. [`AGENTS.md`](../AGENTS.md) — primary operating contract.
2. [`CLAUDE.md`](../CLAUDE.md) — concise collaborator guidance.
3. [`docs/AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — task-selection and verification protocol.
4. [`docs/DECISION_RULES.md`](DECISION_RULES.md) — gates that must not be bypassed.
5. [`SAFETY.md`](../SAFETY.md) — disallowed content and safety defaults.

First useful contribution: select one narrow bottleneck, implement it, add tests, update docs, run the relevant checks, and preserve failure modes.

### Computational biologist

Read in this order:

1. [`VISION.md`](../VISION.md) — what the project is trying to become.
2. [`GOAL.md`](../GOAL.md) — concrete milestones and kill rules.
3. [`docs/METRICS_CURRENT.md`](METRICS_CURRENT.md) — current benchmark evidence.
4. [`docs/BENCHMARKING.md`](BENCHMARKING.md) — benchmark logic and caveats.
5. [`docs/PROOF_LADDER.md`](PROOF_LADDER.md) — what evidence is needed before stronger claims.

First useful contribution: add a leakage-resistant benchmark, improve reference curation, challenge a scorer with a cheaper baseline, or add an adapter with documented limitations.

### Microbiologist, peptide scientist, or wet-lab partner

Read in this order:

1. [`docs/WET_LAB_HANDOFF.md`](WET_LAB_HANDOFF.md) — how computational packages are prepared for review.
2. [`docs/PROOF_LADDER.md`](PROOF_LADDER.md) — claim ladder from dry-lab nomination to independent validation.
3. [`docs/COLLABORATION_PLAYBOOK.md`](COLLABORATION_PLAYBOOK.md) — safe collaboration modes.
4. [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) — allowed and disallowed use.
5. [`docs/NEGATIVE_RESULT_ARCHIVE.md`](NEGATIVE_RESULT_ARCHIVE.md) — how failures become useful evidence.

First useful contribution: review whether candidate evidence packages are interpretable, whether controls are adequate, and whether success/failure criteria are scientifically meaningful.

### Safety reviewer

Read in this order:

1. [`SAFETY.md`](../SAFETY.md) — safety posture.
2. [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) — user-facing boundaries.
3. [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) — release rules.
4. [`docs/DECISION_RULES.md`](DECISION_RULES.md) — gates and hardcoded thresholds.
5. [`docs/COLLABORATION_PLAYBOOK.md`](COLLABORATION_PLAYBOOK.md) — external-workflow boundaries.

First useful contribution: identify where an artifact could be misread, over-released, overclaimed, or used outside scope.

### Funder, institution, or public-interest partner

Read in this order:

1. [`VISION.md`](../VISION.md) — long-term infrastructure thesis.
2. [`GOAL.md`](../GOAL.md) — measurable milestones.
3. [`docs/WHY_WORK_ON_OPENAMP.md`](WHY_WORK_ON_OPENAMP.md) — why this project is worth serious effort.
4. [`docs/OPEN_BIOTECH_STACK.md`](OPEN_BIOTECH_STACK.md) — how this could become shared biotech infrastructure.
5. [`docs/PROOF_LADDER.md`](PROOF_LADDER.md) — how claims mature.

First useful contribution: fund independent validation, benchmark audits, safe result publication, or infrastructure work that makes the project less dependent on any one person or model.

## Core strategic docs

| Document | Job |
|---|---|
| [`VISION.md`](../VISION.md) | Ambitious but grounded long-term vision. |
| [`GOAL.md`](../GOAL.md) | Concrete milestones, kill rules, and metrics. |
| [`MISSION.md`](../MISSION.md) | Scientific mission and claim boundaries. |
| [`AGENTS.md`](../AGENTS.md) | Operating contract for AI agents. |
| [`docs/WHY_WORK_ON_OPENAMP.md`](WHY_WORK_ON_OPENAMP.md) | Positioning: why serious contributors should choose this repo. |
| [`docs/OPEN_BIOTECH_STACK.md`](OPEN_BIOTECH_STACK.md) | Infrastructure thesis and stack model. |
| [`docs/50_LOOP_PLAN.md`](50_LOOP_PLAN.md) | Execution history and future loop structure. |

## Core technical docs

| Document | Job |
|---|---|
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture, data flow, package map, threat model. |
| [`docs/BENCHMARKING.md`](BENCHMARKING.md) | Benchmark targets and commands. |
| [`docs/METRICS_CURRENT.md`](METRICS_CURRENT.md) | Current benchmark state and single source of truth for metrics. |
| [`docs/DECISION_RULES.md`](DECISION_RULES.md) | Pre-registered pass/fail gates. |
| [`docs/EVIDENCE_CERTIFICATE.md`](EVIDENCE_CERTIFICATE.md) | Candidate certificate spec. |
| [`docs/CALIBRATION_POLICY.md`](CALIBRATION_POLICY.md) | Recalibration gate and policy. |
| [`docs/SIMULATION_BENCHMARK.md`](SIMULATION_BENCHMARK.md) | Current verdict on simulation modules. |
| [`docs/VIRTUAL_ASSAY_SCOPE.md`](VIRTUAL_ASSAY_SCOPE.md) | What virtual assay modules may and may not claim. |

## Core safety docs

| Document | Job |
|---|---|
| [`SAFETY.md`](../SAFETY.md) | Project safety policy. |
| [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) | Allowed and disallowed use. |
| [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) | Release policy for models, weights, and sensitive artifacts. |
| [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) | Data and license rules. |
| [`docs/NEGATIVE_RESULT_ARCHIVE.md`](NEGATIVE_RESULT_ARCHIVE.md) | Safe negative-result format. |

## Working loop for any contributor

Every good contribution should follow the same loop:

```text
find bottleneck
  -> define expected evidence
  -> implement smallest useful change
  -> test against cheap baselines
  -> update docs
  -> preserve caveats
  -> run checks
  -> leave the repo easier for the next person or agent
```

The project should compound through small, verified loops rather than dramatic unsupported leaps.

## What not to do

Do not add impressive-sounding biology without evidence.

Do not add a predictor that cannot be challenged by cheap baselines.

Do not publish unscreened high-risk candidate lists.

Do not add wet-lab protocols, pathogen-handling instructions, harmful optimization objectives, or clinical claims.

Do not change a success definition after seeing results.

Do not hide negative results merely because they weaken the story.

## What high-leverage work looks like

High-leverage work usually improves one of five things:

1. **Trust** — stronger evidence, reproducibility, auditability, or safety.
2. **Decision quality** — better selection of scarce experiment slots.
3. **Interoperability** — cleaner schemas, adapters, manifests, or CLI paths.
4. **External usefulness** — easier onboarding for labs, scientists, engineers, and reviewers.
5. **Compounding** — changes that make future agents and humans faster without lowering standards.

## Current strategic bottleneck

The project already has unusually strong dry-lab discipline.

The next bottleneck is not more impressive language.

The next bottleneck is external truth:

- independent review of candidate evidence packages;
- fair comparison against charge/similarity baselines;
- pre-registered wet-lab pilots through qualified partners;
- result intake that preserves both successes and failures;
- calibration that improves the next round without rewriting history.

Everything else should serve that path.
