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

| Benchmark | Purpose | Status |
|---|---|---|
| Random baseline | Prove the pipeline is not noise | Implemented |
| Simple physicochemical baseline | Prove models beat charge/hydrophobicity alone | Implemented |
| Cluster split | Prevent near-duplicate leakage | Implemented (`bench cluster-split`) |
| Cluster-aware CI | Honest bootstrap when positives contain near-duplicate families | Implemented (cluster-aware bootstrap in `bench cluster-split`) |
| Time split | Test future generalization where metadata allows | Deferred (metadata not available) |
| Hidden-positive recovery | Check whether known actives are ranked high | Implemented |
| Toxicity down-ranking | Ensure predicted risky candidates are penalized | Implemented |
| Novelty stress test | Avoid near-clones of references | Implemented |
| Within-AMP selectivity | Test whether scorers distinguish hemolytic from selective AMPs | Implemented (`bench selectivity`) |
| Expert ablation | Test whether expert composite adds value over ensemble | Implemented (`bench expert-ablation`) |
| Multi-class triage | Test selective > hemolytic > decoy ranking in one panel | Implemented (`bench triage`) |

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
