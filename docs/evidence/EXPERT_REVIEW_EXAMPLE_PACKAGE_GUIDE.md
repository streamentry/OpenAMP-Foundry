# ExpertReviewExamplePackage (ERP-) Guide

## Purpose

`ExpertReviewExamplePackage` is a self-contained example of a complete expert-review
submission, using only toy/mock candidates. It exists so external reviewers and
partners know exactly what to expect before receiving real data.

**This schema is for examples only.** Real review submissions use
`ReviewerQuestionnaire` (RVQ-) and `DomainReviewOutcome` (DRO-) schemas.

## Schema Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `erp_id` | str | yes | Unique identifier, must start with `ERP-` |
| `pipeline_version` | str | yes | Pipeline version this example targets |
| `example_version` | str | yes | Version of this example (e.g. `v1.0`) |
| `creation_date` | str | yes | ISO date (YYYY-MM-DD) |
| `review_domain` | str | yes | Domain focus (controlled vocabulary) |
| `mock_candidates` | list | yes | 1-10 toy candidate summaries |
| `overall_clarity_rating` | int | yes | Likert 1-5 overall package clarity |
| `synthesis_recommendation` | str | yes | Example recommendation (controlled vocabulary) |
| `reviewer_comments` | str | yes | Example reviewer comments (≤500 chars) |
| `dry_lab_only` | bool | yes | Must be True |
| `is_example_data` | bool | yes | Must be True |
| `example_use_case` | str | yes | What this example demonstrates |
| `summary` | str | yes | Summary of the example (≤400 chars) |
| `notes` | str | no | Additional context (≤300 chars) |

## Mock Candidate Fields

Each entry in `mock_candidates` must have:
- `candidate_id`: must start with `MOCK-`, `TOY-`, `EXAMPLE-`, `DEMO-`, or `TEST-`
- `sequence_length`: positive integer
- `predicted_mic`: positive float (µg/mL)
- `predicted_toxicity`: `low`, `moderate`, or `high`
- `novelty_score`: float in [0.0, 1.0]
- `include_in_example`: bool (at least one must be True)

## Controlled Vocabularies

**review_domain (6 values):**
`antimicrobial_activity`, `toxicity_safety`, `novelty_assessment`,
`simulation_quality`, `evidence_completeness`, `experimental_design`

**synthesis_recommendation (4 values):**
`proceed`, `proceed_with_conditions`, `defer`, `reject`

## Validation Rules

1. `erp_id` starts with `ERP-`
2. `pipeline_version` non-empty
3. `example_version` non-empty
4. `creation_date` is ISO date (YYYY-MM-DD)
5. `review_domain` in controlled vocabulary (6 values)
6. `mock_candidates` has 1-10 entries
7. Each candidate: ID prefix, sequence_length ≥1, mic >0, toxicity vocab, novelty [0,1]
8. At least one candidate has `include_in_example=True`
9. `overall_clarity_rating` in {1,2,3,4,5}
10. `synthesis_recommendation` in controlled vocabulary (4 values)
11. `reviewer_comments` non-empty and ≤500 chars
12. `dry_lab_only` must be True
13. `is_example_data` must be True
14. `example_use_case` non-empty
15. `summary` non-empty and ≤400 chars
16. `notes` ≤300 chars

## Warnings

- `overall_clarity_rating ≤ 2`: verify the example package is complete
- Excluded candidates: verify `include_in_example=False` is intentional
- `notes` empty: consider documenting example context

## Integration

- Real review submissions: use `ReviewerQuestionnaire` (RVQ-)
- Expert verdicts: use `DomainReviewOutcome` (DRO-)
- This schema: onboarding, CI validation, partner documentation
