# Feature Range Sanity Checks

Sanity checks for feature values in the pipeline.

| Feature | Min | Max | Unit | Notes |
|---------|:---:|:---:|:----:|-------|
| length | 8 | 35 | AA | Filter range |
| charge_density | -1.0 | 2.0 | e/AA | Physically possible range |
| hydrophobic_fraction | 0.0 | 1.0 | ratio | Fraction of hydrophobic AAs |
| aromatic_fraction | 0.0 | 0.5 | ratio | Fraction of F, W, Y |
| helix_propensity | 0.5 | 1.5 | Pα | Chou-Fasman scale |

## Rules
- Features outside these ranges should be flagged as warnings.
- The pipeline should not crash on out-of-range features.
- Out-of-range features should be investigated.
- If a feature is consistently out of range, check the source data.
