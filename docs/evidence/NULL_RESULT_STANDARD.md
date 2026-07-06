# Null Result Standard

OpenAMP Foundry should treat null, weak, and failed-screening results as scientific assets, not as dead ends.

This document defines how to record a result that does **not** support a candidate, scoring rule, benchmark assumption, virtual-assay layer, or wet-lab hypothesis.

The standard is intentionally conservative: it does not add biological protocols, operating instructions, sequences, or optimization recipes. It only defines how to make non-confirming evidence reviewable and reusable.

## Why this matters

A dry-lab foundry can fail quietly by publishing only attractive shortlists and successful-looking certificates.

For AMP discovery, that creates three bad incentives:

1. **Selection bias** — failed candidates vanish, so later agents rediscover the same weak ideas.
2. **Benchmark theater** — scorers look better because the project does not preserve where they failed.
3. **Wet-lab waste** — scarce experimental budget is spent rerunning ideas that the project already had reason to doubt.

A useful foundry remembers what did not work and why.

## What counts as a null result

Record a null result when a method, candidate, model, screen, or assumption fails to produce the expected support under a legitimate test.

Examples:

- A candidate that ranked highly by a baseline scorer is later rejected by novelty, feasibility, safety, synthesis, selectivity, or expert review.
- A predictor or heuristic fails to recover known positives in a declared benchmark slice.
- A calibration run shows that a score threshold does not separate positives from controls strongly enough for its intended use.
- A wet-lab or external-review response does not support the dry-lab expectation.
- A data source thought to be useful turns out to be too noisy, stale, biased, duplicated, or license-constrained for the claim it was supporting.
- A proposed virtual-assay layer adds complexity but no measurable improvement over cheaper baselines.

Do **not** record casual hunches. A null result needs a declared expectation, a test or review event, and a conclusion boundary.

## Minimum record

A null result should be recorded in the nearest relevant artifact: benchmark report, evidence certificate notes, review packet, issue, PR, or a dedicated `null-results.md` file once a workstream has repeated failures worth preserving.

Use this structure:

```markdown
## NR-YYYY-NNN — Short result name

**Object tested:** Candidate ID, scorer, benchmark slice, dataset, review packet, or hypothesis.

**Expected support:** What result would have strengthened the claim?

**Observed result:** What happened instead?

**Method or review event:** Link to run manifest, benchmark report, review comment, external packet, or issue.

**Scope of failure:** What does this weaken, and what does it not prove?

**Decision impact:** no change | threshold changed | claim narrowed | candidate removed | scorer demoted | follow-up required

**Cheapest follow-up:** The smallest safe check that would distinguish noise from a real limitation.
```

## Decision impact semantics

| Impact | Meaning |
|---|---|
| `no change` | Result is recorded but too weak to change selection or claims. |
| `threshold changed` | A cutoff, calibration rule, or confidence boundary should change. |
| `claim narrowed` | The claim may survive only under a narrower scope. |
| `candidate removed` | The candidate should not remain in a shortlist or handoff packet. |
| `scorer demoted` | The scoring component should carry lower weight or be marked exploratory. |
| `follow-up required` | No canonical claim should depend on this object until the follow-up is done. |

## Required boundaries

A null result must not overclaim.

Bad:

> This peptide class does not work.

Better:

> Under the current demo baseline and this benchmark slice, the scorer did not separate this candidate group from weak controls well enough to justify shortlist inclusion.

Bad:

> The model is useless.

Better:

> The model did not improve the declared selection metric over the cheap baseline on this dataset version; it remains exploratory until a new benchmark shows otherwise.

## Reviewer guidance

Reviewers should ask for a null-result record when a PR discovers a non-confirming result that future contributors are likely to repeat.

A PR can still be valuable when the main outcome is "do not pursue this path yet." That is especially true when the path looked plausible, cheap predictors favored it, or an agent would otherwise keep rediscovering it.

## Agent guidance

Before proposing a new candidate-selection rule, model, dataset, or benchmark shortcut, an agent should check whether a similar attempt already produced a null result.

The agent should explicitly answer:

1. Am I repeating a known weak path?
2. Has a threshold, scorer, or candidate family already been bounded by a prior null result?
3. Does my proposed change resolve the old limitation, or merely ignore it?
4. What result would make me abandon this change?

If the answer changes the work plan, the PR should cite or update the null-result record.

## Relationship to safety

Null results are safety infrastructure.

They reduce pressure to over-optimize speculative candidates, discourage selective reporting, and make it easier to stop before unsafe or scientifically weak ideas enter expert-review or wet-lab conversations.

A foundry that cannot remember failure will eventually launder failure into confidence.

## Acceptance test

A null-result record is good when a future contributor can decide in under five minutes whether:

- the failed path is worth retrying;
- the claim boundary changed;
- a candidate, scorer, or dataset should be avoided;
- the next test would produce genuinely new information.

If it cannot do that, it is not yet a useful scientific artifact.
