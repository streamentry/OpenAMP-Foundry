# Calibration Review Policy

OpenAMP Foundry should treat score calibration as a maintained claim, not a one-time benchmark artifact.

A score can be useful today and misleading later if the dataset, baseline, reference set, or selection objective changes. This policy defines when calibration claims should be reviewed again.

This is an evidence-governance document only. It does not add biological protocols, candidate-generation instructions, or optimization objectives.

## What calibration means here

Calibration means that a score, rank, threshold, or confidence label has an interpretable relationship to the decision it supports.

Examples:

- a threshold separates stronger candidates from weak controls in a declared benchmark slice;
- a confidence label maps to a reproducible evidence level;
- a score weight improves a shortlist decision against a cheap baseline;
- a model output remains useful after novelty, feasibility, and safety filters.

Calibration is not proof of biological activity.

## Review triggers

Recheck calibration when any of these changes:

- dataset version;
- benchmark split or benchmark slice;
- reference set;
- scoring weights;
- novelty rules;
- feasibility or safety filters;
- external predictor version;
- candidate-selection objective;
- evidence certificate schema;
- known failure slice;
- accepted baseline.

## Minimum calibration review note

```markdown
## Calibration review

**Component:** Score, threshold, model, ranker, or confidence label.

**Decision supported:** What decision depends on this calibration?

**Last calibrated on:** Dataset, benchmark slice, and date or commit.

**Trigger:** What changed?

**Expected stability:** Why should the old calibration still hold, or why not?

**Check performed:** Report, command, review method, or reason not run.

**Result:** stable | narrowed | exploratory | blocked | follow-up required.

**Decision impact:** What should change in ranking, threshold, confidence, or review status?
```

## Reviewer guidance

Reviewers should ask for calibration review when a PR changes a component that downstream selection relies on.

A PR may still merge without full recalibration if the component is clearly marked exploratory or if the change cannot affect decision weight.

## Agent guidance

Agents should not reuse old thresholds after changing the input distribution.

Before promoting a score or threshold, an agent should identify the last calibration artifact and say whether the current change invalidates it.

## Anti-patterns

Avoid:

- reusing a threshold after changing the dataset;
- treating rank improvement as calibration;
- hiding calibration limits in prose;
- updating a scorer without updating the confidence boundary;
- using a model output as if it were a calibrated probability when it is only a relative score.

## Acceptance test

A calibration review is adequate when a skeptical reviewer can answer:

1. What decision depends on this score or threshold?
2. What changed since the last calibration?
3. Why should confidence stay the same or change?
4. What status should the component carry now?

If those answers are missing, the component should not become load-bearing.
