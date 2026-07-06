# Project Index

## Purpose

This page is the front door for humans and AI agents.

OpenAMP Foundry has many documents because the project is not only code. It is a scientific operating system for honest antimicrobial peptide candidate selection: code, evidence, safety policy, benchmark discipline, calibration, release governance, and eventual wet-lab feedback.

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
4. [`docs/HIGH_LEVERAGE_TASKS.md`](HIGH_LEVERAGE_TASKS.md) — concrete task map.
5. [`docs/NEXT_100_PR_MAP.md`](NEXT_100_PR_MAP.md) — sequenced infrastructure backlog.

First useful contribution: fix a small bug, improve a test, add a doc consistency check, or make one CLI path easier to use.

### AI agent

Read in this order:

1. [`AGENTS.md`](../AGENTS.md) — primary operating contract.
2. [`CLAUDE.md`](../CLAUDE.md) — concise collaborator guidance.
3. [`docs/AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — task-selection and verification protocol.
4. [`docs/HIGH_LEVERAGE_TASKS.md`](HIGH_LEVERAGE_TASKS.md) — concrete task map.
5. [`docs/NEXT_100_PR_MAP.md`](NEXT_100_PR_MAP.md) — PR-sized work map.

First useful contribution: select one narrow bottleneck, implement it, add tests, update docs, run the relevant checks, and preserve failure modes.

### Computational biologist

Read in this order:

1. [`VISION.md`](../VISION.md) — what the project is trying to become.
2. [`GOAL.md`](../GOAL.md) — concrete milestones and kill rules.
3. [`docs/METRICS_CURRENT.md`](METRICS_CURRENT.md) — current benchmark evidence.
4. [`docs/BENCHMARKING.md`](BENCHMARKING.md) — benchmark commands.
5. [`docs/BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md) — benchmark lifecycle and anti-cheating rules.

First useful contribution: add a leakage-resistant benchmark, improve reference curation, challenge a scorer with a cheaper baseline, or add an adapter with documented limitations.

### Data or model contributor

Read in this order:

1. [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) — data license and redistribution policy.
2. [`docs/DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) — dataset cards, labels, leakage, release status.
3. [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) — model and artifact release policy.
4. [`docs/MODEL_CARD_TEMPLATE.md`](MODEL_CARD_TEMPLATE.md) — required model/adapter card structure.
5. [`docs/ARTIFACT_VERSIONING.md`](ARTIFACT_VERSIONING.md) — artifact compatibility rules.

First useful contribution: add a dataset card, model card, schema example, adapter card, or license/release-status clarification.

### Microbiologist, peptide scientist, or wet-lab partner

Read in this order:

1. [`docs/WET_LAB_HANDOFF.md`](WET_LAB_HANDOFF.md) — safe expert-review handoff guide.
2. [`docs/PROOF_LADDER.md`](PROOF_LADDER.md) — claim ladder from dry-lab nomination to independent validation.
3. [`docs/EXTERNAL_REVIEW_PACKET.md`](EXTERNAL_REVIEW_PACKET.md) — standard review packet contents.
4. [`docs/LAB_PARTNER_ONBOARDING.md`](LAB_PARTNER_ONBOARDING.md) — safe partner onboarding boundaries.
5. [`docs/PRE_REGISTERED_PILOT_TEMPLATE.md`](PRE_REGISTERED_PILOT_TEMPLATE.md) — non-protocol template for freezing pilot logic before qualified testing.

First useful contribution: review whether candidate evidence packages are interpretable, whether controls are adequate at the planning level, and whether success/failure criteria are scientifically meaningful.

### Safety reviewer

Read in this order:

1. [`docs/TRUST_CENTER.md`](TRUST_CENTER.md) — safety, evidence, release, and governance overview.
2. [`SAFETY.md`](../SAFETY.md) — safety posture.
3. [`docs/SAFETY_DOC_AUDIT.md`](SAFETY_DOC_AUDIT.md) — documentation safety audit and remediation record.
4. [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) — user-facing boundaries.
5. [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) — release rules.

First useful contribution: identify where an artifact could be misread, over-released, overclaimed, or used outside scope.

### Funder, institution, or public-interest partner

Read in this order:

1. [`VISION.md`](../VISION.md) — long-term infrastructure thesis.
2. [`GOAL.md`](../GOAL.md) — measurable milestones.
3. [`docs/TRUST_CENTER.md`](TRUST_CENTER.md) — trust architecture.
4. [`docs/WHY_WORK_ON_OPENAMP.md`](WHY_WORK_ON_OPENAMP.md) — why this project is worth serious effort.
5. [`docs/ADOPTION_STRATEGY.md`](ADOPTION_STRATEGY.md) — how the repo becomes useful to humans, agents, labs, and institutions.

First useful contribution: fund independent validation, benchmark audits, safe result publication, or infrastructure work that makes the project less dependent on any one person or model.

### Maintainer

Read in this order:

1. [`docs/MAINTAINER_GUIDE.md`](MAINTAINER_GUIDE.md) — maintainer review rules.
2. [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — release checklist.
3. [`docs/DOCS_MAINTENANCE.md`](DOCS_MAINTENANCE.md) — documentation governance.
4. [`docs/ISSUE_LABEL_TAXONOMY.md`](ISSUE_LABEL_TAXONOMY.md) — issue labels and triage rules.
5. [`docs/NEXT_100_PR_MAP.md`](NEXT_100_PR_MAP.md) — next 100 PR map.

First useful contribution: make the repo easier to maintain without lowering safety, evidence, or reproducibility standards.

## Core strategic docs

| Document | Job |
|---|---|
| [`VISION.md`](../VISION.md) | Ambitious but grounded long-term vision. |
| [`GOAL.md`](../GOAL.md) | Concrete milestones, kill rules, and metrics. |
| [`MISSION.md`](../MISSION.md) | Scientific mission and claim boundaries. |
| [`docs/TRUST_CENTER.md`](TRUST_CENTER.md) | Trust front door for safety, evidence, release, governance, and agents. |
| [`docs/NUMBER_ONE_REPO_STANDARD.md`](NUMBER_ONE_REPO_STANDARD.md) | Defines what category leadership means. |
| [`docs/WHY_WORK_ON_OPENAMP.md`](WHY_WORK_ON_OPENAMP.md) | Positioning: why serious contributors should choose this repo. |
| [`docs/OPEN_BIOTECH_STACK.md`](OPEN_BIOTECH_STACK.md) | Infrastructure thesis and stack model. |
| [`docs/ADOPTION_STRATEGY.md`](ADOPTION_STRATEGY.md) | Adoption strategy for humans, agents, labs, and institutions. |
| [`docs/NEXT_100_PR_MAP.md`](NEXT_100_PR_MAP.md) | PR-sized roadmap for compounding work. |
| [`docs/50_LOOP_PLAN.md`](50_LOOP_PLAN.md) | Execution history and future loop structure. |

## Core operating docs

| Document | Job |
|---|---|
| [`AGENTS.md`](../AGENTS.md) | Operating contract for AI agents. |
| [`CLAUDE.md`](../CLAUDE.md) | Concise collaborator guidance. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution rules and PR expectations. |
| [`docs/AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) | Safe agent task protocol. |
| [`docs/HUMAN_ONBOARDING.md`](HUMAN_ONBOARDING.md) | Human contributor onboarding. |
| [`docs/HIGH_LEVERAGE_TASKS.md`](HIGH_LEVERAGE_TASKS.md) | Task map for humans and agents. |
| [`docs/MAINTAINER_GUIDE.md`](MAINTAINER_GUIDE.md) | Maintainer review and governance standard. |
| [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) | Release checklist. |
| [`docs/DOCS_MAINTENANCE.md`](DOCS_MAINTENANCE.md) | Documentation maintenance rules. |
| [`docs/ISSUE_LABEL_TAXONOMY.md`](ISSUE_LABEL_TAXONOMY.md) | Issue-label system. |

## Core technical docs

| Document | Job |
|---|---|
| [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture, data flow, package map, extension points. |
| [`docs/ARTIFACT_VERSIONING.md`](ARTIFACT_VERSIONING.md) | Artifact versioning and compatibility policy. |
| [`docs/BENCHMARKING.md`](BENCHMARKING.md) | Current benchmark suite and commands. |
| [`docs/BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md) | Benchmark lifecycle and anti-cheating rules. |
| [`docs/METRICS_CURRENT.md`](METRICS_CURRENT.md) | Current benchmark state and single source of truth for metrics. |
| [`docs/DECISION_RULES.md`](DECISION_RULES.md) | Pre-registered pass/fail gates. |
| [`docs/EVIDENCE_CERTIFICATE.md`](EVIDENCE_CERTIFICATE.md) | Candidate certificate spec. |
| [`docs/CALIBRATION_POLICY.md`](CALIBRATION_POLICY.md) | Recalibration gate and policy. |
| [`docs/SIMULATION_BENCHMARK.md`](SIMULATION_BENCHMARK.md) | Current verdict on simulation modules. |
| [`docs/VIRTUAL_ASSAY_SCOPE.md`](VIRTUAL_ASSAY_SCOPE.md) | What virtual assay modules may and may not claim. |

## Data, model, and release docs

| Document | Job |
|---|---|
| [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) | Data license and redistribution notice. |
| [`docs/DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) | Dataset cards, label governance, leakage, and release status. |
| [`data/README.md`](../data/README.md) | Data directory policy. |
| [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) | Model and artifact release policy. |
| [`docs/MODEL_CARD_TEMPLATE.md`](MODEL_CARD_TEMPLATE.md) | Model, scorer, simulator, generator, and adapter card template. |
| [`models/README.md`](../models/README.md) | Models directory policy. |
| [`docs/CLAIM_REVIEW_CHECKLIST.md`](CLAIM_REVIEW_CHECKLIST.md) | Claim review checklist. |

## External review and collaboration docs

| Document | Job |
|---|---|
| [`docs/WET_LAB_HANDOFF.md`](WET_LAB_HANDOFF.md) | Safe expert-review handoff guide, not a protocol. |
| [`docs/LAB_PARTNER_ONBOARDING.md`](LAB_PARTNER_ONBOARDING.md) | Safe partner onboarding boundaries. |
| [`docs/EXPERT_REVIEW_PACK.md`](EXPERT_REVIEW_PACK.md) | Expert review pack template. |
| [`docs/EXTERNAL_REVIEW_PACKET.md`](EXTERNAL_REVIEW_PACKET.md) | External review packet standard. |
| [`docs/PRE_REGISTERED_PILOT_TEMPLATE.md`](PRE_REGISTERED_PILOT_TEMPLATE.md) | Non-protocol template for freezing pilot logic before qualified testing. |
| [`docs/ASSAY_PREREGISTRATION.md`](ASSAY_PREREGISTRATION.md) | Candidate-selection pilot pre-registration template, not a protocol. |
| [`docs/COLLABORATION_PLAYBOOK.md`](COLLABORATION_PLAYBOOK.md) | External collaboration modes and boundaries. |
| [`docs/NEGATIVE_RESULT_ARCHIVE.md`](NEGATIVE_RESULT_ARCHIVE.md) | Safe negative-result format. |

## Core safety docs

| Document | Job |
|---|---|
| [`SAFETY.md`](../SAFETY.md) | Project safety policy. |
| [`docs/SAFETY_DOC_AUDIT.md`](SAFETY_DOC_AUDIT.md) | Safety audit and remediation record for docs. |
| [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) | Allowed and disallowed use. |
| [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) | Release policy for models, weights, and sensitive artifacts. |
| [`docs/TRUST_CENTER.md`](TRUST_CENTER.md) | Cross-cutting trust overview. |

## GitHub workflow files

| File | Job |
|---|---|
| [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) | PR checklist for safety, evidence, proof ladder, baselines, and review. |
| [`.github/ISSUE_TEMPLATE/agent_safe_task.md`](../.github/ISSUE_TEMPLATE/agent_safe_task.md) | Agent-safe task template. |
| [`.github/ISSUE_TEMPLATE/benchmark_governance.md`](../.github/ISSUE_TEMPLATE/benchmark_governance.md) | Benchmark proposal/change template. |
| [`.github/ISSUE_TEMPLATE/safety_review.md`](../.github/ISSUE_TEMPLATE/safety_review.md) | Safety/release review template. |
| [`.github/ISSUE_TEMPLATE/model_release_review.md`](../.github/ISSUE_TEMPLATE/model_release_review.md) | Model/artifact release review template. |
| [`.github/ISSUE_TEMPLATE/data_contribution.md`](../.github/ISSUE_TEMPLATE/data_contribution.md) | Data contribution/review template. |
| [`.github/ISSUE_TEMPLATE/claim_review.md`](../.github/ISSUE_TEMPLATE/claim_review.md) | Claim review template. |

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

Do not add operational biological instructions, harmful optimization objectives, or clinical claims.

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
- pre-registered pilots through qualified partners;
- result intake that preserves both successes and failures;
- calibration that improves the next round without rewriting history.

Everything else should serve that path.
