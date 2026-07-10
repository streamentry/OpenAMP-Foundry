# Reviewer Questionnaire Guide

## Purpose

A `ReviewerQuestionnaire` (RVQ-) captures structured feedback from an external reviewer
on a `PilotEvidencePackage` (PEP). It uses Likert-scale ratings for claim clarity, a
synthesis recommendation, and structured comments to make review feedback machine-readable
and comparable across reviewers.

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rvq_id` | str | Yes | Unique ID, must start with `RVQ-` |
| `pipeline_version` | str | Yes | Pipeline version being reviewed |
| `pep_id` | str | Yes | Which PEP is being reviewed (must start with `PEP-`) |
| `reviewer_token` | str | Yes | Anonymized reviewer ID — no PII |
| `review_date` | str | Yes | ISO YYYY-MM-DD date of review |
| `activity_prediction_clarity` | int | Yes | Likert 1-5: how clear is the activity prediction? |
| `safety_claim_clarity` | int | Yes | Likert 1-5: how clear are the safety claims? |
| `novelty_claim_clarity` | int | Yes | Likert 1-5: how clear is the novelty claim? |
| `overall_package_quality` | int | Yes | Likert 1-5: overall quality of the evidence package |
| `would_recommend_for_synthesis` | str | Yes | `yes`, `no`, `conditional`, or `insufficient_information` |
| `missing_information` | List[str] | Yes | Specific gaps identified (empty if none) |
| `reviewer_comments` | str | Yes | Free-text comments (max 600 chars) |
| `dry_lab_only` | bool | No | Default `True` |

## Validation rules

1. `rvq_id` must start with `RVQ-`
2. `pep_id` must start with `PEP-`
3. `pipeline_version`, `reviewer_token` must not be empty
4. `review_date` must be ISO format `YYYY-MM-DD`
5. `activity_prediction_clarity` in [1, 5]
6. `safety_claim_clarity` in [1, 5]
7. `novelty_claim_clarity` in [1, 5]
8. `overall_package_quality` in [1, 5]
9. `would_recommend_for_synthesis` in `{yes, no, conditional, insufficient_information}`
10. `reviewer_comments` at most 600 characters

## Warnings

- `overall_package_quality < 3` — package needs significant improvement
- `conditional` recommendation with no comments — document the conditions
- `no` recommendation with no `missing_information` or comments — document why
- `insufficient_information` with empty `missing_information` — list the specific gaps

## Synthesis recommendations

| Value | Meaning |
|-------|---------|
| `yes` | Package is sufficient for proceeding to wet-lab synthesis |
| `no` | Package is not sufficient in current form |
| `conditional` | Sufficient if specific gaps are addressed (document in comments) |
| `insufficient_information` | Cannot assess — more information required |

## Honest boundaries

- A `yes` recommendation from a single reviewer does not authorize wet-lab synthesis.
- `reviewer_token` must never contain PII (name, email, institutional ID).
- Likert scores reflect the reviewer's perception of the dry-lab package clarity, not biological validity.

## CLI usage

```bash
openamp-foundry reviewer-questionnaire-check \
  --entry-json '{"rvq_id":"RVQ-001","pipeline_version":"v0.10.12","pep_id":"PEP-001","reviewer_token":"REV-A","review_date":"2026-07-10","activity_prediction_clarity":4,"safety_claim_clarity":4,"novelty_claim_clarity":3,"overall_package_quality":4,"would_recommend_for_synthesis":"yes","missing_information":[],"reviewer_comments":"Clear and complete."}' \
  --format text
```
