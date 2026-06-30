# Benchmarking Plan

## Why benchmark hygiene matters

AMP prediction is vulnerable to fake progress. Models can learn dataset artifacts instead of antimicrobial function.

Common artifacts:

- positives from curated AMP databases;
- negatives from unrelated random proteins;
- sequence length differences;
- charge differences;
- duplicate or near-duplicate leakage;
- test peptides too similar to training peptides.

## Required benchmarks

| Benchmark | Purpose |
|---|---|
| Random baseline | Prove the pipeline is not noise |
| Simple physicochemical baseline | Prove models beat charge/hydrophobicity alone |
| Cluster split | Prevent near-duplicate leakage |
| Cluster-aware CI | Honest bootstrap when positives contain near-duplicate families |
| Time split | Test future generalization where metadata allows |
| Hidden-positive recovery | Check whether known actives are ranked high |
| Toxicity down-ranking | Ensure predicted risky candidates are penalized |
| Novelty stress test | Avoid near-clones of references |
| Within-AMP selectivity | Test whether scorers distinguish hemolytic from selective AMPs |

## Minimum report fields

Every benchmark report should include:

- dataset source;
- dataset license;
- number of positives;
- number of negatives;
- deduplication method;
- split method;
- similarity threshold;
- baseline performance;
- model performance;
- confidence intervals where possible;
- known limitations.

## Anti-cheating rule

Do not update feature weights, filters, or thresholds after inspecting held-out performance unless you create a new held-out set.
