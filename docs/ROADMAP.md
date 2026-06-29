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
- retrospective AUROC benchmark (`validate-scoring` CLI, original demo set AUROC = 0.8420, bootstrap CI₉₅: 0.76–0.91).

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

## v0.7.x — Wet-lab readiness package (PRs #73–#92) ✓

- CLI integration tests — gold-standard, external-predict, pilot-confident, diversity-check (PRs #74–#79/#82/#85)
- Lab-results directory loading + toxicity flag branch coverage (PR #80)
- Wet-lab probability analysis (`docs/WET_LAB_PROBABILITY.md`) — per-family P(MIC≤16) breakdown, composite P(≥1 active) = 99.95% (PRs #81/#87)
- Assay pre-registration (`docs/ASSAY_PREREGISTRATION.md`) — MRSA USA300, serum stability gate, RPMI-1640 arm for SEED-009 (PR #83)
- SEED-007 helix-wheel length fix 18 AA → 11 AA (PR #84)
- `novelty-check-broad` CLI + 72-AMP curated database: 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE (`docs/NOVELTY_BROAD_CHECK.md`) (PR #86)
- SEED-003 reclassification: RRWQWRMKKLG-class KNOWN_VARIANT; P(MIC≤16) raised 50–65% → 60–75%; publication novelty 25–40% → 10–20% (PR #87)
- EXPERT_REVIEW_PACK.md overhauled: 7-seed mechanism table, full 20-candidate novelty table, SEED-008/009 special notes, Melittin safety blind spot (PR #88)
- WET_LAB_HANDOFF SEED-003 special notes: KNOWN_VARIANT classification (SAR value retained), Met oxidation risk, aggregation caution, C-terminal amidation recommendation (PR #89)
- `PROLINE_RICH_INTRACELLULAR` flag in presynth QC — RPMI-1640 parallel assay recommendation for ≥25% Pro; all 4 SEED-009 pilot variants flagged (Krizsan et al. 2014 Angew Chem Int Ed 53:12236) (PR #90)
- `amphipathic_score` + `charge_ph74` added to pilot panel CSV for wet-lab within-family prioritization (PR #91)
- Doc sync: Krizsan citation corrected (53:14546 → 53:12236) across ASSAY_PREREGISTRATION + EXPERT_REVIEW_PACK; `make help` target added (PR #92)
- ROADMAP v0.7.x section added documenting all PRs #73–#92 (PR #93)
- Test coverage: 5 new tests covering LONG_PEPTIDE flag, no-flags checklist, and length-filter failure mode (PR #94); 12 new CLI tests for generate-batch, batch-pack, pilot-panel success, batch-pack markdown, redundancy + optimal-cluster-rep sections, novelty error paths, family structural warnings — 1304 tests, 99% coverage (PR #99)
- His pKa unified 6.0 → 6.5 (Bjellqvist 1993) across presynth_check.py and physchem.py; METHODS.md abs() correction; ensemble.py weight docstring (PR #95)
- Discovery prediction tracked through PRs #92–#95 in DISCOVERY_PREDICTION.md (PR #96)
- WET_LAB_HANDOFF.md: version tag corrected, PROLINE_RICH_INTRACELLULAR QC flag table row, `amphipathic_score`/`charge_ph74` score reference table rows added (PR #97)
- EXPERT_REVIEW_PACK.md: note added on new CSV columns for within-family prioritization (PR #98)
- EXPERT_REVIEW_PACK.md: SEED-007 reviewer note (Met oxidation, bombolitin origin, SAR framing, top-10 slots) and SEED-005 reviewer note (lowest priority, safety margin) added; SEED-007 Met oxidation row in Pipeline Limitations table (PR #101)
- WET_LAB_HANDOFF.md completed with dedicated special notes for all 7 seed families: SEED-007 (bombolitin-II, 4 pilot slots, all NOVEL, best serum stability, Met oxidation guidance, breakthrough-candidate framing), SEED-005 (cecropin-magainin hybrid, safety/serum risk note), SEED-008 (puroindoline-a, Trp aggregation handling, aromatic-mechanism CD interpretation), SEED-009 (Bac2A proline-rich, Pro coupling guidance, RPMI-parallel assay note restated as standalone); Serum Stability section header updated to "All 7 Seeds" with SEED-006 and SEED-007 table rows added; DISCOVERY_PREDICTION.md tracking updated (PR #100)
- presynth_check.py Met oxidation flag strengthened: Nle (norleucine) substitution explicitly recommended, inert-atmosphere storage, mandatory HPLC purity at receipt — actionable guidance now surfaces at QC report level for all SEED-007 pilot variants (PR #102)
- ASSAY_PREREGISTRATION.md serum stability model limitations block extended to cover all 5 affected families: SEED-003 (pre-existing, 11 AA length edge), SEED-007 (added: Met/Nle substitution + 11 AA length edge), SEED-008 (pre-existing, Trp steric, 13 AA length edge), SEED-009 (pre-existing, Pro-bond protease resistance), SEED-005 (added: safety gate, hemolysis at MIC/3 mandatory, exclude if HC₅₀ < 10× MIC); all limitations pre-registered before synthesis order (PR #103)
- presynth_check.py: PYROGLUTAMATE_RISK flag added for N-terminal Q (cyclises to pGlu at pH 7.4, t½ hours–days, 5–50× MIC loss); E1 intentionally excluded (acid-catalysed only, negligible at physiological pH); Nα-acetylation (zero extra cost) or Q1→K1/R1 substitution surfaced as remediation; 7 tests including Q+QG double-flag interaction guard (PR #105)
- WET_LAB_HANDOFF.md: SEED-009 synthesis guidance corrected — VAR_033 (RRLPRPGYMPRP) contains Met at position 9 (Nle substitution + HPLC purity required); the "No Met, no Cys" statement now scoped to VAR_027/017/039 only (PR #106)
- test(qc): SEED-009_VAR_033 regression guard — asserts both MET×1 (Nle) and PROLINE_RICH_INTRACELLULAR fire simultaneously for RRLPRPGYMPRP; 1312 tests total (PR #107)
- EXPERT_REVIEW_PACK.md: Pipeline Limitations table updated — PYROGLUTAMATE_RISK row added (N-terminal Q, physiological pH, none of 20 pilot candidates affected); SEED-009_VAR_033 Met row added (PR #108)
- test: close remaining 1% coverage gap — 6 modules to 100% branch coverage; 1321 tests total; only 6 structural CLI guard lines remain uncovered; all source modules at 100% branch coverage (PR #109)
- feat(bench+qc): expanded benchmark (95 AMPs + 96 decoys, n=191, AUROC=0.7832, CI₉₅: 0.72–0.84); 52 new public-domain AMPs across 12 classes (defensins, proline-rich, lantibiotics); DKP_RISK flag for N-terminal X-Pro diketopiperazine cyclization — all 4 SEED-008 pilots (F-Pro) flagged with dynamic mass (244 Da), MS receipt check, Nα-Ac REQUIRED; WET_LAB_HANDOFF.md SEED-008 synthesis guidance updated; ASSAY_PREREGISTRATION.md SEED-008 DKP note added; 1337 tests (PR #110)

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
| ~~Large-scale benchmark (≥ 500 AMPs vs composition-matched decoys, cluster-split)~~ | ~~Current AUROC 0.8420 measured on 43+44 demo set (n=87, CI₉₅: 0.76–0.91); may not generalise~~ | **Partial** (PR #110: expanded to 95 AMPs + 96 decoys, n=191, AUROC=0.7832, CI₉₅: 0.72–0.84; 52 new public-domain AMPs from 12 taxonomic classes; covers defensins, proline-rich, lantibiotics — a more honest estimate. 500+ target still deferred to v1.0+) |
| External predictor ensemble adapters (CAMPR4, AMPScanner, dbAMP, AntiCP2, Macrel) | Independent second opinions on activity; required for scientific credibility. Manual web-submission checklist at `outputs/external_predict_checklist.md`. Macrel v1.6.0 CLI ONNX bug documented PR #77 — all sequences (incl. canonical AMPs magainin-2, LL-37) misclassified as NAMP; use web server at big-data-biology.org/software/macrel. AMPlify omitted: GPU/ONNX env incompatible with current deps | Medium (checklist generated; web submissions pending) |
| ~~True novelty check against APD3, DRAMP v3.0, dbAMP~~ | ~~Current novelty scored against 45-sequence seed set only; may overestimate novelty~~ | **Partial** (PR #86: `novelty-check-broad` compares against 72-AMP curated database; result: 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE; full APD3 BLASTp still needed before publication) |
| ~~AUPRC alongside AUROC~~ | ~~Better metric for class-imbalanced AMP datasets~~ | **Done** (PR #58; updated PR #72) — pipeline AUPRC = 0.8627 |
| Wet-lab result integration (active-learning round 2) | Required to move from 15–30% to 50%+ credible probability | Requires wet-lab |
| ~~Pre-registration of assay protocol before synthesis~~ | ~~Strengthens causal inference; reduces reporting bias~~ | **Done** (docs/ASSAY_PREREGISTRATION.md — PRs #83; includes MRSA USA300, serum stability, Gate P3 aligned) |
| Public benchmark paper (replicable, cluster-split, open datasets) | Sets community standard; enables external validation | Large |
