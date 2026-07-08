# Stratification Coverage Report

Reports how well benchmark stratification covers different AMP classes.

## Current Coverage
| Class | Count in 500-AMP | Per-family AUROC | Coverage |
|-------|:----------------:|:----------------:|:--------:|
| highly_cationic | 73 | 0.958 | ✅ Good |
| moderately_cationic | 115 | 0.894 | ✅ Good |
| cysteine_rich | 153 | 0.723 | ✅ Adequate |
| low_charge | 118 | 0.693 | ✅ Adequate |
| short | 21 | 0.610 | ⚠️ Low count |
| proline_rich | 20 | 0.586 | ⚠️ Low count |

## Recommendations
- Classes with < 30 sequences should be expanded.
- Proline-rich and short AMPs need more representatives.
- Consider adding synthetic variants for underrepresented classes.
- Stratification should be reviewed when new data is added.
