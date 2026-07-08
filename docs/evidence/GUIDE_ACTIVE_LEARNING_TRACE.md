# Active-Learning Decision Trace Artifact

Records the decision process for active-learning candidate selection.

## Fields
| Field | Description |
|-------|-------------|
| round | Active-learning round number |
| candidates_considered | How many candidates were evaluated |
| acquisition_function | What strategy was used (uncertainty, diversity, etc.) |
| selected_candidates | Which candidates were selected |
| selection_scores | Scores used for selection |
| batch_constraints | Batch size, budget, diversity requirements |

## Example
```json
{
  "round": 2,
  "candidates_considered": 50,
  "acquisition_function": "uncertainty_sampling",
  "selected_candidates": ["C001", "C002", "C003"],
  "selection_scores": {"disagreement": 0.45, "ensemble": 0.72},
  "batch_constraints": {"max_batch_size": 12, "min_diversity": 0.75}
}
```

## Rules
- Each active-learning round should produce a decision trace.
- The trace should include enough information to reproduce the selection.
- Selection criteria should be documented in the trace.
