# Mission

## One-sentence mission

**Build the world’s most rigorous open, safety-first AI antimicrobial peptide foundry: a reproducible dry-lab system that generates, filters, documents, and prepares novel antimicrobial candidates for qualified experimental validation through evidence rather than hype.**

## Ultimate goal

OpenAMP Foundry exists to discover whether an AI-directed, open, auditable candidate-selection pipeline can identify novel antimicrobial peptide families that later survive real laboratory validation.

The desired long-term result is:

> An open AI pipeline discovers a novel antimicrobial peptide family, independently validated in qualified lab testing, with the full computational evidence trail released for scientific review.

This project must never claim that a computational prediction is a drug, cure, therapy, or proven antimicrobial result. The lab is the judge.

## Why this matters

Antimicrobial resistance is one of the clearest global scientific threats. The world needs more credible ways to search for new antimicrobial candidates, but most AI-for-science projects fail by overclaiming, cherry-picking, or hiding negative results.

OpenAMP Foundry is designed around the opposite principle:

> Every candidate must carry its evidence, limitations, failure modes, and reproducible selection history.

The project should create value even before any lab hit by producing cleaner benchmarks, safer filters, auditable candidate certificates, and reusable negative-result infrastructure.

## What the project is

OpenAMP Foundry is a dry-lab pipeline for:

1. Loading and cleaning antimicrobial peptide reference data.
2. Checking benchmark leakage and near-duplicate contamination.
3. Generating or importing candidate peptide sequences.
4. Extracting physicochemical features.
5. Scoring predicted antimicrobial activity.
6. Penalizing predicted hemolysis, cytotoxicity, and unsafe properties.
7. Checking novelty against known AMP references.
8. Ranking diverse candidate batches.
9. Producing machine-readable evidence certificates.
10. Preparing qualified, safety-reviewed candidate batches for external experimental validation.

## What the project is not

OpenAMP Foundry is not:

- a wet-lab protocol repository;
- a dangerous pathogen research guide;
- a toxin-design system;
- a clinical drug-discovery claim machine;
- a hype engine for “AI discovered a cure” narratives;
- a project that publishes unscreened high-risk candidate lists without review.

The project does not provide instructions for culturing, enhancing, or misusing biological agents.

## Scientific standard

A result is not meaningful because a model ranks it highly.

A candidate becomes scientifically interesting only when it passes increasingly hard gates:

```text
valid sequence
→ reproducible features
→ predicted activity
→ predicted low toxicity / low hemolysis
→ novelty check
→ synthesis feasibility
→ diversity selection
→ evidence certificate
→ expert review
→ qualified lab assay
→ independent replication
```

Computational evidence can justify testing. It cannot prove biological efficacy.

## Headline-grade result

A result is headline-grade only if all conditions below are met:

| Requirement | Minimum standard |
|---|---|
| Novelty | Candidate family is not a trivial near-duplicate of known AMPs |
| Activity | At least one candidate shows meaningful antimicrobial activity in qualified lab testing |
| Safety | Candidate shows low hemolysis / low mammalian cytotoxicity in initial screening |
| Relevance | Testing uses an appropriate, safety-reviewed bacterial panel through qualified partners |
| Reproducibility | The dry-lab pipeline can be rerun from versioned inputs |
| Evidence | Every selected candidate has a valid evidence certificate |
| Independence | Key result is reproduced by an external lab or CRO |
| Honesty | Negative results and failed candidates are documented where safe |
| Safety | Release is reviewed for dual-use and misuse risk |
| Review | Claims are reviewed by qualified domain experts |

Only then may the project claim:

> An open AI discovery pipeline produced a newly validated antimicrobial peptide family.

## Core operating principles

### 1. Evidence before confidence

Every important claim must point to code, data, tests, benchmark results, literature, evidence certificates, or expert review.

Unsupported claims must be removed or explicitly marked as speculation.

### 2. Reproducibility over impressiveness

A boring result that reproduces is more valuable than an impressive result that cannot be checked.

Major outputs should include:

- input data hash;
- model and scorer versions;
- config file;
- command used;
- random seed;
- code commit;
- output hash;
- timestamp.

### 3. The lab is the judge

Computational scores are pre-lab triage, not biological proof.

Allowed terms before lab validation:

- computationally nominated candidate;
- predicted antimicrobial peptide;
- dry-lab candidate;
- selected by reproducible pipeline.

Forbidden terms before sufficient evidence:

- drug;
- cure;
- safe;
- effective in humans;
- clinically useful;
- proven therapy;
- breakthrough treatment.

### 4. No cherry-picking

Preserve failures, rejected candidates, benchmark weaknesses, model disagreements, and negative results where safe.

A project that only publishes successes is not trustworthy.

### 5. Safety-first optimization

The default objective must combine:

```text
high predicted antimicrobial activity
+ low predicted mammalian toxicity
+ low predicted hemolysis
+ novelty
+ synthesis feasibility
+ candidate diversity
```

The project must not optimize for mammalian toxicity, virulence, immune evasion, harmful delivery, pathogen enhancement, or misuse against humans, animals, or crops.

### 6. Human review remains mandatory

AI agents may propose, implement, score, rank, and report.

AI agents may not make final scientific, safety, legal, release, lab-testing, or public-claim decisions.

## Near-term success criteria

The first serious milestone is not a lab discovery. It is a trustworthy dry-lab system.

Phase 1 is successful when a clean checkout can:

1. Run the demo pipeline.
2. Rank candidate peptide sequences.
3. Validate evidence certificates against JSON Schema.
4. Generate a batch report.
5. Run tests in CI.
6. Penalize obvious unsafe or low-quality candidates.
7. Produce deterministic outputs from fixed inputs.

Phase 2 is successful when retrospective benchmarks show that the pipeline:

1. Recovers hidden known active AMPs better than random or naive baselines.
2. Remains meaningful under cluster-split evaluation.
3. Does not rely on near-duplicate leakage.
4. Down-ranks negative or toxic examples.
5. Produces stable rankings under repeated runs.

Phase 3 is successful when the project has a lab-ready candidate pack with:

1. 50–100 selected candidates.
2. Evidence certificate for each candidate.
3. Novelty report.
4. Toxicity / hemolysis risk report.
5. Diversity clustering report.
6. Synthesis feasibility report.
7. Pre-registered selection rule.
8. Pass/fail criteria.
9. External expert review.
10. Dual-use safety review.

## Kill criteria

Stop, downgrade, or redesign the project if:

| Failure | Required response |
|---|---|
| Pipeline cannot beat simple baselines | Do not proceed to lab preparation |
| Rankings depend on leakage | Fix benchmark before claiming progress |
| Top candidates are near-duplicates of known AMPs | Strengthen novelty filters |
| Toxicity risk is ignored | Block candidate release |
| Outputs are not reproducible | Block external claims |
| Agents propose harmful objectives | Remove, review, and harden policy |
| Human reviewers cannot understand the evidence | Improve reports before continuing |
| Lab tests show no signal after repeated cycles | Publish negative result and reassess |

Failure is allowed. Unverifiable success is not.

## Final desired headline

The project should work toward this headline and no weaker hype version:

> **Open AI pipeline discovers a new antimicrobial peptide family, independently validated in lab tests, with full reproducible evidence trail released for scientific review.**

Everything in this repository should move the project closer to that standard.
