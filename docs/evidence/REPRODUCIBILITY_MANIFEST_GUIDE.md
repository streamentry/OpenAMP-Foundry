# Reproducibility Manifest Guide

A *reproducibility manifest* captures the exact software versions, data checksums,
and random seeds used in a pipeline run, enabling any third party to independently
reproduce the results.

## Purpose

External researchers who receive a preprint evidence bundle need to be able to:
- verify that the reported results can be reproduced from the stated inputs,
- detect if intermediate data was silently modified,
- reproduce the exact stochastic sampling used in ensemble methods.

A reproducibility manifest gives them the information to do this.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `manifest_id` | str | Must start with `"RPM-"` |
| `batch_id` | str | Non-empty |
| `pipeline_version` | str | Non-empty |
| `run_date` | str | ISO 8601 `YYYY-MM-DD` |
| `python_version` | str | Non-empty (e.g. `"3.11.9"`) |
| `package_checksums` | dict[str, str] | At least `MINIMUM_PACKAGES` (3) entries |
| `data_checksums` | dict[str, str] | At least `MINIMUM_DATA_FILES` (1) entry |
| `random_seeds` | dict[str, int] | May be empty; keys are step names |
| `hardware_summary` | str | Non-empty (e.g. `"Apple M3 Pro, 36 GB RAM"`) |
| `reviewer` | str | Non-empty |
| `dry_lab_only` | bool | Must be `True` |

## Package checksums

`package_checksums` maps package name to version string or SHA-256 hash.
Example: `{"openamp_foundry": "0.8.4", "numpy": "1.26.4"}`.

## Data checksums

`data_checksums` maps data file path (relative to repo root) to SHA-256 hex digest.
Example: `{"data/amp_sequences.fasta": "abc123..."}`.

## Warnings

- `random_seeds` is empty — warning: no random seeds recorded; stochastic steps cannot be reproduced exactly.
- `len(package_checksums) < 5` — warning: fewer than 5 packages recorded; consider adding key dependencies.
- hardware_summary contains "unknown" — warning: hardware not identified; reproducibility may vary across platforms.

## How to validate

```bash
make reproducibility-manifest-check
# or
openamp-foundry reproducibility-manifest-check \
  --entry-json '{"manifest_id":"RPM-001","batch_id":"BATCH-001","pipeline_version":"0.8.5","run_date":"2026-07-09","python_version":"3.11.9","package_checksums":{"openamp_foundry":"0.8.4","numpy":"1.26.4","pandas":"2.2.2"},"data_checksums":{"data/amp_sequences.fasta":"abc123def456"},"random_seeds":{"ensemble_sampling":42},"hardware_summary":"Apple M3 Pro, 36 GB RAM","reviewer":"alice","dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Reproducibility manifests describe the computational environment, not the experimental
conditions. They enable computational reproducibility only; wet-lab reproduction requires
independent experimental protocols.
