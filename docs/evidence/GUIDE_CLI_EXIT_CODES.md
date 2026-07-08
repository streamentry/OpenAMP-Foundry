# CLI Exit Code Guide

Exit codes used by OpenAMP Foundry commands.

| Code | Meaning | Example |
|:----:|---------|---------|
| 0 | Success | Command completed successfully |
| 1 | Internal error | Unexpected exception |
| 2 | Input error | Missing file, invalid arguments |
| 3 | Validation failure | Gate check failed, data invalid |

## Consistency Rules
- All CLI commands should follow this exit code convention.
- New scripts should use exit code 2 for input errors, 3 for validation failures.
- Exit code 1 should be reserved for unexpected errors (bugs).
