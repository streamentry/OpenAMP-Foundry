# JSONL Artifact Documentation Standard

JSONL (JSON Lines) files used by the pipeline must follow this standard.

## Format
- One JSON object per line
- No separator between objects (newline only)
- UTF-8 encoding
- Each line must be valid JSON

## Required Fields
- `candidate_id`
- `sequence`
- `scores` — dict of score key to value

## Naming
- Use `.jsonl` extension
- File name should describe the content (e.g., `demo_ranked.jsonl`)
