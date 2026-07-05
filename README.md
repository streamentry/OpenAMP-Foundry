# OpenAMP Foundry

**OpenAMP Foundry** is a verification-first, dry-lab starter repository for AI-assisted antimicrobial peptide (AMP) discovery.

It is designed around a strict principle:

> Computers can triage, falsify, rank, and document candidates. They do **not** prove biological efficacy. Wet-lab assays are still required before any scientific claim of activity.

The current repository is a rigorous **dry-lab foundry**.

The larger mission is more ambitious:

> Build an open **wet-lab compression engine** for AMP discovery: a system that helps qualified scientists decide which small number of experiments are most worth running next, then learns from those outcomes.

This repo gives you a safe starting point for:

- building AMP candidate datasets;
- scoring candidates with transparent baseline heuristics;
- checking novelty against known references;
- penalizing likely safety/synthesis risks;
- selecting diverse candidates;
- generating auditable JSON evidence certificates;
- running a demo pipeline without downloading external biological datasets;
- expanding later with real predictors and CRO/lab validation.

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
  -> lab-ready shortlist, if human review approves
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

Turn qualified assay JSON files into a reproducible review artifact:

```bash
python -m openamp_foundry.cli lab-result-report \
  --results-dir outputs/lab_results \
  --out-json outputs/lab_result_report.json \
  --out-md outputs/lab_result_report.md
```

Join panel predictions with validated lab result actuals:

```bash
python -m openamp_foundry.cli calibration-intake \
  --predictions outputs/predictions.csv \
  --results-dir outputs/lab_results \
  --panel-name "wave1" \
  --out-json outputs/calibration_intake_report.json
```

Evaluate whether a calibration-intake report satisfies the pre-registered recalibration policy:

```bash
python -m openamp_foundry.cli recalibration-gate \
  --intake outputs/calibration_intake_report.json \
  --policy configs/recalibration_policy.yaml \
  --out-json outputs/gate_verdict.json
```

Exit code 0 means the gate allows recalibration; exit code 3 means the policy rejects it.

Bias-aware pilot panel selection for under-ranked structural classes:

```bash
python -m openamp_foundry.cli pilot-panel \
  --ranked outputs/demo_ranked.jsonl \
  --out-csv outputs/pilot_panel.csv \
  --min-per-structural-class 1
```

This is a panel-construction guard, not a claim that those classes are better.
It only prevents the current charge-dominated ranker from excluding low-charge,
proline-rich, short, or cysteine-rich scaffolds by default.

## Repository map

```text
openamp-foundry/
  AGENTS.md                            # agent operating contract and safety mission
  CLAUDE.md                            # concise collaborator guidance
  MISSION.md                           # project mission and claim boundaries
  .github/workflows/ci.yml             # CI checks
  configs/pipeline.yaml                # scoring weights and thresholds
  configs/phase3.yaml                  # wet-lab-ready batch configuration
  configs/recalibration_policy.yaml    # pre-registered recalibration policy
  data/README.md                       # data policy and external data notes
  docs/50_LOOP_PLAN.md                 # 50-loop strategic execution plan
  docs/ARCHITECTURE.md                 # architecture and threat model
  docs/BENCHMARKING.md                 # leakage-resistant benchmark plan
  docs/CALIBRATION_POLICY.md           # pre-registered recalibration policy
  docs/DECISION_RULES.md               # pre-registered pass/fail gates
  docs/EVIDENCE_CERTIFICATE.md         # candidate certificate spec
  docs/LEGACY_LOOP_PROMPT.md           # reusable execution loop prompt
  docs/METRICS_CURRENT.md              # current benchmark summary
  docs/NEW_VISION.md                   # next-horizon wet-lab compression vision
  docs/PLAN.md                         # detailed execution plan
  docs/ROADMAP.md                      # shipped milestones and next horizons
  docs/WET_LAB_HANDOFF.md              # assay package and wet-lab review notes
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

The longer-range milestone is:

> A calibrated virtual assay layer helps the project choose fewer, smarter wet-lab experiments and improves hit-rate or safety-adjusted yield relative to cheap predictors alone.

## License strategy

- Core code: Apache-2.0.
- Documentation: intended for CC BY 4.0 reuse where marked.
- Third-party data: not bundled unless redistribution is allowed.
- Generator weights and unscreened candidate lists: not released by default.
- Project name and logo: trademark retained.

See [`DATA_LICENSE_NOTICE.md`](DATA_LICENSE_NOTICE.md) and [`MODEL_RELEASE_POLICY.md`](MODEL_RELEASE_POLICY.md).
