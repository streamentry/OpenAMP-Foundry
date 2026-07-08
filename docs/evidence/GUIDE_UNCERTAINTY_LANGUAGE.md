# Uncertainty Language Guide

How to communicate uncertainty in documentation.

## Strength of Language
| Certainty | Language | When to Use |
|-----------|----------|-------------|
| High | "The pipeline scores candidates based on..." | Documented, verifiable behavior |
| Medium | "Candidates with high ensemble scores tend to be..." | Benchmark-supported pattern |
| Low | "This suggests that..." | Single experiment or weak signal |
| Speculative | "It is possible that..." | No evidence yet |

## Rules
- Match the language to the evidence level.
- Avoid false precision ("the candidate is 87.3% likely to be antimicrobial").
- State uncertainty alongside every prediction.
- When uncertain, say "we don't know" — it's better than false confidence.
