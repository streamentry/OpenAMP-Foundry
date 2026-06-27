# OpenAMP Foundry

**OpenAMP Foundry** is a verification-first, dry-lab starter repository for AI-assisted antimicrobial peptide (AMP) discovery.

It is designed around a strict principle:

> Computers can triage, falsify, rank, and document candidates. They do **not** prove biological efficacy. Wet-lab assays are still required before any scientific claim of activity.

This repo gives you a safe starting point for:

- building AMP candidate datasets;
- scoring candidates with transparent baseline heuristics;
- checking novelty against known references;
- penalizing likely safety/synthesis risks;
- selecting diverse candidates;
- generating auditable JSON evidence certificates;
- running a demo pipeline without downloading external biological datasets;
- expanding later with real predictors and CRO/lab validation.

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
  -> lab-ready shortlist, if human review approves
```

## What this repo is not

This repo is **not**:

- a medical product;
- a drug-discovery guarantee;
- a wet-lab protocol collection;
- a pathogen-engineering tool;
- a generator for harmful biological capabilities;
- a replacement for qualified microbiologists, toxicologists, or regulatory experts.

## Safe scope

The default repo contains only toy/demo data and transparent baseline scorers. It deliberately avoids:

- dangerous pathogen protocols;
- instructions for culturing or modifying organisms;
- toxicity-maximizing objectives;
- release of unscreened high-risk candidate lists;
- trained generator weights.

See [`SAFETY.md`](SAFETY.md), [`RESPONSIBLE_USE.md`](RESPONSIBLE_USE.md), and [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md).

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

## Repository map

```text
openamp-foundry/
  .github/workflows/ci.yml             # CI checks
  configs/pipeline.yaml                # scoring weights and thresholds
  data/README.md                       # data policy and external data notes
  docs/PLAN.md                         # detailed execution plan
  docs/ARCHITECTURE.md                 # architecture and threat model
  docs/BENCHMARKING.md                 # leakage-resistant benchmark plan
  docs/EVIDENCE_CERTIFICATE.md         # candidate certificate spec
  examples/                            # toy datasets only
  models/README.md                     # model-release rules; no weights shipped
  outputs/.gitkeep                     # generated files ignored by git
  schemas/                             # JSON schemas
  scripts/                             # helper entrypoints
  src/openamp_foundry/                 # Python package
  tests/                               # baseline tests
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

> A reproducible pipeline can recover known AMP positives, reject weak controls, avoid leakage, and generate a small shortlist of candidates that survive independent wet-lab validation.

## License strategy

- Core code: Apache-2.0.
- Documentation: intended for CC BY 4.0 reuse where marked.
- Third-party data: not bundled unless redistribution is allowed.
- Generator weights and unscreened candidate lists: not released by default.
- Project name and logo: trademark retained.

See [`DATA_LICENSE_NOTICE.md`](DATA_LICENSE_NOTICE.md) and [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md).
