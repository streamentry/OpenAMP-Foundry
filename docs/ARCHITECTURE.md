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

This is the **current production architecture**: a deterministic dry-lab candidate foundry.

The repo’s longer-range architecture is a layered system:

```text
candidate generation / import
  -> dry-lab filtering and ranking
  -> higher-fidelity virtual assay proxies
  -> small real assay batch
  -> calibration / active learning
  -> next-round candidate selection
```

The purpose of the added layers is not simulation theater. It is to improve which experiments are chosen next.

## Package map

| Package | Role |
|---|---|
| `openamp_foundry.data` | loading and normalizing candidate/reference data |
| `openamp_foundry.features` | physicochemical feature extraction |
| `openamp_foundry.scoring` | activity, safety, novelty, synthesis, ensemble scoring |
| `openamp_foundry.selection` | ranking and diversity selection |
| `openamp_foundry.evidence` | JSON certificate generation and validation |
| `openamp_foundry.benchmark` | leakage checks, cluster-split benchmark, expert ablation benchmark, within-AMP selectivity benchmark, and evaluation scaffolding |
| `openamp_foundry.generators` | safe, bounded toy candidate generation |
| `openamp_foundry.simulation` | membrane/selectivity/stability proxy modeling (scaffolded) |

Potential future packages, only if benchmarked honestly:

| Future package | Intended role |
|---|---|
| `openamp_foundry.calibration` | learning from assay results and recalibrating scores |
| `openamp_foundry.active_learning` | choosing informative next experiments under uncertainty |

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
| Simulation theater | Require calibration, abstention rules, and baseline comparisons |
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

## Target future data flow

When the project is mature enough, the extended loop should look like:

1. Generate or import candidate sequences.
2. Run the current dry-lab validation, feature extraction, scoring, novelty, and diversity pipeline.
3. Send a smaller frontier set to higher-fidelity selectivity and stability proxy models.
4. Estimate uncertainty and identify where the model is likely wrong.
5. Select a very small assay batch that balances likely winners with high-information probes.
6. Ingest qualified wet-lab outcomes through versioned schemas.
7. Recalibrate decision rules without rewriting success definitions after the fact.
8. Measure whether the added modeling layer actually reduced wasted experiments.

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

Any future simulation or emulator module must implement the `VirtualAssayProxy` interface (in `openamp_foundry.simulation`) and return a `SimulationResult` object matching this schema:

```python
@dataclass
class SimulationResult:
    module: str
    version: str
    scope: list[str]
    scores: dict[str, float]
    uncertainty: float
    calibration_set: str | None
    validated_against: list[str]
    notes: list[str]
```

If calibration data is absent or weak, the `uncertainty` field must surface that directly.
