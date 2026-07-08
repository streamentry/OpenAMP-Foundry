# Example Artifact Naming Convention

Standard naming for example artifacts.

## Patterns
| Type | Pattern | Example |
|------|---------|---------|
| Demo candidates | `demo_{description}.csv` | `demo_candidates.csv` |
| Demo references | `demo_{description}.csv` | `demo_known_amps.csv` |
| Demo output | `demo_{description}.jsonl` | `demo_ranked.jsonl` |
| Lab results | `{candidate_id}_{assay_type}.json` | `SEED-001_VAR_064_MIC.json` |
| Evidence certs | `{candidate_id}.json` | `AMPF-000001.json` |
| Benchmarks | `{description}_benchmark.json` | `validate_scoring_500.json` |

## Rules
- Use snake_case for file names.
- Use lowercase for all file names.
- Group related files in subdirectories.
- Avoid spaces and special characters.
