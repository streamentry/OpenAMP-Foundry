# Project Index

> Looking for a short route instead of the exhaustive catalog? Start at the
> [documentation home](README.md).

## Purpose

This page is the front door for humans and AI agents.

OpenAMP Foundry has many documents because the project is not only code. It is a scientific operating system for honest antimicrobial peptide candidate selection: code, evidence, safety policy, benchmark discipline, calibration, release governance, and eventual wet-lab feedback.

Use this index to find the right document for the job without wandering through the repo.

## Folder guides

These files are not policy documents, but they are the fastest way to orient a
new contributor inside a large subtree:

- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — script layout and compatibility rules.
- [`../scripts/benchmarks/AGENTS.md`](../scripts/benchmarks/AGENTS.md) — canonical benchmark entrypoints.
- [`../scripts/calibration/AGENTS.md`](../scripts/calibration/AGENTS.md) — canonical calibration entrypoints.
- [`../scripts/external/AGENTS.md`](../scripts/external/AGENTS.md) — canonical external predictor and handoff entrypoints.
- [`../scripts/lab/AGENTS.md`](../scripts/lab/AGENTS.md) — canonical lab handoff entrypoints.
- [`../scripts/novelty/AGENTS.md`](../scripts/novelty/AGENTS.md) — canonical novelty and patent-risk entrypoints.
- [`../scripts/release/AGENTS.md`](../scripts/release/AGENTS.md) — canonical release and reproducibility entrypoints.
- [`../scripts/research/AGENTS.md`](../scripts/research/AGENTS.md) — canonical exploratory generation and screening entrypoints.
- [`../scripts/waves/AGENTS.md`](../scripts/waves/AGENTS.md) — canonical wave-program entrypoints.
- [`../tests/AGENTS.md`](../tests/AGENTS.md) — test layout expectations.
- [`../tests/benchmarks/AGENTS.md`](../tests/benchmarks/AGENTS.md) — benchmark test scope.
- [`../tests/calibration/AGENTS.md`](../tests/calibration/AGENTS.md) — calibration test scope.
- [`../tests/external/AGENTS.md`](../tests/external/AGENTS.md) — external workflow test scope.
- [`../tests/lab/AGENTS.md`](../tests/lab/AGENTS.md) — lab handoff test scope.
- [`../tests/novelty/AGENTS.md`](../tests/novelty/AGENTS.md) — novelty test scope.
- [`../tests/release/AGENTS.md`](../tests/release/AGENTS.md) — release test scope.
- [`../tests/waves/AGENTS.md`](../tests/waves/AGENTS.md) — wave-program test scope.

## The shortest accurate description

OpenAMP Foundry is an open, safety-first dry-lab foundry for antimicrobial peptide discovery.

Its current job is to rank, falsify, document, and audit candidate peptides before any lab money is spent.

Its long-term job is harder: become a wet-lab compression engine that helps qualified scientists choose fewer, smarter, safer experiments and learn from every result.

The project never treats computational prediction as biological proof.

## Start here by role

### New engineer

Read in this order:

1. [`README.md`](../README.md) — quickstart and repo map.
2. [`docs/getting-started/FIRST_RUN_WALKTHROUGH.md`](getting-started/FIRST_RUN_WALKTHROUGH.md) — first-run expectations and troubleshooting.
3. [`CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution rules and safety checklist.
4. [`docs/getting-started/COMMAND_SURFACE.md`](getting-started/COMMAND_SURFACE.md) — command workflows and claim boundaries.
5. [`docs/research/NEXT_100_PR_MAP.md`](research/NEXT_100_PR_MAP.md) — sequenced infrastructure backlog.

First useful contribution: fix a small bug, improve a test, add a doc consistency check, or make one CLI path easier to use.

### AI agent

Read in this order:

1. [`AGENTS.md`](../AGENTS.md) — primary operating contract.
2. [`CLAUDE.md`](../CLAUDE.md) — concise collaborator guidance.
3. [`docs/getting-started/AGENT_ONBOARDING.md`](getting-started/AGENT_ONBOARDING.md) — task-selection and verification protocol.
4. [`docs/operations/HUMAN_AGENT_COLLABORATION.md`](operations/HUMAN_AGENT_COLLABORATION.md) — human-agent division of labor.
5. [`docs/research/NEXT_100_PR_MAP.md`](research/NEXT_100_PR_MAP.md) — PR-sized work map.

First useful contribution: select one narrow bottleneck, implement it, add tests, update docs, run the relevant checks, and preserve failure modes.

### Reviewer

Read in this order:

1. [`docs/getting-started/REVIEWER_ONBOARDING.md`](getting-started/REVIEWER_ONBOARDING.md) — reviewer roles and checklists.
2. [`docs/evidence/PROOF_LADDER.md`](PROOF_LADDER.md) — claim levels.
3. [`docs/evidence/CLAIM_REVIEW_CHECKLIST.md`](../evidence/CLAIM_REVIEW_CHECKLIST.md) — claim review.
4. [`docs/evidence/BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) — benchmark review.
5. [`docs/trust/RISK_REGISTER.md`](RISK_REGISTER.md) — major risks and mitigations.

First useful contribution: reject or downgrade weak claims, unclear release status, missing baselines, or unreviewable artifacts.

### Computational biologist

Read in this order:

1. [`VISION.md`](../VISION.md) — what the project is trying to become.
2. [`GOAL.md`](../GOAL.md) — concrete milestones and kill rules.
3. [`docs/evidence/METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md) — current benchmark evidence.
4. [`docs/evidence/BENCHMARKING.md`](../evidence/BENCHMARKING.md) — benchmark commands.
5. [`docs/evidence/BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) — benchmark lifecycle and anti-cheating rules.

First useful contribution: add a leakage-resistant benchmark, improve reference curation, challenge a scorer with a cheaper baseline, or add an adapter with documented limitations.

### Data, schema, model, or adapter contributor

Read in this order:

1. [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) — data license and redistribution policy.
2. [`docs/trust/DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) — dataset cards, labels, leakage, release status.
3. [`docs/engineering/SCHEMA_REGISTRY.md`](../engineering/SCHEMA_REGISTRY.md) — structured artifact registry.
4. [`docs/engineering/ADAPTER_AUTHOR_GUIDE.md`](../engineering/ADAPTER_AUTHOR_GUIDE.md) — safe adapter authoring.
5. [`docs/engineering/ARTIFACT_VERSIONING.md`](../engineering/ARTIFACT_VERSIONING.md) — artifact compatibility rules.

First useful contribution: add a dataset card, schema example, adapter card, model card, validator, or license/release-status clarification.

### Microbiologist, peptide scientist, or wet-lab partner

Read in this order:

1. [`docs/review/WET_LAB_HANDOFF.md`](review/WET_LAB_HANDOFF.md) — safe expert-review handoff guide.
2. [`docs/evidence/PROOF_LADDER.md`](PROOF_LADDER.md) — claim ladder from dry-lab nomination to independent validation.
3. [`docs/review/EXTERNAL_REVIEW_PACKET.md`](review/EXTERNAL_REVIEW_PACKET.md) — standard review packet contents.
4. [`docs/review/LAB_PARTNER_ONBOARDING.md`](review/LAB_PARTNER_ONBOARDING.md) — safe partner onboarding boundaries.
5. [`docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md`](review/PRE_REGISTERED_PILOT_TEMPLATE.md) — non-protocol template for freezing pilot logic before qualified testing.

First useful contribution: review whether candidate evidence packages are interpretable and whether success/failure criteria are scientifically meaningful.

### Safety reviewer

Read in this order:

1. [`docs/trust/TRUST_CENTER.md`](TRUST_CENTER.md) — safety, evidence, release, and governance overview.
2. [`SAFETY.md`](../SAFETY.md) — safety posture.
3. [`SECURITY.md`](../SECURITY.md) — safety-sensitive reporting.
4. [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) — release rules.
5. [`docs/trust/SAFETY_DOC_AUDIT.md`](SAFETY_DOC_AUDIT.md) — safety-doc audit history.

First useful contribution: identify where an artifact could be misread, over-released, overclaimed, or used outside scope.

### Funder, institution, or public-interest partner

Read in this order:

1. [`VISION.md`](../VISION.md) — long-term infrastructure thesis.
2. [`docs/research/OPEN_INFRASTRUCTURE_MOAT.md`](OPEN_INFRASTRUCTURE_MOAT.md) — why infrastructure can be durable.
3. [`docs/trust/TRUST_CENTER.md`](TRUST_CENTER.md) — trust architecture.
4. [`docs/research/ADOPTION_METRICS.md`](ADOPTION_METRICS.md) — adoption metrics that value trust over hype.
5. [`GOVERNANCE.md`](../GOVERNANCE.md) — decision governance.

First useful contribution: fund independent validation, benchmark audits, safe result publication, or infrastructure work that makes the project less dependent on any one person or model.

### Maintainer

Read in this order:

1. [`GOVERNANCE.md`](../GOVERNANCE.md) — project governance.
2. [`docs/getting-started/MAINTAINER_GUIDE.md`](getting-started/MAINTAINER_GUIDE.md) — maintainer review rules.
3. [`docs/operations/SUSTAINABILITY_AND_BUS_FACTOR.md`](operations/SUSTAINABILITY_AND_BUS_FACTOR.md) — sustainability and bus-factor plan.
4. [`docs/trust/RISK_REGISTER.md`](RISK_REGISTER.md) — major risks and mitigations.
5. [`docs/trust/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — release checklist.

First useful contribution: make the repo easier to maintain without lowering safety, evidence, or reproducibility standards.

## Core strategic docs

| Document | Job |
|---|---|
| [`VISION.md`](../VISION.md) | Ambitious but grounded long-term vision. |
| [`GOAL.md`](../GOAL.md) | Concrete milestones, kill rules, and metrics. |
| [`MISSION.md`](../MISSION.md) | Scientific mission and claim boundaries. |
| [`GOVERNANCE.md`](../GOVERNANCE.md) | Project decision governance. |
| [`docs/trust/TRUST_CENTER.md`](TRUST_CENTER.md) | Trust front door for safety, evidence, release, governance, and agents. |
| [`docs/research/OPEN_INFRASTRUCTURE_MOAT.md`](OPEN_INFRASTRUCTURE_MOAT.md) | Why OpenAMP should win through reusable trust infrastructure. |
| [`docs/research/NUMBER_ONE_REPO_STANDARD.md`](NUMBER_ONE_REPO_STANDARD.md) | Defines what category leadership means. |
| [`docs/research/WHY_WORK_ON_OPENAMP.md`](WHY_WORK_ON_OPENAMP.md) | Positioning: why serious contributors should choose this repo. |
| [`docs/research/OPEN_BIOTECH_STACK.md`](OPEN_BIOTECH_STACK.md) | Infrastructure thesis and stack model. |
| [`docs/research/ADOPTION_STRATEGY.md`](ADOPTION_STRATEGY.md) | Adoption strategy for humans, agents, labs, and institutions. |
| [`docs/research/ADOPTION_METRICS.md`](ADOPTION_METRICS.md) | Adoption metrics that prioritize trust and reuse over popularity. |
| [`docs/research/NEXT_100_PR_MAP.md`](research/NEXT_100_PR_MAP.md) | PR-sized roadmap for compounding work. |
| [`docs/trust/RISK_REGISTER.md`](RISK_REGISTER.md) | Major risks and mitigations. |
| [`CITATION.cff`](../CITATION.cff) | Citation metadata. |

## Core operating docs

| Document | Job |
|---|---|
| [`AGENTS.md`](../AGENTS.md) | Operating contract for AI agents. |
| [`CLAUDE.md`](../CLAUDE.md) | Concise collaborator guidance. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Contribution rules and PR expectations. |
| [`docs/getting-started/FIRST_RUN_WALKTHROUGH.md`](getting-started/FIRST_RUN_WALKTHROUGH.md) | First-run path for humans and agents. |
| [`docs/operations/HUMAN_AGENT_COLLABORATION.md`](operations/HUMAN_AGENT_COLLABORATION.md) | Human-agent collaboration model. |
| [`docs/getting-started/AGENT_ONBOARDING.md`](getting-started/AGENT_ONBOARDING.md) | Safe agent task protocol. |
| [`docs/getting-started/HUMAN_ONBOARDING.md`](getting-started/HUMAN_ONBOARDING.md) | Human contributor onboarding. |
| [`docs/getting-started/REVIEWER_ONBOARDING.md`](getting-started/REVIEWER_ONBOARDING.md) | Reviewer guide and checklists. |
| [`docs/operations/HIGH_LEVERAGE_TASKS.md`](operations/HIGH_LEVERAGE_TASKS.md) | Task map for humans and agents. |
| [`docs/getting-started/MAINTAINER_GUIDE.md`](getting-started/MAINTAINER_GUIDE.md) | Maintainer review and governance standard. |
| [`docs/operations/SUSTAINABILITY_AND_BUS_FACTOR.md`](operations/SUSTAINABILITY_AND_BUS_FACTOR.md) | Project sustainability and bus-factor plan. |
| [`docs/trust/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) | Release checklist. |
| [`docs/operations/DECISION_RECORD_TEMPLATE.md`](operations/DECISION_RECORD_TEMPLATE.md) | Decision record template. |
| [`docs/operations/DOCS_MAINTENANCE.md`](operations/DOCS_MAINTENANCE.md) | Documentation maintenance rules. |
| [`docs/operations/ISSUE_LABEL_TAXONOMY.md`](operations/ISSUE_LABEL_TAXONOMY.md) | Issue-label system. |

## Core technical docs

| Document | Job |
|---|---|
| [`docs/engineering/ARCHITECTURE.md`](../engineering/ARCHITECTURE.md) | System architecture, trust architecture, data flow, and extension points. |
| [`docs/getting-started/COMMAND_SURFACE.md`](getting-started/COMMAND_SURFACE.md) | Commands, workflows, and claim boundaries. |
| [`docs/engineering/CI_AND_QUALITY_GATES.md`](../engineering/CI_AND_QUALITY_GATES.md) | CI, quality gates, and gate promotion. |
| [`docs/engineering/SCHEMA_REGISTRY.md`](../engineering/SCHEMA_REGISTRY.md) | Human-readable schema and artifact registry. |
| [`docs/engineering/RUN_MANIFEST_STANDARD.md`](../engineering/RUN_MANIFEST_STANDARD.md) | Provenance standard for reproducible runs. |
| [`docs/engineering/ARTIFACT_VERSIONING.md`](../engineering/ARTIFACT_VERSIONING.md) | Artifact versioning and compatibility policy. |
| [`docs/engineering/ADAPTER_AUTHOR_GUIDE.md`](../engineering/ADAPTER_AUTHOR_GUIDE.md) | Safe external adapter authoring. |
| [`docs/evidence/BENCHMARKING.md`](../evidence/BENCHMARKING.md) | Current benchmark suite and commands. |
| [`docs/evidence/BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md) | Benchmark lifecycle and anti-cheating rules. |
| [`docs/evidence/METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md) | Current benchmark state and single source of truth for metrics. |
| [`docs/evidence/EVIDENCE_CERTIFICATE.md`](../evidence/EVIDENCE_CERTIFICATE.md) | Candidate certificate spec. |
| [`docs/evidence/CALIBRATION_POLICY.md`](CALIBRATION_POLICY.md) | Recalibration gate and policy. |
| [`docs/evidence/VIRTUAL_ASSAY_SCOPE.md`](VIRTUAL_ASSAY_SCOPE.md) | What virtual assay modules may and may not claim. |

## Data, model, release, and claims docs

| Document | Job |
|---|---|
| [`DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md) | Data license and redistribution notice. |
| [`docs/trust/DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) | Dataset cards, label governance, leakage, and release status. |
| [`data/README.md`](../data/README.md) | Data directory policy. |
| [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) | Model and artifact release policy. |
| [`docs/trust/MODEL_CARD_TEMPLATE.md`](MODEL_CARD_TEMPLATE.md) | Model, scorer, simulator, generator, and adapter card template. |
| [`models/README.md`](../models/README.md) | Models directory policy. |
| [`docs/evidence/CLAIM_REVIEW_CHECKLIST.md`](../evidence/CLAIM_REVIEW_CHECKLIST.md) | Claim review checklist. |
| [`docs/trust/PUBLICATION_POLICY.md`](PUBLICATION_POLICY.md) | Publication and public claims policy. |

## External review and collaboration docs

| Document | Job |
|---|---|
| [`docs/review/WET_LAB_HANDOFF.md`](review/WET_LAB_HANDOFF.md) | Safe expert-review handoff guide, not a protocol. |
| [`docs/review/LAB_PARTNER_ONBOARDING.md`](review/LAB_PARTNER_ONBOARDING.md) | Safe partner onboarding boundaries. |
| [`docs/review/EXPERT_REVIEW_PACK.md`](review/EXPERT_REVIEW_PACK.md) | Expert review pack template. |
| [`docs/review/EXTERNAL_REVIEW_PACKET.md`](review/EXTERNAL_REVIEW_PACKET.md) | External review packet standard. |
| [`docs/review/PRE_REGISTERED_PILOT_TEMPLATE.md`](review/PRE_REGISTERED_PILOT_TEMPLATE.md) | Non-protocol template for freezing pilot logic before qualified testing. |
| [`docs/review/ASSAY_PREREGISTRATION.md`](review/ASSAY_PREREGISTRATION.md) | Candidate-selection pilot pre-registration template, not a protocol. |
| [`docs/review/COLLABORATION_PLAYBOOK.md`](review/COLLABORATION_PLAYBOOK.md) | External collaboration modes and boundaries. |
| [`docs/evidence/NEGATIVE_RESULT_ARCHIVE.md`](../evidence/NEGATIVE_RESULT_ARCHIVE.md) | Safe negative-result format. |

## Core safety docs

| Document | Job |
|---|---|
| [`SAFETY.md`](../SAFETY.md) | Project safety policy. |
| [`SECURITY.md`](../SECURITY.md) | Security and safety-sensitive reporting. |
| [`docs/trust/SAFETY_DOC_AUDIT.md`](SAFETY_DOC_AUDIT.md) | Safety audit and remediation record for docs. |
| [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md) | Allowed and disallowed use. |
| [`MODEL_RELEASE_POLICY.md`](../MODEL_RELEASE_POLICY.md) | Release policy for models, weights, and sensitive artifacts. |
| [`docs/trust/TRUST_CENTER.md`](TRUST_CENTER.md) | Cross-cutting trust overview. |

## GitHub workflow files

| File | Job |
|---|---|
| [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) | PR checklist for safety, evidence, proof ladder, baselines, and review. |
| [`.github/CODEOWNERS`](../.github/CODEOWNERS) | Review-intent ownership for sensitive areas. |
| [`.github/ISSUE_TEMPLATE/config.yml`](../.github/ISSUE_TEMPLATE/config.yml) | Issue chooser guidance. |
| [`.github/ISSUE_TEMPLATE/bug_report.md`](../.github/ISSUE_TEMPLATE/bug_report.md) | Bug report template. |
| [`.github/ISSUE_TEMPLATE/documentation_improvement.md`](../.github/ISSUE_TEMPLATE/documentation_improvement.md) | Documentation improvement template. |
| [`.github/ISSUE_TEMPLATE/agent_safe_task.md`](../.github/ISSUE_TEMPLATE/agent_safe_task.md) | Agent-safe task template. |
| [`.github/ISSUE_TEMPLATE/benchmark_governance.md`](../.github/ISSUE_TEMPLATE/benchmark_governance.md) | Benchmark proposal/change template. |
| [`.github/ISSUE_TEMPLATE/safety_review.md`](../.github/ISSUE_TEMPLATE/safety_review.md) | Safety/release review template. |
| [`.github/ISSUE_TEMPLATE/model_release_review.md`](../.github/ISSUE_TEMPLATE/model_release_review.md) | Model/artifact release review template. |
| [`.github/ISSUE_TEMPLATE/data_contribution.md`](../.github/ISSUE_TEMPLATE/data_contribution.md) | Data contribution/review template. |
| [`.github/ISSUE_TEMPLATE/claim_review.md`](../.github/ISSUE_TEMPLATE/claim_review.md) | Claim review template. |

## Working loop for any contributor

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

## What not to do

Do not add impressive-sounding biology without evidence.

Do not add a predictor that cannot be challenged by cheap baselines.

Do not publish unscreened high-risk candidate lists.

Do not add operational biological instructions, harmful optimization objectives, or clinical claims.

Do not change a success definition after seeing results.

Do not hide negative results merely because they weaken the story.

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
