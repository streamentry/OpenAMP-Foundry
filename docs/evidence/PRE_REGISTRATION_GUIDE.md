# Pre-Registration Form Guide

## Purpose

A pre-registration form records what a team commits to test, how they will
measure success, and what baselines they will compare against — all recorded
before experimental results are observed. This prevents post-hoc
rationalization (HARKing: Hypothesising After Results are Known) and makes
the pipeline's predictions independently falsifiable.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| registration_id | str | Unique identifier (prefix "PRE-") |
| batch_id | str | Candidate batch this registration applies to |
| pipeline_version | str | Pipeline version at time of registration |
| registration_date | str | ISO 8601 date of registration (before experiments run) |
| primary_hypothesis | str | The single main claim being tested (max 500 chars) |
| primary_outcome_metric | str | How success is measured (see valid metrics) |
| success_threshold | float | Numeric threshold that constitutes success |
| baseline_comparators | list[str] | Cheap baselines this must beat (at least 1) |
| candidate_ids | list[str] | IDs of candidates included in this experiment |
| assay_type | str | Type of assay to be used (see valid types) |
| statistical_test | str | Planned statistical test (max 200 chars) |
| registered_by | str | Person or system that filed this registration |
| dry_lab_only | bool | Always True (this is a computational pre-commitment) |

## Valid Primary Outcome Metrics

- `fold_change_mic` — fold change in minimum inhibitory concentration
- `hemolysis_fraction` — fraction of red blood cells lysed
- `hit_rate` — fraction of candidates meeting activity threshold
- `mic_value` — raw MIC value in ug/mL
- `selectivity_index` — ratio of cytotoxicity IC50 to MIC
- `survival_improvement` — improvement in survival vs. control

## Valid Assay Types

- `cytotoxicity_assay`
- `hemolysis_assay`
- `membrane_disruption_assay`
- `mic_assay`
- `stability_assay`

## Validation Rules

1. registration_id must start with "PRE-"
2. primary_hypothesis must not be empty and must not exceed 500 characters
3. primary_outcome_metric must be one of the valid metrics
4. success_threshold must be a finite number (not NaN or Inf)
5. baseline_comparators must contain at least 1 baseline
6. candidate_ids must contain at least 1 candidate
7. assay_type must be one of the valid assay types
8. statistical_test must not be empty and must not exceed 200 characters
9. registered_by must not be empty
10. dry_lab_only must be True

## Warning Conditions

- Missing random baseline: "random" not in any baseline_comparators entry → warn that random selection baseline is missing
- Large candidate set: len(candidate_ids) > 20 → warn about multiple comparisons burden
- Short hypothesis: primary_hypothesis < 50 chars → warn that hypothesis may be underspecified
- No statistical test named: statistical_test == "TBD" or "N/A" (case-insensitive) → warn

## Honest Use Boundary

A pre-registration record is a dry-lab commitment document. It does not
guarantee that the assay will be run, that the hypothesis will be tested fairly,
or that the statistical test named will be appropriate. Human scientists must
review this commitment before experiments begin. The value of pre-registration
comes from committing *before* results are known — retroactively filing a
pre-registration after seeing results defeats its purpose entirely.
