# The Open Biotech Stack

## Purpose

This document explains how OpenAMP Foundry can grow from a dry-lab antimicrobial peptide pipeline into a reusable open infrastructure pattern for biotech.

The ambition is large, but it must be earned through narrow evidence.

## The short thesis

The next important open-source layer in biotech is not merely a model that generates biological designs.

It is a trustworthy stack for deciding which AI-generated biological hypotheses deserve real experiments, recording what happened, and learning without rewriting history.

OpenAMP Foundry is an attempt to build that stack first for antimicrobial peptides.

## The problem with “AI for biology”

AI can produce abundant biological suggestions.

Biology cannot test abundant suggestions cheaply.

This creates a new bottleneck:

```text
old bottleneck: generating hypotheses
new bottleneck: selecting experiments worth running
```

A system that generates 100,000 plausible peptides is not automatically useful.

A system that helps a qualified lab choose the 8–12 most informative candidates for the next assay may be useful.

A system that learns from the result of that assay and improves the next batch may become infrastructure.

## The Linux analogy

Linux became powerful because it became a dependable neutral layer that many competing groups could build on.

The OpenAMP version of that ambition is not a kernel for all biology.

It is a neutral experimental-decision layer for a constrained biological design problem.

The analogy only holds if OpenAMP becomes:

- open enough to inspect;
- stable enough to build on;
- boring enough to trust;
- modular enough to extend;
- safe enough to release responsibly;
- rigorous enough to survive hostile review;
- useful enough that independent groups adopt its artifacts.

A slogan does not make infrastructure.

Repeated external use does.

## The stack model

OpenAMP should become a layered stack.

```text
Layer 0: Safety and governance
Layer 1: Data provenance and licensing
Layer 2: Candidate validation and normalization
Layer 3: Feature extraction and baseline scoring
Layer 4: Novelty, safety-risk, synthesis, and diversity checks
Layer 5: Benchmarking and leakage resistance
Layer 6: Evidence certificates and candidate manifests
Layer 7: External predictor and virtual-assay adapters
Layer 8: Human review and lab-handoff packages
Layer 9: Result intake and negative-result archive
Layer 10: Calibration and active learning
Layer 11: Cross-lab reproducibility and governance memory
```

The upper layers are only trustworthy if the lower layers are boring and stable.

## Layer 0 — Safety and governance

Safety is the base layer.

The project must maintain clear boundaries around:

- harmful biological optimization;
- pathogen handling;
- wet-lab protocols;
- unscreened candidate release;
- model-weight release;
- clinical language;
- human-review requirements.

Without safety, openness becomes fragile.

## Layer 1 — Data provenance and licensing

Biology projects often fail silently through data confusion.

OpenAMP should make these distinctions explicit:

- generated candidates;
- public reference data;
- benchmark positives;
- benchmark negatives;
- known controls;
- lab-tested candidates;
- failed candidates;
- restricted or non-redistributable data.

Every dataset should have provenance, license status, date, known bias, and intended use.

## Layer 2 — Candidate validation and normalization

Before scoring, the system should reject or flag invalid candidates.

This includes:

- invalid amino-acid symbols;
- malformed rows;
- duplicate sequences;
- length outliers;
- obvious synthesis problems;
- missing metadata;
- unsafe release context.

A clean pipeline starts by refusing bad inputs.

## Layer 3 — Feature extraction and baseline scoring

Baseline scoring is not a temporary embarrassment.

It is the permanent adversary of model hype.

The stack should preserve transparent baselines such as:

- charge;
- length;
- hydrophobicity;
- amphipathicity;
- similarity;
- simple selectivity proxies;
- random valid selection.

Advanced models earn authority only by beating these under fair tests.

## Layer 4 — Novelty, safety-risk, synthesis, and diversity

A candidate is not useful merely because it scores high for predicted activity.

The project must score and report:

- novelty against known references;
- similarity to known families;
- predicted hemolysis/cytotoxicity risk;
- synthesis feasibility;
- redundancy inside a panel;
- structural-class diversity;
- known model blind spots.

A panel should be designed as an experiment, not scraped from the top of a ranking table.

## Layer 5 — Benchmarking and leakage resistance

The stack must assume benchmarks are easy to fool.

Important benchmark defenses include:

- train/reference/test separation;
- near-duplicate detection;
- charge-matched controls;
- composition-matched controls;
- family-stratified performance;
- cross-dataset evaluation;
- cheap-baseline comparisons;
- regression gates in CI;
- explicit benchmark cards.

A benchmark result is useful only if the easiest cheating explanation has been attacked.

## Layer 6 — Evidence certificates and candidate manifests

A selected candidate should carry a machine-readable evidence package.

A useful certificate should answer:

- What is the sequence?
- Where did it come from?
- What config scored it?
- What features were computed?
- What baselines did it beat?
- What novelty checks were run?
- What safety risks were flagged?
- What failure modes remain?
- What exact code version produced this output?

This is how a dry-lab decision becomes reviewable.

## Layer 7 — External predictor and virtual-assay adapters

The stack should welcome better models without trusting them by default.

Adapters should be:

- versioned;
- explicit about scope;
- optional;
- fail-closed;
- provenance-preserving;
- compared against baselines;
- forbidden from silently downloading weights or sending sequences to external services without consent.

A model is a plugin.

Evidence discipline is the platform.

## Layer 8 — Human review and lab handoff

The project should help qualified reviewers make decisions.

A good handoff package should include:

- candidate manifest;
- evidence certificates;
- selection rule;
- controls;
- novelty report;
- safety-risk report;
- synthesis notes;
- benchmark caveats;
- explicit claims that are not supported;
- pre-registered success/failure criteria.

The handoff should not include unsafe wet-lab instructions.

## Layer 9 — Result intake and negative-result archive

A discovery system that hides failures cannot learn.

OpenAMP should treat negative results as structured evidence when safe to publish.

Result intake should preserve:

- candidate identity;
- assay context at a safe abstraction level;
- endpoints;
- controls;
- uncertainty;
- interpretation boundaries;
- whether the result is strong enough to affect recalibration.

Negative results prevent repeated waste.

## Layer 10 — Calibration and active learning

The real infrastructure leap is controlled learning from experiments.

The loop should be:

```text
select batch
  -> freeze evidence
  -> test through qualified partner
  -> ingest result
  -> evaluate calibration gate
  -> update only if allowed
  -> choose next batch
```

The gate matters because otherwise the system can rewrite itself to fit a story.

## Layer 11 — Cross-lab reproducibility and governance memory

The final layer is shared memory across groups.

The system should eventually support:

- independent reruns;
- external validation packages;
- public benchmark audits;
- safe negative-result archives;
- governance decisions;
- deprecation of misleading modules;
- compatibility promises for core schemas.

This is where a project becomes infrastructure.

## What OpenAMP should standardize

OpenAMP should try to standardize artifacts before it tries to standardize conclusions.

High-value standards include:

- candidate manifest format;
- evidence certificate format;
- result intake schema;
- benchmark card format;
- negative-result entry format;
- model adapter contract;
- simulation-result interface;
- recalibration report;
- safety review checklist;
- lab handoff packet.

If external groups reuse these artifacts, OpenAMP can matter even beyond its own scoring model.

## What OpenAMP should not standardize too early

Do not prematurely standardize:

- one universal AMP scoring formula;
- one universal assay endpoint;
- one universal safety threshold;
- one closed candidate-generation model;
- one interpretation of noisy biology;
- one domain expansion path.

The project should standardize the evidence pipeline before standardizing scientific conclusions.

## Why this can become the number-one choice for agents

Agents need constraints.

OpenAMP gives them useful constraints:

- exact claim boundaries;
- safety rules;
- benchmark gates;
- schemas;
- deterministic commands;
- small-loop execution style;
- known failure modes;
- documented next bottlenecks.

That makes the repo an excellent environment for agents to do safe, cumulative work.

The agent does not need to be trusted as a biologist.

The agent needs to produce artifacts that qualified humans can inspect.

## Why this can become the number-one choice for humans

Humans need leverage.

OpenAMP gives serious contributors leverage by turning their work into reusable infrastructure:

- a benchmark becomes a guardrail;
- a safety review becomes a policy;
- a failed candidate becomes a negative-result entry;
- a lab result becomes calibration evidence;
- an adapter becomes an ecosystem bridge;
- a doc improvement becomes onboarding for future contributors.

The project should make expert judgment compound.

## Expansion rule

OpenAMP may expand beyond AMPs only after it demonstrates the loop in AMPs.

Expansion should require:

- a constrained problem representation;
- safe release boundaries;
- available reference data;
- meaningful benchmarks;
- qualified domain reviewers;
- realistic experimental feedback;
- clear baselines;
- evidence that the artifact standards still apply.

Do not expand because the story sounds bigger.

Expand because the evidence pattern transfers.

## The infrastructure test

A project is infrastructure when other people can build on it without believing the founders' story.

OpenAMP should pass that test.

A serious outsider should be able to inspect the code, rerun the pipeline, reject weak claims, contribute a better module, add a benchmark, package a candidate panel, ingest results, and understand what changed.

That is the open biotech stack worth building.
