# Benchmark Card — OpenAMP Foundry v0.5.x

> **Purpose:** Single-page summary of benchmark methodology, data, and metrics.
> **Last updated:** 2026-07-01 (hemolysis benchmark expanded to 238 peptides)

---

## Identity

| Field | Value |
|-------|-------|
| Pipeline version | v0.5.x |
| Benchmark type | Retrospective AUROC (composition-matched decoys) |
| Date | 2026-06-29 |
| Config | `configs/pipeline.yaml` (primary), `configs/phase3.yaml` (synthesis gate) |
| Commit | See `docs/METRICS_CURRENT.md` |

## Data

| Set | Count | Description |
|-----|:-----:|-------------|
| Positives | **95** | Public-domain AMPs from 12 taxonomic classes |
| Negatives (standard) | **96** | Length-matched random decoys (Swiss-Prot residue frequencies) |
| Negatives (strict) | **95** | Per-sequence composition-matched shuffles |
| Total (standard) | **191** | Expanded from original 87 (PR #110) |
| Reference library | **120** | Unified AMP library (deduplicated curated_72 + expanded_95) |

## Metrics

| Metric | Standard (pipeline) | Phase3 gate | Strict |
|--------|:-------------------:|:-----------:|:------:|
| **AUROC** | **0.7832** | **0.7448** | 0.4335 |
| **CI₉₅** | 0.72–0.84 | 0.68–0.81 | — |
| **AUPRC** | 0.8164 | 0.7933 | — |
| Baseline AUPRC | 0.4974 | 0.4974 | — |
| Recall@10 | 0.1053 | 0.1053 | — |
| Recall@20 | 0.2105 | 0.2105 | — |
| Recall@43 | 0.4211 | 0.4000 | — |
| Bootstrap | 2000 resamples | 2000 resamples | — |
| **Interpretation** | **STRONG** | **STRONG** | Below random (expected) |

## Within-AMP Selectivity Benchmark

> Tests whether scorers can distinguish hemolytic AMPs (HC50 < 25 µg/ml) from
> selective AMPs (HC50 >= 100 µg/ml). Run: `make bench-selectivity`

| Set | Count | Description |
|-----|:-----:|-------------|
| Hemolytic | **54** | HC50 < 25 µg/ml (literature + DBAASP v3) |
| Selective | **125** | HC50 >= 100 µg/ml |
| Border | **59** | 25 <= HC50 < 100 (excluded from binary AUROC) |
| **Total** | **238** | Expanded from 42 in v0.5.11 using DBAASP data |

| Score | Detection AUROC | CI₉₅ | Significant? |
|-------|:--------------:|:----:|:------------:|
| hemolysis_risk | 0.5650 | 0.47–0.66 | No (direction correct) |
| safety | 0.5116 | 0.43–0.60 | No |
| selectivity_proxy | 0.5744 | 0.50–0.66 | Borderline |
| ensemble | 0.4201 | 0.33–0.51 | No (wrong direction) |
| expert_composite | 0.5459 | 0.46–0.63 | No |
| serum_stability | 0.5873 | 0.51–0.66 | Yes (risk detector) |

**Key finding:** The hemolysis risk scorer's original AUROC=0.9218 (CI 0.82-0.99)
on n=35 was small-sample inflation. On the expanded n=179, no scorer achieves
strong hemolysis detection. Hemolysis remains unpredictable by 1D
physicochemical features and must be assayed experimentally.

## Method

AUROC computed via Wilcoxon-Mann-Whitney statistic (concordant-pair enumeration).
AUPRC via trapezoidal integration of precision-recall curve (pessimistic tie-breaking).
Confidence intervals: percentile bootstrap (2000 resamples, seed=0).


## Cluster-Split Analysis

> Added 2026-07-01. 33 of 95 AMPs fall into 14 near-duplicate clusters (sim >= 0.70).

| Metric | Pipeline | Phase3 |
|--------|:--------:|:------:|
| Full AUROC | 0.7832 | 0.7448 |
| Standard CI₉₅ | 0.717–0.8423 | 0.6741–0.8118 |
| **Cluster-aware CI₉₅** | **0.7061–0.8526** | **0.6591–0.8237** |
| Representative AUROC (76 clusters) | 0.7607 | 0.7196 |
| Representative CI₉₅ | 0.6854–0.8301 | 0.6372–0.7985 |
| Held-out AUROC (19 near-dup AMPs) | 0.8734 | 0.8454 |

The cluster-aware bootstrap resamples clusters (not individual sequences), producing
an honest CI when near-duplicate families exist in the positive set. The standard
bootstrap underestimates variance by treating near-identical sequences as independent.

**Verdict:** Signal survives de-inflation. Cluster-aware CI lower bound (0.7061)
stays above 0.65. Representative-only CI lower bound (0.6854) dips below 0.70 —
an honest limitation. The pipeline has real but modest discriminative power.

Near-duplicate clusters: magainin-1/2/3, protegrin-1/2/3, tachyplesin-I/II/polyphemusin-I,
indolicidin/analog/lys-analog, BMAP-27/PMAP-36/bmap-fragment, aurein-1/3, cecropin-A/B,
apidaecin-Ia/Ib, RsAFP-1/2, plectasin/eurocin, piscidin-1/3, buforin/buforin-II,
dermaseptin-S1/S3-fragment, KWK-template/WKL.


## Expert Ablation (added 2026-07-01)

> Run: `make bench-expert-ablation`

The expert composite scorer (`scoring/expert.py`, 7 components) was benchmarked
against the simple ensemble to test whether its additional complexity earns its keep.

| Scorer | AUROC | CI₉₅ | Delta vs ensemble |
|--------|:-----:|:----:|:-----------------:|
| **Ensemble** (pipeline.yaml) | **0.7832** | 0.717–0.8423 | — |
| Expert composite | 0.7360 | 0.6604–0.8037 | **−0.0472** |
| **Ensemble** (phase3.yaml) | **0.7448** | 0.6741–0.8118 | — |
| Expert composite | 0.7360 | 0.6604–0.8037 | −0.0088 |

**Per-component AUROC:**

| Component | AUROC | Signal class |
|-----------|:-----:|:------------:|
| activity | 0.8137 | Signal-bearing |
| selectivity_proxy | 0.7729 | Signal-bearing |
| hinge_selectivity | 0.5180 | Near-zero |
| boman_activity | 0.4620 | Near-zero |
| synthesis | 0.4228 | Anti-signal |
| safety | 0.3487 | Anti-signal |
| serum_stability | 0.2231 | Anti-signal |

**Verdict:** Expert composite does NOT improve AMP-vs-decoy discrimination. Three
components (safety, serum_stability, synthesis) are anti-signal: known AMPs score
worse than random decoys on these axes because real AMPs have extreme biophysical
properties (high charge, high hydrophobic moment, many protease sites) that these
scorers penalise. The ensemble remains the primary synthesis gate.

**Caveat:** This tests binary AMP/non-AMP discrimination only. The expert components
may add value for within-AMP ranking (selective vs hemolytic) — a within-AMP benchmark
is the appropriate next test.

## Known Biases

| Bias | Impact | Mitigation |
|------|--------|------------|
| Helical-centric scorer | β-sheet AMPs (defensins) score below panel | Noted in METRICS_CURRENT.md |
| Melittin safety blind spot | Safety=1.0 despite strong hemolysis | Hemolysis assay mandatory for all |
| Composition-matched scrambled AUROC < 0.5 | Model relies on composition > order; fails strict order-sensitivity test | OpenAMP is an **evidence-ranking tool**, not a validated sequence-order activity predictor. Composition-scrambled test confirms the model captures AMP-like composition, not sequence-order features. |
| Near-seed generation only | Novel sequence space not explored | Acknowledged limitation in all docs |

## Classification

OpenAMP performs well on standard decoys (AUROC 0.7832) but **fails the strict composition-scrambled benchmark (AUROC 0.4335, below random)**. This means the model primarily detects AMP-like amino acid composition rather than sequence-order-dependent antimicrobial features. This is expected for a physicochemical heuristic scorer and is appropriate for its intended use: **triage and ranking**, not deep biological prediction.

## Historical Baseline

| Point | Set | Pipeline AUROC | Phase3 AUROC |
|-------|:---:|:--------------:|:------------:|
| Current (PR #110) | 95+96 (n=191) | **0.7832** | 0.7448 |
| Pre-expansion (PR #72) | 43+44 (n=87) | 0.8420 | 0.8266 |
| Pre-face-bonus (PR #70) | 43+44 | 0.8348 | 0.8126 |
| Pre-windowed-mu_h (PR #66) | 43+44 | 0.8047 | 0.7846 |

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-29 | Initial card — expanded benchmark (PR #110) | OpenAMP CI |
