# Structured Logging Reading Guide

How to interpret structured log output.

## Log Format
```
timestamp  LEVEL  module:line  message  key=value key=value
```

## Levels
| Level | Meaning | Action |
|-------|---------|--------|
| DEBUG | Detailed diagnostic info | Only needed for debugging |
| INFO | Normal operation | Monitor progress |
| WARNING | Unexpected but not an error | Investigate if persistent |
| ERROR | Operation failed | Investigate and fix |
| CRITICAL | System cannot continue | Immediate attention |

## Structured Fields
- `command` — which CLI command was running
- `candidate_id` — which candidate was being processed
- `duration_ms` — how long the operation took
- `exit_code` — exit code of the operation
