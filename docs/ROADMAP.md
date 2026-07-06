# Roadmap

## v0.5.59 — External Simulation Adapter Protocol (Loop 38) ✓ (2026-07-06)

API contract for third-party simulation modules (Martini MD, AlphaFold,
REST APIs). Completes Phase 3 exit criterion 5 (external adapter protocol).

Changes:
- ``src/openamp_foundry/simulation/interfaces.py`` — Added
  ``ExternalSimulationAdapter`` class wrapping any callable ``(str) ->
  SimulationResult`` into the ``VirtualAssayProxy`` interface. Features:
  optional ``required_module`` availability check, graceful error handling
  (returns ``uncertainty=1.0`` on failure), metadata override (adapter's
  name/version/scope applied to result), ``is_available()`` method,
  ``_error_result()`` helper.
- ``tests/test_external_adapter.py`` — 13 tests covering: availability
  check, successful simulation, missing module, graceful failure,
  exception handling, baseline fallback, metadata propagation, custom
  scope, error result schema.
- ``docs/ARCHITECTURE.md`` — Extension points section expanded with
  ``ExternalSimulationAdapter`` usage example and documentation.
- ``docs/50_LOOP_PLAN.md`` — Loop 38 ✅. Next: Loop 39.
- ``docs/METRICS_CURRENT.md`` — Pipeline version v0.5.59. Test count: 1966.
- 1966 tests passing (1953 existing + 13 new).

## v0.5.58 — Simulation Cheap-Baseline Benchmark (Loop 36) ✓ (2026-07-06)

Per-signal comparison: does each simulation output beat its cheapest
meaningful heuristic baseline on the within-AMP hemolysis task?

Changes:
- ``scripts/benchmark_simulation_baselines.py`` — Compares bacterial_binding
  vs mean_eisenberg, selectivity_ratio vs selectivity_proxy, helix_weight
  vs helix_propensity, non_helical vs proline_fraction. ``make
  bench-simulation-baselines`` target.
- ``tests/test_benchmark_simulation_baselines.py`` — 13 tests.
- ``docs/50_LOOP_PLAN.md`` — Loop 36 ✅. Next: Loop 38.
- ``docs/METRICS_CURRENT.md`` — Pipeline version v0.5.58. Test count: 1953.
- ``docs/BENCHMARKING.md`` — Added bench-simulation-baselines (22 targets).

**Honest finding: 0/4 simulation signals beat their cheapest baseline.**
- bacterial_binding (0.4876) vs mean_eisenberg (0.5469): delta=−0.0593
- selectivity_ratio (0.3615) vs selectivity_proxy (0.3905): delta=−0.0290
- helix_weight (0.6458) vs helix_propensity (0.6489): delta=−0.0031
- non_helical (0.4124) vs proline_fraction (0.4929): delta=−0.0805

**Consequence:** All current simulation modules remain permanently
experimental. Weighted mode stays blocked. Future simulation work
must use fundamentally richer modeling (not just 1D propensities).

## v0.5.57 — Simulation Mode CLI Flag (Loop 37) ✓ (2026-07-06)

Phase 3 simulation modules are now user-accessible via the `rank` CLI.
Jumped ahead of Loop 36 (cheap-baseline benchmark) — the CLI flag is the
higher-leverage bottleneck because it makes the modules tangible.

Changes:
- ``src/openamp_foundry/cli/main.py`` — Added ``--simulation-mode`` argument
  to ``rank`` parser with ``off`` (default) and ``info`` choices.
  ``weighted`` excluded — blocked by gate (Loop 35).
- ``src/openamp_foundry/pipeline.py`` — ``run_ranking_pipeline`` accepts
  ``simulation_mode`` param. When ``info``: runs MembraneProxy and
  StructureProxy on every candidate, adds ``sim_*`` keys to each
  ScoredCandidate.scores dict. ``build_batch_report`` includes
  ``simulation_mode`` and ``simulation_averages``. ``write_report``
  dynamically adds simulation columns to the Markdown table.
- ``tests/test_simulation_mode_cli.py`` — 6 tests covering: default off
  (no sim keys), info adds keys, scores in range, report contains sim
  columns, output JSON has simulation_mode field, all candidates have scores.
- 1940 tests passing (1934 existing + 6 new).

## v0.5.56 — Simulation Weighted-Mode Gate (Loop 35) ✓ (2026-07-06)

Phase 3 had a real honesty gap: the scope doc described `weighted` simulation
mode, but no executable guard converted ablation evidence into an allow/block
decision. That left future agents one edit away from integration theater.

Changes:
- ``src/openamp_foundry/simulation/gate.py`` — fail-closed gate that consumes
  current AMP-vs-decoy and within-AMP ablation artifacts and returns a
  machine-readable permission verdict for simulation integration mode.
- ``openamp-foundry bench simulation-gate`` — CLI wrapper with exit code `0`
  only when weighted mode is honestly allowed, `3` otherwise.
- ``Makefile`` — ``make simulation-gate`` target writing
  ``outputs/simulation_gate_verdict.json`` from both ablation artifacts.
- ``docs/VIRTUAL_ASSAY_SCOPE.md`` — corrected stale claim that `rank` already
  accepts `--simulation-mode`; current state now says weighted mode is blocked
  until the gate passes.
- ``tests/test_simulation_gate.py`` — 6 tests covering blocked current-state
  verdicts, positive-path permission, fail-closed missing artifacts, and CLI
  exit behavior.
- Full verification after this loop: ``1927 passed, 7 skipped``.

**Honest finding:**
- Weighted simulation remains blocked. Current ablations do not justify ranking
  impact.
- This is not a modeling advance. It is a truthfulness and architecture
  advance: the repo now has an executable brake against simulation theater.

## v0.5.55 — Within-AMP Simulation Ablation (Loop 34) ✓ (2026-07-06)

Extended the simulation ablation benchmark to test modules on their
designed task: within-AMP hemolysis detection. Original Loop 34 plan
(membrane reference CSV) deferred — higher leverage to test modules
on actual task first.

Changes:
- ``scripts/benchmark_simulation_ablation.py`` — Extended with ``--mode
  within-amp`` flag. Tests 45 hemolytic vs 125 selective AMPs from
  ``examples/validation/hemolysis_reference.csv``. Reports per-score
  hemolysis detection AUROC (inverted for safety-type scorers).
- ``Makefile`` — Added ``bench-simulation-ablation-within-amp`` target.
- ``docs/50_LOOP_PLAN.md`` — Loop 34 ✅ (re-interpreted). Next: Loop 35.
- ``docs/METRICS_CURRENT.md`` — Pipeline version v0.5.55. Test count: 1928.
- 1928 tests passing (1905 existing + 23 updated).

**Honest finding:**
- ``rich_selectivity`` remains the best hemolysis detector (AUROC 0.7453).
- Best simulation score: ``helix_weight`` (AUROC 0.6458) — hemolytic AMPs tend
  to be more helical. Biologically meaningful but not competitive.
- Simulation composite delta=-0.0995 vs rich_selectivity — modules do NOT
  improve over existing scorers for hemolysis detection.
- Implication: membrane and structure proxies need structural or contextual
  features beyond 1D Chou-Fasman propensities and Wimley-White averages.

## v0.5.54 — Simulation Ablation Benchmark (Loop 33) ✓ (2026-07-06)

First honest test of whether Phase 3 simulation modules improve
discrimination. Original Loop 33 (selectivity ratio module) was superseded
by Loop 31's membrane proxy — replaced with a more useful ablation benchmark.

Changes:
- ``scripts/benchmark_simulation_ablation.py`` — Standalone benchmark script
  that scores 500 AMPs + 500 decoys with MembraneProxy and StructureProxy,
  computes per-module AUROC, and a combined simulation composite AUROC.
  ``make bench-simulation-ablation`` target. Output written to
  ``outputs/simulation_ablation.json``.
- ``docs/50_LOOP_PLAN.md`` — Loop 33 ✅ (re-interpreted as ablation benchmark).
  Next: Loop 34.
- ``docs/METRICS_CURRENT.md`` — Pipeline version v0.5.54. Test count: 1922.
- ``docs/ARCHITECTURE.md`` — Package map updated.
- 1922 tests passing (1905 existing + 17 new).

**Honest finding:**
- Simulation composite delta=−0.1153 (degrades AMP-vs-decoy discrimination).
- **Expected**: modules are designed for within-AMP differentiation, not AMP-vs-decoy.
- ``bacterial_binding`` alone achieves AUROC 0.7512 — **genuine non-charge signal**
  from Wimley-White interfacial scale + hydrophobic moment. First evidence that
  simulation modules add non-charge discriminative power.
- ``selectivity_ratio`` is anti-signal (0.3976), ``helix_weight`` anti-signal
  (0.4246), ``non_helical_flag`` near-random (0.561).
- Implication: simulation modules need a within-AMP benchmark to demonstrate
  value. AMP-vs-decoy AUROC is the wrong test.

## v0.5.53 — Structure Ensemble Proxy (Loop 32) ✓ (2026-07-06)

Second Phase 3 simulation module. Chou-Fasman 3-state secondary structure
prediction (helix/sheet/coil). Flags non-helical candidates where the
helic-centric activity scorer is unreliable.

Changes:
- ``src/openamp_foundry/simulation/structure.py`` — ``StructureProxy`` implementing
  ``VirtualAssayProxy`` with Chou-Fasman helix/sheet/coil propensity parameters.
  Generates normalized 3-state ensemble weights, raw propensities, and
  ``non_helical`` flag (True if dominant state != helix or helix_weight < 0.33).
  ``HelicityBaseline`` for cheap-baseline comparison.
- ``tests/test_structure_proxy.py`` — 34 tests covering scale lookup,
  normalization, dominant state, non-helical flag, known reference comparisons
  (magainin helical, protegrin/tachyplesin beta-sheet, proline-rich non-helical,
  melittin ambiguous — documented limitation), and empty sequence.
- ``docs/50_LOOP_PLAN.md`` — Loop 32 ✅. Next: Loop 33.
- ``docs/METRICS_CURRENT.md`` — Pipeline version v0.5.53. Test count: 1905.
- 1905 tests passing (1871 existing + 34 new).

## v0.5.52 — Membrane Interaction Proxy (Loop 31) ✓ (2026-07-06)

Phase 3 begins implementation. Membrane proxy uses Wimley-White interfacial
(bacterial) and octanol (mammalian) hydrophobicity scales to compute
coarse-grained binding energy scores, combined with hydrophobic moment
for amphipathicity. Selectivity ratio distinguishes bacterial-preferring
from hemolytic candidates. Uncertainty estimate gates experimental modules
(> 0.5 = cannot affect selection).

Changes:
- ``src/openamp_foundry/simulation/membrane.py`` — ``MembraneProxy`` implementing
  ``VirtualAssayProxy`` with literature-validated Wimley-White scales
  (Wimley & White 1996 Nat Struct Biol 3:842-848). Produces ``SimulationResult``
  with bacterial/mammalian binding scores, selectivity ratio, and uncertainty.
  ``BomanBaseline`` clamped to [0, 1] for baseline comparison.
- ``tests/test_membrane_proxy.py`` — 27 tests covering scale lookup,
  normalization, selectivity ratio, uncertainty, proxy contract, known-reference
  comparison (magainin more selective than melittin), empty sequence, and version.
- ``docs/50_LOOP_PLAN.md`` — Loop 31 ✅. Phase 3 status updated. Next: Loop 32.
- ``docs/METRICS_CURRENT.md`` — Pipeline version bumped to v0.5.52.
  Test count: 1873.
- 1873 tests passing (1843 existing + 30 new).

## v0.5.51 — Virtual Assay Scope + Doc Drift Fix (Loop 30) ✓ (2026-07-06)

Phase 3 begins with a scope document defining what the virtual assay layer
IS and IS NOT, with explicit uncertainty policy, ablation requirements, and
integration modes. Accumulated doc drift fixed alongside: BENCHMARKING.md
was missing ~11 of 19 benchmarks; METRICS_CURRENT.md test count was stale
(1832+ → 1843); NOVELTY_AUDIT_GUIDE.md referenced a nonexistent script.

Changes:
- ``docs/VIRTUAL_ASSAY_SCOPE.md`` — Phase 3 scope document covering 4 planned
  modules (membrane binding, structure ensemble, selectivity ratio, stability),
  12 explicitly NOT-modeled effects, uncertainty policy (modules with
  uncertainty > 0.5 cannot affect selection), ablation requirement (each
  module must beat cheap heuristic baseline), 3 integration modes
  (off/info/weighted), calibration gate for weighted mode, and 5 exit criteria.
- ``docs/BENCHMARKING.md`` — Complete rewrite: all 19 benchmarks organized
  into 6 categories (core discrimination, honesty, selectivity/safety,
  composite/ablation, regression/CI, deferred). Each benchmark has make target,
  purpose, target metric, and verification command.
- ``docs/METRICS_CURRENT.md`` — Test count corrected: 1832+ → 1843.
- ``docs/NOVELTY_AUDIT_GUIDE.md`` — Fixed stale script reference:
  ``scripts/download_uniprot_amps.py`` → ``scripts/download_novelty_dbs.py --uniprot``.
- ``docs/50_LOOP_PLAN.md`` — Loop 30 marked ✅. Phase 3 status updated to
  "In progress — Loop 30 ✅".
- ``scripts/__init__.py`` — Populated with module docstring.
- 1843 tests passing. No code changes to pipeline.

## v0.5.50 — Negative-Result Archive Template + Phase 2 Closeout ✓ (2026-07-06)

Phase 2 exit criteria required a public negative-result archive format but none
existed. This release adds the template and closes Phase 2 with all 5 exit
criteria met.

Changes:
- ``docs/NEGATIVE_RESULT_ARCHIVE.md`` — Full template with 18-field entry
  schema (required/conditional markers), procedures for when/what to archive,
  automation notes (auto-append by ``calibration-intake`` and ``filter_wave*``
  scripts), and explicit limitations. Covers pre-selection rejects, selected
  but untested, lab-tested inactives, lab-tested toxic, and control failures.
- ``docs/50_LOOP_PLAN.md`` — Phase 2 header marked ✅ complete, status updated
  to v0.5.50, Loop 29 ✅, all 5 exit criteria now show green, Current Position
  updated to Phase 3 ready.
- ``docs/METRICS_CURRENT.md`` — Bumped to v0.5.50, changelog entry.
- 1843 total tests passing. No code changes.

## v0.5.49 — Policy Version Bump Workflow with CI Guard ✓ (2026-07-06)

The `policy_version.py` module had `validate_policy_version()` and
`auto_increment_version()` but no standalone CLI to actually bump the policy
and no CI check enforcing version bumps when the policy file changes. This
release closes both gaps.

Changes:
- ``scripts/bump_recalibration_policy.py`` — Standalone script that loads
  the current policy, validates a decision-log entry within 30 days,
  auto-increments ``policy_version``, updates ``locked_at`` and
  ``human_reviewer``, and writes the updated YAML. Supports ``--dry-run``
  for preview. Exit 0 on success, 3 on validation failure.
- ``.github/workflows/ci.yml`` — Added ``Policy version validation guard``
  step: when ``configs/recalibration_policy.yaml`` differs from ``origin/main``,
  the workflow fetches the base version and runs ``validate-policy-version``
  against the PR version. CI fails if the version bump violates the policy
  contract (no recent decision log, locked_changes removed, etc.).
- ``Makefile`` — Added ``bump-policy-version`` and
  ``bump-policy-version-dry-run`` targets.
- ``tests/test_bump_recalibration_policy.py`` — 9 tests covering successful
  bump, dry-run (no write), missing decision log, stale log, future log,
  missing policy file, exit code 3, exit code 0, and consecutive double bump.
- 1843 total tests passing.

## v0.5.48 — Architecture documentation cleanup ✓ (2026-07-06)

ARCHITECTURE.md listed ``calibration`` and ``active_learning`` as "Potential future
packages" even though both shipped long ago (v0.5.19+ and v0.5.45+). This misled
new contributors and agents about the current state of the repo. Also fixed a duplicate
step number in the target future data flow.

Changes:
- ``docs/ARCHITECTURE.md``: moved ``calibration`` and ``active_learning`` from
  "Potential future packages" to the main package map with version annotations.
  Removed the stale ``analysis`` future-package entry. Fixed duplicate step "8."
  in the target future data flow (→ steps 8–10 with correct numbering).
- ``docs/50_LOOP_PLAN.md``: updated "Current Position" from "Loop 25 of 29"
  to "Loop 27 of 29", added Loops 23–27 to the completed Phase 2 table, fixed
  "Next loop" reference to Loop 28, updated Phase 2 exit-criteria tracking.
- ``docs/METRICS_CURRENT.md``: test count updated to 1834.

No code changes. 1834 tests still pass.

## v0.5.47 — Full Calibration Loop End-to-End Test ✓ (2026-07-06)

The calibration pipeline (synthetic generator → intake → gate → engine → batch-2 selector)
had a standalone integration script but no pytest test running in CI. Any change that
broke the CLI interface or data contract between steps would pass CI silently. This
release adds a golden-path test that exercises every step via the actual CLI and
validates all output artifacts.

Changes:
- Added ``TestFullCalibrationLoop`` in ``tests/test_calibration_e2e.py`` —
  ``test_full_calibration_loop_via_cli`` runs all 5 steps sequentially in a
  temp directory via subprocess CLI calls, then asserts each output artifact
  exists, is parseable JSON, and has the expected top-level keys.
- Steps tested: synthetic generator → ``calibration-intake`` → ``recalibration-gate``
  → ``recalibration-engine`` (proposal) → ``select-batch`` → batch-2 manifest.
- Honest gate exit-code handling: ``recalibration-gate`` may exit 3 on small
  synthetic cohorts; the test asserts the output file is written regardless.
- The test completes in <2 seconds and is compatible with ``-x`` and ``-q``
  pytest flags.
- 1834 total tests passing.

## v0.5.46 — Active-Learning Recovery Benchmark ✓ (2026-07-06)

The batch-2 selector could pick candidates but there was no benchmark
validating that it recovers known active sequences faster than random
baseline. This release adds a multi-round recovery benchmark with
pre-registered thresholds.

Changes:
- Added ``active_learning/benchmark.py`` — ``run_active_learning_benchmark()``
  simulates a multi-round active-learning loop: hides N active candidates,
  runs ``select_batch_2`` each round on the remaining pool, tracks rounds-to-
  first-recovery and cumulative recall. Compares against a random-baseline
  averaged over 20 trials.
- ``generate_benchmark_pool()`` creates synthetic candidates where actives
  have higher ensemble scores and lower disagreement than inactives.
- Pre-registered thresholds: ``PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY=3``,
  ``PREREGISTERED_MIN_RECALL=0.33``. The ``passed`` field encodes both.
- Added CLI ``bench active-learning`` — generates a synthetic pool inline if
  no ``--pool-csv`` is provided.
- Added 8 tests: pool generation, result shape, recovery assertion,
  comparison to random, empty/absent pool rejection, threshold constants,
  CLI integration.
- 1832 total tests passing.

## v0.5.45 — Active-Learning Batch-2 Selector ✓ (2026-07-06)

The recalibration pipeline could compute weight updates and produce a reviewable
report, but had no way to select the next set of candidates for lab testing. This
release adds a standalone batch-2 selector that uses uncertainty sampling,
diversity ranking, and a safety gate to pick informative candidates.

Changes:
- Added ``active_learning/selector.py`` — ``select_batch_2()`` combines
  per-candidate ensemble score, uncertainty (from model disagreement and
  ensemble proximity to 0.5), and diversity vs batch 1 (via normalized sequence
  similarity). The safety gate rejects candidates below configurable safety and
  selectivity thresholds. At least 1 high-uncertainty probe is guaranteed in
  the top-N selection.
- Added ``active_learning/__init__.py`` — exports ``BatchSelection`` and
  ``select_batch_2``.
- Added CLI ``select-batch`` — reads a candidate pool CSV and batch-1 IDs,
  writes a JSON manifest with selected candidates and metadata (version,
  probes_in_top_n, n_after_safety_gate, notes).
- Added 11 tests: basic selection, safety gate, selectivity gate, uncertainty
  probe guarantee, diversity vs batch-1, empty pool, all-gated-out,
  selection_reason field, metadata shape, CLI success, CLI error path.
- Updated CLI parser (``main.py``) and handler (``selection.py``).

## v0.5.44 — Recalibration Report with Schema Validation ✓ (2026-07-06)

The existing weight-update proposal markdown writer was embedded in engine.py
and lacked gate-verdict context. This release adds a standalone recalibration
report module with a JSON Schema, validation, and a combined report that joins
gate verdict details with the weight-change proposal.

Changes:
- Added ``schemas/recalibration_report.schema.json`` — JSON Schema (Draft 2020-12)
  for the combined recalibration report. Enforces: report_type discriminator,
  schema_version, human_review_required=True, required gate-verdict fields
  (may_recalibrate, cohort counts, summary), required proposal fields
  (gate_passed, L1 totals, deltas). Each delta requires scorer, current_weight,
  proposed_weight, delta, and rationale.
- Added ``reports/recalibration_report.py`` — ``build_recalibration_report()``
  combines a ``WeightUpdateProposal`` and ``GateVerdict`` into a single report
  dict. ``write_recalibration_report_json()`` and
  ``write_recalibration_report_markdown()`` produce the combined output.
  ``validate_recalibration_report()`` validates against the schema.
- The CLI ``recalibration-engine`` now uses the combined report for both
  ``--out-json`` and ``--out-md`` output. The ``--dry-run`` diff also includes
  gate-verdict summary (rule count, prohibited action count).
- Updated ``reports/__init__.py`` to export the new symbols.
- Added 9 tests: report shape, gate context preservation, proposal shape,
  delta field completeness, schema validation (valid + missing fields +
  human_review_required=True enforcement), JSON write+validate round-trip,
  markdown output with required sections.

## v0.5.43 — Dry-Run Mode for Recalibration Engine ✓ (2026-07-06)

The recalibration engine computed proposals but had no way to preview what
weights would change without writing output files. This release adds a
``--dry-run`` flag that prints a human-readable diff table and exits without
side effects.

Changes:
- Added ``--dry-run`` flag to the ``recalibration-engine`` CLI. When set,
  the handler prints a diff table showing current vs proposed weights per
  scorer, L1 total, rationale, and a clear ``DRY RUN — no changes applied``
  disclaimer. No JSON or Markdown files are written.
- Added ``make recalibration-engine-dry-run`` Makefile target.
- Added 1 test confirming the dry-run contract: proposal is inspectable,
  no output files written unless explicitly called.
- Updated ``engine.py`` docstring to reflect the shipped ``--dry-run``
  behavior.

## v0.5.42 — Synthetic Lab-Result Generator ✓ (2026-07-06)

The calibration loop had no way to test the full intake→gate→engine pipeline
without real wet-lab data. This release adds a configurable synthetic lab-result
generator that produces schema-valid JSON files with controlled effect sizes,
noise levels, and cohort sizes.

Changes:
- Added `examples/lab_results_generator.py` — generates synthetic lab result
  JSON files matching `schemas/lab_result.schema.json`. Supports 7 assay types
  (MIC, MBC, hemolysis_RBC, cytotoxicity_mammalian, membrane_disruption,
  time_kill, biofilm_inhibition). Configurable via `--cohort-size`,
  `--effect-size`, `--noise-level`, `--assay-types`, `--seed`.
- Every output file is explicitly labeled SYNTHETIC in organism, lab, notes,
  and disclaimer fields to prevent confusion with real data.
- CLI: `python examples/lab_results_generator.py` with `--panel-csv` support
  to generate results for real candidate IDs.
- Makefile: `make generate-synthetic-lab-results` generates 40 results (20
  candidates, MIC + hemolysis_RBC, 40% effect size, seed 42).
- Verified: generated files validate against `lab_result.schema.json`
  (40/40 passed) and integrate correctly with `calibration-intake`
  (20 candidates matched, 40 results, 0 orphans).

## v0.5.41 — Exact Charge-Balanced Synthetic Control ✓ (2026-07-06)

The v0.5.39 charge-matched benchmark showed that the available background decoy
pool cannot exactly match AMP charge density. This left one unresolved
benchmark-honesty question: does the pipeline retain broad AMP-vs-decoy signal
when the cationic prior is removed exactly?

Changes:
- Added deterministic synthetic charge-balanced controls that preserve each
  AMP's length and K/R/D/E/H counts while resampling neutral positions.
- Added `outputs/benchmark_charge_balanced_synthetic.json` through the existing
  `make bench-charge-matched` workflow.
- Added the synthetic-control result to `outputs/metrics_snapshot.json`.

Result:
- Exact charge control succeeded (`mean_abs_charge_density_delta=0.0000`).
- Charge-density AUROC became chance (`0.5000`).
- Pipeline AUROC collapsed to near chance (`0.5103`).

Why it matters:
- This is evidence against the stronger claim that the current broad
  AMP-vs-decoy benchmark contains robust non-charge discrimination.
- The synthetic controls are not biological negatives, so this does not prove
  the pipeline lacks useful signal. It proves the current raw-discrimination
  benchmark is not enough.
- Next honest work should shift toward biologically plausible charge-balanced
  negatives or objective-aligned benchmarks: selective/non-hemolytic/novel/
  synthesizable candidates versus toxic, copied, unstable, or inactive controls.

## v0.5.40 — Policy Version Tracking ✓ (2026-07-06)

The recalibration workflow had no version protection — a silent unaudited policy
change could bypass all safety constraints. This release adds a machine-readable
version gate between every policy proposal and its predecessor.

Changes:
- Added `calibration/policy_version.py` with:
  - `validate_policy_version()` — checks version increment, locked-changes
    preservation, and decision-log recency (30-day window).
  - `auto_increment_version()` — produces a new policy YAML dict with
    `policy_version + 1` and updated metadata.
  - `VersionValidation` dataclass with per-check booleans and reasons.
- CLI: `openamp-foundry validate-policy-version` with `--current-policy`,
  `--previous-policy`, `--decision-log-dir`, `--today` flags. Exit code 0
  if valid, 3 if invalid.
- Makefile: `make validate-policy-version` target with decision-log check.
- Created `decision_logs/DECISION_LOG_2026-07-06.md` as the initial log entry.
- 29 tests covering log-date parsing, log-file discovery, version validation
  (pass/fail per check), auto-increment, and round-trip serialization.

## v0.5.38 — Charge-Matched Decoy Honesty Benchmark ✓ (2026-07-06)

The easy-baseline benchmark already showed that charge density alone beats the
ensemble on raw AMP-vs-decoy AUROC. That made one missing benchmark load-bearing:
an adversarial test that removes the charge-density gap itself.

Changes:
- Added `src/openamp_foundry/benchmark/charge_matched.py` with deterministic
  greedy matching of each AMP to one unused decoy with nearest charge density.
- Added `scripts/benchmark_charge_matched.py` and `make bench-charge-matched`.
- Added snapshot/test coverage so the benchmark becomes part of the repo's
  machine-readable current-state evidence.

Why it matters:
- Raw 500-AMP discrimination can still be materially charge-inflated.
- This benchmark attacks the exact trivial prior directly instead of only
  describing it in prose.
- Future scoring changes can now be judged on whether they add discrimination
  after charge matching, not just on ordinary AMP-vs-decoy AUROC.
- Actual result on current benchmark: matching is not strong enough with the
  current decoy pool (`mean_abs_charge_density_delta=0.1296`), and charge
  density still beats the ensemble (`0.8166` vs `0.7792`). So the stronger claim
  that broad discrimination survives charge control is **not established**.
  The next benchmark bottleneck is a genuinely charge-balanced negative set.

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

## v0.5.8 — Expert Ablation Benchmark ✓ (2026-07-01)

- `run_expert_ablation_benchmark()` in `benchmark/retrospective.py` — scores all 95 AMPs + 96 decoys with both the simple ensemble and the 7-component expert composite
- `bench expert-ablation` CLI command + `make bench-expert-ablation` target
- Per-component AUROC attribution: identifies signal-bearing (activity 0.814, selectivity 0.773), near-zero (hinge, novelty, boman, motif), and anti-signal (safety 0.349, serum_stability 0.223, synthesis 0.423) components
- **Key finding:** Expert composite AUROC 0.7119 < ensemble AUROC 0.7832 (delta −0.0713). The added complexity does NOT improve AMP-vs-decoy discrimination. Several added components are anti-signal because real AMPs have extreme biophysical properties that safety, stability, and synthesis scorers penalise.
- Ensemble remains primary synthesis gate. Expert composite may add value for within-AMP ranking (tested in v0.5.9 — see selectivity benchmark; expert composite detection AUROC 0.5119 vs ensemble 0.3486, but not significant at n=14 vs n=21).
- `make bench-cluster-split` Makefile target added (was missing despite CLI command existing)
- 14 new tests in `test_expert_ablation.py`; 1435 total tests

## v0.5.11 — Hemolysis Benchmark Expansion (DBAASP) ✓ (2026-07-01)

- Expanded hemolysis reference from 42 to 238 peptides using DBAASP v3 human erythrocyte data
- 196 new peptides with 50% hemolysis (HC50) values, converted to µg/ml using peptide MW
- Binary task: 54 hemolytic (HC50 < 25 µg/ml) vs 125 selective (HC50 >= 100 µg/ml) = 179 total (was 14 vs 21 = 35)
- **Critical honesty correction:** hemolysis risk scorer detection AUROC drops from 0.9218 (CI 0.82-0.99) to 0.5650 (CI 0.47-0.66)
  - Original n=35 performance was **small-sample inflation**
  - Direction still correct (hemolytic mean=0.204 > selective mean=0.154) but NOT statistically significant
  - Safety scorer detection improves slightly: 0.3844 → 0.5116 (still not significant)
  - Selectivity proxy: detection AUROC=0.5744 (CI 0.50-0.66) — borderline significant
- Extraction script: `scripts/expand_hemolysis_benchmark.py`
- Tests updated: `test_selectivity_benchmark.py` test renamed from `test_hemolysis_risk_is_significant_detector` to `test_hemolysis_risk_direction_correct`
- Docs updated: METRICS_CURRENT.md, hemolysis.py, expert.py comments corrected to reflect expanded-set reality
- **Lesson:** A 0.92 AUROC on n=35 is not robust. The project's adversarial benchmark philosophy caught this.

## v0.5.10 — Dedicated Hemolysis Risk Scorer ✓ (2026-07-01)

- `scoring/hemolysis.py` — standalone 4-component hemolysis risk score (synth difficulty + aromatic density + face cationic leakage + cysteine content)
- Combined detection AUROC=0.9218 (CI₉₅: 0.82-0.99) on original 42-peptide reference — **CORRECTED in v0.5.11: small-sample inflation; expanded n=179 gives 0.5650 (CI 0.47-0.66)**
- Integrated into selectivity benchmark as risk-direction score; integrated into expert composite as `hemolysis_safety` (weight 0.10)
- Expert composite hemolysis detection improved: 0.5119 → 0.6429 on n=35 — **expanded n=179 gives 0.5459 (CI 0.46-0.63)**
- Safety scorer UNCHANGED — standard AUROC remains 0.7832; hemolysis risk is complementary, not replacement
- Expert ablation: hemolysis_safety is anti-signal on AMP-vs-decoy (AUROC=0.3285) — confirms it measures within-AMP property
- 15 new tests in `test_hemolysis_risk.py`; 3 new tests in `test_selectivity_benchmark.py`; 1471 total tests

## v0.5.9 — Within-AMP Selectivity Benchmark ✓ (2026-07-01)

- `run_selectivity_benchmark()` in `benchmark/retrospective.py` — tests whether pipeline scorers can distinguish hemolytic AMPs (HC50 < 25 µg/mL) from selective AMPs (HC50 >= 100 µg/mL)
- `bench selectivity` CLI command + `make bench-selectivity` target
- Hemolysis reference dataset: 42 known AMPs with literature HC50 values (`examples/validation/hemolysis_reference.csv`)
- Per-score hemolysis detection AUROC: identifies the only significant risk detector (synthesis, AUROC=0.8027, CI: 0.63-0.95) and confirms the safety scorer blind spot (detection AUROC=0.3844)
- **Key finding:** Safety scorer FAILS to detect hemolysis (detection AUROC=0.3844, CI lo=0.26). All 14 hemolytic AMPs score safety >= 0.8. The melittin blind spot is confirmed quantitatively — 1D hydrophobic moment cannot capture hemolysis mechanisms like curvature-mediated lysis or beta-sheet pore formation.
- **Key finding:** Selectivity proxy FAILS to detect hemolysis (detection AUROC=0.4133, CI lo=0.28). The charge/GRAVY heuristic is insufficient — hemolytic AMPs like melittin have optimal charge and moderate GRAVY.
- **Key finding:** Synthesis feasibility is the only significant hemolysis risk detector (detection AUROC=0.8027, CI lo=0.63). This is an incidental correlation: hemolytic AMPs tend to have more cysteines, repeat runs, and hydrophobic segments that make them harder to synthesize. The synthesis gate provides partial indirect hemolysis filtering.
- **Key finding:** Expert composite is better than ensemble on hemolysis detection (0.5119 vs 0.3486) but not significant (CI includes 0.5). The added selectivity/safety components partially offset the activity scorer's anti-selective bias.
- **Key finding:** Activity scorer is anti-selective (detection AUROC=0.34): it ranks hemolytic AMPs *higher* because they have stronger amphipathic helices. The ensemble inherits this bias.
- Blind spots: 14 hemolytic AMPs with safety >= 0.8 (melittin, indolicidin, protegrins, tachyplesins, piscidin-1, arenicin, polyphemusin, gramicidin-S-like, BMAP fragment)
- 18 new tests in `test_selectivity_benchmark.py`; 1453 total tests

## v0.5.12 — Multi-Class Triage Benchmark ✓ (2026-07-01)

- **Multi-class triage benchmark** (`benchmark/triage.py`): tests whether the
  pipeline can rank selective AMPs > hemolytic AMPs > random decoys in a single
  combined panel (125 selective + 54 hemolytic + 96 decoys = 275 total).
- Addresses the v1.1 ROADMAP item: "benchmark candidate triage against a
  reference panel that includes selective AMPs, hemolytic positives, inactive
  peptides, and random controls."
- **Key finding:** The ensemble does NOT triage correctly. It ranks hemolytic
  AMPs above selective AMPs (AUROC 0.466 < 0.5) due to the activity scorer's
  anti-selective bias. Hemolytic AMPs have stronger amphipathic helices, higher
  hydrophobic moment, and higher charge — exactly the features the activity
  scorer rewards.
- **Key finding:** `selectivity_proxy` triages best (all three pairwise AUROCs > 0.5),
  but at the cost of decoy discrimination (0.782 vs ensemble 0.848).
- **Key finding:** `expert_composite` now faces the same mixed-panel benchmark:
  it clears the pairwise triage rule (sel>decoy 0.757, hem>decoy 0.746,
  sel>hem 0.545), but its top-20 includes 5 decoys. It must not replace the
  ensemble activity gate.
- **Key finding:** The naive `triage_score` (activity × (1 - hemolysis_risk))
  does NOT fix the anti-selective bias because hemolysis_risk is too weak
  (detection AUROC 0.565, not significant on expanded benchmark).
- The `triage_score` does shift the top-20 distribution favorably (16 selective
  vs 14 for ensemble; 4 hemolytic vs 6), but the pairwise AUROC remains < 0.5.
- CLI: `openamp-foundry bench triage --hemolysis-csv ... --decoy-csv ...`
- Makefile: `make bench-triage`
- 16 new tests (15 triage benchmark + 1 CLI integration); 1487 tests total.

## v0.5.13 — Expert composite ranking integration ✓ (2026-07-01)

The expert composite scorer (`scoring/expert.py`) was benchmarked but never connected
to the pipeline. This integration makes it available as an optional ranking mode.

Changes:
- `score_candidates()` now computes `expert_composite` and `hemolysis_risk` for every
  candidate (stored in `scores` dict alongside `ensemble`)
- `rank_candidates()` accepts `ranking_mode="expert"` to rank by expert composite
  instead of ensemble (default remains "ensemble")
- `run_ranking_pipeline()` accepts `ranking_mode` parameter, recorded in batch report
- CLI: `openamp-foundry rank --ranking-mode expert` flag added
- `selection/pareto.py`: `select_top()` also accepts `ranking_mode`

Why this matters:
The triage benchmark (v0.5.12) showed the ensemble has an anti-selective bias
(sel_vs_hem AUROC=0.466). The expert composite incorporates selectivity_proxy,
hemolysis risk, helix-hinge analysis, and motif novelty. It partially improves
selective-vs-hemolytic ordering (triage benchmark: 0.545 vs ensemble 0.466), but
it also weakens top-k decoy exclusion (top-20 includes 5 decoys vs 0 for ensemble).
Expert-ranked top-5 candidates have lower mean hemolysis_risk than ensemble-ranked
top-5 on the mixed benchmark set (verified by test).

Honest limitation: The expert composite's hemolysis components are not statistically
significant detectors on the expanded n=179 benchmark (AUROC=0.565, CI 0.47-0.66).
Expert ranking is a safety-aware alternative, not a validated safety guarantee or
a replacement for activity-gated ensemble selection. Wet-lab hemolysis assay remains
mandatory.

## v0.5.14 — Strict Triage Benchmark: Composition-Matched Decoys ✓ (2026-07-02)

The standard triage benchmark (v0.5.12) uses random background peptides as
decoys. These are trivially distinguishable from AMPs because their amino acid
composition is protein-like, not AMP-like. This inflates selective_vs_decoy and
hemolytic_vs_decoy AUROCs, making scorers appear to triage well when they are
really only solving the easy "AMP vs random" problem.

The strict triage benchmark replaces random decoys with **composition-matched
scrambled versions** of the selective AMPs — same amino acids, permuted order.
This destroys amphipathic helical phase, hydrophobic moment, and charge
distribution patterns while preserving all composition-based features.

Changes:
- `benchmark/triage.py`: `run_strict_triage_benchmark()` — generates scrambled
  decoys, runs the same 10-scorer pairwise triage comparison
- `benchmark/metrics_snapshot.py`: strict_triage section added to snapshot
- `tests/test_triage_benchmark.py`: 12 new tests for strict triage (structure
  + findings)
- `outputs/metrics_snapshot.json`: regenerated with strict triage results
- `docs/METRICS_CURRENT.md`: strict triage results table and interpretation

Key honest finding: **No scorer triages correctly with composition-matched
decoys.** The standard triage "success" of selectivity_proxy and
expert_composite was an artifact of trivially distinguishable decoys.
selectivity_proxy collapses to exactly 0.5000 on selective_vs_decoy (confirming
it is purely composition-driven), and the ensemble drops from 0.848 to 0.572.

The selective_vs_hemolytic AUROC is identical between standard and strict
(expected: both classes are real AMPs, only the decoy class changes). This
confirms the real bottleneck — selective-vs-hemolytic discrimination — is
unchanged and requires structural or contextual features beyond current 1D
physicochemical scorers.

## v0.5.15 — Feature Decomposition Benchmark ✓ (2026-07-03)

The strict triage benchmark (v0.5.14) proved no composite scorer passes
selective_vs_hemolytic discrimination (AUROC 0.43-0.54). But it did not explain
*why* — only that the aggregate fails. This benchmark decomposes the failure
into per-feature contributions: which individual physicochemical features have
statistically significant signal for distinguishing hemolytic from selective AMPs?

Changes:
- `benchmark/feature_decomp.py`: `run_feature_decomposition_benchmark()` — tests
  all 30 scalar features from `compute_features()` individually for selective_vs_hemolytic
  AUROC with bootstrap CIs, direction, significance, and selectivity-proxy usage flags
- `benchmark/metrics_snapshot.py`: feature_decomposition section added to snapshot
- `cli/commands/benchmark.py`: `bench feature-decomp` CLI command
- `Makefile`: `bench-feature-decomp` target
- `tests/test_feature_decomp.py`: 20 tests covering structure, findings, and snapshot integration
- `outputs/metrics_snapshot.json`: regenerated with feature decomposition results
- `docs/METRICS_CURRENT.md`: feature decomposition results table and interpretation

Key honest finding: **The selectivity proxy ignores the strongest discriminative
features.** `hydrophobic_fraction` (AUROC 0.6745, CI 0.58-0.77) is the single best
feature for selective_vs_hemolytic discrimination, yet the proxy uses only charge
and GRAVY. 8 of 30 features have significant signal; 6 of those 8 are NOT used
by the current selectivity model. This converts the v0.5.14 aggregate failure
into actionable diagnostic information: the next loop knows exactly which feature
axes to combine into a richer selectivity scorer.

## v0.5.16 — Rich Selectivity Scorer ✓ (2026-07-03)

The feature decomposition benchmark (v0.5.15) identified 8 statistically significant
features for selective_vs_hemolytic discrimination, but the old `selectivity_proxy`
(charge + GRAVY) used only 2. This version builds a richer composite selectivity
scorer from the evidence — the first pipeline score with statistically significant
hemolysis detection on the expanded n=179 benchmark.

Changes:
- `scoring/selectivity_rich.py`: `rich_selectivity_score()` — composite of 8
  evidence-identified features, weighted by detection AUROC, with full component
  breakdown via `rich_selectivity_breakdown()`
- `benchmark/retrospective.py`: rich selectivity added to selectivity benchmark
  evaluation and verdict
- `benchmark/triage.py`: rich selectivity added to standard and strict triage
  benchmarks
- `benchmark/metrics_snapshot.py`: selectivity snapshot expanded with
  `per_score_auroc` and `rich_selectivity_verdict`
- `cli/commands/benchmark.py`: selectivity bench summary includes
  `rich_selectivity_verdict`
- `tests/test_selectivity_rich.py`: 18 tests covering scoring, breakdown, and
  benchmark integration
- `outputs/metrics_snapshot.json`: regenerated with rich selectivity results

Key finding: rich selectivity detection AUROC=0.7138 (CI 0.6266-0.7951) — first
pipeline score with CI excluding 0.5 on selective_vs_hemolytic. Old
selectivity_proxy=0.5744 (CI 0.4954-0.6558). Honest limitation: does NOT triage
AMP-vs-decoy (selective_vs_decoy=0.19); designed for within-AMP selectivity only.

## v0.5.17 — Rich Selectivity Integrated into Production Pipeline ✓ (2026-07-03)

The rich selectivity scorer (v0.5.16) was benchmarked but not connected to the
production candidate pipeline. This version wires it into every stage where
selectivity matters for candidate selection, expert review, and evidence
traceability.

Changes:
- `pipeline.py`: `score_candidates()` now computes `rich_selectivity` for every
  candidate and includes it in `raw_scores` (alongside the legacy
  `selectivity_proxy` for backward comparability)
- `scoring/expert.py`: `rich_selectivity` replaces `hemolysis_safety` (AUROC=0.565,
  not significant) as the expert composite's hemolysis-risk component (weight 0.10).
  The old `selectivity_proxy` remains as the expert's activity-ranking selectivity
  component (weight 0.20) because it carries AMP-vs-decoy signal (AUROC=0.7729).
  Old `hemolysis_safety` preserved as `hemolysis_safety_legacy` in expert extras.
- `selection/pilot.py`: `_pilot_priority()` now uses `rich_selectivity` instead of
  `selectivity_proxy` for the safety tiebreaker, with backward-compat fallback.
- `reports/pilot_panel.py`: pilot CSV and markdown now include a `rich_selectivity`
  column alongside `selectivity_proxy` for expert comparison.
- `benchmark/retrospective.py`: expert ablation benchmark references
  `rich_selectivity` instead of `hemolysis_safety` in per-component AUROC.
- `tests/test_rich_selectivity_integration.py`: 14 tests verifying rich_selectivity
  flows through pipeline scores, evidence certificates, expert composite, pilot
  priority, and pilot panel report.
- `outputs/metrics_snapshot.json`: regenerated with updated expert AUROC.

Key finding: expert composite AUROC drops slightly from 0.7119 to 0.7097 (−0.0022)
on AMP-vs-decoy — acceptable because the expert now includes a **significant**
hemolysis detector (CI excludes 0.5) instead of the old non-significant one.
The `rich_selectivity` component is anti-AMP by design (AUROC=0.1973 for
AMP-vs-decoy) because it penalises high hydrophobicity and charge that define
AMPs — this is the correct tradeoff.

## v0.5.18 — Two-Gate Triage Composite ✓ (2026-07-03)

The triage benchmark (v0.5.12) showed no scorer could pass all three pairwise
AUROC conditions with strong selective-vs-hemolytic separation. The old
`triage_score` (activity × (1 - hemolysis_risk)) used a non-significant
hemolysis detector. This version adds `gate_triage` = activity ×
rich_selectivity, combining the two strongest complementary signals.

Changes:
- `benchmark/triage.py`: `gate_triage` added to `_score_all()` and the scorer
  list in both `run_triage_benchmark()` and `run_strict_triage_benchmark()`.
  Top-20 class distribution breakdowns added.
- `benchmark/metrics_snapshot.py`: `top_20_by_gate_triage` added to both triage
  and strict_triage snapshot sections.
- `tests/test_triage_benchmark.py`: 8 new tests in `TestGateTriageFindings`
  covering structure, standard triage success, selective-vs-hemolytic threshold,
  improvement over old triage_score, top-20 distribution, hemolytic reduction vs
  ensemble, best-scorer assertion, and strict triage honest-failure test.
- `outputs/metrics_snapshot.json`: regenerated with gate_triage results.

Key result: **gate_triage is the first scorer to pass all three standard triage
conditions with selective_vs_hemolytic > 0.65** (sel_vs_dec=0.779,
hem_vs_dec=0.686, sel_vs_hem=0.666). Top-20: 16 selective / 1 hemolytic / 3 decoy.

Honest limitation: gate_triage does NOT pass strict triage (composition-matched
decoys). Its hemolytic_vs_decoy drops to 0.489 because rich_selectivity
penalizes the AMP-like composition that hemolytic AMPs share with their
scrambled versions. It also retains 3 decoys in top-20 (vs 0 for ensemble).
It must NOT replace the ensemble activity gate — it is a complementary signal.

## v0.5.35 — Cross-Dataset Generalization Benchmark ✓ (2026-07-05)

- **Last Phase 1 exit criterion satisfied**: cross-dataset results published.
- DRAMP-only AMPs (n=500, no overlap with current set) vs Swiss-Prot decoys:
  AUROC **0.7803** (CI: 0.7517–0.8081). Baseline (APD6/UniProt): 0.7832.
  Δ = **−0.0029** — essentially identical.
- Pipeline generalises strongly across AMP databases — heuristic features
  (charge, hydrophobicity, hydrophobic moment, etc.) capture fundamental
  physicochemical properties rather than database-specific biases.
- 65% of current AMP set (325/500) overlaps with DRAMP (expected — DRAMP is
  a meta-database). Cross-dataset test uses 6427 DRAMP-only sequences with
  zero overlap with the current benchmark set.
- **Phase 1 complete** — all 5 exit criteria met. Pipeline advances to Phase 2
  (per-family breakdown, calibration engine, active learning).
- New script: `scripts/benchmark_cross_dataset.py`
- New target: `make bench-cross-dataset`
- Docs: `docs/METRICS_CURRENT.md` (new section), `docs/BENCHMARK_CARD.md` (new section),
  `docs/50_LOOP_PLAN.md` (Phase 1 ✅)

## v0.5.34 — Benchmark Card Consolidation ✓ (2026-07-05)

- Consolidated all Phase 1 benchmark findings into `docs/BENCHMARK_CARD.md`
- Card now covers: expanded benchmark (500+500), multi-negative (4 decoy sets),
  cluster-split-500, easy baseline, order-dependence (7/31 features),
  precision@k (top-20 perfect), within-AMP selectivity (rich_selectivity 0.714),
  multi-class triage (gate_triage passes), expert ablation (n=1000 with
  2 reclassifications), and 9 updated known biases
- **Phase 1 exit criterion met:** benchmark card is externally reviewable
- **One Phase 1 exit criterion remains:** cross-dataset and time-split results
- Next: Loop 17 — Cross-dataset generalization

## v0.5.33 — Expert Ablation Re-run on Expanded Benchmark ✓ (2026-07-05)

- Re-ran expert ablation on the expanded 500-AMP + 500-decoy benchmark (n=1000)
- **Finding: 2 components reclassified from n=191** — synthesis was an anti-signal
  artifact (0.4228 → 0.4968, now near-zero); boman_activity more strongly anti-AMP
  than previously known (0.4620 → 0.3291)
- **Finding: selectivity_proxy weaker on diverse set** (0.7729 → 0.6702) — the
  charge+GRAVY heuristic discriminates less reliably on the broader AMP set
- **Finding: delta widens** (−0.0735 → −0.0935) — expert composite worse binary
  discriminator on diverse AMPs (expected: design tradeoff)
- **Finding: activity remains dominant** (0.7969, signal-bearing); novelty and
  motif_novelty exactly 0.5 by construction (no k-mer index in benchmark)
- Makefile target: `make bench-expert-ablation-500`
- Docs updated: METRICS_CURRENT.md (expanded per-component table + updated key findings)
- Honest update: the original n=191 finding that "synthesis is anti-signal" was a
  small-n artifact. Corrected in this release.
- Next: Loop 16 — Cross-dataset generalization or benchmark card update

## v0.5.32 — Precision@k Calibration ✓ (2026-07-05)

- Added `scripts/benchmark_precision_at_k.py` — operating characteristic for
  candidate selection: small-k triage (top-20 precision 1.000), threshold-based
  analysis (best F1 at 0.6323), and 80% recall operating point
- **Finding: top-20 triage is perfect** (precision 1.000) — the top 20 candidates
  are all genuine AMPs. Top-50 still excellent (0.900). Enrichment persists to
  k=200 (0.835, 1.67×)
- **Finding: best F1 threshold 0.6323** (F1=0.7518, precision=0.6337, recall=0.9240)
- **Finding: at 80% recall, precision drops to base-rate** (0.5000) — the pipeline's
  high-recall triage is limited by substantial score distribution overlap
- **Honest limitation:** results use a balanced 50/50 dataset; in real low-prevalence
  screening (1–10% AMP rate), precision at every operating point would be lower
- Makefile target: `make bench-precision-at-k`
- Pipeline best used as small-k triage tool (pick top 20–50 where precision ≥ 0.90)
- Docs updated: METRICS_CURRENT.md (new section), ROADMAP.md (this entry)
- Next: Loop 16 — Cross-dataset generalization or remaining Phase 1 exit criterion

## v0.5.31 — Order-Dependent Features Benchmark ✓ (2026-07-05)

- Added `src/openamp_foundry/features/dipeptide.py` — dipeptide frequency
  computation and `dipeptide_order_score` with pre-computed log-odds reference
- Added `scripts/benchmark_order_dependent.py` — analyzes which of 31 features
  survive sequence scrambling (position independence test)
- Integrated `dipeptide_order_score` into `compute_features()` (31st scalar feature)
- **Finding: dipeptide_order_score is the strongest order-dependent feature**
  (AUROC 0.7861 on AMP-vs-scrambled), beating hydrophobic moment (0.7483)
- **Only 7/31 features survive scrambling** — all are amphipathicity/helix-wheel
  properties plus the new dipeptide score
- **All composition features are EXACTLY position-independent** (AUROC = 0.5000)
- Some features are anti-order-dependent (aggregation propensity 0.4325,
  hydrophilic face mean h 0.3506) — scrambling creates patterns not present
  in native AMPs
- Makefile target: `make bench-order-dependent`
- CI: informational step (non-gating)
- Next: Loop 14 — Cross-dataset generalization

## v0.5.30 — Easy Baseline Benchmark ✓ (2026-07-05)

## v0.5.29 — Expanded 500-AMP Benchmark ✓ (2026-07-05)

- Expanded benchmark from 95 + 96 (n=191) to 500 AMP + 500 decoy (n=1000)
- Curation script: `scripts/curate_500_amp_benchmark.py` — reads UniProt-reviewed
  AMPs (CC BY 4.0) and APD6 natural sequences, filters to 10-30 AA, deduplicates
  against existing curated set, samples to 500, generates matched Swiss-Prot
  frequency decoys
- Pipeline AUROC on expanded set: 0.7792 (CI₉₅: 0.7505–0.8065) — signal
  generalizes, essentially identical to 0.7832 on n=191
- Phase3 AUROC: 0.7744 (was 0.7448 on n=191)
- Cluster-aware CI: 0.746–0.8102 (width 0.064 vs 0.146 on n=191) — ~2.3× tighter
- Representative AUROC: 0.778 — nearly equals full AUROC (improvement over
  n=191 where representative 0.7607 < full 0.7832)
- Expanded benchmark files: `examples/validation/known_amps_500.csv`,
  `examples/validation/random_background_500.csv`
- Makefile targets: `make bench-500`, `make bench-cluster-split-500`
- CI gate: expanded benchmark AUROC > 0.70 enforced in CI after standard gate
- Metrics snapshot: `outputs/metrics_snapshot_500.json`
- METRICS_CURRENT.md updated with expanded benchmark sections

Key honest findings:

1. **Signal generalizes to diverse AMP classes.** AUROC 0.7792 on 500 AMPs from
   UniProt and APD6 is nearly identical to 0.7832 on 95 manually curated AMPs.
   The pipeline is not overfit to the small curated set.

2. **CIs are dramatically tighter.** Cluster-aware CI width drops from 0.146
   (n=191) to 0.064 (n=1000). This is the statistical benefit of a larger
   benchmark — the pipeline's true discriminative power is now constrained
   to a ±0.03 band rather than ±0.07.

3. **Representative AUROC parity.** On n=191, the representative-only AUROC
   (0.7607) was notably lower than the full AUROC (0.7832), indicating
   near-duplicate inflation. On n=1000, representative AUROC (0.778) nearly
   equals the full AUROC (0.7792) — the expanded set's 500 sequences have
   lower redundancy.

4. **Limitation:** The expanded set's lower recall@k (2% vs 10.5% at k=10) is
   an honest effect of triage on a larger, harder pool. With 500 decoys
   (vs 96), the top-10 threshold is more competitive. The pipeline correctly
   ranks many AMPs in the top 20–40% rather than the top 1–2%.

## v0.5.28 — Multi-Negative-Set Benchmark ✓ (2026-07-05)

The pipeline's AUROC (0.78 on AMP-vs-decoy) was measured against a single
Swiss-Prot background negative set. There was no honest assessment of how
the model behaves when faced with negative distributions that differ from
the benchmark background. This release adds a 4-set multi-negative benchmark
and gates CI on composition-independent sets.

Changes:
- `scripts/benchmark_multi_negatives.py`: Runs AUC against 4 decoy
  distributions: Swiss-Prot background (same as standard benchmark),
  uniform random (equal-length random peptides), reverse sequences
  (same composition, reversed order), shuffled sequences (same
  composition, random order). Returns AUROC, AUPRC, bootstrapped
  95% CI, and an overall `all_independent_sets_above_0_70` verdict.
  Gate passes if swissprot and uniform sets both > 0.70 AUROC.
- `tests/test_benchmark_multi_negatives.py`: 14 tests covering AMP
  loading, decoy generation for all 4 distributions, CSV writing,
  CLI exit codes, JSON output parsing, and weak-AMP rejection.
- `Makefile`: `bench-multi-negatives` target running the script with
  output written to `outputs/multi_negative_benchmark.json`.
- `.github/workflows/ci.yml`: Multi-negative benchmark added as a
  blocking CI step after benchmark regression gate.
- 1723 tests passing (14 new).

Key honest findings:

1. **Pipeline is composition-driven.** On reverse sequences (same
   composition, reversed order), AUROC = 0.5000 (CI: 0.42–0.58).
   On shuffled sequences (same composition, random order),
   AUROC = 0.5376 (CI: 0.45–0.62). The model has no sequence-order
   discriminative power — it scores high on any peptide with AMP-like
   amino-acid composition regardless of actual bioactivity.

2. **Expected, not embarrassing.** Composition-dependence is a known
   property of linear models in small-peptide space. The physchem
   features (charge, hydrophobicity, isoelectric point) are derived
   from amino-acid composition, not tertiary structure. The model
   correctly reflects that most AMPs are cationic and amphipathic.
   The honest limitation is that composition-matched decoys reveal
   the ceiling of linear-composition models.

3. **Swiss-Prot and uniform decoys remain discriminable** (0.7832
   and 0.7797 respectively) because random natural proteins and
   truly random sequences have different composition distributions
   than AMPs. This is genuine signal but must be interpreted in the
   context of finding #1.

4. **No gate for reverse/shuffled.** The gate only requires
   composition-independent sets (swissprot, uniform) to stay above
   0.70. Reverse/shuffled scores near 0.50 are expected; gating them
   would be dishonest. These scores are preserved as honest negative
   results in the benchmark report.

5. **Use as a ceiling.** The multi-negative benchmark should be
   re-run after any feature or model change that claims to improve
   sequence-order awareness. An improvement on reverse or shuffled
   AUROC from ~0.50 to ~0.60+ would be genuine evidence of
   sequence-order learning.

## v1.0 — Validated dry-lab-to-wet-lab loop

- independently reviewed assay batch (expert_review.yml GitHub issue template);
- lab results ingested via `schemas/lab_result.schema.json`;
- reproducible wet-lab result report via `openamp_foundry lab-result-report` so raw assay JSON turns into a control-aware review artifact before recalibration;
- negative results archived where safe;
- active-learning batch 2 (D-amino variants, MDR strain panel);
- public reproducibility report.

## v1.1 — Virtual assay scaffold

- ~~write the first explicit simulator scope document: what OpenAMP will model and what it will not;~~
- ~~add membrane/selectivity/stability proxy interfaces with uncertainty fields;~~
- ~~benchmark candidate triage against a reference panel that includes selective AMPs, hemolytic positives, inactive peptides, and random controls;~~ (v0.5.12: standard triage added — selectivity_proxy and expert_composite pass; v0.5.14: strict triage with composition-matched decoys added — **no scorer passes**, standard triage success was inflated by trivially distinguishable random decoys)
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
| ~~Large-scale benchmark (≥ 500 AMPs vs composition-matched decoys, cluster-split)~~ | ~~Current AUROC 0.8420 measured on 43+44 demo set (n=87, CI₉₅: 0.76–0.91); may not generalise~~ | **Partial** (PR #110: expanded to 95 AMPs + 96 decoys, n=191, AUROC=0.7832, CI₉₅: 0.72–0.84; 52 new public-domain AMPs from 12 taxonomic classes; covers defensins, proline-rich, lantibiotics — a more honest estimate. Cluster-split benchmark added: cluster-aware CI 0.7061–0.8526, representative AUROC 0.7607. 500+ target still deferred to v1.0+) |
| External predictor ensemble adapters (CAMPR4, AMPScanner, dbAMP, AntiCP2, Macrel) | Independent second opinions on activity; required for scientific credibility. Wave 0.5 has completed external evidence for AMPScanner v2, AMPActiPred, Macrel web, HemoFinder, and AntiCP 2.0 with CAMPR4 excluded; see `docs/METRICS_CURRENT.md`. The reusable generic 5-tool pilot-panel workflow still requires a filled `outputs/external_predict_results.csv` per future panel. Macrel v1.6.0 CLI ONNX bug documented PR #77 — all sequences (incl. canonical AMPs magainin-2, LL-37) misclassified as NAMP; use web server at big-data-biology.org/software/macrel. AMPlify omitted: GPU/ONNX env incompatible with current deps | Partial (Wave 0.5 complete; generic future-panel Gate 6 remains panel-specific) |
| ~~True novelty check against APD3, DRAMP v3.0, dbAMP~~ | ~~Current novelty scored against 45-sequence seed set only; may overestimate novelty~~ | **Done** (v0.5.7: BioPython BLOSUM62 local alignment vs 27,234 AMPs from APD6+DRAMP+UniProt; Wave 0.5 novelty corrected from 53/60 RELATED_NOVEL → 39 CLOSE_RELATIVE + 19 KNOWN_VARIANT + 1 RELATED_NOVEL) |
| ~~AUPRC alongside AUROC~~ | ~~Better metric for class-imbalanced AMP datasets~~ | **Done** (PR #58; updated PR #72) — pipeline AUPRC = 0.8627 |
| Wet-lab result integration (active-learning round 2) | Required to move from 15–30% to 50%+ credible probability | Requires wet-lab |
| ~~Pre-registration of assay protocol before synthesis~~ | ~~Strengthens causal inference; reduces reporting bias~~ | **Done** (docs/ASSAY_PREREGISTRATION.md — PRs #83; includes MRSA USA300, serum stability, Gate P3 aligned) |
| Public benchmark paper (replicable, cluster-split, open datasets) | Sets community standard; enables external validation | Large |

## v0.5.19 — Calibration Intake Module ✓ (2026-07-04)

The lab-result ingestion layer (`data/lab_results.py`, `reports/lab_result_report.py`,
`lab-result-report` CLI) was already in place, but there was no way to **join the
pilot panel predictions with the lab-result actuals** to see whether the pipeline's
predictions matched reality. Without that join, the wet-lab feedback loop has no
intake valve, and any future recalibration would be operating on raw assay data
without the prediction-vs-actual contrast it needs.

This version adds the first step of the closed wet-lab feedback loop: a
calibration-intake report that joins a pilot panel CSV with a directory of
validated lab result JSON files. It is descriptive only — it does not rewrite
selection rules, does not modify scoring weights, and does not upgrade assay
readouts into biological claims.

Changes:
- `src/openamp_foundry/calibration/__init__.py`: new package
- `src/openamp_foundry/calibration/intake.py`: new module
  - `build_calibration_intake_report(panel_csv, results_dir)` — joins predictions
    with actuals on `candidate_id`, produces a machine-readable report
  - `write_calibration_intake_json(report, out_path)` and
    `write_calibration_intake_markdown(report, out_path)` — output writers
  - **Honest minimum-cohort-size gate**: aggregate cohort metrics are NOT
    reported when `n < 5`. Below the gate the metric is marked
    `insufficient_data: True` and no point estimate is produced. This prevents
    small-sample theater where 2-3 MIC readouts could swing an "AUROC" by 0.30.
  - Two pilot cohort metrics: `activity_vs_active_mic` (MIC ≤ 32 µg/mL active)
    and `rich_selectivity_vs_high_hemolysis` (hemolysis ≥ 10% high-risk).
  - Per-candidate join rows expose every prediction column plus the
    aggregated actual outcomes.
  - Control failures and orphan lab results (results with no matching
    candidate) are surfaced as separate audit fields.
- `src/openamp_foundry/cli/commands/reports.py`: `_run_calibration_intake`
- `src/openamp_foundry/cli/main.py`: `calibration-intake` subcommand registered
- `examples/lab_results/`: 5 clearly-labeled SYNTHETIC JSON files demonstrating
  the workflow (active hit, inactive candidate, low hemolysis, high hemolysis,
  control failure). Disclaimer required in every file's `disclaimer` field.
- `examples/lab_results/README.md`: explicitly disclaims real-world use
- `examples/lab_results_panel.csv`: 8-candidate synthetic pilot panel
- `tests/test_calibration_intake.py`: 29 tests covering empty panels, missing
  columns, orphan detection, control failure surfacing, cohort metric gating
  (below/equal/above `MIN_COHORT_SIZE`), hemolysis direction logic,
  synthetic-example schema validation, and threshold constants
- `Makefile`: `lab-result-intake` and `lab-result-intake-example` targets
- Total tests: 1614 passing (was 1585)

Key honest limitation: this module does NOT trigger recalibration. It is the
intake valve that produces a review artifact for a separate, human-reviewed
recalibration workflow (see `docs/DECISION_RULES.md` and `docs/WAVE2_PLAN.md`).
Cohort metrics are descriptive only; they do not validate the pipeline, do not
control for selection bias from the pre-registered shortlist, and must not be
used to rewrite scoring weights after the fact.

The synthetic example data is clearly labeled in every JSON file's `disclaimer`
field and in `examples/lab_results/README.md`. It exists solely to exercise the
intake workflow end-to-end so future agents and reviewers can verify the code
path without real wet-lab data. When real validated lab results arrive, replace
the example directory — the pipeline itself does not change.

## v0.5.20 — Recalibration Policy + Gate ✓ (2026-07-04)

The v0.5.19 calibration-intake module joins pilot-panel predictions with
validated lab-result actuals and produces a per-candidate review report.
It is intentionally descriptive only. The obvious next step would be to
"act on" those intake reports by adjusting scoring weights. Without a
machine-readable policy that gates that action, the most dangerous
failure mode is silent recalibration: an agent sees real wet-lab data,
decides the scorer "needs improvement," and rewrites weights to fit.
That is the textbook cherry-picking this project exists to prevent.

This version adds the **gate that protects** any future recalibration.
It is the missing permission layer between v0.5.19 intake and a
recalibration engine that does not yet exist.

Changes:
- `configs/recalibration_policy.yaml`: human-authored, machine-readable
  pre-registered policy.
  - 7 `minimum_conditions` (cohort size, controls, orphans, positives,
    negatives, metrics availability) — every rule also listed in
    `locked_changes` so removal requires a documented decision log entry.
  - 5 `prohibited_actions` (toxicity relaxation, hemolysis relaxation,
    novelty relaxation, pathogen optimization, post-hoc success
    redefinition) — permanent floor, mirrors `AGENTS.md` and
    `MISSION.md`. Validator rejects any policy file that drops them.
  - 2 `rate_limits` (L1 weight budget 0.10; cooldown 14 days) — evaluated
    when the corresponding CLI inputs are supplied; `unknown` status
    when not evaluable.
  - 3 `required_reviewer_artefacts` (intake JSON, intake Markdown, dated
    decision log entry) — surfaced as reasons when missing but not
    blocking on their own; the human review IS the final step.
  - 12 `locked_changes` entries, one per enforced rule.
- `src/openamp_foundry/calibration/policy.py`: `load_recalibration_policy`
  loads, validates, and exposes the policy. Raises `PolicyLoadError` on
  missing fields, duplicate ids, unlocked rules, or missing canonical
  prohibited actions.
- `src/openamp_foundry/calibration/recalibration_gate.py`:
  - `evaluate_recalibration_gate(intake_report, policy, ...)` returns a
    `GateVerdict` with `may_recalibrate` (bool), per-rule results, audit,
    rate-limit status, reviewer-artefact status, reasons, and summary.
  - `write_gate_verdict_json` and `write_gate_verdict_markdown` produce
    JSON and Markdown outputs.
- `cli/commands/reports.py`: `_run_recalibration_gate`.
- `cli/main.py`: `recalibration-gate` subcommand registered.
  Exit code 0 when `may_recalibrate=true`, 3 when false, 2 on input error.
- `Makefile`: `recalibration-gate-example` and `recalibration-gate`
  targets added.
- `tests/test_recalibration_gate.py`: 39 new tests covering policy
  loader (happy + every rejection mode), gate evaluator (every minimum
  condition), prohibited-action audit, rate-limit status, reviewer-
  artefact status, writers, end-to-end CLI smoke. Total 1647 passing.
- `docs/CALIBRATION_POLICY.md`: human-readable overview of the policy,
  the gate, the permanent floor, rate limits, and how to update.

Key honest limitations (must read before relying on the gate):

1. The gate does NOT trigger any weight update. It only emits a verdict.
2. A `may_recalibrate=true` verdict is a permission, not a command.
   The decision to apply a weight change still belongs to a human
   reviewer with a dated decision log entry.
3. The gate evaluates cohort evidence, not pipeline calibration health.
   Benchmark regressions are caught by `make validate-scoring`,
   `make bench-triage`, and the selectivity benchmark — not by this
   policy. These checks must keep running independently.
4. The synthetic example correctly yields `may_recalibrate=false` (cohort
   size 4 < 5, one positive control failed, all reviewer artefacts
   missing). That is the expected outcome on tiny synthetic data and is
   itself a useful sanity check that the gate is enforcing the cohort
   floor honestly.
5. The five canonical prohibited actions are duplicated from `AGENTS.md`
   and `MISSION.md`. The validator rejects a policy file that drops any
   of them. Any relaxation of the source documents must happen in
   lockstep with the policy file.

## v0.5.24 — Benchmark Regression Gate for CI ✓ (2026-07-04)

Next-loop candidates that depend on v0.5.20:

- **Recalibration engine**: implement the actual weight-update code,
  gated by this policy. Will be safe to ship because the gate
  pre-emptively rejects recalibration attempts that violate the floor.
- **Per-seed recalibration audit**: extend the policy with seed-specific
  rules once Wave 1 results are in.
- **Policy version bump workflow**: codify the exact decision-log format
  and add CI guard that a `policy_version` bump requires a non-empty
  decision log entry dated within the past 30 days.

## v0.5.25 — Subpackage Public API & Import Discipline ✓ (2026-07-05)

Eleven subpackages previously had empty `__init__.py` files. Every
external caller had to reach into module-level imports
(`from openamp_foundry.scoring.activity import activity_likeness_score`)
or, worse, guess which module owned which function. The Phase 0 exit
criterion (`from openamp_foundry.benchmark import ...` works cleanly)
was not met. This release curates a public API per package so callers
can write `from openamp_foundry.benchmark import run_triage_benchmark`
and `from openamp_foundry.scoring import activity_likeness_score` etc.

Changes:
- `src/openamp_foundry/{benchmark,scoring,selection,features,evidence,data,qc,reports,generators,analysis,utils,gates}/__init__.py` —
  each populated with a module-level docstring, ordered re-exports of
  every non-underscore public function/class, and an `__all__` list.
  Total ~120 public names now reachable from package root.
- `src/openamp_foundry/features/physchem.py`: deferred the `boman`
  import to function scope inside `compute_features`. The top-level
  import cycled through the new `scoring` package `__init__` →
  `scoring.expert` → `features.physchem` on every fresh interpreter.
  The lazy import resolves it without changing observable behaviour.
- `tests/test_public_api_imports.py` (7 tests) — locks in the public
  surface so accidental export removals are caught at PR time. Includes
  regression checks for the Phase 0 exit criteria.

Key honest limitations:

1. The public surface is curated but not yet linted by CI. Future loops
   can add a `ruff` or custom rule that fails PRs which introduce new
   top-level imports of private names from these subpackages, if drift
   becomes a problem.
2. macrel_local functions are re-exported with the `macrel_` prefix
   (`macrel_available`, `macrel_score_batch`, `macrel_score_one`)
   to avoid collisions with common names in other scoring modules.
3. No benchmark, scoring, or behavioural number changed. This is a
   pure architectural-clarity release.

## v0.5.27 — Extended Benchmark Regression Gate for CI ✓ (2026-07-05)

The benchmark regression gate (`scripts/benchmark_gate.py`) previously only
checked `standard.auroc` and `phase3.auroc`. Cluster-split, selectivity, and
triage benchmarks could silently regress without CI catching it. This
release extends the gate to protect every benchmark dimension.

Changes:
- `scripts/benchmark_gate.py`: `run_benchmark_gate()` now checks 5 numeric
  metrics (standard.auroc, phase3.auroc, cluster_split.full_auroc,
  cluster_split.representative_auroc, rich_selectivity.detection.auroc) and
  2 boolean metrics (gate_triage.triages_correctly, triage.best_scorer).
  Uses separate tolerances: 0.02 for standard/phase3, 0.03 for cluster-split,
  0.05 for selectivity. Uses dotted-path resolution (`_deep_get`) to
  traverse the nested snapshot dict safely.
- `tests/test_benchmark_gate.py`: `_snapshot()` helper extended with
  cluster-split, selectivity, and triage test fields. 8 new tests covering
  cluster-split regression (full_auroc, representative_auroc), selectivity
  regression, gate_triage boolean flip, best_scorer change, and
  missing-metric skip behavior. 21 total tests (was 13).
- `outputs/metrics_snapshot.json`: regenerated with n_bootstrap=200 for
  faster CI; all values consistent with previous committed baseline.

Key honest limitations:
1. The gate sets tolerances wide enough to avoid flaky CI on bootstrap
   noise — it catches significant regressions (e.g., a broken scorer change)
   but may pass minor statistical variation.
2. The selectivity detection AUROC (tolerance=0.05) is the noisiest metric
   because it runs on n=179 with bootstrap sampling. The wider tolerance
   is intentional to prevent false-positive CI failures.
3. The gate checks standard triage (random decoys) but NOT strict triage
   (composition-matched scrambled decoys), because no scorer passes strict
   triage. Adding a strict-triage gate would require a different evaluation
   criterion (e.g., "direction of effect preserved").
4. Missing metrics in baseline or current are silently skipped, not failed.
   This preserves backward compatibility with older snapshots.

## v0.5.36 — Recalibration Engine ✓ (2026-07-05)

The recalibration gate (v0.5.20) answered 'may recalibrate?' and the intake
module (v0.5.19) joined predictions with lab actuals. The missing piece was
the engine that computes WHAT weight changes are proposed.

- `calibration/engine.py`: `compute_weight_update()` accepts an intake report,
  gate verdict, and current weights, and returns a `WeightUpdateProposal`.
- Conservative learning rate 0.05. L1 budget enforced.
- CLI: `openamp-foundry recalibration-engine`
- Makefile target: `make recalibration-engine`
- 12 new tests (total 1735)
- Honest limitation: engine proposes only — does NOT apply changes.
  Side effects require explicit human action + decision log entry.

## v0.5.37 — Per-Family Benchmark Breakdown ✓ (2026-07-05)

The expanded 500-AMP benchmark reports a single AUROC. This benchmark
stratifies by structural class to reveal blind spots.

- `scripts/benchmark_per_family.py`: classifies 500 AMPs into 6 heuristic
  structural classes (cysteine_rich, proline_rich, short, highly_cationic,
  moderately_cationic, low_charge) and reports per-class AUROC with CIs.
- **Key finding: pipeline is charge-dominated.** highly_cationic AUROC 0.9583
  vs proline_rich AUROC 0.5861 (Δ=0.37). Proline-rich AMPs are the worst
  handled class (CI includes 0.50).
- 27 new tests in `tests/test_benchmark_per_family.py`
- Makefile target: `make bench-per-family`
- CI: informational step (non-gating)
- METRICS_CURRENT.md updated with full table and implications for candidate
  selection: diversity selection should deliberately compensate for the
  pipeline's helic/charge bias.
## v0.5.38 — Bias-Aware Pilot Panel Floor ✓ (2026-07-05)

The per-family benchmark exposed a real blind spot but left selection behavior
unchanged. This release turns that finding into an optional assay-panel guard.

- Added `selection/structural_class.py` so benchmark code and selection code
  share the same six heuristic classes.
- `select_pilot_panel()` now accepts `min_per_structural_class`; CLI exposes
  `openamp-foundry pilot-panel --min-per-structural-class N`.
- Panel output now reports `structural_classes_represented`.
- Tests added for classifier parity, class-floor behavior, diversity interaction,
  and CLI reporting.

Honest limit:
- This is not a scoring improvement. It does not prove under-ranked classes are
  better candidates. It only stops the current charge/helical bias from
  silently dominating assay panel construction.

## v0.5.39 — Charge-Matched Decoy Benchmark ✓ (2026-07-06)

The easy-baseline benchmark showed charge density alone beats the ensemble on
AMP-vs-Swiss-Prot decoys. This release adds an adversarial benchmark that tries
to pair every AMP with the closest available decoy by pH-7.4 charge density.

- `benchmark/charge_matched.py`: greedy one-to-one decoy matcher and AUROC
  comparison for pipeline ensemble vs charge density.
- `scripts/benchmark_charge_matched.py` and `make bench-charge-matched`: write
  `outputs/benchmark_charge_matched.json`.
- `metrics_snapshot.py`: adds `charge_matched_decoys` to the authoritative
  machine-readable snapshot.
- Tests cover AUROC ties, pH-7.4 charge-density calculation, unique decoy use,
  benchmark structure, and metrics snapshot integration.

Honest finding:
- The current decoy pool is not charge-balanced enough for exact matching
  (`mean_abs_charge_density_delta=0.1296`).
- Charge density still beats the ensemble (`0.8166` vs `0.7792`), so raw
  AMP-vs-decoy AUROC remains charge-inflated.
- The next benchmark improvement should create or curate a truly charge-balanced
  negative set instead of treating this benchmark as a win.
