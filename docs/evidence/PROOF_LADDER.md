# Proof Ladder

## Purpose

This document defines how OpenAMP Foundry should move from computational nomination to stronger scientific claims without skipping evidence levels.

The central rule is simple:

**A claim may not be stronger than the evidence behind it.**

## The ladder

```text
Level 0 — Valid input
Level 1 — Reproducible dry-lab features
Level 2 — Baseline-triaged candidate
Level 3 — Leakage-aware benchmark support
Level 4 — Multi-signal candidate evidence
Level 5 — Expert-reviewed assay proposal
Level 6 — Initial qualified assay result
Level 7 — Safety-adjusted follow-up signal
Level 8 — Independent replication
Level 9 — Reusable discovery loop
Level 10 — Translational or clinical relevance
```

Most repository outputs are currently Levels 0–4.

No dry-lab artifact should be described as Level 6 or higher.

## Level 0 — Valid input

### Evidence

- Sequence is parseable.
- Symbols are valid for the intended representation.
- Required metadata exists.
- Obvious duplicates or malformed records are handled.

### Allowed claim

> This is a valid candidate sequence for computational processing.

### Not allowed

Do not imply activity, novelty, safety, or usefulness.

## Level 1 — Reproducible dry-lab features

### Evidence

- Features are computed deterministically.
- Code version, config, and input are known.
- Output can be regenerated.

### Allowed claim

> This candidate has reproducible computed features under a specified pipeline version.

### Not allowed

Do not imply that features prove biological function.

## Level 2 — Baseline-triaged candidate

### Evidence

- Candidate passes basic validity, novelty, synthesis, and safety-risk filters.
- Candidate receives a transparent baseline score.
- Candidate is compared against simple heuristics where relevant.

### Allowed claim

> This candidate is computationally nominated by a transparent dry-lab triage pipeline.

### Not allowed

Do not call it active, safe, therapeutic, or validated.

## Level 3 — Leakage-aware benchmark support

### Evidence

- The pipeline or component has been tested on documented benchmarks.
- Leakage risks are addressed.
- Performance is compared with cheap baselines.
- Known weaknesses are documented.

### Allowed claim

> The scoring method has benchmark support under specified assumptions and limitations.

### Not allowed

Do not generalize benchmark performance to real biological efficacy.

## Level 4 — Multi-signal candidate evidence

### Evidence

- Candidate has an evidence certificate.
- Multiple independent scorers or checks support selection.
- Novelty is audited against known references.
- Safety-risk and synthesis concerns are recorded.
- Model disagreement and uncertainty are visible.
- Failure modes are listed.

### Allowed claim

> This candidate has a reviewable computational evidence package and may deserve qualified expert review.

### Not allowed

Do not claim it is a hit.

## Level 5 — Expert-reviewed assay proposal

### Evidence

- Candidate package has been reviewed by qualified humans.
- Selection rule is pre-registered.
- Controls and endpoints are defined at an appropriate safe abstraction level.
- Success and failure criteria are frozen before testing.
- Safety review has occurred.

### Allowed claim

> This candidate or panel has been selected for possible qualified experimental testing under pre-registered criteria.

### Not allowed

Do not imply that selection for testing means expected success.

## Level 6 — Initial qualified assay result

### Evidence

- Candidate has been tested by a qualified lab or partner.
- Controls are interpretable.
- Result context is recorded.
- Raw claims are limited to the exact assay conditions.

### Allowed claim

> This candidate showed activity under specified experimental conditions.

or

> This candidate did not show activity under specified experimental conditions.

### Not allowed

Do not generalize to clinical usefulness, broad antimicrobial effect, or human safety.

## Level 7 — Safety-adjusted follow-up signal

### Evidence

- Activity signal is paired with initial safety-relevant screening.
- Hemolysis, mammalian cytotoxicity, or other relevant concerns are assessed by qualified methods.
- Novelty and redundancy remain acceptable.
- Candidate remains worth follow-up after safety adjustment.

### Allowed claim

> This candidate has an early activity/safety profile worth follow-up under specified conditions.

### Not allowed

Do not call it safe in humans.

## Level 8 — Independent replication

### Evidence

- A separate lab or CRO reproduces the key result.
- The evidence package is sufficient for external interpretation.
- Differences between contexts are documented.

### Allowed claim

> This candidate family has independently replicated early antimicrobial evidence under specified conditions.

### Not allowed

Do not claim therapeutic value without the appropriate translational evidence.

## Level 9 — Reusable discovery loop

### Evidence

- Multiple experimental rounds exist.
- Calibration decisions are gated and documented.
- Later batches improve over earlier or baseline batches under pre-defined metrics.
- Negative results are preserved where safe.
- Independent groups can reproduce the process.

### Allowed claim

> OpenAMP improved experiment selection in repeated antimicrobial peptide discovery loops under specified conditions.

### Not allowed

Do not claim the system solves antimicrobial resistance or replaces expert-led discovery.

## Level 10 — Translational or clinical relevance

### Evidence

This level requires evidence far outside the normal scope of this repository, including advanced pharmacology, toxicity, formulation, animal studies where appropriate, regulatory work, manufacturing, and clinical evidence.

### Allowed claim

Only qualified domain experts may decide.

### Not allowed

OpenAMP maintainers, contributors, and agents must not casually imply Level 10 claims.

## Claim mapping table

| Phrase | Minimum evidence level | Notes |
|---|---:|---|
| Valid peptide sequence | 0 | Syntax only. |
| Computed features | 1 | Reproducible dry-lab output. |
| Computationally nominated candidate | 2 | Dry-lab triage passed. |
| Benchmark-supported predictor | 3 | Benchmark support, caveats required. |
| Candidate with evidence certificate | 4 | Reviewable package. |
| Selected for qualified testing | 5 | Human and safety review required. |
| Showed activity in assay | 6 | Exact conditions required. |
| Worth follow-up after safety screen | 7 | Still early. |
| Independently replicated early signal | 8 | Stronger but not clinical. |
| Experiment-selection engine | 9 | Requires repeated feedback loops. |
| Drug, therapy, clinical candidate | 10 | Outside repo authority. |

## Forbidden shortcuts

Do not jump from Level 4 to “validated.”

Do not jump from Level 6 to “drug candidate.”

Do not jump from benchmark AUROC to “biological activity.”

Do not jump from model agreement to “safe.”

Do not jump from novelty score to “new family” unless the novelty analysis supports that specific claim.

Do not use “AI discovered” unless independent experimental evidence and claim review justify it.

## Evidence downgrade rules

Claims must be downgraded when:

- benchmark leakage is discovered;
- a cheap baseline beats the method;
- novelty audit finds near-duplicates;
- safety-risk flags are strong;
- simulation fails ablation;
- controls fail;
- external review rejects the interpretation;
- replication fails;
- result context is too weak to interpret.

A good project downgrades claims quickly.

## How agents should use this ladder

Before writing or editing any claim, agents should ask:

1. What evidence level supports this?
2. Does the wording exceed that level?
3. What caveat is required?
4. What would falsify this claim?
5. Is human review required?

If uncertain, choose weaker language.

## How reviewers should use this ladder

Reviewers should reject changes that:

- use Level 6+ language for dry-lab results;
- hide baseline failures;
- describe computational safety as biological safety;
- imply clinical relevance;
- turn a candidate-selection artifact into a discovery claim;
- omit relevant uncertainty.

## The highest-status behavior

In this repo, the highest-status behavior is not making stronger claims.

It is making claims exactly as strong as the evidence allows and no stronger.
