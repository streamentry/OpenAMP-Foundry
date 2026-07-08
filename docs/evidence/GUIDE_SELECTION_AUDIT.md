# Selection Audit Summary Report

Summary of candidate selection decisions for audit.

## Report Sections
- Total candidates considered
- Candidates passing each gate
- Candidates selected (final)
- Candidates excluded with reasons
- Diversity metrics of selected set

## Example
```json
{
  "total_candidates": 100,
  "passed_validity": 95,
  "passed_novelty": 80,
  "passed_safety": 65,
  "passed_synthesis": 60,
  "selected": 24,
  "excluded": [
    {"candidate_id": "C001", "reason": "low_novelty"},
    {"candidate_id": "C002", "reason": "safety_risk"}
  ]
}
```

## Rules
- The audit report must include exclusion reasons.
- Exclusion reasons should follow the exclusion reason taxonomy.
- The report should be generated when the final panel is selected.
