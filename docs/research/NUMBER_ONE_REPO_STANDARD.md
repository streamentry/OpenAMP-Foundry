# Number-One Repo Standard

## Purpose

This document defines what it means for OpenAMP Foundry to become the number-one open repository for humans and AI agents working on trustworthy antimicrobial peptide experiment selection.

The standard is intentionally severe.

OpenAMP should not become number one by being loud. It should become number one by being the most useful, safest, hardest-to-fool, easiest-to-extend, and most scientifically honest place to do this work.

## One-line standard

**OpenAMP is number one when serious outsiders trust its process even when they disagree with its current models.**

That is the target.

## The seven pillars

```text
1. Trustworthy evidence
2. Safe openness
3. Easy first run
4. Agent-ready execution
5. Human expert usefulness
6. Benchmark honesty
7. External adoption of artifacts
```

A repo that lacks any one of these is not the category leader.

## Pillar 1 — Trustworthy evidence

Every important output should answer:

- What produced this?
- Which inputs were used?
- Which config was used?
- Which commit produced it?
- Which baselines were challenged?
- Which gates passed or failed?
- Which uncertainty remains?
- Which claims are not supported?

Evidence should be inspectable by people who do not trust the maintainers.

### Number-one bar

A serious reviewer can reconstruct a candidate-selection decision from repository artifacts alone.

### Failure mode

The repo becomes a model demo that asks users to trust opaque scores.

## Pillar 2 — Safe openness

The project should be open where openness creates public value and conservative where release creates misuse risk.

Open by default:

- code for validation, scoring, benchmarking, reporting, and schemas;
- transparent baseline scorers;
- toy/demo data;
- evidence-certificate tools;
- safety filters;
- benchmark infrastructure;
- negative-result formats where safe.

Restricted, delayed, or reviewed by default:

- unscreened high-risk candidate lists;
- high-throughput generator weights;
- harmful objectives;
- sensitive datasets;
- operational wet-lab details;
- artifacts that could materially increase biological misuse capability.

### Number-one bar

A safety reviewer can point to exact docs, policies, gates, and defaults that prevent foreseeable misuse.

### Failure mode

The repo confuses openness with unrestricted release.

## Pillar 3 — Easy first run

The first run should be boring.

A new human or agent should not need private maintainer knowledge to install, run the demo, inspect outputs, and understand what the outputs do not prove.

### Number-one bar

A new contributor can:

1. understand the project in 5 minutes;
2. run the demo in 15 minutes;
3. inspect generated evidence in 30 minutes;
4. identify a safe first contribution in 60 minutes.

### Failure mode

The repo has impressive docs but the first workflow is brittle.

## Pillar 4 — Agent-ready execution

AI agents can be useful here only if the repo gives them constraints.

Agents need:

- a primary operating contract;
- allowed and disallowed task classes;
- safe defaults;
- clear verification commands;
- doc index;
- claim ladder;
- task map;
- benchmark gates;
- review requirements.

### Number-one bar

A fresh agent can complete a narrow useful task without broadening biological scope, overclaiming, or bypassing safety review.

### Failure mode

Agents create plausible scientific-looking content that weakens truth and safety.

## Pillar 5 — Human expert usefulness

The repo should make qualified humans more effective.

For engineers, it should expose clean interfaces and tests.

For computational scientists, it should expose benchmarks and baselines.

For wet-lab experts, it should expose candidate rationale, not unsafe protocols.

For safety reviewers, it should expose release boundaries.

For funders and institutions, it should expose milestones and kill rules.

### Number-one bar

Each serious role has a clear entrypoint, useful artifact, and contribution path.

### Failure mode

The repo is understandable only to the original author.

## Pillar 6 — Benchmark honesty

The repo should be harder to fool than its competitors.

Every advanced module should be attacked by:

- random baselines;
- cheap physicochemical baselines;
- similarity baselines;
- charge-matched controls;
- family-stratified analysis;
- cross-dataset checks;
- leakage checks;
- ablation studies;
- negative-result records.

### Number-one bar

A model that does not beat cheap baselines cannot silently affect ranking.

### Failure mode

A sophisticated model wins because the benchmark is weak.

## Pillar 7 — External adoption of artifacts

The strongest adoption signal is not stars.

The strongest signal is that external groups reuse OpenAMP artifacts even when they do not use OpenAMP scoring.

High-value reusable artifacts:

- candidate manifest format;
- evidence certificate format;
- benchmark card format;
- result intake schema;
- negative-result archive format;
- adapter contract;
- recalibration report;
- pre-registered pilot template;
- proof ladder.

### Number-one bar

An external group can use OpenAMP formats to make its own candidate-selection workflow more auditable.

### Failure mode

OpenAMP is useful only if everyone adopts its internal scorer.

## Number-one scorecard

| Category | Bronze | Silver | Gold | Number-one bar |
|---|---|---|---|---|
| First run | Demo runs | Outputs understandable | Reproducible report | New user contributes safely in one session |
| Evidence | Scores visible | Certificates valid | Baselines included | External reviewer reconstructs decision |
| Safety | Policy exists | Release rules exist | Safety gates affect workflow | Unsafe contribution paths are structurally difficult |
| Agents | AGENTS.md exists | Task protocol exists | Agent-safe tasks documented | Fresh agent improves repo without overclaiming |
| Benchmarks | AUROC reported | CIs reported | Cheap baselines reported | Failed baselines block integration |
| Wet-lab bridge | Handoff doc exists | Review packet exists | Pre-registration exists | Qualified partner can evaluate without private context |
| Ecosystem | Docs readable | Adapters possible | Schemas stable | External groups reuse artifacts |

## What must never be sacrificed

Do not sacrifice safety for adoption.

Do not sacrifice evidence for excitement.

Do not sacrifice reproducibility for speed.

Do not sacrifice claim discipline for attention.

Do not sacrifice baseline honesty for model prestige.

## The repo promise

A contributor should be able to trust that OpenAMP rewards the right behavior:

- finding flaws;
- publishing safe negative results;
- strengthening baselines;
- reducing ambiguity;
- improving reproducibility;
- rejecting overclaims;
- making external review easier.

That culture is the real product.

## The final test

OpenAMP becomes number one when the most skeptical qualified reviewer says:

> I do not trust biological prediction easily, but this repo gives me enough evidence, caveats, baselines, and safety boundaries to evaluate its claims seriously.

Build for that reviewer.
