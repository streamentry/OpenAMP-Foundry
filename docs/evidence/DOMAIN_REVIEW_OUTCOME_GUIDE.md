# Domain Review Outcome Guide

## Purpose

A `DomainReviewOutcome` (DRO-) records the formal verdict of a domain expert after
reviewing a `PilotEvidencePackage`. It uses a controlled taxonomy of expert domains
and outcome verdicts, making review decisions structured, auditable, and comparable
across multiple reviewers. It links to the preceding `ReviewerQuestionnaire` (RVQ-).

## Chain in Phase E

```
ESC- (external sharing) → RVQ- (reviewer questionnaire) → DRO- (expert verdict)
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dro_id` | str | Yes | Unique ID, must start with `DRO-` |
| `pipeline_version` | str | Yes | Pipeline version being reviewed |
| `pep_id` | str | Yes | Which PEP was reviewed (must start with `PEP-`) |
| `rvq_id` | str | Yes | Preceding questionnaire (must start with `RVQ-`) |
| `reviewer_token` | str | Yes | Anonymized reviewer ID — no PII |
| `review_domain` | str | Yes | Expert domain (controlled vocabulary) |
| `review_date` | str | Yes | ISO YYYY-MM-DD date of verdict |
| `outcome_verdict` | str | Yes | Expert verdict (controlled vocabulary) |
| `outcome_confidence` | str | Yes | `high`, `medium`, or `low` |
| `outcome_rationale` | str | Yes | Rationale (max 400 chars) |
| `dry_lab_only` | bool | No | Default `True` |

## Expert domains

| Domain | When to use |
|--------|-------------|
| `antimicrobial_activity` | Reviewer assessing predicted AMP activity |
| `toxicology` | Reviewer assessing cytotoxicity/hemolysis claims |
| `structural_biology` | Reviewer assessing structural predictions |
| `clinical_microbiology` | Reviewer assessing clinical relevance |
| `computational_chemistry` | Reviewer assessing computational methods |
| `general_biomedical` | General biomedical domain expertise |

## Outcome verdicts

| Verdict | Meaning |
|---------|---------|
| `approve` | Package is sufficient for proceeding |
| `reject` | Package is not sufficient in current form |
| `conditional_approve` | Approve if specific conditions are met (document in rationale) |
| `request_revision` | Package needs specific revisions before re-review |
| `insufficient_data` | Cannot reach a verdict — more data required |

## Validation rules

1. `dro_id` must start with `DRO-`
2. `pep_id` must start with `PEP-`
3. `rvq_id` must start with `RVQ-`
4. `pipeline_version`, `reviewer_token` must not be empty
5. `review_domain` must be in the controlled vocabulary
6. `review_date` must be ISO format `YYYY-MM-DD`
7. `outcome_verdict` must be in the controlled vocabulary
8. `outcome_confidence` must be `high`, `medium`, or `low`
9. `outcome_rationale` at most 400 characters

## Warnings

- `conditional_approve` with no rationale — document the conditions
- `reject` with `low` confidence — may need additional reviewer
- `insufficient_data` with no rationale — document what is missing

## Honest boundaries

- A DRO- record reflects one expert's judgment; it does not authorize synthesis.
- `approve` does not imply biological validation — it is a dry-lab package assessment only.
- `reviewer_token` must never contain PII.

## CLI usage

```bash
openamp-foundry domain-review-outcome-check \
  --entry-json '{"dro_id":"DRO-001","pipeline_version":"v0.10.13","pep_id":"PEP-001","rvq_id":"RVQ-001","reviewer_token":"REV-A","review_domain":"antimicrobial_activity","review_date":"2026-07-10","outcome_verdict":"approve","outcome_confidence":"high","outcome_rationale":"Evidence base is solid."}' \
  --format text
```
