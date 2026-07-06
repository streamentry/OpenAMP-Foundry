# Benchmarking Plan

## Source-of-truth relationship

This document lists the current benchmark suite and how to run it.

Benchmark creation, modification, promotion, and deprecation are governed by [`BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md).

Current metric values live in [`METRICS_CURRENT.md`](METRICS_CURRENT.md).

## Why benchmark hygiene matters

AMP prediction is vulnerable to fake progress. Models can learn dataset artifacts instead of antimicrobial function.

Common artifacts:

- positives from curated AMP databases;
- negatives from unrelated random proteins;
- sequence length differences;
- charge differences;
- duplicate or near-duplicate leakage;
- test peptides too similar to training peptides;
- amphipathic-helix bias inflating discrimination on canonical AMPs;
- small-n benchmark confidence intervals masking uncertainty.

## Benchmarks

Each benchmark has or should have a `make` target, a script in `scripts/`, and a documented result in `docs/METRICS_CURRENT.md` and `outputs/metrics_snapshot.json` where applicable.

### Core discrimination

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-baseline` | Random baseline — pipeline is not noise | AUROC > 0.5 | `make bench-baseline` |
| `bench-hidden-active` | Known active AMPs hidden from training appear in top ranks | Better-than-random recovery | `make bench-hidden-active` |
| `validate-scoring` | Standard benchmark (n=191, 95 AMPs + 96 decoys) | AUROC > 0.70 | `make validate-scoring` |
| `bench-500` | Expanded benchmark (500 AMPs + 500 decoys, n=1000) | AUROC > 0.70, tighter CI | `make bench-500` |
| `bench-cluster-split` | Cluster-aware bootstrap on n=191 — near-duplicate de-inflation | Cluster-aware CI lower bound > 0.65 | `make bench-cluster-split` |
| `bench-cluster-split-500` | Cluster-split on expanded 500-AMP set | Cluster-aware CI lower bound > 0.65 | `make bench-cluster-split-500` |

### Honesty benchmarks

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-easy-baseline` | Compare pipeline against single-feature trivial predictors | Document delta; pipeline may trade raw discrimination for safety | `make bench-easy-baseline` |
| `bench-charge-matched` | Test signal beyond cationic prior | Informational; documents whether pipeline retains signal after charge matching | `make bench-charge-matched` |
| `bench-order-dependent` | Test which features survive sequence scrambling | Document order-dependent signal and composition artifacts | `make bench-order-dependent` |
| `bench-precision-at-k` | Operating characteristic for candidate selection | Document small-k triage precision/recall | `make bench-precision-at-k` |
| `bench-multi-negatives` | Test robustness across multiple decoy distributions | Pipeline behavior stable across decoy sources | `make bench-multi-negatives` |
| `bench-cross-dataset` | Generalization to DRAMP-only AMPs | AUROC within expected tolerance of baseline | `make bench-cross-dataset` |

### Selectivity / safety

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-selectivity` | Within-AMP hemolysis detection | rich_selectivity AUROC > 0.65 where current benchmark supports it | `make bench-selectivity` |
| `bench-per-family` | Stratify benchmark by structural/sequence classes | Document per-class AUROC and ranker blind spots | `make bench-per-family` |
| `bench-feature-decomp` | Per-feature selective-vs-hemolytic AUROC | Identify individual features with selectivity signal | `make bench-feature-decomp` |

### Composite / ablation

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-triage` | Multi-class selective > hemolytic > decoy ranking | Gate triage behavior documented | `make bench-triage` |
| `bench-expert-ablation` | Ablate expert composite components on n=191 | Document component behavior | `make bench-expert-ablation` |
| `bench-expert-ablation-500` | Ablate expert composite on expanded n=1000 | Re-run on diverse set | `make bench-expert-ablation-500` |
| `bench-simulation-ablation` | Ablate virtual-assay proxies on expanded benchmark | Document whether simulation improves or degrades selection | `make bench-simulation-ablation` |
| `bench-simulation-ablation-within-amp` | Ablate simulation modules on within-AMP hemolysis detection | Compare against existing selectivity scorers | `make bench-simulation-ablation-within-amp` |
| `bench-simulation-baselines` | Compare each simulation signal vs cheapest heuristic baseline | Advanced modules must beat simple enemies before ranking impact | `make bench-simulation-baselines` |

### Regression / CI

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-gate` | Multi-metric regression gate enforced in CI | All metrics within tolerance | `make bench-gate` |
| `bench-leakage` | Train/test leakage detection | Zero sequence overlap between train and test sets | `make bench-leakage` |

## Deferred or desired benchmarks

| Benchmark | Purpose | Reason deferred or desired |
|-----------|---------|----------------------------|
| Time split | Test future generalization | Metadata not available for most sequences. |
| Biologically plausible charge-balanced negative set | Stronger non-charge signal test | Requires curated negative sequences. |
| Candidate-panel baseline trial | Compare OpenAMP-selected panels against charge/similarity/random panels | Requires qualified external pilot design. |
| External-review benchmark audit | Have outside reviewer attack benchmark suite | Requires independent reviewer availability. |

## Minimum report fields

Every serious benchmark result should include:

- benchmark ID;
- dataset source and license;
- number of positives and negatives;
- negative construction method;
- split method and similarity threshold;
- cheap-baseline performance;
- model performance with confidence intervals;
- known limitations;
- claim gated or not gated;
- command used;
- commit hash where available.

## Anti-cheating rule

Do not update feature weights, filters, or thresholds after inspecting held-out performance unless you create a new held-out set or explicitly mark the result as exploratory.

Pre-registered analysis plans are recommended for any benchmark that gates a release decision.

## Benchmark promotion rule

A benchmark starts as exploratory.

It becomes informational after implementation and documentation.

It becomes a gate only after adversarial review, cheap-baseline comparison, and threshold pre-registration.

It becomes deprecated when it no longer protects the claim it was meant to protect.

See [`BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md) for the full lifecycle.
