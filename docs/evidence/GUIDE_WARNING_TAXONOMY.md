# Warning Taxonomy Guide

Types of warnings and how to handle them.

| Warning Type | Meaning | Example | Action |
|-------------|---------|---------|--------|
| `stale_config` | Config option is deprecated | `deprecated key 'foo'` | Update config |
| `missing_field` | Optional field is absent | `field 'bar' not found` | Check source |
| `low_confidence` | Score uncertainty is high | `uncertainty > 0.5` | Treat as experimental |
| `regression` | Metric dropped | `AUROC dropped 0.02` | Investigate |
| `overclaim` | Risky wording detected | `found 'proven'` | Rewrite |

## Rules
- Warnings should not change behavior.
- Warnings should include actionable information.
- Warnings should be logged to stderr, not stdout.
