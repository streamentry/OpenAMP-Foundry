# Vision

## One-sentence vision

**OpenAMP Foundry exists to become the open, auditable discovery layer that helps qualified scientists spend fewer wet-lab experiments finding safer, novel antimicrobial peptide candidates.**

The project is not trying to make biology look solved by software.

It is trying to make biological discovery more honest, cheaper to test, easier to reproduce, and harder to hype.

## The Linux analogy, stated precisely

The goal is not to become famous by calling ourselves the “Linux of biology.”

The goal is to earn the parts of that analogy that matter:

- a neutral substrate that many independent groups can build on;
- stable interfaces between tools, data, models, assays, and evidence;
- reproducible behavior across machines, labs, and years;
- transparent failure modes instead of vendor mystique;
- a contributor ecosystem that improves the shared base layer;
- governance strong enough that trust survives growth.

Linux did not win because it was a slogan. It won because it became dependable infrastructure.

OpenAMP Foundry should win only if it becomes dependable infrastructure for a narrow but important part of biotech discovery: **choosing better antimicrobial peptide experiments and learning from the results.**

## The world we are trying to build

A qualified researcher should be able to start with a scientific question such as:

> Which small set of antimicrobial peptide candidates is most worth testing next, given what is already known, what is unsafe, what is redundant, and what the model is uncertain about?

OpenAMP Foundry should return something more valuable than a ranked list.

It should return a reviewable scientific package:

```text
candidate set
  -> provenance
  -> validation checks
  -> feature evidence
  -> novelty audit
  -> safety-risk flags
  -> synthesis feasibility
  -> baseline comparisons
  -> model disagreement
  -> diversity rationale
  -> uncertainty
  -> evidence certificate
  -> pre-registered lab handoff
  -> result intake schema
  -> calibration decision
  -> next experiment proposal
```

The ideal user does not say:

> The model predicted it, therefore it works.

The ideal user says:

> This candidate earned a scarce assay slot because the evidence trail survived several cheap attempts to disprove it.

## The core insight

The bottleneck is not generating more biological guesses.

The bottleneck is deciding which guesses deserve real experiments.

Modern AI can generate far more candidate molecules than any lab can test. That abundance is dangerous if the ranking system is weak. It creates false confidence, cherry-picked success stories, redundant candidates, hidden toxicity, and wasted wet-lab capacity.

OpenAMP Foundry should be an **experiment-selection engine**, not a miracle generator.

The project should compress wet-lab search by answering four questions better over time:

1. What should we test next?
2. Why this instead of the obvious baseline?
3. What failure would change our mind?
4. What did the lab teach the system?

## Why antimicrobial peptides first

Antimicrobial peptides are a strong first domain because they sit at the intersection of urgent need, tractable representation, and brutal biological reality.

They are attractive because peptide sequences are compact enough for reproducible computational workflows, many public references exist, and initial assays can produce relatively direct activity and safety readouts through qualified partners.

They are dangerous to overclaim because antimicrobial activity, selectivity, hemolysis, cytotoxicity, stability, delivery, resistance, manufacturing, and clinical relevance are not solved by sequence scoring.

That tension is exactly why this domain is useful.

A project that stays honest here can teach open biotech a deeper lesson: **how to connect AI-generated hypotheses to real biological evidence without pretending the computer has replaced the lab.**

## What makes OpenAMP different

Most AI-for-bio projects optimize for impressive claims.

OpenAMP Foundry should optimize for claims that survive attack.

The project’s advantage should not be that it has the flashiest model. Models will change. Predictors will age. Benchmarks will break. Better tools will arrive.

The durable advantage should be the evidence discipline around the model:

- pre-registered decision rules;
- leakage-aware benchmarks;
- cheap-baseline comparisons;
- novelty auditing against known references;
- safety-first scoring;
- candidate diversity controls;
- evidence certificates;
- negative-result preservation;
- external predictor adapters;
- explicit uncertainty;
- fail-closed gates;
- wet-lab result intake;
- recalibration policies that cannot be silently rewritten after the outcome is known.

A better model should be easy to plug in.

A worse model should be easy to reject.

A misleading model should be unable to hide.

## The system we are building

OpenAMP Foundry should grow into a layered open stack.

### Layer 1 — Provenance and data hygiene

Every candidate, reference, benchmark, score, and lab result should carry enough provenance to be inspected later.

The project should make it difficult to confuse training data, reference data, benchmark data, generated candidates, and validated results.

### Layer 2 — Candidate validation and feature evidence

The system should reject invalid, low-quality, redundant, or obviously unsafe candidates before more expensive reasoning begins.

The first duty of the pipeline is not to be clever. It is to be clean.

### Layer 3 — Baseline-first scoring

Every advanced method must compete against the dumb baseline it claims to improve.

Charge density, similarity to known AMPs, length, hydrophobicity, amphipathicity, simple selectivity proxies, and random selection are not embarrassing baselines. They are necessary adversaries.

If a model cannot beat cheap heuristics under fair conditions, it should not influence ranking.

### Layer 4 — Virtual assay adapters

Simulation and learned predictors should be pluggable, versioned, calibrated, and allowed to abstain.

A virtual assay earns authority only by improving decision quality. It does not earn authority by sounding biologically sophisticated.

### Layer 5 — Batch design

The system should select small assay panels that balance:

- likely activity;
- predicted safety;
- novelty;
- synthesis feasibility;
- structural diversity;
- uncertainty probes;
- positive and negative controls;
- information value for the next round.

A batch is not just a top-k list. It is an experimental question.

### Layer 6 — Wet-lab result intake

Qualified lab results should enter through schemas that preserve context, controls, endpoints, uncertainty, and limitations.

The system should never treat a raw assay number as magic truth. It should ask whether the result is controlled, comparable, and strong enough to change the model or the next experiment.

### Layer 7 — Calibration and active learning

The long-term prize is a loop:

```text
design -> rank -> test -> learn -> select the next better test
```

The project becomes important only if that loop improves over repeated real outcomes.

A single hit is useful.

A system that learns how to spend experiments better is infrastructure.

## The standard for greatness

OpenAMP Foundry becomes genuinely great only if independent groups can use it to do work that is more reproducible, more honest, and more experimentally efficient than their default workflow.

The project should not measure greatness by stars, demos, model size, or dramatic claims.

It should measure greatness by harder evidence:

- independent wet-lab pilots using pre-registered candidate-selection rules;
- published safe negative results;
- clear wins over cheap baselines;
- lower cost per validated lead-like signal;
- reproducible evidence packages;
- external contributors adding adapters, benchmarks, and result schemas;
- laboratories using the same formats without needing the same models;
- reviewers being able to audit why a candidate was tested;
- failed models being removed or downgraded before they waste experiments.

The most important future sentence is not:

> AI discovered an antibiotic.

It is:

> An open, auditable experiment-selection system repeatedly helped independent labs choose better antimicrobial experiments than cheap baselines, and every claim can be checked.

## What success looks like by time horizon

### Near horizon — trustworthy dry lab

OpenAMP Foundry should be the cleanest open dry-lab AMP triage system available:

- deterministic pipeline runs;
- transparent scoring;
- leakage-aware benchmarks;
- valid evidence certificates;
- safe toy/demo data by default;
- no unsupported wet-lab claims;
- CI-tested workflows;
- documented failure modes;
- clear extension interfaces.

This is not glamorous. It is the foundation.

### First truth horizon — real wet-lab feedback

The first major scientific test is a small, pre-registered pilot with qualified partners.

The goal is not to prove a therapy.

The goal is to learn whether OpenAMP-selected candidates produce more useful experimental information than simple baselines under fair comparison.

Success means the system survives contact with real assays.

Failure is acceptable if the failure is clean, documented, and changes the next design.

### Platform horizon — shared experiment infrastructure

The next step is to make the loop reusable:

- standardized candidate packages;
- standardized evidence certificates;
- standardized result intake;
- benchmark leaderboards that penalize leakage;
- adapter contracts for external predictors;
- lab-handoff templates;
- public negative-result archives where safe;
- governance for safety-sensitive releases.

At this stage OpenAMP Foundry stops being only a project and starts becoming a protocol ecosystem.

### Decade horizon — open biotech substrate

If the project compounds for years, the broader ambition is a trusted open layer between AI systems and experimental biology.

Not one model.

Not one lab.

Not one vendor.

A substrate where candidate-selection logic, evidence trails, assay results, calibration, safety rules, and reproducibility standards can move across tools and institutions.

AMP discovery is the first beachhead. The deeper pattern is reusable across other constrained biological design problems, but expansion must be earned by evidence, not branding.

## What we refuse to become

OpenAMP Foundry must not become:

- a hype engine for “AI discovered a cure” narratives;
- a repository of unsafe wet-lab instructions;
- a toxicity or pathogen-optimization tool;
- a black-box ranking service with no audit trail;
- a leaderboard that rewards leakage;
- a benchmark tuned after seeing the answer;
- a candidate dump without safety review;
- a project that hides failures to preserve a story;
- a model playground detached from real biological validation.

If forced to choose between being impressive and being trustworthy, choose trustworthy.

## The load-bearing assumptions

The vision depends on several assumptions that may be false.

### Assumption 1 — Open experiment selection can beat cheap baselines

If OpenAMP cannot outperform charge, similarity, and simple physicochemical heuristics in real candidate selection, it should not pretend to be a discovery engine.

### Assumption 2 — Labs will value evidence packages

If qualified labs do not find the evidence certificates, controls, and handoff artifacts useful, the project is solving the wrong interface problem.

### Assumption 3 — Calibration improves over rounds

If real assay feedback does not improve future selection, the active-learning thesis is weak.

### Assumption 4 — Safety and openness can coexist

If open release materially increases misuse risk, the release policy must remain conservative. Openness is a tool, not a suicide pact.

### Assumption 5 — A narrow wedge can generalize

AMP discovery may teach reusable infrastructure patterns, but it may also remain a narrow domain. Expansion must be earned by repeated success.

## How the vision can fail

The project fails if it becomes another AI-bio demo that produces plausible candidates but no trusted evidence.

It fails if it optimizes benchmarks that do not predict wet-lab utility.

It fails if it beats random but loses to charge density.

It fails if it generates impressive reports that qualified experimentalists do not trust.

It fails if safety review is treated as paperwork.

It fails if negative results disappear.

It fails if the project becomes dependent on one maintainer, one model, one lab, or one narrative.

These are not edge cases. They are the default failure modes.

## The cultural standard

OpenAMP Foundry should be harder on itself than its critics are.

Every major claim should answer:

- What is the evidence?
- What is the cheapest alternative explanation?
- What baseline did this beat?
- What would falsify it?
- What uncertainty remains?
- What safety boundary applies?
- What should a qualified human review before acting?

The project should make good science easier and bad science more visible.

## The north star

The long-term goal is a world where a small lab, a nonprofit group, a university team, or a public-health consortium can run an open discovery loop that is transparent from idea to assay result.

They should not need to trust a black box.

They should not need to hide failures.

They should not need to pretend that a model score is biological truth.

They should be able to ask better experimental questions, spend fewer experiments, learn from each answer, and leave behind evidence that others can inspect.

That is the version of “Linux for biotech” worth building.

Not a slogan.

A shared base layer for trustworthy biological discovery.
