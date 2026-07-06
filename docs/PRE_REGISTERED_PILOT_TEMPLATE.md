# Pre-Registered Pilot Template

## Purpose

This template helps OpenAMP Foundry prepare a future qualified experimental pilot without cherry-picking, overclaiming, or weakening safety boundaries.

This document is not a wet-lab protocol.

It does not describe how to culture organisms, run assays, handle pathogens, or perform biological procedures.

It defines the computational and review artifacts that should be frozen before qualified partners run any independent testing under their own approved procedures and oversight.

## Pilot name

`<pilot_name>`

## Pilot status

Choose one:

- Draft
- Under expert review
- Frozen before testing
- Results received
- Interpreted
- Archived

## Responsible parties

| Role | Name / organization | Responsibility |
|---|---|---|
| Computational lead | TBD | Produces candidate evidence package. |
| Safety reviewer | TBD | Reviews release and misuse boundaries. |
| Domain reviewer | TBD | Reviews biological plausibility and candidate panel. |
| Qualified testing partner | TBD | Runs any experimental work under its own approved procedures. |
| Result interpreter | TBD | Interprets results within claim boundaries. |

## Scope statement

This pilot asks whether an OpenAMP-selected candidate panel produces more useful early antimicrobial evidence than simple baseline selection under qualified testing conditions.

It does not ask whether any candidate is a drug, treatment, cure, clinical candidate, or proven safe/effective antimicrobial.

## Evidence level before testing

Before testing, every candidate must be treated as Level 4 or below under [`PROOF_LADDER.md`](PROOF_LADDER.md): a computationally nominated candidate with a reviewable evidence package.

## Candidate panel

### OpenAMP-selected panel

| Field | Requirement |
|---|---|
| Number of candidates | TBD |
| Selection commit | TBD |
| Selection config | TBD |
| Candidate manifest | TBD |
| Evidence certificates | Required for every candidate |
| Novelty report | Required |
| Safety-risk report | Required |
| Synthesis-risk report | Required |
| Diversity report | Required |
| Known blind spots | Required |

### Baseline comparison panels

At least one baseline panel should be included if scientifically and operationally feasible.

Possible baselines:

- random valid candidates;
- charge-density-ranked candidates;
- similarity-to-known-AMP candidates;
- human expert-selected candidates;
- external predictor consensus;
- diversity-only panel;
- safety-first conservative panel.

Baseline selection rules must be frozen before results are known.

## Controls

Controls should be selected and interpreted by qualified experts.

This template does not specify biological procedures or operational details.

Record only the safe, reviewable rationale:

| Control type | Rationale | Reviewer |
|---|---|---|
| Positive control | TBD | TBD |
| Negative control | TBD | TBD |
| Process/control artifact | TBD | TBD |

## Pre-registered success criteria

Define success before testing.

Examples of acceptable computationally interpretable criteria:

- OpenAMP panel produces more useful activity signals than the baseline panel.
- OpenAMP panel produces better safety-adjusted yield than the baseline panel.
- OpenAMP panel produces a clear negative result that falsifies a selection assumption.
- Result quality is sufficient to support or reject recalibration.

Do not use vague criteria such as “promising” without measurable interpretation rules.

## Pre-registered failure criteria

Define failure before testing.

Examples:

- OpenAMP panel does not outperform cheap baselines.
- Candidate effects are uninterpretable due to control failure.
- Safety-relevant screens reject the apparent activity signal.
- Hits are near-duplicates of known AMPs and do not support novelty claims.
- Results are too noisy or incomplete to justify recalibration.

A clean failure is useful if it changes the next experiment-selection loop.

## Claim boundaries

Before results:

Allowed:

- computationally nominated candidates;
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

After results, claims must follow [`PROOF_LADDER.md`](PROOF_LADDER.md).

## Safety review

Answer before freezing the pilot:

| Question | Answer |
|---|---|
| Does the package publish unsafe operational details? | TBD |
| Does it include unscreened high-risk candidate dumps? | TBD |
| Does it include harmful optimization objectives? | TBD |
| Does it blur computational and experimental evidence? | TBD |
| Does it require staged release? | TBD |
| Does an external safety/domain expert need to review before publication? | TBD |

## Data and artifact freeze

Before any result is known, freeze:

- candidate manifest;
- evidence certificates;
- config files;
- code commit;
- baseline panels;
- selection rules;
- success/failure criteria;
- claim boundaries;
- safety review decision.

Record hashes where possible.

## Result intake plan

Results should enter through versioned schemas or structured artifacts.

Required result context:

- candidate identifier;
- panel identity;
- control interpretation at a safe abstraction level;
- endpoint summary;
- uncertainty or quality flag;
- whether the result is interpretable;
- whether the result supports recalibration;
- limitations.

Do not publish unsafe operational details.

## Recalibration decision

After result intake, run the pre-registered recalibration gate.

A gate rejection is not a failure of the project.

It means the evidence was not strong enough to justify changing model behavior.

Record:

| Field | Value |
|---|---|
| Intake report | TBD |
| Gate verdict | TBD |
| Recalibration allowed? | TBD |
| Human reviewer | TBD |
| Decision rationale | TBD |

## Publication plan

Before public release, decide:

- what can be safely published;
- what must be summarized rather than released;
- what negative results can be shared;
- what claims are allowed;
- what limitations must appear in the first paragraph;
- whether external review is required before release.

## Post-pilot questions

After the pilot, answer:

1. Did OpenAMP beat the baseline panels?
2. Did safety adjustment change the interpretation?
3. Were any candidates near-duplicates of known references?
4. Did the results justify recalibration?
5. What assumption was falsified?
6. What should the next batch test?
7. What should be documented as a negative result?
8. What claim level is now justified?

## Pilot verdict

Choose one:

- Strong positive evidence for selection improvement.
- Weak positive evidence; needs replication.
- Negative but informative; selection logic should change.
- Negative and not informative; pilot design should change.
- Inconclusive due to control/result quality.
- Safety or release concern; do not publish full artifact.

## Final rule

The pilot exists to discover the truth about OpenAMP’s selection logic.

It does not exist to protect the story.
