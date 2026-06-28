# Roadmap

## v0.1 — Safe starter ✓

- toy data;
- transparent heuristic scoring;
- JSON evidence certificates;
- report generation;
- tests and CI.

## v0.2 — Dataset layer ✓

- license-aware dataset loaders;
- dataset cards;
- deduplication;
- cluster splitting (`benchmark/splits.py`);
- leakage checks (`bench leakage` CLI + `test_cluster_split.py`).

## v0.3 — Predictor adapters ✓

- Boman index adapter (independent second scorer, `scoring/boman.py`);
- ensemble scoring with configurable weights (`scoring/ensemble.py`);
- model disagreement uncertainty signal (disagreement = |activity − boman|).

## v0.4 — Benchmark suite ✓

- hidden-positive recovery (`bench baseline`, `test_hidden_active_recovery.py`);
- negative control rejection (`test_negative_penalization.py`, `test_negative_robustness.py`);
- novelty stress test (`test_novelty_pressure.py`);
- toxicity penalty benchmark (`test_toxicity_penalty.py`);
- retrospective AUROC benchmark (`validate-scoring` CLI, AUROC = 0.8420 on demo set, bootstrap CI₉₅: 0.76–0.91).

## v0.5 — Lab-batch package ✓

- pre-registration template (`docs/SELECTION_RULE.md`);
- batch manifest (`outputs/run_manifest.json` with SHA-256 input hashes);
- candidate certificates (JSON + `schemas/candidate.schema.json`);
- expert-review checklist (`docs/EXPERT_REVIEW_PACK.md`);
- wet-lab handoff guide (`docs/WET_LAB_HANDOFF.md`);
- safe publication template (`docs/NOMINATION_REPORT.md`).

## v0.5.x — Scoring enhancements (shipped alongside v0.5)

Implemented during the pre-wet-lab improvement loop (PRs #31–#54):

- Serum stability scoring — HNE elastase + trypsin + chymotrypsin site density
- Selectivity proxy — charge/GRAVY-based mammalian cytotoxicity risk detector
- Pilot panel selection — `pilot_priority` formula with serum stability, novelty, selectivity, cytotox_penalty
- Aggregation propensity scoring — consecutive hydrophobic run + β-branched density
- Aggregation-safe mutation generation — prevents creating VILMFW runs ≥ 4
- Proline synthesis penalty — DKP/coupling-difficulty penalty at > 15% proline
- Helix propensity bonus — Chou-Fasman Pα weight increased 0.01 → 0.03 in activity scorer
- Safety score uses pH-7.4 charge consistently with activity scorer
- C-terminal amidation and N-terminal acetylation recommendations in QC
- Wave 2 D-amino guidance in synthesis order
- DISCOVERY_PREDICTION.md — quantified discovery probability model (internal: ~29–49% pre-correlation-correction; calibrated: ~15–30% accounting for near-seed correlation)
- External Calibration section added (2026-06-28): acknowledges competitor landscape, corrects effective independence assumption, identifies path to higher confidence

## v0.6.x — Scoring accuracy improvements (PRs #61–#72)

- Trp-weighted aromatic bonus (1.5× Trp vs Phe/Tyr); safety abs() bug fix; AUROC 0.8164→0.8086 (PR #65)
- Duplicate benchmark entry removed (REF-GIG-001 = REF-MAG-001); corrected AUROC 0.8086→0.8047 (PR #66)
- Windowed hydrophobic moment (Eisenberg window=11) + anionic charge guard; AUROC 0.8047→0.8348 (PR #70)
- Moment-oriented helix-wheel face analysis with per-face feature extraction (PR #71)
- Face segregation bonus (helix_wheel_amphipathic_score × 0.05) in activity_likeness_score; AUROC 0.8348→0.8420, bootstrap CI₉₅: 0.76–0.91 (PR #72)
- max_disagreement gate raised 0.30→0.40 (PR #61), 0.40→0.45 (PR #72) to correctly accommodate SEED-008 Trp-rich puroindoline-a mechanism class

## v1.0 — Validated dry-lab-to-wet-lab loop

- independently reviewed assay batch (expert_review.yml GitHub issue template);
- lab results ingested via `schemas/lab_result.schema.json`;
- negative results archived where safe;
- active-learning batch 2 (D-amino variants, MDR strain panel);
- public reproducibility report.

## Beyond v1.0 — What is still needed for a major breakthrough

The following are not implemented in this pipeline. Each is a known gap flagged in external
review (2026-06-28). Progress on these would materially raise breakthrough probability.

| Gap | Why it matters | Effort estimate |
|-----|----------------|-----------------|
| Large-scale benchmark (≥ 500 AMPs vs composition-matched decoys, cluster-split) | Current AUROC 0.8420 measured on 43+44 demo set (n=87, CI₉₅: 0.76–0.91); may not generalise | Medium |
| External predictor ensemble adapters (CAMPR4, AMPScanner, dbAMP, AntiCP2, Macrel) | Independent second opinions on activity; required for scientific credibility. Manual web-submission checklist at `outputs/external_predict_checklist.md`. Macrel v1.6.0 CLI ONNX bug documented PR #77 — all sequences (incl. canonical AMPs magainin-2, LL-37) misclassified as NAMP; use web server at big-data-biology.org/software/macrel. AMPlify omitted: GPU/ONNX env incompatible with current deps | Medium (checklist generated; web submissions pending) |
| True novelty check against APD3, DRAMP v3.0, dbAMP, UniProt | Current novelty scored against 45-sequence seed set only; may overestimate novelty | Small–Medium |
| ~~AUPRC alongside AUROC~~ | ~~Better metric for class-imbalanced AMP datasets~~ | **Done** (PR #58; updated PR #72) — pipeline AUPRC = 0.8627 |
| Wet-lab result integration (active-learning round 2) | Required to move from 15–30% to 50%+ credible probability | Requires wet-lab |
| Pre-registration of assay protocol before synthesis | Strengthens causal inference; reduces reporting bias | Small |
| Public benchmark paper (replicable, cluster-split, open datasets) | Sets community standard; enables external validation | Large |
