# Reviewer Onboarding

## Purpose

This guide helps reviewers evaluate OpenAMP Foundry contributions, artifacts, claims, and releases.

OpenAMP reviewers should not ask only “does it work?”

They should ask:

> Does this make the project more trustworthy, safer, more reproducible, and harder to fool?

## Reviewer roles

### Engineering reviewer

Focus:

- tests;
- determinism;
- schema validation;
- code quality;
- dependency risk;
- CLI behavior;
- reproducibility.

### Scientific reviewer

Focus:

- benchmark validity;
- cheap-baseline comparison;
- leakage risk;
- label meaning;
- novelty interpretation;
- uncertainty;
- proof-ladder placement.

### Safety reviewer

Focus:

- release scope;
- misuse risk;
- claim safety;
- external-facing boundaries;
- model/data/candidate release;
- human review gates.

### Agent-work reviewer

Focus:

- scope creep;
- generated overclaims;
- missing limitations;
- unsupported broad rewrites;
- required source-of-truth updates;
- whether human review is needed.

## Review class mapping

| Class | Examples | Review expectation |
|---|---|---|
| A | typo, small docs, bug fix | basic correctness. |
| B | schema, CLI, report, CI, docs governance | tests/docs/compatibility. |
| C | scoring, benchmark, selection, calibration | scientific review and baselines. |
| D | safety, release, external-facing artifacts | safety review required. |

## Universal review checklist

Ask these for every meaningful PR:

1. Is the scope clear?
2. Does the change solve a real bottleneck?
3. Are tests or checks included?
4. Are docs updated if behavior changed?
5. Are limitations stated?
6. Does the change affect safety or release status?
7. Does the wording exceed evidence?
8. Does a future human or agent have enough context?

## Scientific review checklist

Ask:

- What claim does this support?
- What proof-ladder level applies?
- What cheap baseline challenges it?
- Could charge, length, hydrophobicity, or similarity explain the result?
- Could leakage explain the result?
- Is the negative set meaningful?
- Are confidence intervals or uncertainty visible?
- Does the result generalize or only fit one benchmark?
- Does a failed result get preserved?

## Safety review checklist

Ask:

- Does this release sensitive artifacts?
- Does this change candidate or model release status?
- Does this include operational biological detail?
- Does this encourage unqualified use?
- Does this imply biological proof from computation?
- Does this need staged, restricted, metadata-only, or no release?
- Is the review decision recorded?

## Agent review checklist

Ask:

- Did the agent stay within allowed scope?
- Did it change safety-sensitive files?
- Did it strengthen claims?
- Did it update the project index for new docs?
- Did it add limitations?
- Did it create broad churn without evidence?
- Does a human need to approve final interpretation?

## Common review comments

Use direct comments like:

- “Please map this claim to `docs/PROOF_LADDER.md`.”
- “This needs a cheap-baseline comparison before it can affect ranking.”
- “This reads like validation, but the evidence is dry-lab only.”
- “Please add release status.”
- “This belongs in a review packet, not the README.”
- “This needs safety review before merge.”
- “Good negative result. Please preserve it in the appropriate artifact.”

## Review outcomes

Allowed outcomes:

- approve;
- approve with caveats;
- request tests;
- request docs;
- request baseline comparison;
- request safety review;
- request scientific review;
- downgrade claim;
- split PR;
- reject as unsafe;
- reject as unsupported.

## Final standard

A good reviewer protects the future credibility of the project.

The best review often makes a claim weaker, a benchmark harder, or a release slower.
