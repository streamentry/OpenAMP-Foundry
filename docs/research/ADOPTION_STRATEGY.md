# Adoption Strategy

## Purpose

This document defines how OpenAMP Foundry should become the obvious first choice for serious humans, agents, labs, and institutions working on open, safety-first antimicrobial peptide experiment selection.

Adoption should not come from hype.

Adoption should come from trust and usefulness.

## Positioning statement

OpenAMP Foundry is the open evidence layer for antimicrobial peptide experiment selection.

It helps qualified humans and AI agents move from candidate sequences to reviewable evidence packages, baseline comparisons, safety-aware panels, result intake, and calibrated next-round selection.

It does not claim that software proves biology.

It helps decide which biological questions are worth asking next.

## The adoption wedge

The adoption wedge is not “use our model.”

The adoption wedge is:

> Use our evidence standard.

A lab, researcher, or agent may disagree with the current scorer and still use:

- candidate manifests;
- evidence certificates;
- benchmark cards;
- proof ladder;
- lab handoff packets;
- result intake schemas;
- negative-result archive format;
- adapter contracts;
- calibration reports;
- safety release rules.

That is how OpenAMP becomes infrastructure rather than one more model repo.

## Target users

### 1. AI agents

Agents need scoped tasks, machine-checkable outputs, and clear forbidden zones.

OpenAMP should be attractive to agents because it has:

- explicit operating contracts;
- deterministic commands;
- schema validation;
- benchmark gates;
- safety boundaries;
- task maps;
- clear docs;
- small-loop contribution style.

The repo should become one of the best places for agents to do useful scientific infrastructure work without pretending to be scientists.

### 2. Engineers

Engineers need work that matters and can be verified.

OpenAMP should be attractive to engineers because it needs:

- robust CLIs;
- reproducible pipelines;
- stable schemas;
- deterministic report generation;
- data provenance;
- CI gates;
- adapter architecture;
- error handling;
- package quality.

The repo should feel like real infrastructure, not a notebook dump.

### 3. Computational biologists and ML researchers

Researchers need honest benchmarks and places where negative results matter.

OpenAMP should be attractive because it rewards:

- stronger baselines;
- leakage audits;
- family-stratified evaluation;
- cross-dataset testing;
- uncertainty estimation;
- model disagreement;
- calibration experiments;
- falsification of weak scorers.

The project should become the place where a model earns authority by surviving attacks.

### 4. Wet-lab experts

Wet-lab experts need computational packages that respect biological reality.

OpenAMP should be attractive because it provides:

- candidate rationale;
- controls and baselines;
- novelty audit;
- safety-risk flags;
- synthesis considerations;
- failure modes;
- pre-registration templates;
- result intake formats.

The project should make it easier for experts to say yes, no, or not yet.

### 5. Institutions and funders

Institutions need durable public goods.

OpenAMP should be attractive because it can produce:

- reusable standards;
- independent validation packages;
- negative-result infrastructure;
- safe open-science workflows;
- benchmark governance;
- public-interest discovery tooling.

The project should be fundable even when a candidate fails because the infrastructure still improves.

## The trust funnel

Adoption should move through this funnel:

```text
clear repo promise
  -> easy first run
  -> understandable outputs
  -> visible safety boundaries
  -> credible benchmarks
  -> easy first contribution
  -> external review package
  -> pre-registered pilot
  -> result intake
  -> improved next round
  -> independent reuse
```

Every broken link in this funnel loses serious users.

## What must be true for OpenAMP to become number one

### 1. The first run must be boringly reliable

A new user should be able to run the demo without hunting through docs.

The output should be clear enough that they understand the claim boundary immediately.

### 2. The docs must be role-specific

Different users need different entrypoints.

The project should not force a wet-lab expert, AI agent, engineer, and funder through the same path.

### 3. The project must be harder to fool than alternatives

If competitors show prettier models, OpenAMP should show stronger evidence discipline.

That means cheap baselines, leakage checks, hard gates, negative results, and claim ladders.

### 4. The artifacts must be reusable outside the repo

Evidence certificates and result schemas should be useful even when another group uses different models.

### 5. Agents must have safe rails

The repo should make it obvious what agents may improve and what they must not touch without human review.

### 6. External experts must be able to reject outputs

A serious lab or reviewer should not need to trust maintainers.

They should be able to inspect enough evidence to reject a candidate, panel, benchmark, or claim.

### 7. Failures must improve the project

OpenAMP should be more useful after a clean failure than a hype repo is after a weak success.

## Adoption milestones

### Milestone A — Best first-run experience

A new contributor can:

- understand the mission in 5 minutes;
- run the demo in 15 minutes;
- inspect generated evidence in 30 minutes;
- identify a safe first contribution in 60 minutes.

### Milestone B — Best agent workspace

A new agent can:

- read the operating contract;
- choose a high-leverage task;
- avoid unsafe scope;
- implement a narrow change;
- update docs and tests;
- leave a clear audit trail.

### Milestone C — Best benchmark honesty

A researcher can:

- see every current benchmark;
- see where cheap baselines beat the pipeline;
- see known weaknesses;
- reproduce core metrics;
- add a new benchmark without changing the claim standard.

### Milestone D — Best expert-review package

A domain expert can:

- inspect candidate rationale;
- see controls and baselines;
- identify unsafe or weak candidates;
- reject unsupported claims;
- recommend whether a panel is worth qualified testing.

### Milestone E — First credible external pilot

A qualified external pilot can:

- freeze candidates before testing;
- compare against cheap baselines;
- record outcomes through schemas;
- preserve negative results where safe;
- decide whether calibration is justified.

### Milestone F — Reusable standard

External groups begin using OpenAMP artifacts even if they do not use OpenAMP scoring.

That is the strongest adoption signal.

## What not to optimize

Do not optimize for:

- stars without use;
- press without evidence;
- model complexity without baseline wins;
- positive results without negative-result memory;
- speed without safety;
- generality before the AMP loop works;
- agent autonomy without human-review gates.

## Messaging rules

Use this language:

- “open evidence layer”;
- “dry-lab foundry”;
- “experiment-selection engine”;
- “wet-lab compression, if validated”;
- “computationally nominated candidates”;
- “reviewable evidence packages”;
- “baseline-aware candidate selection.”

Avoid this language unless evidence later supports it:

- “AI discovered an antibiotic”;
- “drug candidate”;
- “clinical potential”;
- “safe”;
- “proven antimicrobial”;
- “automated biology.”

## External credibility strategy

OpenAMP should seek criticism before praise.

Highest-value external credibility steps:

1. Independent doc/claim audit.
2. Independent benchmark audit.
3. Domain expert review of evidence packages.
4. Safety review of release boundaries.
5. Pre-registered baseline-controlled pilot.
6. Publication of negative results where safe.
7. Independent replication if any meaningful signal appears.

## Community strategy

The community should be built around standards, not fan energy.

Reward contributors who:

- find weaknesses;
- add baselines;
- improve safety;
- reduce ambiguity;
- help external reviewers;
- make failures useful;
- keep claims precise.

Do not reward contributors for unsupported hype.

## Agent strategy

Agents should be treated as force multipliers for infrastructure, not as autonomous scientific authorities.

Best agent work:

- schema examples;
- tests;
- doc index updates;
- deterministic scripts;
- report improvements;
- benchmark comparisons;
- adapter scaffolds;
- consistency checks.

Human review required:

- claim strengthening;
- model release;
- candidate release;
- safety policy changes;
- wet-lab-facing changes;
- benchmark threshold changes;
- calibration policy changes.

## The adoption flywheel

```text
better docs
  -> easier contribution
  -> more tests and benchmarks
  -> more trust
  -> better external review
  -> stronger artifacts
  -> safer pilots
  -> better result memory
  -> better docs
```

The flywheel should compound trust, not excitement.

## The number-one test

OpenAMP becomes number one when a serious outsider says:

> I may not trust every model in this repo, but I trust the repo’s process for proving, rejecting, documenting, and safely using models better than the alternatives.

That is the adoption target.
