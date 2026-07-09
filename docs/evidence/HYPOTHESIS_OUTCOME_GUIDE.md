# Hypothesis Outcome Record Guide

## Purpose

A hypothesis outcome record documents whether a pre-registered hypothesis was
confirmed or refuted after experimental results are received. It links the
outcome to the pre-registration form, records the observed metric value,
and requires an explicit interpretation. This closes the HARKing-prevention
loop: the pre-registration (N1) commits to what will be tested; the outcome
record (N2) reports what was found, whether convenient or not.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| outcome_id | str | Unique identifier (prefix "HOR-") |
| registration_id | str | Matching PRE- registration this outcome closes |
| batch_id | str | Batch that was tested |
| pipeline_version | str | Pipeline version used |
| outcome_date | str | ISO 8601 date results were recorded |
| outcome_verdict | str | Whether hypothesis was confirmed or refuted (see valid verdicts) |
| observed_metric_value | float | Actual observed value for the primary outcome metric |
| success_threshold_met | bool | Whether the pre-specified threshold was met |
| interpretation | str | Researcher's plain-language interpretation (max 500 chars) |
| deviation_from_plan | str | Any deviation from pre-registered plan (empty string if none) |
| recorded_by | str | Person or system that recorded this outcome |
| dry_lab_only | bool | False if real lab data; True if computational simulation only |

## Valid Outcome Verdicts

- `confirmed` — hypothesis was supported by observations
- `refuted` — hypothesis was not supported by observations
- `inconclusive` — results were ambiguous or experiment had quality issues
- `partially_confirmed` — hypothesis was supported for a subset of candidates

## Validation Rules

1. outcome_id must start with "HOR-"
2. registration_id must start with "PRE-"
3. outcome_verdict must be one of the valid verdicts
4. observed_metric_value must be finite (not NaN or Inf)
5. interpretation must not be empty and must not exceed 500 characters
6. recorded_by must not be empty

## Warning Conditions

- Verdict/threshold mismatch: success_threshold_met=True but outcome_verdict="refuted" → warn about inconsistency
- Verdict/threshold mismatch: success_threshold_met=False but outcome_verdict="confirmed" → warn about inconsistency
- No deviation documented: outcome_verdict is "inconclusive" but deviation_from_plan is empty → warn that deviations should be documented when results are inconclusive
- Short interpretation: interpretation < 50 chars → warn that interpretation may be underspecified

## Honest Use Boundary

A hypothesis outcome record is scientific evidence of what happened. A
"refuted" verdict is not a failure — it is information. Do not suppress,
reframe, or omit refuted outcomes. The value of pre-registration comes
entirely from honest reporting of all outcomes including inconvenient ones.
Selectively reporting confirmed outcomes while omitting refuted ones
defeats the entire purpose and should be treated as a protocol violation.
