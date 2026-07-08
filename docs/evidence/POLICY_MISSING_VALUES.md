# Per-Feature Missing-Value Policy

How missing feature values are handled.

## Default Values
| Feature | Default When Missing | Reason |
|---------|:-------------------:|--------|
| charge_density | 0.0 | Neutral charge assumption |
| hydrophobic_moment | 0.0 | No amphipathicity |
| helix_propensity | 1.0 | Indifferent helix propensity |
| boman_index | 0.0 | No binding potential |

## Rules
- Features should not be missing under normal pipeline operation.
- If a feature is missing, log a warning with the feature name.
- Use the default value that makes the least assumption.
- Missing features should be investigated and fixed at the source.
- The pipeline should not crash on missing features.
