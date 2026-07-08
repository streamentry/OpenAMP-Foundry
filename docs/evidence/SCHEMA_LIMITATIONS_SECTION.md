# Limitations Section Schema

Standard structure for limitations sections in documentation.

## Required Sections
- What the limitation is
- Why it exists
- What it does NOT affect
- Planned mitigation or status

## Example
```markdown
### Charge-Dominated Scoring
The pipeline's primary discriminative signal is charge density,
not sophisticated multi-feature scoring. The ensemble AUROC of
0.7792 is charge-inflated (collapses to 0.5103 under exact charge
control). This does NOT affect the safety or novelty scoring.
**Mitigation:** `charge_bias` score available per candidate;
charge-matched benchmarks track this gap.
```

## Rules
- Every limitations section should follow this schema.
- Limitations should be specific, not general.
- Include both impact and mitigation.
- Link to related docs where available.
