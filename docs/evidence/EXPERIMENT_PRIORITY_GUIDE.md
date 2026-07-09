# Experiment Priority Justification Guide

## Purpose

The experiment priority justification records why a specific batch of candidates
was selected for the next experimental wave over alternatives. This prevents
the most common form of selection bias in pipeline-driven research: choosing
experiments based on convenience, intuition, or results-seeking rather than
pre-specified scientific reasoning.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| justification_id | str | Unique identifier (prefix "EPJ-") |
| batch_id | str | Batch selected for the next experiment |
| pipeline_version | str | Pipeline version at decision time |
| decision_date | str | ISO 8601 date of this decision |
| selection_criteria | list[str] | Criteria used to prioritize this batch (at least 2) |
| rejected_alternatives | list[str] | Batch or candidate IDs that were considered but not selected (at least 1) |
| rejection_rationale | str | Why alternatives were not chosen (max 500 chars) |
| resource_constraint | str | Resource/capacity constraint driving prioritization (max 200 chars) |
| safety_reviewed | bool | Whether safety criteria were checked before selection |
| pre_specified | bool | Whether selection criteria were pre-specified before seeing candidates |
| decided_by | str | Person or system making this decision |
| dry_lab_only | bool | Always True (computational prioritization) |

## Validation Rules

1. justification_id must start with "EPJ-"
2. selection_criteria must contain at least 2 criteria
3. rejected_alternatives must contain at least 1 alternative
4. rejection_rationale must not be empty and must not exceed 500 characters
5. resource_constraint must not exceed 200 characters (may be empty)
6. safety_reviewed must be True
7. decided_by must not be empty
8. dry_lab_only must be True

## Warning Conditions

- Post-hoc selection: pre_specified=False → warn that selection criteria were not pre-specified
- Few criteria: len(selection_criteria) == 2 → warn that only minimum criteria used; more criteria strengthens defensibility
- No resource constraint documented: resource_constraint is empty → warn that documenting constraints improves transparency
- Many criteria: len(selection_criteria) > 6 → warn that many criteria may introduce over-fitting to batch characteristics

## Honest Use Boundary

An experiment priority justification is a dry-lab decision record. It documents
the computational reasoning for prioritization. The ultimate decision to run
experiments must involve qualified scientists. Safety_reviewed=True means the
pipeline's safety checks were run — it does not mean a domain expert has
signed off on the biological safety of the candidates.
