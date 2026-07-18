# Recalibration Policy

## Purpose

This document defines the pre-registered policy that gates any OpenAMP recalibration.

The machine-readable contract lives in `configs/recalibration_policy.yaml`.

The policy exists because the most dangerous failure mode in a feedback-loop discovery system is silent self-rewriting after seeing outcomes.

## Synthetic data restriction

Synthetic lab results must not influence recalibration decisions or raise any candidate's proof_ladder_level. Only qualified wet-lab outcomes may trigger recalibration or elevate evidence levels. See VIRTUAL_ASSAY_SCOPE.md for the full synthetic-data policy.

## Prime rule

**Lab-result intake may describe what happened. It may not change ranking behavior unless the recalibration gate permits it and a qualified human review records the decision.**

A `may_recalibrate=true` verdict is permission to consider a change.

It is not a command to change the model.

## Why this exists

OpenAMP’s long-term goal is wet-lab compression: learn which experiments are worth running next.

That requires learning from outcomes.

But naive learning creates cherry-picking risk:

```text
see result
  -> adjust weights to make past result look expected
  -> claim improvement
  -> lose scientific validity
```

The recalibration policy prevents that failure by separating:

1. result intake;
2. gate evaluation;
3. weight-change proposal;
4. human review;
5. documented decision;
6. future-batch selection.

## What the gate protects

The gate protects against:

- too-small cohorts;
- failed or missing controls;
- orphan results;
- post-hoc success redefinition;
- relaxing safety floors;
- relaxing novelty floors;
- activity-only optimization;
- excessive weight movement;
- too-frequent recalibration;
- undocumented reviewer decisions.

Calibration intake keeps control-failed observations in the report so the
failure cannot be hidden, but excludes them from the per-assay actual
predicates and retrospective cohort metrics. The recalibration gate still
rejects any intake containing a control failure. This is an input-integrity
boundary, not a claim that the underlying assay is valid.

## Current recalibration architecture

```text
lab result files
  -> calibration intake
  -> intake report
  -> recalibration gate
  -> gate verdict
  -> recalibration engine proposal, if allowed
  -> human review
  -> decision log
  -> next-batch selection
```

The engine is subordinate to the gate.

If the gate rejects recalibration, the engine must not change ranking behavior.

## Gate evaluation

The gate:

1. Loads and validates `configs/recalibration_policy.yaml`.
2. Rejects the policy if canonical prohibited actions are missing.
3. Loads the calibration intake report.
4. Evaluates minimum conditions.
5. Surfaces prohibited actions as non-negotiable floors.
6. Evaluates rate limits where inputs are available.
7. Reports missing reviewer artifacts.
8. Emits a binary verdict plus reasons.

Exit codes:

| Code | Meaning |
|---:|---|
| 0 | Gate permits recalibration consideration. |
| 3 | Gate rejects recalibration. |
| 2 | Input missing or malformed. |

## Minimum conditions

| Rule | Purpose |
|---|---|
| `MIN_COHORT_SIZE` | Prevent one-off cherry-picking. |
| `MIN_POSITIVES_IN_COHORT` | Require positive evidence before learning from hits. |
| `MIN_NEGATIVES_IN_COHORT` | Require negative evidence before learning from failures. |
| `POSITIVE_CONTROLS_ALL_PASS` | Prevent interpreting a failed experiment as model evidence. |
| `NEGATIVE_CONTROLS_ALL_PASS` | Prevent false-positive interpretation. |
| `NO_ORPHAN_LAB_RESULTS` | Require every result to map to a known panel candidate. |
| `COHORT_METRICS_AVAILABLE` | Require enough data to interpret cohort behavior. |

Every rule should be listed in `locked_changes` in the policy YAML.

Relaxing any rule requires a policy version bump and decision record.

## Permanent prohibited actions

These floors are not normal tunable parameters.

| ID | Meaning |
|---|---|
| `NO_TOXICITY_RELAXATION` | Do not improve apparent activity by allowing more toxic candidates. |
| `NO_HEMOLYSIS_RELAXATION` | Do not relax hemolysis-related safety floors to rescue hits. |
| `NO_NOVELTY_RELAXATION` | Do not make rediscovery look like novelty. |
| `NO_DANGEROUS_PATHGEN_OPTIMIZATION` | Do not optimize harmful biological capability. |
| `NO_POST_HOC_SUCCESS_REDEFINITION` | Do not change success definitions after seeing outcomes. |

A policy file that omits canonical prohibited actions should fail validation.

## Rate limits

Rate limits prevent overfitting to a small or noisy batch.

| Rule | Purpose |
|---|---|
| `WEIGHT_CHANGE_L1_BUDGET` | Limits total weight movement per event. |
| `COOLDOWN_DAYS` | Prevents repeated rapid recalibration. |

If rate-limit inputs are missing, the verdict should surface uncertainty rather than pretending the rate limit was evaluated.

## Reviewer artifacts

A recalibration decision should have:

- intake report JSON;
- intake report Markdown;
- gate verdict;
- proposed weight update if any;
- human decision log;
- explanation of why the update is allowed or rejected;
- next-batch impact statement;
- claim-boundary statement.

Missing reviewer artifacts should be visible.

## Human review standard

Human review must answer:

1. Did the gate permit recalibration?
2. Are controls interpretable?
3. Does the result beat relevant baselines?
4. Does the proposed change preserve safety floors?
5. Does the proposed change preserve novelty floors?
6. Does the proposed change respect the L1 budget?
7. What claim, if any, becomes stronger?
8. What claim must remain unchanged?
9. What next-batch decision changes?
10. What would make this update wrong?

## Rejection is success

A rejected recalibration is not a failed system.

It means the evidence was not strong enough to justify changing behavior.

The gate should reject often when data are weak, noisy, uncontrolled, too small, unsafe, or ambiguous.

## What this policy is not

This policy is not:

- proof that a candidate works;
- proof that OpenAMP improves discovery;
- a replacement for human review;
- a benchmark regression gate;
- a safety review by itself;
- a license to optimize activity at the expense of safety;
- a way to change success definitions after the fact.

## Policy update procedure

To update the policy:

1. State the reason for change.
2. Identify whether the change tightens, relaxes, or clarifies a rule.
3. Bump `policy_version`.
4. Update `locked_at`.
5. Add or update `locked_changes` entries.
6. Write a dated decision log entry.
7. Run policy validation tests.
8. Update docs if interpretation changes.
9. Require human review for any relaxation.
10. Stop if the change removes a canonical prohibited action.

## Relationship to benchmark governance

Recalibration gates cohort-driven updates.

Benchmark governance gates model and benchmark claims.

Both are required.

A recalibration may be allowed by cohort evidence but still rejected if it worsens benchmark honesty or violates safety boundaries.

## Relationship to proof ladder

Recalibration can improve the system’s internal decision policy.

It does not automatically move a candidate up the proof ladder.

A candidate moves up the proof ladder only through the relevant evidence, especially qualified experimental results and independent replication.

## Final standard

The recalibration policy should make OpenAMP capable of learning from biology without letting the project rewrite its past to look smarter than it was.
