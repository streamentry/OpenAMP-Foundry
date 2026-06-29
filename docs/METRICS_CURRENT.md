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
| Wave 0 panel size | 20 candidates |
| Wave 0 scaffold families | 7 (SEED-001, 003, 005, 006, 007, 008, 009) |
| **Wave 1 final panel (Wave 0.5)** | **24 candidates** |
| **Wave 1 scaffold families** | **15 (Wave 0 carry-overs + 9 new families)** |
| Wave 0.5 new families | 10 (SEED-010 through SEED-019) |
| Wave 0.5 shortlisted | 60 (6 per family × 10 families) |
| Wave 0.5 novelty (v2, 27k DB) | 1 RELATED_NOVEL / 39 CLOSE_RELATIVE / 19 KNOWN_VARIANT / 1 EXACT_MATCH_OR_FRAGMENT |
| Wave 0.5 novelty v1 (72 refs, Levenshtein) | 53/60 RELATED_NOVEL or higher — v1 method overstated novelty |
| Broad novelty Wave 0 (72 refs) | 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE |
| 5-tier audit Wave 0 (120 refs) | 13 HIGH_CONFIDENCE_NOVEL + 3 NOVEL + 1 CLOSE_RELATIVE + 3 KNOWN_VARIANT |
| Wave 0 panel ensemble range | 0.796–0.857 |
| Wave 0 panel safety range | 0.845–1.000 |
| Positive control | SEED-001_VAR_064 (magainin-1 derivative, ensemble 0.802) |
| Blind spot | Melittin scores Safety=1.0 despite hemolysis; hemolysis assay mandatory |
| Wave 0.5 external predictors | **COMPLETE** — AMPScanner 59/60, AMPActiPred 60/60, Macrel AMP 52/60 |
| Wave 0.5 activity consensus | **STRONG_ACTIVITY: 52/60 (87%)** — passes W0.5-3 gate (≥70%) |
| Wave 0.5 HemoFinder | LOW: 40/60 (67%), HIGH: 20/60 |
| Wave 0.5 AntiCP 2.0 | Non-AntiCP: 4/60 (7%), AntiCP: 56/60 |
| Best clean candidate | SEED-019_VAR_004 (RVRIRLVKRLLK) — STRONG + Non-AntiCP + HemoFinder LOW |
| **Wave 0.5b** | **23 candidates shortlisted** (5 new families SEED-020→024, no aromatics) |
| Wave 0.5b design goal | Lower AntiCP risk: no W/Y/F residues; broken helix pattern |
| Wave 0.5b expected AntiCP | < 0.50 (by design — pending external predictor confirmation) |

### Wave 1 Panel Composition (Wave 0.5 output, post-v2 novelty update)

| Role | Count |
|------|-------|
| BALANCED_LEAD | 15 |
| HIGH_UPSIDE_RISKY | 4 |
| POSITIVE_CONTROL | 1 |
| SAR_CONTROL | 4 |

### Novel families (Wave 0 leads)

| Family | Mechanism | Panel slots | Novelty | Key risk |
|--------|-----------|:-----------:|---------|----------|
| SEED-006 | Mastoparan-X, wasp-venom helix insertion | 2 | 0.643 | Mast-cell degranulation |
| SEED-007 | Bombolitin-II, bumblebee venom | 1 | 0.643 | Met oxidation at pos 6 |
| SEED-008 | Puroindoline-a, Trp-rich interfacial | 2 | 0.692 | DKP risk (FP), HemoFinder HIGH |
| SEED-009 | Bac2A, proline-rich intracellular | 2 | 0.647 | AntiCP risk, RPMI-1640 arm |

### New Wave 0.5 families in Wave 1 panel (v2 novelty classes)

| Family | Mechanism | Panel slots | v2 Novelty class |
|--------|-----------|:-----------:|---------------|
| SEED-010 | Histatin-5 P-113 oral innate AMP fragments | 1 | KNOWN_VARIANT (SAR_CONTROL) |
| SEED-011 | Pro-kinked amphipathic | 1 | CLOSE_RELATIVE |
| SEED-012 | Glycine-rich low-hydrophobicity design | 2 | CLOSE_RELATIVE |
| SEED-014 | Cathelicidin-mini scattered helix | 1 | CLOSE_RELATIVE |
| SEED-015 | KFLK de novo cationic helix | 1 | CLOSE_RELATIVE |
| SEED-016 | RRWK dual-Trp low-aromatic | 2 | CLOSE_RELATIVE |
| SEED-018 | GKRK scattered-charge design | 2 | CLOSE_RELATIVE |
| SEED-019 | Arg-Val alternating pattern | 2 | RELATED_NOVEL / CLOSE_RELATIVE |

---

## External Predictor Results (Wave 0.5)

| Tool | Status | Result |
|------|--------|--------|
| CAMPR4 | ⏳ Not submitted | PENDING |
| AMPScanner v2 | ✅ Complete | 59/60 AMP (98%) |
| AMPActiPred | ✅ Complete | 60/60 ABP (100%) |
| Macrel AMP | ✅ Complete | 52/60 AMP (87%) |
| HemoFinder | ✅ Complete | 40/60 LOW (67%), 20/60 HIGH |
| AntiCP 2.0 | ✅ Complete | 4/60 Non-AntiCP, 56/60 AntiCP |
| Macrel Hemolysis | ✅ Complete | 60/60 flagged (non-discriminating — flags all) |

**Activity consensus (3 tools, CAMPR4 excluded):** 52/60 STRONG_ACTIVITY, 7/60 MODERATE, 1/60 WEAK

**Safety profile concern:** 56/60 AntiCP-positive is expected for amphipathic-helix designs.
AntiCP 2.0 detects anticancer peptide (ACP) patterns, not antimicrobial activity directly.
Mitigation: Wave 0.5b designs avoid aromatic residues and pure amphipathic helix.

Machine-readable: `outputs/wave0_5_external_predict_results.csv`, `outputs/wave0_5_external_consensus.csv`

---

## Test Suite

| Metric | Value |
|--------|-------|
| Total tests | 1343 |
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
| APD/DRAMP novelty (v2) | Complete — 27,234-sequence combined DB (APD6+DRAMP+UniProt); BLOSUM62 local alignment; Wave 0.5 results updated |
| No wet-lab data | All probabilities are upper bounds; true hit rate unknown |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-06-29 | Novelty audit v2: BioPython BLOSUM62 local alignment vs 27,234 AMPs (APD6+DRAMP+UniProt); panel updated (15 families, 4 SAR_CONTROL); all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5b: 23-candidate safety-optimized shortlist (SEED-020–024, no aromatics) | OpenAMP Wave 0.5b |
| 2026-06-29 | External predictor results filled from wave05_combined_consensus.csv; all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5 scaffold diversification — 24-candidate Wave 1 panel across 14 families | OpenAMP Wave 0.5 |
| 2026-06-29 | Initial — expanded benchmark (PR #110) | OpenAMP CI |
