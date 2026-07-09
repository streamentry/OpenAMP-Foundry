# Audit Chain Completeness Guide

## Purpose

The audit chain completeness checker validates that an evidence package for a
batch contains all required chain links — from raw sequence input through
pipeline scoring, filtering, candidate selection, and submission readiness.
A gap anywhere in the chain blocks external reproducibility.

## Schema Fields

| Field | Type | Description |
|---|---|---|
| chain_id | str | Unique identifier (prefix "ACH-") |
| batch_id | str | Batch under audit |
| pipeline_version | str | Pipeline version string |
| audit_date | str | ISO 8601 date of this audit |
| has_sequence_input | bool | Raw sequences are documented |
| has_benchmark_results | bool | Benchmark comparison results exist |
| has_filter_log | bool | Candidate filter decisions are logged |
| has_score_decomposition | bool | Score decomposition reports exist |
| has_selection_rationale | bool | Selection rationale documents exist |
| has_evidence_certificate | bool | Evidence certificates are present |
| has_claim_mappings | bool | Claim-to-evidence mappings exist |
| has_pipeline_decision_audit | bool | Pipeline decision audit entries exist |
| has_reviewer_briefing | bool | Reviewer briefing package exists |
| missing_links | list[str] | Auto-populated: names of chain links that are False |
| auditor | str | Person or system performing this audit |
| dry_lab_only | bool | Always True |

## Chain Links (all required)

1. `has_sequence_input` — without this, the pipeline has no traceable starting point
2. `has_benchmark_results` — performance claims need benchmark backing
3. `has_filter_log` — what was excluded must be recorded alongside what was included
4. `has_score_decomposition` — composite scores must be decomposable
5. `has_selection_rationale` — why *these* candidates and not others
6. `has_evidence_certificate` — certificate of computational evidence
7. `has_claim_mappings` — every claim traces to an artifact
8. `has_pipeline_decision_audit` — filter/threshold decisions are traceable
9. `has_reviewer_briefing` — external auditor has a complete briefing

## Validation Rules

1. chain_id must start with "ACH-"
2. auditor must not be empty
3. dry_lab_only must be True
4. All 9 chain links must be True (any False is an error)
5. missing_links must match the set of chain links that are False

## Warning Conditions

- Single auditor: auditor contains no "@" character → warn that a named human auditor is recommended
- Future audit date: audit_date appears to be after the current year (year > 2030) → warn about implausible date

## Honest Use Boundary

Audit chain completeness is a meta-check: it verifies that all *other* evidence
artifacts exist, not that they are scientifically correct. A passing audit chain
means the evidence package is structurally complete, not that every artifact
contains accurate science. Human expert review is still required.
