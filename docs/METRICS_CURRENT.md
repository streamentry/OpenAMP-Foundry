# Current Pipeline Metrics — Single Source of Truth

> **Purpose:** One authoritative table of current pipeline metrics. If any doc disagrees
> with this file, this file wins. Updated whenever benchmark/benchmark config changes.
>
> **Last updated:** 2026-06-29 (PR #110 expanded benchmark)
> **Pipeline version:** v0.5.x
> **Branch:** main

---

## Benchmark Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Benchmark type | Standard (composition-matched decoys) | Default `make validate-scoring` |
| Positives | **95** public-domain AMPs | 12 taxonomic classes; see `examples/validation/known_amps.csv` |
| Negatives | **96** length-matched random decoys | Swiss-Prot residue frequencies, seed=1729 |
| Total (n) | **191** | Expanded from original 87 (PR #110) |
| **Pipeline AUROC** | **0.7832** | Bootstrap CI₉₅: 0.72–0.84 (n_bootstrap=2000) |
| **Phase3 AUROC** | **0.7448** | Synthesis gate config; CI₉₅: 0.68–0.81 |
| **Pipeline AUPRC** | **0.8164** | Random baseline: 0.4974 |
| **Phase3 AUPRC** | **0.7933** | Random baseline: 0.4974 |
| Strict AUROC (scrambled) | 0.4335 | 95 shuffled decoys; below random — expected for helic-centric scorer |
| Recall@10 | 0.1053 | 10/95 positives in top 10 |
| Recall@20 | 0.2105 | 20/95 positives in top 20 |
| Recall@43 | 0.4211 | 40/95 positives in top 43 |
| Interpretation | **STRONG** | AUROC > 0.70 gate passed |

### Historical baselines

| Point | Benchmark | AUROC | Phase3 AUROC | Source |
|-------|-----------|-------|--------------|--------|
| Current | 95 AMP + 96 decoy (n=191) | **0.7832** | **0.7448** | PR #110 |
| Original demo set | 43 AMP + 44 decoy (n=87) | 0.8420 | 0.8266 | PR #72 |
| Pre-face-bonus | 43 + 44 | 0.8348 | 0.8126 | PR #70 |
| Pre-windowed-mu_h | 43 + 44 | 0.8047 | 0.7846 | PR #66 |
| Pre-Trp-bonus | 43 + 44 | 0.8164 | — | PR #65 (transient) |

**Note:** All historical baselines use the original demo set (43 AMPs + 44 decoys). Direct
comparison with the expanded benchmark is not meaningful — the expanded set is more
representative of diverse AMP classes not covered by the helic-centric scorer.

---

## Candidate Panel

| Metric | Value |
|--------|-------|
| Panel size | 20 candidates |
| Scaffold families | 7 (SEED-001, 003, 005, 006, 007, 008, 009) |
| Seeds in synthesis pool | 7 families (SEED-002, 004, 010 excluded at gates) |
| Total synthesis pool | 100 candidates from 7 families |
| Broad novelty (72 refs) | 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE | See NOVELTY_AUDIT_FULL.md for 5-tier breakdown |
| 5-tier audit (120 refs) | 12 HIGH_CONFIDENCE_NOVEL + 4 NOVEL + 1 CLOSE_RELATIVE + 3 KNOWN_VARIANT | Audited against unified AMP library (120 seqs) |
| Panel ensemble range | 0.796–0.857 |
| Panel safety range | 0.845–1.000 |
| Positive control | SEED-001_VAR_064 (magainin-1 derivative, ensemble 0.802) |
| Blind spot | Melittin scores Safety=1.0 despite hemolysis; hemolysis assay mandatory |

### Novel families (SEED-006, 007, 008, 009)

| Family | Mechanism | Panel slots | Novelty | Key risk |
|--------|-----------|:-----------:|---------|----------|
| SEED-006 | Mastoparan-X, wasp-venom helix insertion | 4 | 0.643 | Mast-cell degranulation |
| SEED-007 | Bombolitin-II, bumblebee venom | 4 | 0.615–0.727 | Met oxidation at pos 6 |
| SEED-008 | Puroindoline-a, Trp-rich interfacial | 4 | 0.600–0.692 | DKP risk (FP), Trp photolability |
| SEED-009 | Bac2A, proline-rich intracellular | 4 | 0.647–0.692 | Requires RPMI-1640 assay |

---

## External Predictor Checklist

| Tool | Status | Consensus |
|------|--------|:---------:|
| CAMPR4 | ⏳ Web submission pending | ?/5 |
| AMPScanner v2 | ⏳ Web submission pending | ?/5 |
| dbAMP 2.0 | ⏳ Web submission pending | ?/5 |
| AntiCP 2.0 | ⏳ Web submission pending | ?/5 |
| Macrel | ⏳ Web submission pending (use web server, not CLI) | ?/5 |

Consensus gate: ≥3/5 tools positive. Currently **PENDING** before synthesis order.
See `outputs/external_predict_checklist.md` for submission details.

---

## Test Suite

| Metric | Value |
|--------|-------|
| Total tests | 1338 |
| Coverage (branch) | 99% (6 CLI guard lines only) |
| Source modules at 100% | All pipeline, QC, scoring modules |

---

## Key Limitations

| Limitation | Impact |
|------------|--------|
| AUROC 0.7832 | ~22% of benchmark pairs misranked; wet-lab is the judge |
| Safety model blind spot | Melittin scores Safety=1.0; hemolysis assay mandatory |
| No structural modeling | Helical assumption may misclassify non-helical mechanisms |
| Near-seed generation only | Novel sequence space not explored de novo |
| Benchmark at 191 sequences | Still far from 500+ target flagged in ROADMAP (v1.0+) |
| APD3/DRAMP novelty check | Pending (72-reference check done; full database BLAST pending) |
| No wet-lab data | All probabilities are upper bounds; true hit rate unknown |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-29 | Initial — expanded benchmark (PR #110) | OpenAMP CI |
