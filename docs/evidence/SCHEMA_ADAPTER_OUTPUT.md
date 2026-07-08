# Adapter Output Schema

Standard output schema for external adapters.

## SimulationResult Fields
| Field | Type | Description |
|-------|------|-------------|
| module | string | Adapter name |
| version | string | Adapter version |
| scope | list | What was modeled |
| scores | dict | Score key-value pairs |
| uncertainty | float | 0-1 scale, higher = less certain |
| calibration_set | string or null | Reference to calibration data |
| validated_against | list | Validation datasets |
| notes | list | Human-readable notes |

## Rules
- All adapters must return a SimulationResult.
- uncertainty=1.0 means completely uncertain (do not use).
- calibration_set=null means no calibration data exists.
- notes should include warnings, limitations, and context.
