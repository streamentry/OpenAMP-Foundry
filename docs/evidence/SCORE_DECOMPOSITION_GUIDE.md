# Score Decomposition Report Guide

## Purpose

Every composite score used to rank or filter candidates must be decomposable
into its constituent sub-scores. This schema records that decomposition so
external auditors can verify that the ranking algorithm behaves as documented.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| report_id | str | Unique identifier (prefix \"SDR-\") |
| batch_id | str | Batch this report belongs to |
| candidate_id | str | Candidate being scored |
| pipeline_version | str | Pipeline version string |
| composite_score | float | Final aggregated score |
| component_scores | dict[str, float] | Named sub-scores (at least 2 required) |
| component_weights | dict[str, float] | Weight assigned to each component (must sum to ~1.0) |
| scoring_method | str | Algorithm used (see valid methods) |
| score_range_min | float | Minimum possible composite score |
| score_range_max | float | Maximum possible composite score |
| reviewer | str | Reviewer who validated this decomposition |
| dry_lab_only | bool | Always True for computational scoring |

## Valid Scoring Methods

- `additive_weighted` — weighted sum of components
- `geometric_mean` — geometric mean of components
- `harmonic_mean` — harmonic mean of components
- `max_component` — maximum of component scores
- `min_component` — minimum of component scores (conservative)
- `rank_aggregation` — aggregated from per-component ranks

## Validation Rules

1. report_id must start with \"SDR-\"
2. composite_score must be between score_range_min and score_range_max (inclusive)
3. component_scores must contain at least 2 components
4. component_weights keys must match component_scores keys exactly
5. component_weights values must sum to between 0.99 and 1.01 (tolerance for float rounding)
6. scoring_method must be one of the valid methods
7. score_range_min must be less than score_range_max
8. reviewer must not be empty
9. dry_lab_only must be True

## Warning Conditions

- Dominant component: any single component weight > 0.6 → warn about over-reliance
- Low composite: composite_score < 20% of score range → warn that candidate is weakly ranked
- Unbalanced: max weight / min weight > 5.0 → warn about highly unbalanced weighting
- Many components: len(component_scores) > 8 → warn about scoring complexity

## Honest Use Boundary

Score decomposition records are computational. They document how the pipeline
ranks candidates, not how candidates perform in biological assays. A high
composite score means \"ranked highly by the algorithm\" — not \"active AMP\".
