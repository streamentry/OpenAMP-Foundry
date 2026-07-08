# Leakage Concept Guide

Leakage occurs when information from outside the training set influences the model.

## Types of Leakage
| Type | Description | Example |
|------|-------------|---------|
| Near-duplicate leakage | Test sequence is similar to a training sequence | Cluster split prevents this |
| Composition leakage | Test and train share composition features | Hard to avoid; tracked by charge-matched benchmark |
| Temporal leakage | Future data influences past predictions | Time splits where metadata permits |
| Feature leakage | Features indirectly encode the target | Avoided by using transparent heuristics |

## Detection
- Cluster split benchmarks detect near-duplicate leakage.
- Charge-matched benchmarks detect composition leakage.
- Cross-dataset benchmarks detect overfitting to database artifacts.

## Related
- `docs/evidence/LEAKAGE_AUDIT_CHECKLIST.md`
