# Data Source Card Schema

Standard schema for dataset documentation.

## Required Fields
| Field | Type | Description |
|-------|------|-------------|
| name | string | Dataset name |
| source | string | Source URL or reference |
| license | string | SPDX license identifier |
| version | string | Dataset version or date |
| description | string | Description of the data |
| labeled | boolean | Whether labels are available |

## Optional Fields
| Field | Type | Description |
|-------|------|-------------|
| size | integer | Number of records |
| format | string | File format (CSV, FASTA, JSON) |
| limitations | list | Known biases or limitations |
| citation | string | Preferred citation |

## Example
```json
{
  "name": "known_amps_500",
  "source": "UniProt reviewed + APD6 natural",
  "license": "CC BY 4.0",
  "version": "2026-07-01",
  "description": "500 antimicrobial peptide sequences",
  "labeled": true,
  "size": 500,
  "format": "CSV",
  "limitations": ["Enriched for helical AMPs"]
}
```
