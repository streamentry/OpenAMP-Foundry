# Changelog

All notable changes to OpenAMP Foundry are documented here.

---

## [Unreleased — Pre-synthesis Quality Sprint] — 2026-06

**Status:** Pipeline frozen for synthesis batch ordering. All changes below were quality
improvements made before committing the ~$10k wet-lab synthesis budget.

### Added

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

### Fixed

- `ensemble_score()` no longer crashes with KeyError for missing weight keys; emits
  `UserWarning` listing missing names and defaults to 0.0 (PR #24)
- Eligibility filter: `>= min_novelty` boundary confirmed and tested (PR #24)
- `load_candidates_csv()` validates CSV header before iterating rows; raises descriptive
  `ValueError` instead of bare `KeyError` (PR #25)
- Disagreement gate (`max_disagreement`) added to eligibility filter in `pipeline.py`
  (PR #25); `pipeline.yaml: 0.40`, `phase3.yaml: 0.30`
- `WET_LAB_HANDOFF.md` μH boundary table corrected to `> 0.55` (matching code) vs
  closed interval; phase3 disagreement threshold (0.30) explicitly named in troubleshooting

### Tests

- **814 tests passing** (up from initial ~400 at start of sprint)
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
