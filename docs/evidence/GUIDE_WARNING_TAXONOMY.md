# Warning Taxonomy Guide

Types of warnings produced by the pipeline.

| Type | Meaning | Example |
|------|---------|---------|
| stale_config | Deprecated config key | "key 'foo' is deprecated" |
| missing_field | Optional field missing | "field 'bar' not found" |
| low_confidence | High uncertainty | "uncertainty > 0.5" |
| regression | Metric declined | "AUROC dropped 0.02" |
| overclaim | Risky wording | "found 'proven'" |

## Rules
- Warnings are logged to stderr, not stdout.
- Warnings should include actionable information.
- Warnings must not change pipeline behavior.
