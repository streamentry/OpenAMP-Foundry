# Reviewer Briefing Package Guide

## Purpose

A reviewer briefing package collects all references an external auditor needs
before starting a review. It ensures auditors are not missing critical context,
prevents wasted review cycles, and creates a documented handoff between the
pipeline and external reviewers.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| briefing_id | str | Unique identifier (prefix "RBP-") |
| batch_id | str | Batch under review |
| pipeline_version | str | Pipeline version string |
| prepared_date | str | ISO 8601 date the briefing was prepared |
| reviewer_name | str | Name or identifier of assigned reviewer |
| candidate_count | int | Number of candidates in this batch |
| artifact_ids | list[str] | IDs of all artifacts included (at least 3) |
| open_questions | list[str] | Questions the reviewer should address (may be empty) |
| scope_description | str | What the reviewer is asked to evaluate (max 500 chars) |
| conflict_of_interest_declared | bool | Reviewer has declared any CoI |
| dry_lab_only | bool | Always True (computational pipeline only) |

## Validation Rules

1. briefing_id must start with "RBP-"
2. reviewer_name must not be empty
3. candidate_count must be at least 1
4. artifact_ids must contain at least 3 artifact IDs
5. scope_description must not be empty and must not exceed 500 characters
6. conflict_of_interest_declared must be True
7. dry_lab_only must be True

## Warning Conditions

- Large batch: candidate_count > 50 → warn about review burden
- Many open questions: len(open_questions) > 5 → warn that briefing is underfocused
- Long scope: scope_description > 300 chars → warn to tighten scope
- Minimal artifacts: exactly 3 artifact_ids → warn to consider adding more

## Honest Use Boundary

A reviewer briefing package is a dry-lab artifact. It organises computational
evidence for human review. The outcome of the review is a human judgment call,
not a pipeline output. Do not conflate a completed briefing with a positive
review outcome.
