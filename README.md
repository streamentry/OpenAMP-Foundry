# OpenAMP Foundry

**OpenAMP Foundry** is a verification-first, safety-constrained dry-lab foundry for AI-assisted antimicrobial peptide (AMP) discovery.

It is designed around a strict principle:

> Computers can triage, falsify, rank, and document candidates. They do **not** prove biological efficacy. Wet-lab assays are still required before any scientific claim of activity.

The current repository is a rigorous **dry-lab foundry**.

The larger mission is more ambitious:

> Build an open **wet-lab compression engine** for AMP discovery: a system that helps qualified scientists decide which small number of experiments are most worth running next, then learns from those outcomes.

The long-term infrastructure ambition is described in [`VISION.md`](VISION.md), [`GOAL.md`](GOAL.md), [`docs/OPEN_BIOTECH_STACK.md`](docs/OPEN_BIOTECH_STACK.md), [`docs/NUMBER_ONE_REPO_STANDARD.md`](docs/NUMBER_ONE_REPO_STANDARD.md), and [`docs/TRUST_CENTER.md`](docs/TRUST_CENTER.md).

## Start here

| You are | Read first | Then read |
|---|---|---|
| New human contributor | [`docs/HUMAN_ONBOARDING.md`](docs/HUMAN_ONBOARDING.md) | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/COMMAND_SURFACE.md`](docs/COMMAND_SURFACE.md) |
| AI agent | [`AGENTS.md`](AGENTS.md) | [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md), [`docs/HUMAN_AGENT_COLLABORATION.md`](docs/HUMAN_AGENT_COLLABORATION.md) |
| Reviewer | [`docs/REVIEWER_ONBOARDING.md`](docs/REVIEWER_ONBOARDING.md) | [`docs/CLAIM_REVIEW_CHECKLIST.md`](docs/CLAIM_REVIEW_CHECKLIST.md), [`docs/BENCHMARK_GOVERNANCE.md`](docs/BENCHMARK_GOVERNANCE.md) |
| Computational scientist | [`docs/METRICS_CURRENT.md`](docs/METRICS_CURRENT.md) | [`docs/BENCHMARKING.md`](docs/BENCHMARKING.md), [`docs/BENCHMARK_GOVERNANCE.md`](docs/BENCHMARK_GOVERNANCE.md) |
| Wet-lab/domain expert | [`docs/WET_LAB_HANDOFF.md`](docs/WET_LAB_HANDOFF.md) | [`docs/EXTERNAL_REVIEW_PACKET.md`](docs/EXTERNAL_REVIEW_PACKET.md), [`docs/PRE_REGISTERED_PILOT_TEMPLATE.md`](docs/PRE_REGISTERED_PILOT_TEMPLATE.md) |
| Safety reviewer | [`docs/TRUST_CENTER.md`](docs/TRUST_CENTER.md) | [`SAFETY.md`](SAFETY.md), [`SECURITY.md`](SECURITY.md) |
| Data/model contributor | [`docs/DATA_GOVERNANCE.md`](docs/DATA_GOVERNANCE.md) | [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md), [`docs/MODEL_CARD_TEMPLATE.md`](docs/MODEL_CARD_TEMPLATE.md) |
| Funder/institution | [`VISION.md`](VISION.md) | [`GOAL.md`](GOAL.md), [`docs/ADOPTION_METRICS.md`](docs/ADOPTION_METRICS.md) |
| Maintainer | [`GOVERNANCE.md`](GOVERNANCE.md) | [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md), [`docs/CI_AND_QUALITY_GATES.md`](docs/CI_AND_QUALITY_GATES.md) |

## Why this repo exists

AI generation is cheap.

Trusted candidate selection is scarce.

OpenAMP Foundry exists to build the open evidence layer between AI-generated biological hypotheses and qualified experimental testing. The project is not trying to make biology look solved by software. It is trying to make experiment selection more reproducible, auditable, baseline-aware, and safe.

This repo gives you a safe starting point for:

- building AMP candidate datasets;
- scoring candidates with transparent baseline heuristics;
- checking novelty against known references;
- penalizing likely safety/synthesis risks;
- selecting diverse candidates;
- generating auditable JSON evidence certificates;
- bundling expert-review packs with provenance and identity hashes;
- running a demo pipeline without downloading external biological datasets;
- expanding later with real predictors and qualified external validation.

It also establishes the architecture and governance needed for a future **virtual assay layer** that can improve experiment selection without pretending to replace biology.

## What this repo is

A starter implementation of a **computer-first AMP candidate foundry**:

```text
candidate sequences
  -> validity checks
  -> physicochemical features
  -> activity-likeness score
  -> safety-risk score
  -> synthesis-feasibility score
  -> novelty score against references
  -> ensemble rank
  -> evidence certificate
  -> chain-of-custody hash manifest
  -> expert-review package, if human review approves
```

The present repo answers:

> Can we build a reproducible, leakage-aware, safety-first ranking pipeline that earns the right to guide real experiments?

The next-horizon repo should answer:

> Can we compress wet-lab cost by learning which peptide experiments are worth running, better than cheap predictors alone?

## What this repo is not

This repo is **not**:

- a medical product;
- a drug-discovery guarantee;
- a wet-lab protocol collection;
- an unsafe biological-design tool;
- a generator for harmful biological capabilities;
- a replacement for qualified microbiologists, toxicologists, or regulatory experts.

## Safe scope

The default repo contains only toy/demo data and transparent baseline scorers. It deliberately avoids:

- operational biological instructions;
- unsafe optimization objectives;
- release of unscreened high-risk candidate lists;
- trained generator weights;
- clinical or medical advice.

See [`SAFETY.md`](SAFETY.md), [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md), and [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md).

## Vision ladder

OpenAMP now operates on two connected horizons:

1. **Current horizon — trustworthy dry lab**
   Build deterministic ranking, evidence certificates, leakage-resistant benchmarks, novelty auditing, synthesis checks, and reviewable shortlist generation.
2. **Next horizon — wet-lab compression**
   Add higher-fidelity membrane, selectivity, stability, and learned-surrogate layers that improve which 8-12 experiments a qualified lab should run next.

The second horizon only matters if the first one stays honest. Better simulation without calibration is not a breakthrough.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make demo
```

Or run directly:

```bash
python -m openamp_foundry.cli rank \
  --candidates examples/sequences/demo_candidates.csv \
  --references examples/known_reference/demo_known_amps.csv \
  --out outputs/demo_ranked.jsonl \
  --report outputs/demo_report.md
```

Validate one generated evidence certificate:

```bash
python -m openamp_foundry.cli validate \
  --certificate outputs/evidence/AMPF-000001.json \
  --schema schemas/candidate.schema.json
```

For command interpretation, read [`docs/COMMAND_SURFACE.md`](docs/COMMAND_SURFACE.md). Commands produce artifacts; artifacts support claims only when the proof ladder allows them.

## Repository map

```text
openamp-foundry/
  README.md                              # primary entrypoint
  VISION.md                              # long-term infrastructure vision
  GOAL.md                                # milestones, kill rules, metrics
  MISSION.md                             # project mission and claim boundaries
  GOVERNANCE.md                          # decision governance
  AGENTS.md                              # agent operating contract
  CLAUDE.md                              # concise collaborator guidance
  CONTRIBUTING.md                        # contributor workflow and PR checklist
  SAFETY.md                              # safety policy
  SECURITY.md                            # security and safety-sensitive reporting
  RESPONSIBLE_USE.md                     # allowed/disallowed use
  MODEL_RELEASE_POLICY.md                # model and artifact release policy
  DATA_LICENSE_NOTICE.md                 # data license and redistribution policy
  CITATION.cff                           # citation metadata
  .github/PULL_REQUEST_TEMPLATE.md       # PR checklist
  .github/ISSUE_TEMPLATE/                # agent, benchmark, data, safety, release, claim templates
  configs/                               # scoring and recalibration policy
  data/README.md                         # data directory rules
  models/README.md                       # model directory rules
  docs/PROJECT_INDEX.md                  # human/agent navigation hub
  docs/TRUST_CENTER.md                   # safety/evidence/governance trust front door
  docs/NUMBER_ONE_REPO_STANDARD.md       # category-leader standard
  docs/NEXT_100_PR_MAP.md                # PR-sized roadmap for compounding work
  docs/COMMAND_SURFACE.md                # command workflows and claim boundaries
  docs/CI_AND_QUALITY_GATES.md           # CI and quality gates
  docs/HUMAN_AGENT_COLLABORATION.md      # human-agent collaboration model
  docs/REVIEWER_ONBOARDING.md            # reviewer guide
  docs/ADOPTION_METRICS.md               # adoption metrics focused on trust
  docs/DECISION_RECORD_TEMPLATE.md       # decision record template
  docs/HUMAN_ONBOARDING.md               # human contributor onboarding
  docs/AGENT_ONBOARDING.md               # agent task protocol
  docs/WHY_WORK_ON_OPENAMP.md            # contributor positioning thesis
  docs/OPEN_BIOTECH_STACK.md             # Linux-for-biotech infrastructure thesis
  docs/ADOPTION_STRATEGY.md              # adoption strategy
  docs/PROOF_LADDER.md                   # evidence levels and claim ladder
  docs/CLAIM_REVIEW_CHECKLIST.md         # claim review checklist
  docs/SAFETY_DOC_AUDIT.md               # safety audit and remediation record
  docs/DATA_GOVERNANCE.md                # data governance standard
  docs/MODEL_CARD_TEMPLATE.md            # model/adapter card template
  docs/ARTIFACT_VERSIONING.md            # artifact compatibility policy
  docs/RELEASE_CHECKLIST.md              # release checklist
  docs/COLLABORATION_PLAYBOOK.md         # external collaboration rules
  docs/EXTERNAL_REVIEW_PACKET.md         # external review packet standard
  docs/PRE_REGISTERED_PILOT_TEMPLATE.md  # non-protocol pilot planning template
  docs/HIGH_LEVERAGE_TASKS.md            # task map for humans and agents
  docs/MAINTAINER_GUIDE.md               # maintainer review rules
  docs/DOCS_MAINTENANCE.md               # documentation governance
  docs/ISSUE_LABEL_TAXONOMY.md           # issue labels and triage system
  docs/BENCHMARKING.md                   # benchmark suite
  docs/BENCHMARK_GOVERNANCE.md           # benchmark lifecycle and governance
  docs/METRICS_CURRENT.md                # current benchmark summary
  docs/CALIBRATION_POLICY.md             # recalibration gate policy
  docs/EVIDENCE_CERTIFICATE.md           # candidate certificate spec
  docs/VIRTUAL_ASSAY_SCOPE.md            # virtual-assay scope and gates
  docs/WET_LAB_HANDOFF.md                # safe expert-review handoff guide
  examples/                              # toy datasets only
  outputs/.gitkeep                       # generated files ignored by git
  schemas/                               # JSON schemas
  scripts/                               # helper entrypoints
  src/openamp_foundry/                   # Python package
  tests/                                 # baseline tests
```

## Philosophy

The project optimizes for **honest candidate selection**, not impressive claims.

A candidate is only worth lab money if it survives independent attacks:

- basic validity;
- novelty check;
- synthesis feasibility;
- predicted activity;
- predicted safety;
- diversity selection;
- reproducible evidence bundle;
- human review.

The first serious milestone is not “AI discovered an antibiotic.”

The first serious milestone is:

> A reproducible pipeline can recover known AMP positives, reject weak controls, avoid leakage, and generate a small shortlist of candidates that survives qualified external review.

The longer-range milestone is:

> A calibrated virtual assay layer helps the project choose fewer, smarter experiments and improves hit-rate or safety-adjusted yield relative to cheap predictors alone.

## License strategy

- Core code: Apache-2.0.
- Documentation: intended for CC BY 4.0 reuse where marked.
- Third-party data: not bundled unless redistribution is allowed.
- Generator weights and unscreened candidate lists: not released by default.
- Project name and logo: trademark retained.
