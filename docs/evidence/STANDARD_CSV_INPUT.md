# CSV Input Documentation Standard

CSV input files must document:

## Required Columns
- `candidate_id` — unique identifier for each candidate
- `sequence` — amino acid sequence (standard single-letter codes)
- `source` — origin of the candidate (generated, imported, seed-derived)

## Optional Columns
- `batch` — batch name or ID
- `family` — scaffold family name
- Any score columns that were used for selection

## Header
CSV files must have a header row with column names. Column names should use snake_case.

## Encoding
UTF-8 with BOM is accepted. ASCII is preferred.
