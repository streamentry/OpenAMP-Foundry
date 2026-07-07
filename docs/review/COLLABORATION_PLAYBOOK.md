# Collaboration Playbook

## Purpose

This playbook defines how OpenAMP Foundry should collaborate with humans, labs, institutions, funders, safety reviewers, and AI agents without weakening scientific honesty or safety posture.

The project should be easy to work with, but hard to misuse.

## Collaboration principle

**OpenAMP provides auditable computational evidence and experiment-selection infrastructure. Qualified humans decide whether and how any biological testing proceeds.**

The repo does not provide wet-lab protocols, clinical advice, pathogen-handling instructions, or claims of biological efficacy without experimental evidence.

## Collaboration modes

### Mode 1 — Software contribution

Best for engineers, agents, and infrastructure contributors.

Useful work:

- tests;
- CLI improvements;
- schema validation;
- reproducibility scripts;
- report generation;
- adapter interfaces;
- benchmark gates;
- documentation consistency;
- safe packaging.

Required boundaries:

- no unsafe biological capability;
- no wet-lab instructions;
- no unsupported claims;
- no unscreened candidate dumps.

### Mode 2 — Benchmark contribution

Best for computational biologists, ML researchers, and data curators.

Useful work:

- new negative sets;
- cross-dataset evaluation;
- charge-matched controls;
- family-stratified benchmarks;
- benchmark cards;
- leakage audits;
- external predictor comparisons;
- cheap-baseline challengers.

Required boundaries:

- license status must be clear;
- benchmark construction must be documented;
- leakage risks must be stated;
- known weaknesses must not be hidden.

### Mode 3 — Domain expert review

Best for microbiologists, peptide scientists, toxicologists, medicinal chemists, and assay experts.

Useful work:

- review candidate evidence packages;
- identify obvious biological implausibilities;
- critique controls and endpoints;
- flag safety or selectivity concerns;
- review novelty interpretations;
- reject inflated language;
- help define pre-registered pilot criteria.

Required boundaries:

- no unsafe protocol publication;
- no clinical claims;
- no recommendation for unsupervised biological testing;
- no overinterpretation of computational evidence.

### Mode 4 — Wet-lab validation partnership

Best for qualified labs, CROs, and institutions with appropriate oversight.

Useful work:

- independently review candidate panels;
- test pre-registered panels under qualified conditions;
- provide safe, structured result summaries;
- help interpret controls and uncertainty;
- support negative-result publication where safe.

Required boundaries:

- OpenAMP does not instruct unqualified users to run assays;
- detailed lab procedures are not published here;
- results are interpreted only within their tested context;
- safety review controls release of sensitive artifacts;
- candidate claims remain conservative until evidence matures.

### Mode 5 — Funding or institutional support

Best for public-interest funders, universities, nonprofits, and research institutions.

Useful support:

- independent benchmark audits;
- qualified expert reviews;
- wet-lab validation pilots;
- infrastructure maintenance;
- safety review;
- documentation and onboarding;
- long-term governance;
- public negative-result infrastructure.

Required boundaries:

- funding should not create pressure to overclaim;
- negative results must remain publishable where safe;
- safety review must remain independent enough to say no;
- governance should protect the project’s credibility.

## External review package

A serious external review package should include:

- project version and commit hash;
- candidate manifest;
- evidence certificates;
- scoring configuration;
- benchmark summary;
- cheap-baseline comparisons;
- novelty audit;
- safety-risk summary;
- synthesis feasibility summary;
- diversity rationale;
- known blind spots;
- pre-registered selection criteria;
- explicit unsupported claims;
- safety review note.

The package should let a reviewer reject the panel without private maintainer context.

## Wet-lab collaboration minimum bar

Before any candidate panel is treated as wet-lab-ready, the project should have:

1. Frozen candidate list.
2. Frozen selection rule.
3. Evidence certificate for each candidate.
4. Control rationale.
5. Novelty audit.
6. Safety-risk review.
7. Baseline comparison.
8. Pre-registered success and failure criteria.
9. Human expert review.
10. Release review for what can be published safely.

A panel that lacks these is not ready.

## What OpenAMP can provide to labs

OpenAMP can provide:

- ranked candidate panels;
- evidence certificates;
- novelty analysis;
- safety-risk flags;
- synthesis-risk flags;
- diversity analysis;
- baseline comparisons;
- pre-registration templates;
- result intake schemas;
- negative-result archive templates;
- computational reproducibility package.

OpenAMP should not provide:

- wet-lab protocols;
- pathogen handling guidance;
- clinical advice;
- claims that a candidate is safe or effective;
- directions for unqualified biological testing;
- unsafe candidate-release workflows.

## How to compare OpenAMP fairly

A fair collaboration should compare OpenAMP against cheap alternatives.

Possible comparison groups:

- random valid peptides;
- charge-ranked peptides;
- known-AMP-similar peptides;
- human expert selection;
- external predictor consensus;
- diversity-only selection;
- safety-first conservative selection.

Without baseline comparison, a positive outcome is hard to interpret.

## How to publish results responsibly

Responsible result publication should include:

- exact claim level from [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md);
- candidate evidence package where safe;
- selection rule;
- baseline comparison;
- controls and outcome summary at a safe abstraction level;
- limitations;
- negative results where safe;
- safety review note;
- statement that computational prediction did not prove activity.

Do not publish unsafe operational details.

Do not imply clinical relevance.

Do not convert one early assay signal into a broad discovery claim.

## Collaboration anti-patterns

### The press-release collaboration

A collaboration built around a headline before evidence exists.

Reject it.

### The hidden-failure collaboration

A collaboration where only positive results can be shared.

Reject it or narrow the claim severely.

### The no-baseline collaboration

A collaboration that tests OpenAMP candidates but does not compare against simple alternatives.

Treat it as exploratory only.

### The protocol-leak collaboration

A collaboration that tries to turn this repo into a wet-lab instruction repository.

Reject it.

### The over-broad collaboration

A collaboration that jumps from AMPs to all drug discovery before proving the loop.

Reject or split into a narrow evidence-generating pilot.

## What good collaboration looks like

A good collaboration produces artifacts that outlive the project narrative:

- better benchmarks;
- better schemas;
- external review notes;
- pre-registered candidate panels;
- interpretable negative results;
- honest baseline comparisons;
- documented failures;
- safer release decisions;
- reusable lessons for future rounds.

The point is not to make OpenAMP look right.

The point is to find out where it is right, where it is wrong, and whether it can learn.

## Collaboration decision rule

Accept collaborations that increase trust.

Reject collaborations that only increase attention.

Trust comes from evidence, reproducibility, safety, and external scrutiny.

Attention without those is a liability.
