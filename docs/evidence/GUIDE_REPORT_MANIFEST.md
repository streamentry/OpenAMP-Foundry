# Report Manifest Reading Guide

How to read a run manifest.

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

## How to Verify
1. Check that `pipeline_version` matches the expected version.
2. Verify `config_hash` matches the config used.
3. Check that all expected inputs are listed.
4. Verify that all expected outputs exist.
5. If an input hash doesn't match, the input file has changed since the run.
