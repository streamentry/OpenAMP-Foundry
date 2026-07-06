# Command Surface

## Purpose

This document explains the OpenAMP command surface for humans and agents.

A repo becomes agent-friendly when its important workflows are discoverable, reproducible, and mapped to evidence levels.

## Prime rule

**Commands produce artifacts. Artifacts support claims only when the proof ladder allows them.**

A ranking command does not prove biology.

A benchmark command does not prove real-world utility.

A recalibration command does not by itself authorize behavior changes.

## Workflow map

```text
first run
  -> demo ranking
  -> evidence certificates
  -> benchmark checks
  -> candidate panel construction
  -> external review packet
  -> structured result intake
  -> recalibration gate
  -> human-reviewed decision
```

## First-run commands

### Install and demo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make demo
```

Expected outputs:

- ranked demo candidates;
- demo report;
- evidence certificates;
- run manifest.

Claim level: dry-lab demonstration only.

### Test

```bash
make test
make lint
make ci
```

Claim level: engineering quality evidence, not scientific evidence.

## Ranking workflow

The ranking workflow takes candidate records and reference records, computes dry-lab features, produces a ranked artifact, and emits evidence certificates.

Allowed claim:

> Candidates were computationally ranked by a reproducible dry-lab pipeline.

Not allowed:

> Candidates are active, safe, or validated.

## Evidence-certificate workflow

Certificate validation checks structure and required fields.

It does not establish biological truth.

A valid certificate is a review artifact.

## Benchmark workflow

Benchmarks should be interpreted using:

- [`docs/evidence/BENCHMARKING.md`](../evidence/BENCHMARKING.md)
- [`docs/evidence/BENCHMARK_GOVERNANCE.md`](../evidence/BENCHMARK_GOVERNANCE.md)
- [`docs/evidence/METRICS_CURRENT.md`](../evidence/METRICS_CURRENT.md)

Important benchmark families include:

- scoring validation;
- expanded benchmark runs;
- easy-baseline comparisons;
- charge-matched checks;
- order-dependence checks;
- precision-at-k checks;
- family-stratified checks;
- simulation ablations;
- benchmark gates.

Allowed claim:

> The pipeline passed or failed a specified benchmark under stated assumptions.

Not allowed:

> Benchmark success proves biological activity or safety.

## Panel-construction workflow

Panel-construction commands should be treated as experiment-selection planning tools.

A candidate panel is not a top-k dump. It should explain roles such as:

- likely lead hypothesis;
- baseline challenger;
- uncertainty probe;
- diversity probe;
- control or comparison role where appropriate.

Panel outputs require human review before any external-facing use.

## Structured result-intake workflow

Structured result-intake commands join prior predictions with qualified result summaries at a safe abstraction level.

They describe what happened.

They do not update model behavior.

They do not create clinical, safety, or broad biological claims.

## Recalibration workflow

The recalibration gate evaluates whether a structured intake artifact satisfies a pre-registered policy.

A positive gate verdict means recalibration may be considered.

A negative gate verdict means recalibration is rejected.

Neither result should be hidden.

Any proposed update requires human review and a decision record.

## Agent command policy

Agents should prefer commands that:

- validate structure;
- run tests;
- compare baselines;
- generate reports;
- inspect artifacts;
- check docs;
- preserve limitations.

Agents must not use commands to produce public candidate releases without human review.

## Command documentation standard

Every important command should document:

- purpose;
- inputs;
- outputs;
- proof-ladder level;
- allowed claim;
- disallowed claim;
- safety impact;
- related source-of-truth docs.

## Final standard

A serious contributor should be able to run a command, inspect its output, and understand exactly what that output does and does not prove.
