# Responsible Use

## Purpose

This policy defines allowed and disallowed use of OpenAMP Foundry.

OpenAMP is an open dry-lab infrastructure project for antimicrobial peptide candidate triage, evidence packaging, benchmark governance, and qualified review.

It is not a clinical, laboratory-instruction, or unrestricted biological-design system.

## Allowed uses

You may use this project to:

- evaluate peptide candidates computationally;
- build reproducible benchmarks;
- generate auditable evidence certificates;
- compare scorers against cheap baselines;
- document model limitations;
- prepare candidates for qualified expert review;
- produce external review packets;
- pre-register candidate-selection logic;
- ingest structured result summaries at a safe abstraction level;
- preserve safe negative and positive scientific findings;
- build validators, schemas, reports, and tooling that improve auditability.

## Disallowed uses

You may not use this project to:

- design or optimize harmful biological capabilities;
- optimize toxicity, unsafe delivery, persistence, immune evasion, or pathogenicity;
- bypass safety review;
- bypass qualified expert review;
- publish unscreened high-risk candidate lists;
- claim biological activity without qualified evidence;
- claim human safety from dry-lab scores;
- market candidates as treatments;
- use outputs as medical or clinical advice;
- provide operational laboratory instructions through this repo;
- misrepresent computational nomination as biological validation.

## Claim rules

Allowed before experimental evidence:

- computationally nominated candidate;
- dry-lab candidate;
- selected for expert review;
- selected by reproducible pipeline;
- evidence package;
- candidate-selection hypothesis.

Not allowed before sufficient evidence:

- active antimicrobial;
- safe;
- drug candidate;
- therapeutic;
- clinically useful;
- proven;
- AI-discovered antibiotic.

Use `docs/PROOF_LADDER.md` and `docs/CLAIM_REVIEW_CHECKLIST.md`.

## Data and artifact rules

Users must respect:

- third-party data licenses;
- dataset redistribution limits;
- citation requirements;
- model release boundaries;
- candidate release review;
- safety review decisions;
- institutional and legal requirements.

If release status is unclear, do not publish the artifact.

## Agent use

AI agents may work on this repo only within explicit safety and task boundaries.

Good agent work:

- tests;
- validators;
- doc consistency;
- benchmark scaffolding;
- schema examples;
- report improvements;
- reproducibility checks;
- safe onboarding improvements.

Agents must not autonomously strengthen claims, release candidates, change safety policy, change model release policy, or add external-facing biological instructions.

## External partner use

External partners should treat OpenAMP outputs as computational evidence packages, not as instructions.

Any experimental, institutional, or clinical decision remains outside this repository and requires qualified oversight.

## Enforcement

Maintainers may reject, edit, restrict, remove, or revert contributions that violate this policy.

For sensitive issues, use safety-review workflows rather than public artifact release.

## Final note

This document is a governance policy, not a substitute for law, institutional review, biosafety review, ethics review, or domain expert review.
