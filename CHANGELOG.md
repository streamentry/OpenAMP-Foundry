# Changelog

All notable changes to OpenAMP Foundry are documented here.

---

## [Unreleased — Dedicated Hemolysis Risk Scorer] — 2026-07-01

### v0.5.10 — Dedicated Hemolysis Risk Scorer

- **`scoring/hemolysis.py`**: standalone hemolysis risk score combining four
  empirically-validated components from the selectivity benchmark:
  - Synthesis difficulty (1 - synthesis_feasibility_score) — detection AUROC=0.8027
  - Cationic-on-hydrophobic-face fraction (helix_wheel_h_face_cationic_fraction) — AUROC=0.7585
  - Cysteine fraction (beta-sheet defensin/protegrin class) — AUROC=0.7500
  - Aromatic fraction (Trp/Phe/Tyr intercalation) — AUROC=0.8299
- **Combined detection AUROC=0.9218** (CI₉₅: 0.82-0.99) — first statistically
  significant hemolysis detector in the pipeline. CI lower bound (0.82) clears
  the 0.5 threshold with wide margin.
- **Integrated into selectivity benchmark**: `hemolysis_risk` added as a
  risk-direction score (higher = more risk; detection AUROC = raw AUROC, not 1-AUROC)
- **Integrated into expert composite**: `hemolysis_safety` component (weight 0.10,
  = 1 - hemolysis_risk_score). Expert weights rebalanced: activity 0.22→0.20,
  selectivity 0.22→0.20, safety 0.18→0.15, synthesis 0.13→0.12, motif_novelty
  0.12→0.10.
- **Expert composite detection AUROC improved**: 0.5119 → 0.6429 on hemolysis
  detection (not significant, CI lo=0.45, but trend is correct)
- **Safety scorer UNCHANGED**: no modification to `safety_score()`. Standard
  AUROC remains 0.7832 (CI: 0.72-0.84). The hemolysis risk score is a
  complementary signal, not a replacement.
- **Expert ablation updated**: `hemolysis_safety` is anti-signal on AMP-vs-decoy
  (AUROC=0.3285) — expected, since real AMPs have higher hemolysis risk than
  random decoys. This confirms the component is measuring a within-AMP property,
  not an AMP-vs-non-AMP property.
- **15 new tests** in `test_hemolysis_risk.py`; 3 new tests in
  `test_selectivity_benchmark.py`; updated `test_expert_ablation.py`;
  1471 total tests (7 skipped)

**Key finding:** The safety scorer's hemolysis blind spot (detection AUROC=0.3844)
can be substantially addressed by a dedicated 4-component risk score that
combines synthesis difficulty, face cationic leakage, cysteine content, and
aromatic density. The combined score achieves detection AUROC=0.9218 — the
first pipeline score with a statistically significant hemolysis signal.

**Honest limitation:** The reference set is small (n=35: 14 hemolytic vs 21
selective). The CI is wide (0.82-0.99). Melittin's risk score (0.13) remains
modest because its bent-helix hemolysis mechanism is not fully captured by 1D
features. Hemolysis must still be assayed experimentally for every candidate.

---

## [Unreleased — Within-AMP Selectivity Benchmark] — 2026-07-01

### v0.5.9 — Within-AMP Selectivity Benchmark

- **Hemolysis reference dataset**: 42 known AMPs with literature HC50 values
  (`examples/validation/hemolysis_reference.csv`): 14 HEMOLYTIC (HC50 < 25 µg/mL),
  21 SELECTIVE (HC50 >= 100 µg/mL), 7 BORDER (25-100 µg/mL)
- **`run_selectivity_benchmark()`** in `benchmark/retrospective.py`: tests whether
  pipeline scorers can distinguish hemolytic from selective AMPs — the within-AMP
  ranking task that the expert ablation identified as the correct test for
  safety/selectivity/synthesis components
- **`bench selectivity` CLI command** + `make bench-selectivity` Makefile target
- **18 new tests** in `test_selectivity_benchmark.py`; 1453 total tests

**Key findings:**

1. Safety scorer FAILS hemolysis detection (detection AUROC=0.3844, CI lo=0.26).
   All 14 hemolytic AMPs score safety >= 0.8. Melittin blind spot confirmed
   quantitatively.
2. Selectivity proxy FAILS hemolysis detection (detection AUROC=0.4133, CI lo=0.28).
   Charge/GRAVY heuristic insufficient.
3. Synthesis feasibility is the only significant hemolysis risk detector
   (detection AUROC=0.8027, CI lo=0.63) — incidental correlation via cysteine
   content and repeat runs in hemolytic AMPs.
4. Expert composite is better than ensemble on hemolysis detection (0.5119 vs
   0.3486) but not significant (CI includes 0.5) at n=14 vs n=21.
5. Activity scorer is anti-selective (detection AUROC=0.34): ranks hemolytic
   AMPs higher due to stronger amphipathic helices. Ensemble inherits this bias.

---

## [Unreleased — Pre-synthesis Quality Sprint] — 2026-06

**Status:** Pipeline frozen for synthesis batch ordering. All changes below were quality
improvements made before committing the ~$10k wet-lab synthesis budget.

### Latest fixes (PRs #61–72)

- **PR #72** — Face segregation bonus in `activity_likeness_score()`: adds
  `helix_wheel_amphipathic_score × 0.05` as an eighth scoring term capturing how well
  hydrophobic and cationic residues are segregated onto opposite helical faces (complementary
  to μH which measures total moment magnitude); pre-clamp ceiling becomes 1.02 (clamped to
  1.0 by final `clamp01()`); benchmark improvements: pipeline AUROC 0.8348→**0.8420**
  (+0.0072), phase3 AUROC 0.8126→**0.8266** (+0.0140), pipeline AUPRC 0.8443→0.8627,
  phase3 AUPRC 0.8357→0.8479; retrospective test sentinels updated (phase3 ≥0.81, <0.84;
  pipeline remains the config-identity reference); `max_disagreement` raised from 0.40→0.45
  in both pipeline.yaml and phase3.yaml because face_segregation_bonus raises SEED-008
  Trp-rich activity scores by ~0.03, pushing their disagreement from ~0.40 to ~0.43 (no
  non-Trp-rich candidate exceeds 0.41, so the new threshold still blocks genuinely uncertain
  candidates); 6 new tests for face_segregation_bonus (zero when key absent, linear scaling,
  max bonus 0.05, anionic guard priority, Magainin-2 improvement); test for score ceiling
  split into 0.97 (no hw key) and 1.0-clamped (with hw=1.0); 1245 tests passing

- **PR #71** — Rotation-invariant helix-wheel face analysis (`helix_wheel_faces()` in
  `features/physchem.py`): uses the hydrophobic moment vector direction to define the
  hydrophobic face for each specific peptide (rotation-invariant, unlike fixed cos(θ≥0)
  splits); computes face contrast, cationic segregation (h_face_cationic_fraction vs
  ph_face_cationic_fraction), and amphipathic_score (normalised [0,1]); all 6 keys added
  to `compute_features()` output as `helix_wheel_*`; pilot panel analysis: SEED-003/005
  show ideal architecture (contrast 2.06/1.94, 0% cationic on H-face), SEED-006/007 good
  (contrast ~0.96-0.98), SEED-008/009 correctly flagged as non-helical (puroindoline
  aromatic anchoring, Bac2A intracellular targeting — expected by design); 13 new tests;
  `make coverage` + `make typecheck` targets added to Makefile; WET_LAB_HANDOFF.md new
  section with per-seed helix-wheel table and mechanism-specific assay interpretation
  matrix; 1237 tests passing
- **PR #70** — Windowed hydrophobic moment (window=11, Eisenberg standard) + anionic charge guard:
  `max_windowed_hydrophobic_moment()` added to `features/physchem.py`; `max_hydrophobic_moment`
  feature now in `compute_features()` output; `activity_likeness_score()` uses
  `max(hydrophobic_moment, max_hydrophobic_moment)` so long-sequence AMPs (magainin-2: 1.51×
  improvement, cecropin-A: 2.90×) get credit for their best helical window rather than a
  diluted full-sequence average; anionic guard returns 0.0 for peptides with
  `charge_density_ph74 < 0.0` (bacterial membrane repulsion; corrects EEIEIEIEIEIEIEE
  receiving 0.42 erroneously); fixed Python eager-evaluation bug in feature dict fallback
  (`dict.get(key, features["k"])` → `if key in features` conditional); 23 new tests covering
  windowed mu_h behaviour, max_hydrophobic_moment in compute_features(), anionic guard cases;
  AUROC pipeline.yaml 0.8047→0.8348, phase3.yaml 0.7846→0.8126; regression sentinel updated
  (≥0.79); config-identity sentinel updated (<0.82, sits between phase3=0.8126 and
  pipeline=0.8348); METHODS.md and DISCOVERY_PREDICTION.md AUROC values updated;
  1223 tests passing
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

---

## [Unreleased — Calibration Intake Module] — 2026-07-04

### v0.5.19 — Calibration Intake Module

- **`openamp_foundry/calibration/intake.py`**: new module
  - `build_calibration_intake_report(panel_csv, results_dir)` joins a pilot
    panel CSV (computational predictions) with a directory of validated lab
    result JSON files (experimental actuals) on `candidate_id`.
  - `write_calibration_intake_json` and `write_calibration_intake_markdown`
    produce machine-readable and human-readable review artifacts.
  - **Honest minimum-cohort-size gate (`MIN_COHORT_SIZE=5`)**: aggregate
    cohort metrics are NOT reported when `n < 5`. Below the gate the metric
    is marked `insufficient_data: True` and no point estimate is produced.
    This prevents small-sample theater.
  - Two pilot cohort metrics: `activity_vs_active_mic` (MIC ≤ 32 µg/mL active)
    and `rich_selectivity_vs_high_hemolysis` (hemolysis ≥ 10% high-risk).
  - Per-candidate join rows expose every prediction column plus aggregated
    actual outcomes. Control failures and orphan lab results surfaced.
- **`cli/commands/reports.py`**: new `_run_calibration_intake` command.
- **`cli/main.py`**: new `calibration-intake` subcommand registered.
- **`examples/lab_results/`**: 5 SYNTHETIC JSON files demonstrating the
  workflow (active hit, inactive candidate, low hemolysis, high hemolysis,
  control failure). All files include a `disclaimer` field that explicitly
  states they are synthetic examples. README in the directory repeats the
  warning prominently.
- **`examples/lab_results_panel.csv`**: 8-candidate synthetic pilot panel.
- **`tests/test_calibration_intake.py`**: 29 tests covering empty panels,
  missing columns, orphan detection, control failure surfacing, cohort
  metric gating (below/equal/above `MIN_COHORT_SIZE`), hemolysis direction
  logic, synthetic-example schema validation, threshold constants.
- **`Makefile`**: `lab-result-intake` and `lab-result-intake-example`
  targets added. Test-count help text updated.
- **Total tests:** 1614 passing (was 1585).

#### Honest limitations

- This module does **NOT** trigger recalibration. It is the intake valve that
  produces a review artifact for a separate, human-reviewed recalibration
  workflow (see `docs/DECISION_RULES.md` and `docs/WAVE2_PLAN.md`).
- Cohort metrics are descriptive only; they do not validate the pipeline, do
  not control for selection bias from the pre-registered shortlist, and must
  not be used to rewrite scoring weights after the fact.
- Synthetic example data is clearly labeled in every JSON file's `disclaimer`
  field and in `examples/lab_results/README.md`. It exists solely to exercise
  the intake workflow end-to-end. When real validated lab results arrive,
  replace the example directory — the pipeline itself does not change.

---

## [Unreleased — Recalibration Policy + Gate] — 2026-07-04

### v0.5.20 — Recalibration Policy + Gate

Pre-registered, machine-readable policy that gates any pipeline recalibration.
This is the missing piece between v0.5.19 calibration-intake (descriptive
join) and a future recalibration engine: the gate now answers the binary
question "may recalibration proceed from this intake report?" with a
verdict that no agent can silently bypass.

**New policy contract — `configs/recalibration_policy.yaml`**

- `minimum_conditions` (7 rules): MIN_COHORT_SIZE, MIN_POSITIVES_IN_COHORT,
  MIN_NEGATIVES_IN_COHORT, POSITIVE_CONTROLS_ALL_PASS,
  NEGATIVE_CONTROLS_ALL_PASS, NO_ORPHAN_LAB_RESULTS, COHORT_METRICS_AVAILABLE.
- `prohibited_actions` (5 permanent floors): NO_TOXICITY_RELAXATION,
  NO_HEMOLYSIS_RELAXATION, NO_NOVELTY_RELAXATION,
  NO_DANGEROUS_PATHGEN_OPTIMIZATION, NO_POST_HOC_SUCCESS_REDEFINITION.
- `rate_limits` (2 rules): WEIGHT_CHANGE_L1_BUDGET (0.10), COOLDOWN_DAYS (14).
- `required_reviewer_artefacts` (3 artefacts): intake JSON, intake
  Markdown, dated decision log entry.
- `locked_changes` records the lock date for every enforced rule. The
  validator rejects a policy file that lists an enforced rule without a
  matching `locked_changes` entry.

**New modules**

- `openamp_foundry/calibration/policy.py`: `load_recalibration_policy`
  parses, validates, and exposes the policy. Removes or relocations of
  any canonical prohibited action cause `PolicyLoadError` at load time.
- `openamp_foundry/calibration/recalibration_gate.py`:
  `evaluate_recalibration_gate` consumes an intake report + a loaded
  policy and returns a `GateVerdict`. Writes JSON and Markdown via
  `write_gate_verdict_json` and `write_gate_verdict_markdown`.
- `openamp_foundry/cli/commands/reports.py`: `_run_recalibration_gate`.
- `cli/main.py`: `recalibration-gate` subcommand registered.
  Exit code 0 when `may_recalibrate=true`, 3 when false, 2 on input error.

**Makefile targets**

- `recalibration-gate-example`: runs the gate on the synthetic intake
  report. Expect exit code 3 (cohort size too small, one positive
  control failed, all required reviewer artefacts missing).
- `recalibration-gate INTAKE=... [DATE=YYYY-MM-DD] [PREV=YYYY-MM-DD] [L1=float]`
  for real intake reports.

**Tests — 39 new, total 1647 passing (was 1614)**

- `tests/test_recalibration_gate.py` covers:
  - policy loader happy path + every rejection mode (missing fields,
    duplicate ids, unlocked rules, missing canonical prohibited
    actions, missing locked_changes entries, bad types);
  - gate evaluator with synthetic intake reports for every minimum
    condition (cohort size, positives, negatives, controls, orphans,
    insufficient metrics);
  - prohibited-action audit always in force;
  - rate-limit status (unknown / ok / exceeded for cooldown + L1 budget);
  - reviewer-artefact status (missing / present based on disk);
  - JSON + Markdown writers produce non-empty, schema-valid output;
  - end-to-end smoke test of the CLI (exit code 3 on synthetic example).

**Documentation**

- `docs/CALIBRATION_POLICY.md` (new): explains the policy, the gate, the
  prohibited-action floor, the rate limits, how to update the policy,
  and how the policy fits the wet-lab compression roadmap.
- `docs/ARCHITECTURE.md`: links the calibration package into the
  wet-lab compression loop.
- `docs/PLAN.md`: marks Phase 5 (active-learning) as gated by this policy.
- `docs/ROADMAP.md`: new v0.5.20 milestone entry.
- `docs/METRICS_CURRENT.md`: new entry in the change log.

**Honest limitations (must read before relying on the gate)**

- The gate **does NOT trigger any weight update**. It only emits a verdict.
- A `may_recalibrate=true` verdict is a **permission**, not a command.
  The decision to apply a weight change still belongs to a human reviewer
  with a dated decision log entry (`docs/DECISION_LOG_<date>.md`).
- The gate evaluates **cohort evidence**, not pipeline calibration
  health. Benchmark regressions are caught by `make validate-scoring`,
  `make bench-triage`, and the selectivity benchmark — not by this
  policy. These checks must keep running independently.
- The synthetic example correctly yields `may_recalibrate=false`. That
  is the expected outcome on tiny synthetic data and is itself a
  useful sanity check that the gate is enforcing the cohort floor.
- The five canonical prohibited actions are duplicated from
  `AGENTS.md` and `MISSION.md`. The validator rejects a policy file
  that drops any of them; the human source documents must be updated
  in lockstep before the policy file can be edited.
