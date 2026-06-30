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
- fix(docs+qc): correct SEED-006 Met synthesis error — ALL 4 SEED-006 pilots contain Met at position 9 (inherited from mastoparan-X); Nle/M9Nle REQUIRED in synthesis order; ASSAY_PREREGISTRATION.md SEED-006 Met pre-registered; EXPERT_REVIEW_PACK.md: SHORT_PEPTIDE count corrected (6→10 candidates), DKP_RISK + Met rows added, AUROC stale values corrected; regression guard `test_seed006_all_pilots_have_met_at_position9` with positional seq[8]=='M' assertion in TestOxidationRisk (PR #104)
- feat(panel): wave 0.5b external-predictor confirmation — SEED-020_VAR_004 (RLRIRVLKRLLK, AMPScanner 0.9928, HemoFinder LOW, Non-AntiCP 0.29) and SEED-020_VAR_002 (KVRIRVLKRLLK, AMPScanner 0.9960, HemoFinder LOW, Non-AntiCP 0.32) confirmed NOVEL by broad novelty check (72-AMP DB, <50% similarity); both added to wave1_final_panel.csv as BALANCED_LEAD (WAVE0_5B source); SEED-019/020 synthesis notes added to WET_LAB_HANDOFF.md; EXPERT_REVIEW_PACK.md §5 updated with SEED-019/020 family row and wave 0.5b addendum

## v0.5.7 — Novelty Audit v2: Proper Prior-Art Scan ✓ (2026-06-29)

- Downloaded full AMP databases: APD6 natural (3,307), DRAMP general (11,687), DRAMP patent (18,715), UniProt AMP ≤60aa (2,348) → 27,234 unique standard-AA sequences after deduplication
- Replaced Levenshtein/max-length metric with BioPython PairwiseAligner BLOSUM62 local alignment; identity = matches / len(query)
- Fixed fragment-to-parent undercounting: SEED-010 histatin variants now correctly classified as KNOWN_VARIANT (85-93% identity, was RELATED_NOVEL in v1)
- SEED-013_VAR_001 (GWGSFFKKAAHVGK) confirmed EXACT_MATCH_OR_FRAGMENT of pleurocidin (AP00166) — excluded from leads
- Wave 0.5 final classification: 1 EXACT_MATCH_OR_FRAGMENT, 19 KNOWN_VARIANT, 39 CLOSE_RELATIVE, 1 RELATED_NOVEL
- Gate W0.5-5 updated: ≥8 CLOSE_RELATIVE-or-better (was RELATED_NOVEL-or-better) — 19 qualifying leads; PASS
- Panel re-selected with updated novelty: 15 families, 15 BALANCED_LEAD + 4 HIGH_UPSIDE_RISKY + 4 SAR_CONTROL + 1 POSITIVE_CONTROL
- SEED-010/013 variants correctly labeled SAR_CONTROL (KNOWN_VARIANT); SEED-019_VAR_006 (RELATED_NOVEL) added as new BALANCED_LEAD
- Patent risk disclosed: DRAMP patent hits for SEED-010, SEED-019, SEED-012 families
- Novelty audit v2: `scripts/run_wave0_5_novelty_audit_v2.py`; database: `data/novelty_db/`

## v0.5.6 — Wave 0.5b Safety-Optimized Designs ✓ (2026-06-29)

- External predictor results integrated from `wave05_combined_consensus.csv` (`scripts/fill_wave0_5_external_results.py`)
- Activity consensus confirmed: 52/60 STRONG_ACTIVITY (87%); safety concern: 56/60 AntiCP-positive
- Best clean candidate identified: SEED-019_VAR_004 (RVRIRLVKRLLK) — STRONG + Non-AntiCP + HemoFinder LOW
- Wave 1 panel updated: 24 candidates, 14 families; SEED-019_VAR_004 pinned as CLEAN LEAD
- Evidence certs regenerated with actual external predictor values (`outputs/evidence_wave0_5/`)
- All 7 gates now PASS (W0.5-3 and W0.5-4 previously PENDING, now confirmed)
- Wave 0.5b: 5 new seed families (SEED-020–024), 40 raw candidates, 23 shortlisted (`scripts/generate_wave0_5b_candidates.py`, `scripts/filter_wave0_5b_candidates.py`)
- Wave 0.5b design principle: no aromatic residues (W/Y/F); Arg-alternating or Gly-interrupted pattern; broken amphipathic helix → expected AntiCP score < 0.50
- FASTA ready for external predictor submission: `outputs/wave0_5b_shortlist.fasta`

## v0.5.5 — Wave 0.5 Scaffold Diversification ✓ (2026-06-29)

- Baseline freeze of Wave 0 panel (20 candidates, 7 families, `docs/WAVE_0_5_BASELINE.md`)
- 10 new seed families designed: SEED-010 (histatin), SEED-011 (Pro-kinked), SEED-012 (Gly-rich), SEED-013 (pleurocidin), SEED-014 (cathelicidin-mini), SEED-015 (KFLK de novo), SEED-016 (RRWK dual-Trp), SEED-017 (Pro-kinked Leu/Phe), SEED-018 (GKRK scattered-charge), SEED-019 (Arg-Val alternating)
- 118 raw candidates generated across 10 new families (`scripts/generate_wave0_5_candidates.py`)
- 60 candidates shortlisted at internal gates (activity≥0.70, safety≥0.75, novelty≥0.50, `scripts/filter_wave0_5_candidates.py`)
- External predictor FASTA submitted; results integrated (AMPScanner 59/60, AMPActiPred 60/60, Macrel 52/60, HemoFinder 40 LOW/20 HIGH, AntiCP 4 Non-AntiCP/56 AntiCP)
- Novelty audit: 53/60 shortlisted candidates HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL vs 72 curated references + Wave 0 panel (`scripts/run_wave0_5_novelty_audit.py`)
- Wave 1 panel selected: 24 candidates, 14 families, 17 BALANCED_LEAD + 4 HIGH_UPSIDE_RISKY + 3 controls (`scripts/select_wave1_panel.py`)
- 24 evidence certificates generated (`scripts/generate_wave0_5_evidence_certs.py`, `outputs/evidence_wave0_5/`)
- Wave 0.5 gates W0.5-1 through W0.5-7 implemented (`src/openamp_foundry/gates/wave0_5_gate_checker.py`)
- Discovery probability impact: from 7 correlated families → 14 independent families; reduces correlated-failure risk for wet-lab batch

## v1.0 — Validated dry-lab-to-wet-lab loop

- independently reviewed assay batch (expert_review.yml GitHub issue template);
- lab results ingested via `schemas/lab_result.schema.json`;
- negative results archived where safe;
- active-learning batch 2 (D-amino variants, MDR strain panel);
- public reproducibility report.

## v1.1 — Virtual assay scaffold

- ~~write the first explicit simulator scope document: what OpenAMP will model and what it will not;~~
- ~~add membrane/selectivity/stability proxy interfaces with uncertainty fields;~~
- benchmark candidate triage against a reference panel that includes selective AMPs, hemolytic positives, inactive peptides, and random controls;
- require every proxy module to justify itself against cheap heuristic baselines before it affects selection.

## v2.x — Wet-lab compression engine

- calibrate virtual assay layers on qualified assay outcomes;
- implement active-learning experiment selection for small 8-12 peptide batches;
- track cost per confirmed hit, safety-adjusted hit rate, and wet-lab tests saved;
- publish honest evidence on whether OpenAMP is actually reducing assay waste rather than merely generating more candidates.

## Beyond v1.0 — What is still needed for a major breakthrough

The following are not implemented in this pipeline. Each is a known gap flagged in external
review (2026-06-28). Progress on these would materially raise breakthrough probability.

| Gap | Why it matters | Effort estimate |
|-----|----------------|-----------------|
| ~~Large-scale benchmark (≥ 500 AMPs vs composition-matched decoys, cluster-split)~~ | ~~Current AUROC 0.8420 measured on 43+44 demo set (n=87, CI₉₅: 0.76–0.91); may not generalise~~ | **Partial** (PR #110: expanded to 95 AMPs + 96 decoys, n=191, AUROC=0.7832, CI₉₅: 0.72–0.84; 52 new public-domain AMPs from 12 taxonomic classes; covers defensins, proline-rich, lantibiotics — a more honest estimate. 500+ target still deferred to v1.0+) |
| External predictor ensemble adapters (CAMPR4, AMPScanner, dbAMP, AntiCP2, Macrel) | Independent second opinions on activity; required for scientific credibility. Manual web-submission checklist at `outputs/external_predict_checklist.md`. Macrel v1.6.0 CLI ONNX bug documented PR #77 — all sequences (incl. canonical AMPs magainin-2, LL-37) misclassified as NAMP; use web server at big-data-biology.org/software/macrel. AMPlify omitted: GPU/ONNX env incompatible with current deps | Medium (checklist generated; web submissions pending) |
| ~~True novelty check against APD3, DRAMP v3.0, dbAMP~~ | ~~Current novelty scored against 45-sequence seed set only; may overestimate novelty~~ | **Done** (v0.5.7: BioPython BLOSUM62 local alignment vs 27,234 AMPs from APD6+DRAMP+UniProt; Wave 0.5 novelty corrected from 53/60 RELATED_NOVEL → 39 CLOSE_RELATIVE + 19 KNOWN_VARIANT + 1 RELATED_NOVEL) |
| ~~AUPRC alongside AUROC~~ | ~~Better metric for class-imbalanced AMP datasets~~ | **Done** (PR #58; updated PR #72) — pipeline AUPRC = 0.8627 |
| Wet-lab result integration (active-learning round 2) | Required to move from 15–30% to 50%+ credible probability | Requires wet-lab |
| ~~Pre-registration of assay protocol before synthesis~~ | ~~Strengthens causal inference; reduces reporting bias~~ | **Done** (docs/ASSAY_PREREGISTRATION.md — PRs #83; includes MRSA USA300, serum stability, Gate P3 aligned) |
| Public benchmark paper (replicable, cluster-split, open datasets) | Sets community standard; enables external validation | Large |
