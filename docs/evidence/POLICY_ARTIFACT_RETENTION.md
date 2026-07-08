# Artifact Retention Policy

How long different artifact types are retained.

| Artifact Type | Retention | Location | Cleanup |
|:-------------|:---------:|:---------|:--------|
| Evidence certificates | Permanent | outputs/evidence/ | Manual |
| Run manifests | 2 years | outputs/ | Automated |
| Benchmark results | Permanent | outputs/ | Manual |
| Lab results | Permanent | outputs/lab_results/ | Manual |
| Temporary outputs | 90 days | outputs/ | Automated |
| Logs | 30 days | outputs/logs/ | Automated |

## Rules
- Permanent artifacts must never be deleted without a decision log entry.
- Temporary outputs can be cleaned up with `make clean`.
- Lab results must be preserved for the duration of the study.
- Retention periods start from the date of creation.
