# Backward Compatibility Report

Tracks backward compatibility of pipeline outputs.

| Artifact | Current Version | Breaking Changes Planned | Migration Path |
|----------|:---------------:|:------------------------:|:---------------|
| Evidence certificates | 1.0 | None | — |
| Lab results | 1.0 | None | — |
| Run manifests | 1.0 | None | — |
| Batch reports | 1.0 | None | — |
| Panel CSVs | 1.0 | None | — |

## Rules
- Breaking changes must be documented in the decision log.
- A breaking change is any change that would cause downstream code to fail.
- Adding optional fields is NOT a breaking change.
- Removing or renaming fields IS a breaking change.
- Changing field types IS a breaking change.
