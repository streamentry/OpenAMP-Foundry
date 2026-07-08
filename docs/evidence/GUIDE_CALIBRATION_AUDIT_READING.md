# Calibration Audit Reading Guide

How to read a calibration audit report.

## Key Sections
| Section | What to Look For |
|---------|------------------|
| Intake report | How many results matched? Any orphans? |
| Gate verdict | Did the gate pass? If not, why? |
| Weight proposal | What weights would change? By how much? |
| Before/after comparison | Would the change improve or degrade benchmarks? |

## Red Flags
- Gate rejected (exit code 3) — recalibration is not allowed
- Weight change > 10% — may indicate a fundamental model issue
- No calibration data — synthetic data only, no real results
- Proposal applied without human review — safety violation

## Related
- `configs/recalibration_policy.yaml` — the gate policy
- `docs/evidence/CALIBRATION_POLICY.md` — full policy documentation
