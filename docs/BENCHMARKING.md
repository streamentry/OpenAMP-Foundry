# Benchmarking Plan

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

Each benchmark has a `make` target, a script in `scripts/`, and a
documented result in `docs/METRICS_CURRENT.md` and
`outputs/metrics_snapshot.json`.

### Core discrimination

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-baseline` | Random baseline — pipeline is not noise | AUROC > 0.5 | `make bench-baseline` |
| `bench-hidden-active` | Known active AMPs hidden from training appear in top ranks | Better-than-random recovery | `make bench-hidden-active` |
| `validate-scoring` | Standard benchmark (n=191, 95 AMPs + 96 decoys) | AUROC > 0.70 | `make validate-scoring` |
| `bench-500` | Expanded benchmark (500 AMPs + 500 decoys, n=1000) | AUROC > 0.70, ~2.3× tighter CI | `make bench-500` |
| `bench-cluster-split` | Cluster-aware bootstrap on n=191 — near-duplicate de-inflation | Cluster-aware CI lo > 0.65 | `make bench-cluster-split` |
| `bench-cluster-split-500` | Cluster-split on expanded 500-AMP set | Cluster-aware CI lo > 0.65 | `make bench-cluster-split-500` |

### Honesty benchmarks

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-easy-baseline` | Compare pipeline against single-feature trivial predictors (charge, length, charge density) | Document delta; pipeline expected to trade raw discrimination for safety | `make bench-easy-baseline` |
| `bench-charge-matched` | Greedy charge-density matching — test signal beyond cationic prior | Informational; documents whether pipeline retains signal after charge matching | `make bench-charge-matched` |
| `bench-order-dependent` | Test which features survive sequence scrambling (composition-control) | 7/31 features are order-dependent; dipeptide_order_score AUROC 0.786 | `make bench-order-dependent` |
| `bench-precision-at-k` | Operating characteristic for candidate selection — small-k triage precision/recall | top-20 precision 1.000, best F1 threshold documented | `make bench-precision-at-k` |
| `bench-multi-negatives` | Test robustness across 4 decoy distributions (random, reverse, shuffled proteome, inactive variants) | Pipeline rank order stable across decoy sources | `make bench-multi-negatives` |
| `bench-cross-dataset` | Generalization to DRAMP-only AMPs — test source-independence of heuristic features | AUROC within 0.03 of APD6/UniProt baseline | `make bench-cross-dataset` |

### Selectivity / safety

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-selectivity` | Within-AMP hemolysis detection — can scorers distinguish hemolytic from selective AMPs? | rich_selectivity AUROC > 0.65 (CI lo > 0.5) | `make bench-selectivity` |
| `bench-per-family` | Stratify 500 AMPs by 6 heuristic structural classes — reveal charge-dominated pipeline bias | Document per-class AUROC; compensate via diversity selection | `make bench-per-family` |
| `bench-feature-decomp` | Per-feature selective-vs-hemolytic AUROC — which individual features have signal? | 8/30 features significant; 6/8 unused by current selectivity model | `make bench-feature-decomp` |

### Composite / ablation

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-triage` | Multi-class: selective > hemolytic > decoy ranking in a single panel | gate_triage passes all 3 pairwise AUROCs; strict triage (composition-matched) fails honestly | `make bench-triage` |
| `bench-expert-ablation` | Ablate expert composite components on n=191 | Document per-component AUROC; expert lower than ensemble on AMP-vs-decoy (by design) | `make bench-expert-ablation` |
| `bench-expert-ablation-500` | Ablate expert composite on expanded n=1000 | Re-run on diverse set; 2 components reclassified from n=191 | `make bench-expert-ablation-500` |
| `bench-simulation-ablation` | Ablate MembraneProxy + StructureProxy on 500-AMP benchmark | Composite degrades AMP-vs-decoy (expected — modules are for within-AMP tasks); bacterial_binding alone AUROC 0.7512 (non-charge signal) | `make bench-simulation-ablation` |
| `bench-simulation-ablation-within-amp` | Ablate simulation modules on within-AMP hemolysis detection | Best simulation helix_weight AUROC 0.6458; rich_selectivity best at 0.7453. No improvement | `make bench-simulation-ablation-within-amp` |

### Regression / CI

| Benchmark | Purpose | Target | Verification |
|-----------|---------|--------|-------------|
| `bench-gate` | Multi-metric regression gate: cluster-split, selectivity, triage — enforced in CI | All metrics within tolerance; fails CI if AUROC drops | `make bench-gate` |
| `bench-leakage` | Train/test leakage detection | Zero sequence overlap between train and test sets | `make bench-leakage` |

## Deferred benchmarks

| Benchmark | Purpose | Reason deferred |
|-----------|---------|----------------|
| Time split | Test future generalization | Metadata not available for most sequences |
| Virtual-assay ablation | Test whether simulation modules improve triage | Shipped: `make bench-simulation-ablation`, `make bench-simulation-ablation-within-amp`, `make simulation-gate` |
| Biologically plausible charge-balanced negative set | Honest non-charge signal test | Requires curated negative sequences — see v0.5.41 recommendation |

## Minimum report fields

Every benchmark result stored in `outputs/metrics_snapshot.json` includes:

- dataset source and license;
- number of positives and negatives;
- split method and similarity threshold;
- baseline performance;
- model performance with confidence intervals;
- known limitations.

## Anti-cheating rule

Do not update feature weights, filters, or thresholds after inspecting
held-out performance unless you create a new held-out set. Pre-registered
analysis plans are recommended for any benchmark that gates a release
decision.
