# Wet-Lab Handoff Guide

**Status:** Safe expert-review handoff, not a protocol.
**Audience:** Qualified domain experts, safety reviewers, and potential institutional partners.
**Source-of-truth companions:** [`PROOF_LADDER.md`](PROOF_LADDER.md), [`EXTERNAL_REVIEW_PACKET.md`](EXTERNAL_REVIEW_PACKET.md), [`PRE_REGISTERED_PILOT_TEMPLATE.md`](PRE_REGISTERED_PILOT_TEMPLATE.md), [`RESPONSIBLE_USE.md`](../RESPONSIBLE_USE.md).

## Purpose

This document explains how OpenAMP Foundry should package computational candidate-selection evidence for qualified external review.

It is not a wet-lab protocol.

It does not instruct anyone how to culture organisms, run assays, handle pathogens, prepare biological materials, or perform experimental procedures.

OpenAMP produces dry-lab evidence packages. Qualified partners decide whether and how any experimental work proceeds under their own approved procedures, oversight, and safety systems.

## Prime rule

**A handoff package should help experts decide whether a candidate panel is worth considering, not tell unqualified people how to test it.**

## What OpenAMP hands off

OpenAMP may hand off:

- candidate manifest;
- evidence certificates;
- scoring configuration;
- selection rule;
- novelty audit;
- safety-risk summary;
- synthesis-feasibility summary at a non-operational level;
- diversity rationale;
- benchmark caveats;
- baseline comparisons;
- unsupported-claim warning;
- pre-registration draft;
- result-intake schema.

OpenAMP should not hand off:

- experimental protocols;
- pathogen-handling instructions;
- culturing instructions;
- operational assay recipes;
- clinical recommendations;
- unscreened high-risk candidate dumps;
- claims of activity, safety, or therapeutic value without qualified evidence.

## Handoff levels

### Level 0 — Internal dry-lab output

Used for local development and debugging.

Required:

- ranked candidate JSONL;
- generated report;
- schema-valid certificates;
- demo or toy data status clearly labeled.

Claim level: computational output only.

### Level 1 — Expert-review package

Used when a qualified scientist reviews whether the computational package is coherent.

Required:

- candidate manifest;
- evidence certificates;
- novelty summary;
- safety-risk summary;
- synthesis-risk summary;
- selection rationale;
- benchmark caveats;
- failure modes;
- proof-ladder level.

Claim level: candidates selected for expert review.

### Level 2 — Pre-registered pilot package

Used only when a qualified partner is considering independent testing.

Required:

- frozen candidate panel;
- frozen baseline comparison panels where feasible;
- frozen selection rule;
- frozen success/failure criteria;
- external review packet;
- safety review;
- result-intake plan;
- publication/release boundaries.

Claim level: candidates selected for possible qualified testing under pre-registered criteria.

### Level 3 — Result-intake package

Used after a qualified partner provides structured results.

Required:

- result summaries at a safe abstraction level;
- control interpretation supplied by qualified partner;
- outcome quality flags;
- negative results where safe;
- recalibration-gate verdict;
- claim-level update;
- next-batch recommendation or rejection.

Claim level: depends on evidence; see [`PROOF_LADDER.md`](PROOF_LADDER.md).

## Score interpretation for reviewers

All OpenAMP scores are dry-lab decision aids.

They should be interpreted as reasons for review, not evidence of biological truth.

| Evidence area | Reviewer question | What the score can support | What it cannot support |
|---|---|---|---|
| Activity-likeness | Does the sequence resemble known AMP-like physicochemical patterns? | Prioritization for review. | Biological activity. |
| Safety-risk | Does the dry-lab model flag host-cell or selectivity concerns? | Caution, rejection, or follow-up review. | Human safety. |
| Novelty | Is the candidate distant from known references under the chosen method? | Novelty hypothesis. | True novelty across all biology. |
| Synthesis feasibility | Are obvious feasibility risks visible? | Expert/vendor feasibility review. | Guaranteed synthesis success. |
| Ensemble score | Did the candidate survive the configured scoring tradeoff? | Ranking within a dry-lab run. | Experimental efficacy. |
| Disagreement/uncertainty | Do scorers disagree or abstain? | Need for caution or uncertainty probes. | Proof that the candidate will fail or succeed. |

## Required handoff packet

A serious expert-review handoff should include:

```text
handoff_packet/
  README.md
  candidate_manifest.json
  evidence_certificates/
  selection_rule.md
  benchmark_summary.md
  baseline_comparison.md
  novelty_summary.md
  safety_risk_summary.md
  synthesis_feasibility_summary.md
  diversity_rationale.md
  unsupported_claims.md
  reviewer_questions.md
  release_review.md
```

The exact format may evolve, but the packet must preserve enough context for an outsider to reject or revise the panel.

## Candidate manifest fields

A review-ready manifest should include:

- candidate ID;
- sequence or safe sequence reference;
- sequence hash;
- panel role;
- cluster/scaffold family;
- proof-ladder level;
- selection reason;
- key scores;
- key safety flags;
- novelty label;
- synthesis-risk label;
- baseline caveat;
- release status.

## Baseline comparison requirement

A handoff packet should say whether candidate selection was compared against cheap alternatives.

Possible comparison panels:

- random valid candidates;
- charge-ranked candidates;
- similarity-to-known-AMP candidates;
- external-predictor consensus candidates;
- diversity-only candidates;
- human-expert candidates where available.

If no baseline panel exists, the handoff must say:

> This package is exploratory. It cannot support claims that OpenAMP improves experiment selection relative to simple alternatives.

## Novelty review

Novelty claims should be conservative.

A novelty summary should state:

- reference sets checked;
- date/version/hash of references;
- similarity method;
- nearest-neighbor summary;
- novelty label;
- known limitations;
- whether the candidate is a near-duplicate, family derivative, related novel sequence, or high-confidence novel hypothesis.

A candidate is not novel merely because one reference file did not contain it.

## Safety-risk review

Safety-risk summaries should state:

- dry-lab safety flags;
- model limitations;
- whether risk is enough to reject candidate from the panel;
- whether release should be restricted;
- what claims remain unsupported.

OpenAMP safety scores do not prove biological safety.

## Synthesis-feasibility review

Synthesis feasibility should remain non-operational in this repo.

The handoff may flag broad feasibility concerns that a qualified synthesis provider or expert should review.

The handoff should not provide operational procedures, storage instructions, assay instructions, or experimental recipes.

## Expert reviewer questionnaire

A reviewer should answer:

1. Is the candidate panel coherent for the stated goal?
2. Are any candidates obvious rejects?
3. Are novelty claims too strong?
4. Are safety-risk concerns understated?
5. Are the baseline comparisons adequate?
6. Are there missing controls or comparison groups at the planning level?
7. Are the unsupported claims clearly stated?
8. Is the packet sufficient to decide whether further review or possible qualified testing is warranted?
9. What should be changed before any external pilot?
10. What result would falsify the selection logic?

## Handoff acceptance criteria

A handoff is review-ready only if:

- every selected candidate has an evidence certificate;
- the selection rule is frozen;
- baseline comparisons are present or the exploratory limitation is explicit;
- novelty audit is documented;
- safety-risk summary is documented;
- synthesis feasibility is documented at a non-operational level;
- known benchmark caveats are included;
- unsupported claims are listed;
- proof-ladder level is stated;
- release review is included.

## Handoff rejection criteria

Reject or revise the handoff if:

- candidates are selected without evidence certificates;
- claims exceed dry-lab evidence;
- novelty audit is missing;
- safety-risk concerns are hidden;
- benchmark caveats are missing;
- no baseline comparison exists and the package is not labeled exploratory;
- operational wet-lab detail appears;
- candidate release status is unclear;
- qualified review is implied but not documented.

## Result intake boundary

If a qualified partner later provides results, OpenAMP should ingest them through structured artifacts that preserve:

- candidate ID;
- panel ID;
- endpoint summary at a safe abstraction level;
- outcome quality flag;
- control interpretation supplied by qualified partner;
- whether the result is interpretable;
- whether it can affect recalibration;
- limitations;
- claim-level update.

Detailed experimental procedures remain outside this repository.

## Publication boundary

Before public release of any handoff-derived result, answer:

- What proof-ladder level is justified?
- What can be safely published?
- What should be summarized rather than released?
- What negative results can be shared?
- What safety review occurred?
- What claim must be avoided?
- Was independent review performed?

## Final standard

A wet-lab handoff should make OpenAMP more useful to qualified experts while making misuse and overclaiming harder.

If the handoff reads like instructions for unqualified biological testing, it is wrong.

If the handoff reads like an auditable expert-review package, it is doing its job.
