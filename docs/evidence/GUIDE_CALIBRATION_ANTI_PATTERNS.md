# Calibration Anti-Patterns

Common mistakes in calibration workflow.

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| Calibrating on synthetic data | No signal from real biology | Only calibrate with real lab results |
| Post-hoc threshold changes | Changes success definition | Lock thresholds before results arrive |
| Ignoring the gate | Skips safety checks | Gate is not bypassable by design |
| Over-fitting to small data | 1-2 results don't justify weight changes | Minimum cohort size enforced |
| Calibrating without human review | Automates decision-making | Human review always required |

## Related
- `configs/recalibration_policy.yaml` — the gate policy
- `docs/evidence/CALIBRATION_POLICY.md` — full policy
