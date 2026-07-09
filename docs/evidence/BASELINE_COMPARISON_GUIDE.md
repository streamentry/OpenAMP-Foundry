# Baseline Comparison Manifest Guide

## Purpose

The baseline comparison manifest records whether the pipeline's predictions
actually beat cheap baselines on a specific metric. Every performance claim
must be grounded in a documented comparison. Without this, it is impossible
to know whether the pipeline adds value over random selection, charge matching,
or length matching.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| manifest_id | str | Unique identifier (prefix "BCM-") |
| batch_id | str | Batch being evaluated |
| pipeline_version | str | Pipeline version at time of comparison |
| comparison_date | str | ISO 8601 date of comparison |
| metric_name | str | The metric being compared (see valid metrics) |
| pipeline_score | float | Pipeline's score on this metric |
| baseline_scores | dict[str, float] | Score of each baseline (at least 1 required) |
| pipeline_beats_all_baselines | bool | Whether pipeline outperforms every baseline |
| effect_size | float | Quantified difference between pipeline and best baseline |
| p_value | float | Statistical significance (0.0–1.0, or -1.0 if not computed) |
| comparison_direction | str | Whether higher or lower is better (see valid directions) |
| notes | str | Optional context (max 300 chars, may be empty) |
| reviewer | str | Person or system that validated this comparison |
| dry_lab_only | bool | Always True (computational comparison) |

## Valid Metric Names

- `fold_change_mic` — fold change in minimum inhibitory concentration
- `hemolysis_fraction` — fraction of hemolysis
- `hit_rate` — fraction of candidates meeting activity threshold
- `mic_value` — raw MIC value
- `novelty_score` — sequence novelty vs. known AMPs
- `selectivity_index` — cytotoxicity IC50 / MIC ratio

## Valid Comparison Directions

- `higher_is_better` — e.g. hit rate, selectivity index
- `lower_is_better` — e.g. MIC value, hemolysis fraction

## Validation Rules

1. manifest_id must start with "BCM-"
2. metric_name must be one of the valid metrics
3. pipeline_score must be finite (not NaN or Inf)
4. baseline_scores must contain at least 1 baseline
5. all baseline_scores values must be finite
6. effect_size must be finite
7. p_value must be in [0.0, 1.0] or exactly -1.0 (sentinel for "not computed")
8. comparison_direction must be one of the valid directions
9. notes must not exceed 300 characters
10. reviewer must not be empty
11. dry_lab_only must be True

## Warning Conditions

- Pipeline does not beat all baselines: pipeline_beats_all_baselines=False → warn that pipeline underperforms at least one baseline
- Inconsistent verdict: pipeline_beats_all_baselines=True but pipeline score is actually worse than some baseline (accounting for direction) → warn about inconsistency
- No p-value: p_value == -1.0 → warn that statistical significance was not computed
- Large effect unchecked: abs(effect_size) > 10.0 and p_value == -1.0 → warn that a large claimed effect needs statistical validation

## Honest Use Boundary

A baseline comparison manifest records computational comparisons only. The
baselines must actually be evaluated — not assumed. A claim that the pipeline
beats random selection is only meaningful if random selection was actually
run and measured on the same data split. Cherry-picking the comparison metric
after seeing results defeats the purpose; comparisons should be pre-specified
(link to a PRE- registration where possible).
