# Exclusion Reason Taxonomy for Selection Workflows

Standard exclusion reasons for candidate selection.

| Reason | Description | Gate |
|--------|-------------|:----:|
| invalid_sequence | Non-canonical amino acids | validity |
| too_short | Below minimum length | validity |
| too_long | Above maximum length | validity |
| low_novelty | Near-duplicate of known AMP | novelty |
| safety_risk | Above safety threshold | safety |
| synthesis_risk | Above synthesis difficulty | synthesis |
| low_activity | Below activity threshold | activity |
| low_diversity | Too similar to selected candidate | diversity |
| budget_limit | Not enough budget for all candidates | selection |

## Rules
- Every excluded candidate must have an exclusion reason.
- Exclusion reasons are recorded in the selection audit report.
- Multiple exclusion reasons can apply to a single candidate.
- If no reason applies, use `other` and document the reason.
