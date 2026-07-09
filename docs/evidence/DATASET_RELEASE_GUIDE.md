# Dataset Release Package Guide

A *dataset release package* record validates that an open dataset release meets all
data governance requirements before publication. This guide defines what a release
package must contain, how it is validated, and the honesty constraints that apply.

## Purpose

Before releasing a dataset (sequences, scores, negative results, benchmark data)
to the public, the release package ensures that:
- a data license has been chosen,
- a data usage policy has been documented,
- provenance of all included data is declared,
- dual-use risks have been assessed,
- the release has been approved by a reviewer.

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `release_id` | str | Must start with `"DSR-"` |
| `dataset_name` | str | Non-empty |
| `dataset_version` | str | Non-empty |
| `release_date` | str | ISO 8601 `YYYY-MM-DD` |
| `license_identifier` | str | One of `VALID_LICENSE_IDENTIFIERS` |
| `data_sources` | list[str] | ≥ `MINIMUM_DATA_SOURCES` (1) entry |
| `contains_sequences` | bool | Required field |
| `contains_activity_data` | bool | Required field |
| `dual_use_assessed` | bool | Must be `True` |
| `usage_policy_url` | str | Non-empty |
| `contact_email` | str | Non-empty |
| `release_approved` | bool | Must be `True` |
| `dry_lab_only` | bool | Must be `True` |

## Valid license identifiers

`Apache-2.0`, `CC-BY-4.0`, `CC-BY-NC-4.0`, `MIT`, `CC0-1.0`

## Warnings

- `license_identifier == "CC-BY-NC-4.0"` — warning: non-commercial license may restrict some research uses.
- `contains_activity_data` is True and `dual_use_assessed` would be False — blocked at validation (error).
- `data_sources` has only 1 entry — warning: single data source; consider whether additional provenance is needed.

## How to validate

```bash
make dataset-release-check
# or
openamp-foundry dataset-release-check \
  --entry-json '{"release_id":"DSR-001","dataset_name":"OpenAMP Wave 0.5 Candidates","dataset_version":"1.0.0","release_date":"2026-07-09","license_identifier":"CC-BY-4.0","data_sources":["UniProt AMP database","APD3","in-house pipeline"],"contains_sequences":true,"contains_activity_data":false,"dual_use_assessed":true,"usage_policy_url":"https://openamp.example.org/data-policy","contact_email":"data@openamp.example.org","release_approved":true,"dry_lab_only":true}' \
  --format text
```

## Honest-use boundary

Dataset release packages describe computational outputs only. Released datasets must
not claim experimental validation unless wet-lab confirmation has been independently
performed and documented. `dry_lab_only` must be `True`.
