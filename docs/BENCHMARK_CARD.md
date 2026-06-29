# Benchmark Card — OpenAMP Foundry v0.5.x

> **Purpose:** Single-page summary of benchmark methodology, data, and metrics.
> **Last updated:** 2026-06-29 (PR #110 expanded benchmark)

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

## Method

AUROC computed via Wilcoxon-Mann-Whitney statistic (concordant-pair enumeration).
AUPRC via trapezoidal integration of precision-recall curve (pessimistic tie-breaking).
Confidence intervals: percentile bootstrap (2000 resamples, seed=0).

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
