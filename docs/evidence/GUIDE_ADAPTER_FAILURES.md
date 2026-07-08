# Adapter Failure Interpretation Guide

How to interpret failures from external adapters.

## Common Failure Modes
| Error | Likely Cause | Action |
|-------|-------------|--------|
| Connection refused | External service is down | Retry later, check service status |
| Timeout | Request took too long | Increase timeout or reduce request size |
| Rate limited | Too many requests | Reduce request frequency |
| Invalid response | Service returned unexpected data | Check adapter version compatibility |
| Authentication failed | Credentials are invalid | Update credentials |

## Response Format
All adapters return a `SimulationResult` with:
- `module` — adapter name
- `version` — adapter version
- `scope` — what was modeled
- `scores` — dict of score key to value
- `uncertainty` — 0-1 scale
- `calibration_set` — reference to calibration data
- `notes` — human-readable notes about the result
