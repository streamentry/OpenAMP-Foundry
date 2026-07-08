# Feature Provenance Records to Scoring Outputs

Tracks which features contributed to which scores.

## Format
Each scored candidate includes feature values used in scoring:
```json
{
  "candidate_id": "AMPF-000001",
  "features": {
    "charge_density_ph74": 0.4545,
    "hydrophobic_fraction": 0.3636,
    "hydrophobic_moment": 0.5741
  },
  "scores": {
    "activity": 0.8387,
    "charge_bias": 0.2345
  }
}
```

## Rules
- Feature values are included in the ranked JSONL output.
- Feature provenance enables debugging and auditing.
- If a feature is derived from other features, document the derivation.
- Feature provenance should be preserved through the scoring pipeline.
