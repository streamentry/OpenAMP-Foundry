# Documentation Decision Record Policy

Significant documentation decisions should be recorded for future reference.

## What Requires a Decision Record

- Adding or removing a policy document
- Restructuring the documentation directory
- Changing the documentation license
- Adopting or changing a documentation standard
- Retiring a document

## Format

Use `schemas/decision_log.schema.json` for machine-readable records.

## Required Fields

- `date` — ISO 8601 date
- `decision_type` — one of the schema's allowed types
- `decision` — approved, rejected, or deferred
- `evidence_refs` — links to relevant PRs or discussions
- `reasoning_notes` — rationale for the decision
