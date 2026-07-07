# Manifest — Concept Card

A manifest records what inputs, configs, and outputs a pipeline run used.

## Required Fields

| Field | Description |
|-------|-------------|
| `run_id` | UUID for the run |
| `pipeline_version` | Version string |
| `config_hash` | SHA-256 of config |
| `generated_at` | ISO 8601 timestamp |
| `inputs` | List of input file paths |
| `input_hashes` | SHA-256 per input file |
| `outputs` | List of output paths |

## Purpose

Manifests enable reproducibility audits. A reviewer can verify that the same
inputs and config produce the same outputs.

## Related

- `schemas/run_manifest.schema.json` — manifest schema
- `docs/engineering/RUN_MANIFEST_STANDARD.md` — full spec
