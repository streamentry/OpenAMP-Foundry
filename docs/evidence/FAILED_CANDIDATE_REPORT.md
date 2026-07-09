# Failed Candidate Report

## Purpose

Generate structured, reviewable reports from batches of rejected candidates.
Each report uses the rejection taxonomy codes (`schemas/rejection_taxonomy.schema.json`)
to provide consistent categorization, severity assessment, and evidence-impact
tracking across all pipeline failures.

## Source

- **Generator:** `scripts/generate_failed_candidate_report.py`
- **Input format:** JSON file with `candidates` array, each containing rejection codes from the taxonomy
- **Output formats:** JSON (machine-readable) + Markdown (human-readable)

## Usage

Generate a report from an example input:

```bash
python scripts/generate_failed_candidate_report.py \
    --input examples/failed_candidates_example.json \
    --out-json outputs/failed_candidate_report.json \
    --out-md outputs/failed_candidate_report.md \
    --validate-rejection-codes
```

Or using the Makefile target:

```bash
make failed-candidate-report
```

## Input Format

The input file is a JSON object with:

| Field | Required | Description |
|-------|----------|-------------|
| `source_batch` | Yes | Batch identifier (e.g. `wave0.5`) |
| `pipeline_version` | Yes | Pipeline version string |
| `date` | Yes | Report date (ISO 8601) |
| `candidates` | Yes | Array of candidate objects |

Each candidate object:

| Field | Required | Description |
|-------|----------|-------------|
| `candidate_id` | Yes | Unique identifier |
| `sequence` | No | Amino-acid sequence (recommended) |
| `rejections` | Yes | Array of rejection objects |

Each rejection object:

| Field | Required | Description |
|-------|----------|-------------|
| `code` | Yes | Rejection taxonomy code (e.g. `PIPE_ACTIVITY_LOW`) |
| `detail` | No | Human-readable explanation with relevant scores/thresholds |

## Output Formats

### JSON report

The JSON report includes:

- **report_metadata**: generation timestamp, source batch, pipeline version, taxonomy source
- **summary**: totals, unique codes, by-category aggregation, by-severity aggregation,
  by-stage aggregation, rejection-code frequency table, unknown codes if validation was skipped
- **candidates**: per-candidate breakdown with rejection details and taxonomy metadata
- **caveats**: standard disclaimer array
- **dry_lab_only**: always `true`

### Markdown summary

The Markdown summary includes:

1. Report metadata table
2. Summary metrics table
3. By-category table
4. By-severity table
5. By-evidence-impact table
6. Rejection-code frequency table
7. Per-candidate breakdown with detailed tables
8. Standard caveats

## Validation

The `--validate-rejection-codes` flag checks every rejection code in the input
against the taxonomy. Unknown codes produce a non-zero exit code and error
messages on stderr. This is recommended for automated pipelines.

## Caveats

- Rejection codes reflect pipeline or reviewer decisions, not biological inactivity unless confirmed by lab assay.
- Soft rejections may be overcome by threshold or policy changes.
- Hard rejections require new evidence to overturn.
- This report is informational only and requires qualified review.
- Computational outputs are hypotheses and review aids — they are not biological proof.

## Cross-references

- `schemas/rejection_taxonomy.schema.json` — Taxonomy defining all valid rejection codes
- `examples/rejection_taxonomy_example.json` — Complete taxonomy with 21 entries
- `docs/evidence/REJECTION_TAXONOMY.md` — Taxonomy reference documentation
- `schemas/negative_result_entry.schema.json` — Negative-result archive entry schema
- `docs/evidence/NEGATIVE_RESULT_ARCHIVE.md` — Archive format for persistent records
