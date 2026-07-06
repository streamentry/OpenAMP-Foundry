# Benchmark Governance

## Purpose

This document defines how OpenAMP Foundry should create, change, retire, and interpret benchmarks.

Benchmarks are not decorations. They are the project’s immune system against self-deception.

## Prime rule

**No model, scorer, simulator, selector, or calibration change earns authority until it survives fair comparison against cheap baselines and documented failure modes.**

## Why governance is necessary

AMP discovery benchmarks are easy to fool.

A model can appear strong by exploiting:

- charge differences;
- length differences;
- database-source artifacts;
- near-duplicate leakage;
- canonical amphipathic-helix bias;
- easy random decoys;
- post-hoc threshold tuning;
- selective publication of favorable splits;
- hidden reuse of reference sequences.

Benchmark governance exists because accidental cheating is still cheating.

## Benchmark lifecycle

Every benchmark should move through five stages.

```text
proposal -> implementation -> adversarial review -> gated use -> maintenance/deprecation
```

## Stage 1 — Proposal

A benchmark proposal must state:

- what question it answers;
- what claim it gates;
- what dataset it uses;
- what licenses apply;
- what leakage risks exist;
- what cheap baselines must be compared;
- what failure would mean;
- whether it is exploratory or release-gating.

A benchmark without a target claim is noise.

## Stage 2 — Implementation

A benchmark implementation should include:

- deterministic script or CLI command;
- documented input paths;
- frozen random seed if sampling is used;
- output JSON artifact;
- human-readable summary;
- tests for parser and metric behavior;
- Makefile target where appropriate.

The benchmark must be runnable by a fresh contributor.

## Stage 3 — Adversarial review

Before a benchmark gates claims, reviewers should attack it.

Ask:

1. Could charge alone explain the result?
2. Could sequence length explain it?
3. Could similarity to known AMPs explain it?
4. Could train/test leakage explain it?
5. Could database source explain it?
6. Could negative-set construction make the task too easy?
7. Could threshold tuning after inspection explain it?
8. Does the result survive family stratification?
9. Does the result survive cross-dataset testing?
10. Is the confidence interval wide enough to make the result unstable?

If these attacks are not answered, the benchmark should stay exploratory.

## Stage 4 — Gated use

A benchmark may gate releases or integration only when:

- inputs are documented;
- outputs are deterministic;
- cheap baselines are included;
- known limitations are recorded;
- thresholds are pre-registered;
- metric drift is visible in `docs/METRICS_CURRENT.md`;
- CI or a manual release checklist enforces the relevant gate.

## Stage 5 — Maintenance and deprecation

Benchmarks age.

A benchmark should be reviewed or deprecated when:

- a better dataset becomes available;
- leakage is discovered;
- cheap baselines now beat the pipeline;
- the benchmark no longer matches the claim;
- the dataset license changes;
- the result is too easy to game;
- the biological question changes.

Deprecation is not failure. Keeping a misleading benchmark is failure.

## Benchmark classes

### Exploratory benchmark

Purpose: learn where signal may exist.

Allowed use: documentation, research direction, hypothesis generation.

Forbidden use: production ranking authority, public discovery claims.

### Informational benchmark

Purpose: inspect a model or module but not affect selection.

Allowed use: report fields, reviewer context, future planning.

Forbidden use: candidate ranking impact.

### Gate benchmark

Purpose: enforce minimum quality for integration or release.

Allowed use: CI, release decisions, integration permission.

Required: pre-registered threshold and regression tolerance.

### Kill benchmark

Purpose: disprove an overconfident claim.

Allowed use: downgrading, disabling, or removing modules.

Required: result must be documented even if embarrassing.

## Required benchmark card

Every serious benchmark should have a card with these fields:

```yaml
benchmark_id: stable-name
title: human-readable title
status: exploratory | informational | gate | deprecated
claim_gated: what this benchmark allows or blocks
dataset_sources: list of sources
license_status: redistribution / reference-only / restricted
n_positive: number
n_negative: number
negative_construction: method
split_method: method
leakage_controls: list
cheap_baselines: list
primary_metric: AUROC/AUPRC/precision@k/etc
secondary_metrics: list
pre_registered_threshold: value or none
confidence_interval_method: method
known_biases: list
failure_interpretation: what failure means
last_updated: YYYY-MM-DD
owner: maintainer or reviewer
```

## Cheap-baseline policy

A benchmark without cheap baselines is incomplete.

Common baselines:

- random valid selection;
- charge density;
- net charge;
- length;
- hydrophobicity;
- hydrophobic moment;
- sequence similarity to known AMPs;
- simple selectivity proxy;
- previous released pipeline.

The baseline does not need to be fair to the model’s ego.

It needs to be fair to the scientific claim.

## Threshold policy

Thresholds must be set before inspecting held-out results whenever the result gates a claim.

If a threshold changes after inspection:

1. record the reason;
2. mark the previous result as non-confirmatory;
3. create or reserve a fresh validation set where possible;
4. update documentation;
5. require human review.

Silent threshold drift is forbidden.

## CI gate policy

A CI benchmark gate should fail when:

- a required output is missing;
- schema validation fails;
- a metric falls outside tolerance;
- a prohibited action is detected;
- a source-of-truth metric is stale;
- a gate benchmark no longer matches documented thresholds.

CI gates are not only engineering checks. They are scientific integrity checks.

## How to report a benchmark failure

A benchmark failure report should include:

- benchmark name;
- commit hash;
- command run;
- observed metric;
- expected threshold;
- cheap-baseline result;
- likely cause;
- claim that must be downgraded;
- next action.

Do not bury failures in commit messages.

## What benchmark success does not prove

Benchmark success does not prove:

- biological activity;
- clinical value;
- human safety;
- novelty beyond the reference set;
- mechanism;
- broad generalization;
- usefulness under real assay conditions.

It proves only that a defined computational test passed.

## What benchmark failure may prove

Benchmark failure may prove:

- the model is exploiting a shortcut;
- the benchmark is too hard or badly designed;
- a claim was too strong;
- a module should remain informational;
- a ranking rule should not change;
- more data or a better comparison is needed.

This is useful information.

## Review roles

### Benchmark author

Builds the benchmark and documents intended use.

### Adversarial reviewer

Tries to explain the result by cheap artifacts.

### Safety reviewer

Checks whether benchmark outputs could encourage unsafe release or claims.

### Maintainer

Decides whether the benchmark becomes exploratory, informational, gate, or deprecated.

## Benchmark governance motto

A benchmark should make the project harder to fool.

If it makes the project easier to market but not harder to fool, it is not doing its job.
