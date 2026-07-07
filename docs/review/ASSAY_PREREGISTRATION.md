# Pilot Pre-Registration — Candidate-Selection Evaluation

## Status

**Template / planning artifact. Not a wet-lab protocol.**

This document freezes the computational selection logic, comparison groups, success/failure criteria, result-intake expectations, and claim boundaries for a future qualified external pilot.

It does not provide experimental procedures, culturing conditions, assay recipes, organism-handling guidance, biospecimen procedures, or operational biological instructions.

Qualified partners must use their own approved protocols, oversight, biosafety systems, and institutional review processes.

## Purpose

Pre-registration prevents p-hacking, outcome switching, selective reporting, and after-the-fact story repair.

The pilot asks one narrow question:

> Does an OpenAMP-selected candidate panel produce more useful experimental information than simple baseline-selection strategies under qualified external review/testing conditions?

The pilot does not ask whether any candidate is a drug, therapy, cure, clinical candidate, proven antimicrobial, or safe/effective in humans.

## Related documents

- [`PRE_REGISTERED_PILOT_TEMPLATE.md`](PRE_REGISTERED_PILOT_TEMPLATE.md) — general pilot template.
- [`EXTERNAL_REVIEW_PACKET.md`](EXTERNAL_REVIEW_PACKET.md) — review packet standard.
- [`WET_LAB_HANDOFF.md`](WET_LAB_HANDOFF.md) — safe expert-review handoff guide.
- [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md) — evidence levels and claim ladder.
- [`CALIBRATION_POLICY.md`](../evidence/CALIBRATION_POLICY.md) — gate before any recalibration.
- [`NEGATIVE_RESULT_ARCHIVE.md`](../evidence/NEGATIVE_RESULT_ARCHIVE.md) — safe negative-result format.

## Pilot identity

| Field | Value |
|---|---|
| Pilot name | TBD |
| Status | Draft / frozen / results received / interpreted / archived |
| Selection commit | TBD |
| Pipeline version | TBD |
| Candidate manifest | TBD |
| Manifest hash | TBD |
| Pre-registration date | TBD |
| Locked by | TBD |
| Safety reviewer | TBD |
| Domain reviewer | TBD |
| Qualified external partner | TBD |

## Candidate set

Before any result is known, freeze:

- candidate IDs or safe sequence references;
- panel role for each candidate;
- evidence certificate for each candidate;
- novelty label;
- safety-risk label;
- synthesis-feasibility label;
- diversity cluster or scaffold family;
- proof-ladder level;
- release status.

Full candidate identities or sequences should be handled according to safety and release policy.

## Panel roles

A well-designed panel should include more than top-ranked leads.

Possible roles:

| Role | Purpose |
|---|---|
| Lead candidate | Tests the pipeline’s best current selection logic. |
| Baseline challenger | Tests whether simple heuristics perform as well or better. |
| Known-control reference | Helps contextualize the external partner’s result interpretation. |
| Negative-control candidate | Helps test specificity of selection logic. |
| Uncertainty probe | Tests a candidate where the model is unsure but information value is high. |
| Diversity probe | Tests underrepresented structural or sequence classes. |
| Safety-boundary probe | Tests whether predicted safety-risk flags are meaningful, if ethically and safely appropriate. |

A panel is an experimental question, not a top-k list.

## Baseline comparison plan

At least one baseline-selection strategy should be frozen before results are known.

Possible baselines:

- random valid candidates;
- charge-density selection;
- similarity-to-known-AMP selection;
- diversity-only selection;
- conservative safety-first selection;
- external-predictor consensus;
- human expert selection where available.

If no baseline comparison is included, the pilot must be labeled exploratory and cannot support experiment-compression claims.

## Pre-registered success criteria

Choose and freeze measurable criteria before results.

Examples:

| Criterion | Interpretation |
|---|---|
| OpenAMP panel outperforms baseline panel on useful activity signals | Supports selection improvement under tested context. |
| OpenAMP panel outperforms baseline panel on safety-adjusted yield | Stronger than activity alone. |
| OpenAMP panel reveals a model blind spot that changes next-batch selection | Negative or mixed result still useful. |
| Result quality is sufficient for recalibration-gate evaluation | Supports learning-loop progress. |

Do not use vague criteria such as “promising” unless the term is operationally defined by qualified reviewers before results.

## Pre-registered failure criteria

Choose and freeze failure criteria before results.

Examples:

| Criterion | Interpretation |
|---|---|
| OpenAMP panel does not beat cheap baselines | Experiment-compression claim is unsupported. |
| Controls or partner quality flags make results uninterpretable | No model update should occur. |
| Apparent hits are near-duplicates of known references | Novelty claim must be downgraded. |
| Activity-like signals are safety-adjusted failures | Activity-only selection is not enough. |
| Result set is too small or too imbalanced for calibration | Recalibration gate should reject. |

A clean failure is useful if it changes the next selection loop.

## Result-intake plan

Results should return as structured summaries compatible with project schemas.

Required safe fields include:

- candidate ID;
- panel ID;
- endpoint type at a safe abstraction level;
- result summary;
- quality/control interpretation supplied by the qualified partner;
- whether the result is interpretable;
- whether the result can be used in calibration intake;
- limitations;
- release status.

Operational experimental detail should remain outside this repository.

## Calibration decision plan

After structured result intake:

1. Generate a calibration intake report.
2. Run the recalibration gate.
3. Record the gate verdict.
4. If rejected, preserve the rejection and do not update selection behavior.
5. If permitted, prepare a weight-change proposal or next-batch policy proposal.
6. Require human review before applying any change.
7. Record the decision in a dated decision log.

See [`CALIBRATION_POLICY.md`](../evidence/CALIBRATION_POLICY.md).

## Claim boundaries

### Before results

Allowed:

- computationally nominated candidate;
- selected for expert review;
- selected for possible qualified testing;
- evidence package;
- pre-registered pilot.

Forbidden:

- active antimicrobial;
- safe;
- drug candidate;
- therapeutic;
- clinical;
- AI-discovered antibiotic;
- proven.

### After results

Claims must follow [`PROOF_LADDER.md`](../evidence/PROOF_LADDER.md).

Examples:

- “showed activity under specified partner-reported conditions” may require initial qualified evidence.
- “independently replicated early signal” requires external replication.
- “clinical” or “therapeutic” language is outside normal repo authority.

## Reporting obligations

The pilot should report:

- all candidates in the frozen panel, where safe;
- all baseline candidates, where safe;
- inactive or negative candidates, where safe;
- uninterpretable results;
- deviations from the frozen plan;
- safety or release restrictions;
- claim level;
- recalibration-gate verdict;
- next-batch implications.

Selective reporting is forbidden.

## Deviation log

Any deviation from the frozen computational/review plan should be recorded before interpretation.

| Date | Deviation | Why it occurred | Approved by | Effect on interpretation |
|---|---|---|---|---|
| — | — | — | — | — |

## Sign-off

| Role | Name | Organization | Decision | Date |
|---|---|---|---|---|
| Computational lead | TBD | TBD | Draft / approved / rejected | TBD |
| Domain reviewer | TBD | TBD | Draft / approved / rejected | TBD |
| Safety reviewer | TBD | TBD | Draft / approved / rejected | TBD |
| Qualified partner representative | TBD | TBD | Draft / approved / rejected | TBD |

## Final rule

The pre-registration exists to find out whether OpenAMP’s selection logic works.

It does not exist to protect OpenAMP’s story.
