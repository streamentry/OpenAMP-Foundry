# Architecture

## System overview

```text
CSV/JSONL candidates
  -> loaders
  -> validation
  -> feature extraction
  -> independent scorers
  -> ensemble scorer
  -> novelty checker
  -> diversity selector
  -> evidence certificate
  -> report
```

## Package map

| Package | Role |
|---|---|
| `openamp_foundry.data` | loading and normalizing candidate/reference data |
| `openamp_foundry.features` | physicochemical feature extraction |
| `openamp_foundry.scoring` | activity, safety, novelty, synthesis, ensemble scoring |
| `openamp_foundry.selection` | ranking and diversity selection |
| `openamp_foundry.evidence` | JSON certificate generation and validation |
| `openamp_foundry.benchmark` | leakage checks and evaluation scaffolding |
| `openamp_foundry.generators` | safe, bounded toy candidate generation |

## Threat model

The system is designed to reduce these failures:

| Failure | Mitigation |
|---|---|
| Cherry-picking candidates | Predefined ranking rule and evidence certificate |
| Rediscovering known AMPs | Novelty score and reference matching |
| Unsafe optimization | No toxicity-maximizing objectives; safety penalties by default |
| Model self-confirmation | Separate generator and judges |
| Dataset leakage | Cluster/time split plan and leakage checks |
| Overclaiming | Explicit confidence and failure modes |
| Misuse by unsafe forks | Controlled release policy for high-capability components |

## Data flow

1. Load candidate sequences.
2. Normalize to uppercase canonical amino-acid symbols.
3. Reject invalid sequences.
4. Compute features.
5. Score independently.
6. Rank by weighted ensemble.
7. Select diverse candidates.
8. Write JSONL results.
9. Generate one certificate per selected candidate.
10. Generate a human-readable report.

## Extension points

Later external predictors should be added as adapters. Each adapter must return:

```json
{
  "tool": "predictor-name",
  "version": "x.y.z",
  "score": 0.0,
  "confidence": "low|medium|high",
  "notes": []
}
```

Adapters must not silently download model weights or send sequences to third-party services without explicit user consent.
