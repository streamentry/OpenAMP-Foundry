# Changelog

All notable changes to OpenAMP Foundry are documented here.

---

## [Unreleased — Pre-synthesis Quality Sprint] — 2026-06

**Status:** Pipeline frozen for synthesis batch ordering. All changes below were quality
improvements made before committing the ~$10k wet-lab synthesis budget.

### Latest fixes (PRs #61–69)

- **PR #69** — synthesis_readiness_report.md updated for current 20-candidate pilot panel
  (AUROC 0.8047; 43 AMPs; 6 seed families; all output files regenerated: presynth_qc_report.md,
  diversity_report.md, gold_standard_calibration.md); external predictor gate marked PENDING for
  new panel; SEED-007 HIGH SPPS difficulty noted; SEED-008 photolability warning added;
  serum stability caveats from PR #68 incorporated; synthesis decision tree and 6-candidate
  minimal diverse panel recommendation updated; stale reference to old 16-candidate
  confident_panel.csv removed
- **PR #68** — Stage 3 serum stability table updated with actual pilot-panel seed families
  (SEED-003/005/006/007/008/009; old SEED-001/002/004 removed as excluded at earlier gates);
  probability 28–42% → 30–46% (short/Trp-rich model correction; actual pilot-panel data);
  SEED-006/SEED-007 gate labels corrected from Pass to Borderline (scores 0.61–0.67 below
  ≥0.70 threshold); SEED-007 slot count corrected 4→5; Root Cause Analysis updated to
  acknowledge model uncertainty before citing <40 min estimate; early serum screening protocol
  added with time points, concentration, reference control; WET_LAB_HANDOFF.md new section
  with SEED-003/005/008 stability model limitation table
- **PR #67** — JSONL error handling in `pilot-panel` CLI (CRITICAL: bare crash on malformed
  line → structured error with line number and preview); synthesis-order CSV header validation;
  `validate-scoring` stdout now includes `n_positives`, `n_negatives`, `benchmark_type`, `auprc`;
  `check_sequence()` validates canonical amino acids (all 20 standard AAs) before QC;
  WAVE2_PLAN.md SEED-008 Trp mechanism divergence note; CHANGELOG updated for PRs #61–66
- **PR #66** — Removed duplicate validation entry REF-GIG-001 (magainin-2 = REF-MAG-001 counted
  twice); corrected AUROC 0.8086→0.8047 (pipeline), 0.7890→0.7846 (phase3); config-identity
  sentinel tightened from `< 0.83` to `< 0.795`; orphaned DECOY-GIG-001 removed from
  scrambled_decoys.csv; default `recall_ks` updated to [10, 20, 43]; 1191 tests passing
- **PR #65** — Trp-weighted aromatic bonus (1.5× Trp vs Phe/Tyr, PR #65); safety `abs()` bug fix
  (negative charge_density does not cause hemolysis); Eisenberg scale comment corrected; synthesis
  pool regenerated (SEED-006: 11→10, SEED-009: 18→19); AUROC 0.8164→0.8086
- **PR #64** — Stale docs corrected: max_disagreement 0.30→0.40 for phase3.yaml in WET_LAB_HANDOFF;
  reference set "45-sequence" → "72-sequence"; SEED-005 exemplar corrected (KRFFKKIGSALKFA →
  seed KRLFKKIGSALKFL with note about VAR_009)
- **PR #63** — Phase3.yaml AUROC regression test added: gate (>0.70), sentinel (≥0.75), config-
  identity check (<0.83 then <0.795 in PR #66); `make validate-scoring-phase3` Makefile target
- **PR #62** — Discovery probability updated to 10–18% (6 confirmed scaffold families; honest
  corrected estimate replacing prior over-confident numbers)
- **PR #61** — CRITICAL FIX: SEED-008 (puroindoline-a, Trp-rich) reinstated in synthesis pool
  after Boman-scale artifact diagnosis; all 10 seeds generated; max_disagreement raised to 0.40
  for both configs to accommodate mechanism-divergent Trp-rich scaffolds; SEED-004 correctly
  excluded by safety gate; 6 mechanism-diverse scaffold families confirmed

### Added (earlier sprint)

- `docs/WET_LAB_HANDOFF.md` — score interpretation table, synthesis decision thresholds,
  per-flag QC remediation guide, MIC/hemolysis assay protocols, troubleshooting section
- `configs/phase3.yaml` now validated by CI at the same level as `pipeline.yaml`
  (selection keys, weights, filters all pinned in test_config.py)
- `test_compute_features_supplies_synthesis_feasibility_keys` — integration contract test
  ensuring `compute_features()` always returns the three keys accessed without `.get()` by
  `synthesis_feasibility_score()` (`length`, `longest_repeat_run`, `cysteine_fraction`)
- `SynthQC.to_dict()` fully covered with 16 tests (key presence, types, value round-trips)
- `presynth-qc` CLI command now has 4 integration tests (exit code, file creation, flag
  detection, summary table content)
- `validate_json_schema()` error paths covered: ValidationError, missing required field,
  wrong type, FileNotFoundError on bad schema path
- `synthesis_feasibility_score()` missing-key tests document the direct dict-access contract
- `check_panel()` missing-column error tests for `candidate_id` and `sequence`
- `make ci` target: runs `lint` then `test` in one command

### Fixed (earlier sprint)

- `ensemble_score()` no longer crashes with KeyError for missing weight keys; emits
  `UserWarning` listing missing names and defaults to 0.0 (PR #24)
- Eligibility filter: `>= min_novelty` boundary confirmed and tested (PR #24)
- `load_candidates_csv()` validates CSV header before iterating rows; raises descriptive
  `ValueError` instead of bare `KeyError` (PR #25)
- Disagreement gate (`max_disagreement`) added to eligibility filter in `pipeline.py`
  (PR #25); `pipeline.yaml: 0.40`, `phase3.yaml: 0.40` (unified in PR #61)
- `WET_LAB_HANDOFF.md` μH boundary table corrected to `> 0.55` (matching code) vs
  closed interval; phase3 disagreement threshold correctly set to 0.40 in PR #61

### Tests

- **1191 tests passing** (up from initial ~400 at start of sprint; ~814 after earlier sprint)
- All ruff lint checks passing

---

## [v0.4.0] — Boman Scorer + Safety Stratification

- Added Boman index scorer (`scoring/boman.py`)
- Added hydrophobic moment (μH) to physchem features
- Added μH-based hemolysis stratification to pre-synthesis QC report
- Added model disagreement score (`|activity_likeness − boman_activity|`)
- 89 lab-ready AMP nominees with evidence certificates

## [v0.3.0] — Pre-Synthesis QC + Pilot Panel

- `qc/presynth_check.py`: full SPPS QC report (MW, pI, charge, trypsin sites, deamidation,
  aggregation risk, UV chromophore, formulation notes)
- `pilot-panel` CLI command: 20-candidate first-synthesis-wave selector
- Bootstrap AUROC confidence intervals for benchmark results
- Gold-standard calibration check against known-active AMP panel

## [v0.2.0] — Confidence Gaps + Benchmarking

- Benchmark leakage detection (`bench leakage`)
- Run manifest with input file hashes and config snapshot
- Standard AUROC benchmark gate (AUROC = 0.8037 on held-out positives)
- Evidence certificates (JSON-schema-validated) for each nominated candidate

## [v0.1.0] — Initial Pipeline

- Template mutation generator
- Physchem feature extraction (length, charge, hydrophobicity, aromatic fraction, etc.)
- Activity likeness, safety, synthesis feasibility, novelty scoring
- Ensemble scoring with configurable weights
- JSONL output with per-candidate `selected` field
- `pipeline.yaml` and `phase3.yaml` configs
