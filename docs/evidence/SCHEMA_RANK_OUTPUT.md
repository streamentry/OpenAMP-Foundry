# Rank Output Schema for JSONL Records

Schema for ranked candidate JSONL output.

## Record Structure
```json
{
  "candidate_id": "AMPF-000001",
  "sequence": "RRWQWRMKKLG",
  "source": "demo",
  "valid": true,
  "selected": true,
  "scores": {
    "activity": 0.8387,
    "safety": 0.9638,
    "ensemble": 0.8889,
    "charge_bias": 0.2345
  },
  "features": {
    "length": 11,
    "charge_density": 0.4545,
    "hydrophobic_fraction": 0.3636
  },
  "selection_reason": ["High transparent activity-likeness score"]
}
```

## Rules
- Every record must have `candidate_id`, `sequence`, `scores`.
- `scores` must include at least `ensemble`.
- `selected` is a boolean indicating if the candidate passed all gates.
- `selection_reason` explains why a candidate was selected or rejected.
