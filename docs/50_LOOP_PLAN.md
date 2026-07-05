# 50-Loop Execution Plan

> **Status:** Strategic roadmap. Updated v0.5.26.
> **Current state:** 1700 tests, pipeline AUROC 0.7832, calibration intake + gate shipped,
> calibration e2e test (Loop 4), benchmark regression gate (Loop 5), deterministic regenerate-all (Loop 6),
> public API exports (Loop 7), Wave 0.5 panel ready (24 candidates, 15 families), no wet-lab data yet.
>
> Each loop = one focused PR: bottleneck identified → implemented → verified → merged.
> Loops compound. Earlier loops unlock later ones.

---

## Phase 0 — Structural Integrity & Agent Handoff (Loops 1–8)

Make the repo self-documenting, clean to navigate, and easy for a fresh agent or collaborator to continue.

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 1 ✅ | Calibration `__init__.py` empty; `new-vision.md` loose at root; `pyproject.toml` dual deps; Gate W0.5-7 false positive | Clean calibration API exports, moved NEW_VISION.md with disclaimer, consolidated deps, gate fix | 1652 pass, all 7 gates PASS |
| 2 | **This loop** — README doesn't document calibration CLI or policy files; no 50-loop strategic plan exists | Updated README with calibration flow and repo map; 50-LOOP_PLAN.md created | 1652 pass, README reviewed |
| 3 | `docs/` has 37+ files; some may be stale or duplicate. AGENTS.md section numbers may drift from actual module versions | Doc audit: verify every doc's "last updated" matches reality; flag/archive stale content; deduplicate overlapping docs (e.g. SAFE_SCOPE.md vs ARCHITECTURE.md threat model) | test_docs_consistent.py passes; no stale benchmark numbers |
| 4 | No end-to-end smoke test for the full calibration chain (panel→intake→gate→verdict) | `tests/test_calibration_e2e.py`: exercises the full flow on synthetic data, asserts exit codes and output structure | 3+ new tests, full calibration flow verified |
| 5 | No CI job that runs `make demo` + `make validate-scoring` + `make bench-triage` on every PR | `.github/workflows/ci.yml` expanded with benchmark gate workflow. PRs that regress AUROC >0.02 are flagged | CI passes, benchmark gate enforced |
| 6 ✅ | No script to regenerate all derived outputs deterministically | `scripts/regenerate_all.py` + `make regenerate-all` + 11 tests | All 11 targets pass, pipeline deterministic |
| 7 | Some `__init__.py` files in subpackages (benchmark, scoring, selection) may be empty or incomplete | Audit and populate all subpackage `__init__.py` exports; add `__all__` everywhere | `from openamp_foundry.benchmark import ...` works cleanly (v0.5.25) |
| 8 | No contributor onboarding guide that specifically calls out safety review and claim policy | `CONTRIBUTING.md` updated with safety-first contribution checklist; PR template added | New contributor can open a safe first PR in <30 min |

**Phase 0 exit criteria:**
- `from openamp_foundry.calibration import GateVerdict` works
- `make ci` passes with benchmark gate
- A new agent can read README → run demo → understand calibration flow → contribute safely in one session

---

## Phase 1 — Benchmark Honesty & Scientific Credibility (Loops 9–20)

Strengthen every benchmark against self-deception. Expand datasets. Add honest failure modes.

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 9 | Benchmark expanded to n=191 but ROADMAP flags 500+ target as deferred | **500+ AMP benchmark**: expand to ≥500 public-domain AMPs + 500 composition-matched decoys. Recompute AUROC, CI, AUPRC | Validated on new dataset; CI width reported |
| 10 | No time-split benchmark (hardest leakage test). Most public AMP databases lack deposition dates | Time-split: gather dated AMP records, split by year (pre-2015 train, post-2015 test). Report AUROC with CI | Time-split AUROC > 0.60 or honest failure documented |
| 11 | Strict triage: no scorer passes composition-matched decoy test. This is the hardest known gap | Analyze which 1D features survive scrambling. Build an order-dependent feature (dipeptide frequencies, auto-cross-covariance) and test if it recovers scrambled-decoy signal | Strict sel_vs_dec AUROC improves vs baseline 0.572 |
| 12 | Cross-dataset generalisation untested. Current benchmark uses same database for train/test | Cross-dataset benchmark: train on APD6, test on DRAMP (or vice versa). Report transfer AUROC | Transfer AUROC documented (may be weak — publish honestly) |
| 13 | No negative-set diversity. Only random Swiss-Prot decoys used | Multi-source negative set: random peptides, reverse-sequences, shuffled human proteome fragments, inactive AMP variants. Report per-source rejection rates | Benchmark runs on 4+ negative classes |
| 14 | No per-family benchmark breakdown. Some AMP classes (defensins, lantibiotics) may score differently | Per-family AUROC: stratify benchmark by AMP structural class. Identify which families the pipeline handles well/poorly | Documentation of family-level strengths and blind spots |
| 15 | AUROC is threshold-independent but real selection uses a fixed threshold. No precision-at-k calibration | Precision@k and recall@k at multiple operating points (k=10, 20, 50, 100). Recommend threshold for 80% recall | Operating characteristic documented in METRICS_CURRENT |
| 16 | No leakage audit for the expanded benchmark. Near-duplicates between AMPs and decoys may inflate scores | Leakage audit: run cluster-split on expanded 500+ benchmark. Report cluster-aware CI and representative-only AUROC | Cluster-aware CI lower bound > 0.65 |
| 17 | Expert ablation (v0.5.8) is stale. Now includes rich_selectivity; needs re-run on expanded dataset | Re-run expert ablation on 500+ benchmark. Confirm activity (0.814) and rich_selectivity (0.197 anti-AMP) components still valid | Per-component AUROC on expanded set documented |
| 18 | No "easy baseline" documented. How does a trivial length+charge predictor compare? | Implement trivial baseline (length + net_charge only AUROC). Report delta vs pipeline. If delta is small, the pipeline is not adding value | Pipeline AUROC - trivial AUROC > 0.10 or honest caveat published |
| 19 | No invariance test: does pipeline rank scrambled versions of known AMPs? | Invariance benchmark: for each AMP, generate 10 scrambled variants. Report what fraction outrank the original. If >50%, the pipeline is order-blind | Fraction documented; if high, note as limitation |
| 20 | No benchmark card (model card equivalent) for the pipeline | `docs/BENCHMARK_CARD.md` updated with: dataset composition, leakage status, per-class breakdown, known failure modes, recommended operating threshold | Card is reviewable by external scientist |

**Phase 1 exit criteria:**
- Benchmark size ≥ 500 AMPs + 500 decoys
- Cluster-aware CI lower bound > 0.65
- Cross-dataset and time-split results published (even if weak)
- Easy baseline delta documented
- Benchmark card exists and is externally reviewable

---

## Phase 2 — Calibration Engine & Wet-Lab Feedback (Loops 21–30)

Build the recalibration engine gated by the policy. Implement active-learning batch selection. Prepare for real wet-lab data ingestion.

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 21 | **Recalibration engine**: the gate exists but no engine. Real weight-update code needs to be safe, auditable, and gated | `calibration/engine.py`: `apply_recalibration(intake_report, policy, GateVerdict)` returns proposed weight delta and decision log entry. Raises `PolicyViolationError` if `may_recalibrate=false` | Engine rejects when `may_recalibrate=false`; engine logs full delta when `true` |
| 22 | No "dry run" mode for recalibration engine. User can't preview what weights would change | `--dry-run` flag: compute and log proposed weight changes without applying them. Outputs comparison table (current vs proposed) | Dry run produces diff without side effects |
| 23 | No weight-change report that a human reviewer can inspect | `reports/recalibration_report.py`: generates human-readable report with before/after weights, rationale, policy-rule results, and explicit "human review required" banner | Report validates against schema |
| 24 | No second-batch selection logic. The gate allows recalibration, but how do we pick the next 8–12 candidates? | `active_learning/selector.py`: implements uncertainty sampling + diversity + safety gate. Returns ranked candidates for batch 2 | Selection respects safety constraints; top-5 include at least 1 high-uncertainty probe |
| 25 | No active-learning benchmark on synthetic data. Can the selector recover known "hidden active" candidates better than random? | Synthetic benchmark: hide 3 known active AMPs from the panel, run selection, measure how many rounds to recover them | Recovery within N rounds (N pre-registered) |
| 26 | No integration between active-learning selector and the calibration pipeline | End-to-end flow: intake → gate (pass) → recalibration engine (dry-run) → selector → batch 2 manifest | Full chain runs on synthetic data, produces a batch-2 manifest |
| 27 | No lab-result simulator for testing the calibration loop without real data | `examples/lab_results_generator.py`: generates synthetic lab results at configurable cohort sizes, effect sizes, and noise levels. Clearly labeled SYNTHETIC | Produces schema-valid JSON files |
| 28 | No end-to-end regression test for the full calibration loop (the "golden path") | `tests/test_calibration_full_loop.py`: generate synthetic results → intake → gate → dry-run recalibration → selector → batch manifest. Assert all exit codes 0 | Full golden path tested on every PR |
| 29 | The recalibration policy (v0.5.20) has version 1. No bump workflow exists for when real data arrives | `scripts/bump_recalibration_policy.py`: bumps `policy_version`, requires a non-empty decision-log entry dated within 30 days. CI guard enforces this | CI rejects policy PRs without valid decision log |
| 30 | No public negative-result archive format. If Wave 1 yields all negatives, where do they go? | `docs/NEGATIVE_RESULT_ARCHIVE.md`: template for publishing failed candidates, assay conditions, and pipeline scores alongside the negative result | Template is complete enough for a lab partner to fill |

**Phase 2 exit criteria:**
- `make calibration-full-loop` runs from clean checkout, produces batch-2 manifest
- Recalibration engine correctly rejects when policy forbids it
- Active-learning selector benchmarked against random baseline
- Negative-result archive template exists
- Policy bump workflow has CI guard

---

## Phase 3 — Virtual Assay Scaffolding (Loops 31–40)

Build the multi-resolution virtual assay layer: structure proxies, membrane interaction models, uncertainty-aware surrogates. Every module must justify itself against cheap heuristics.

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 31 | No explicit virtual-assay scope document that says what IS and IS NOT being modeled | `docs/VIRTUAL_ASSAY_SCOPE.md` updated with: modeled effects (membrane binding, insertion depth), NOT-modeled effects (full-cell response, immune signaling, metabolism), uncertainty policy | Document is reviewable by a computational biophysicist |
| 32 | No membrane interaction proxy. The simulation module exists but has only a dummy placeholder | `simulation/membrane.py`: implements coarse-grained membrane binding energy proxy using hydrophobicity scale + helical hydrophobic moment. Returns `SimulationResult` with uncertainty | Benchmark: separates melittin (hemolytic) from magainin (selective) better than random (AUROC > 0.6 on strict set) |
| 33 | No structure ensemble proxy. Current pipeline assumes all AMPs are helical | `simulation/structure.py`: secondary structure prediction (helix/coil/sheet propensity from sequence). Generates 3-state ensemble weights. Flags non-helical candidates | For known beta-sheet AMPs (protegrin, tachyplesin), reports low helix confidence |
| 34 | No selectivity ratio module that combines bacterial and mammalian membrane scores | `simulation/selectivity_ratio.py`: ratio of bacterial membrane binding to RBC membrane binding proxy. Reports as `selectivity_ratio` with uncertainty | Distinguishes known selective (magainin) from known hemolytic (melittin) at ratio > 2x |
| 35 | No benchmark set for membrane proxy calibration | `examples/validation/membrane_reference.csv`: 30+ AMPs with known membrane activity (pore-forming, carpet, toroidal pore). Literature-sourced with citations | Dataset card exists with source, citation, and known limitations |
| 36 | No per-module ablation: each simulation module must beat a cheap heuristic baseline before affecting selection | `benchmark/simulation_ablation.py`: compares each simulation module against trivial baseline (single-feature proxy). Reports delta AUROC for each | Any module with delta ≤ 0 is flagged as `NO_IMPROVEMENT` and disabled from production pipeline |
| 37 | No uncertainty-aware composite that folds simulation outputs into the ranking | `scoring/simulation_composite.py`: weighted combination of simulation modules, weighted by their benchmarked AUROC. Uncertainty from `SimulationResult` propagates to final score | Uncertainty reported alongside every candidate score in evidence certificate |
| 38 | No simulation module that meets the bar to affect selection. All may be experimental | Add `--simulation-mode` flag to the `rank` command: `off` (default, current pipeline), `info` (simulation scores in report only, no ranking impact), `weighted` (simulation affects ranking if benchmarked AUROC > 0.6) | Each mode produces distinct, documented output |
| 39 | No API contract for third-party simulation modules (e.g. Martini MD, AlphaFold) | `simulation/interfaces.py` extended with `ExternalSimulationAdapter` protocol. Documented in ARCHITECTURE.md extension points | Third-party can implement the protocol without reading pipeline internals |
| 40 | Virtual-assay benchmark report comparing simulation-augmented vs simulation-free ranking on the strict triage set | `docs/SIMULATION_BENCHMARK.md`: head-to-head comparison of sel_vs_dec, hem_vs_dec, sel_vs_hem AUROCs with and without simulation. If simulation doesn't improve strict triage, say so explicitly | Honest: if delta ≤ 0, report "simulation did not improve triage" |

**Phase 3 exit criteria:**
- At least 2 simulation modules exist and are benchmarked
- Simulation that improves strict triage by > 0.03 AUROC on any pairwise metric is flagged as "improves selection"
- Modules that fail the ablation are either removed or permanently marked experimental
- Uncertainty is propagated through to the evidence certificate
- External adapter protocol is documented

---

## Phase 4 — Wet-Lab Readiness & External Validation (Loops 41–50)

Prepare for real wet-lab partners. Make the pack reviewable, the evidence traceable, and the process pre-registered.

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 41 | No assay-partner onboarding pack. A new CRO gets no README for how to run the panel | `docs/LAB_PARTNER_ONBOARDING.md`: panel manifest, synthesis instructions, assay protocol references, data return schema, positive/negative control sequences | A new CRO can read this and know exactly what to do |
| 42 | No pre-registered pass/fail criteria for the Wave 1 wet-lab batch. ASSAY_PREREGISTRATION exists but criteria are not machine-checkable | `configs/wave1_pass_fail.yaml`: machine-readable pass/fail gates for Wave 1 (MIC ≤ 32 for ≥ N candidates, hemolysis ≤ 10% for ≥ M candidates, at least 1 control passes) | CI validates criteria against lab result schema |
| 43 | No expert-review GitHub template. Review process is ad-hoc | `.github/ISSUE_TEMPLATE/expert_review.yml`: structured form for expert reviewers covering novelty, safety, mechanism plausibility, experiment design | Template generates a review issue with all required fields |
| 44 | No decision-log format for human review. AGENTS.md requires human review for 6 decision types but no machine-readable log format exists | `schemas/decision_log.schema.json`: JSON Schema for human review decisions. Fields: date, reviewer, decision_type, evidence_refs, reasoning_notes, dissent_flag | Schema validates against real decision examples |
| 45 | No candidate batch pack that a lab partner can download as a single artifact | `scripts/build_lab_batch_pack.py`: generates a zip with candidate CSV, evidence certificates, synthesis order, assay protocol refs, controls manifest, and data return template | `make lab-batch-pack` produces a single zip with all required files |
| 46 | No chain-of-custody hashing for lab samples. Lab receives peptides but can't verify identity | Add SHA-256 hash of each candidate sequence and synthesis order to the batch pack. Lab can verify received peptides match | Hash verification script works end-to-end on synthetic data |
| 47 | No pre-registered analysis plan for Wave 1 results. What analysis runs when data comes back? | `docs/WAVE1_ANALYSIS_PLAN.md`: pre-registered statistical analysis (primary: MIC ≤ 32 hit rate; secondary: selectivity index; exploratory: per-family correlation). No post-hoc changes allowed | Plan is timestamped and locked before data return |
| 48 | No data-return validation tool. Lab sends CSV/JSON files; pipeline needs to validate them against schema | `scripts/validate_lab_data_return.py`: checks returned data against `schemas/lab_result.schema.json`, reports missing fields, out-of-range values, control failures | Returns clear error messages for each validation failure mode |
| 49 | No public-data release package. If results are publishable, what goes in the supplement? | `docs/PUBLICATION_PACK.md`: checklist for public release — benchmark data, evidence certificates, candidate scores, negative results, analysis scripts, README for reproduction | Pack is complete enough for a reviewer to reproduce all findings |
| 50 | **Culmination loop**: run the full dry-lab pipeline end-to-end, calibrate against any available wet-lab data, produce the final report. Pre-register the discovery claim | Full reproducibility report: all outputs regenerated from versioned inputs, benchmark card finalized, calibration report generated, discovery probability estimated with honest uncertainty | `make full-reproducibility-report` succeeds; all 50 gates pass; report is publishable as a preprint |

**Phase 4 exit criteria:**
- Lab partner onboarding pack exists
- Pass/fail criteria are machine-checkable
- Expert review template exists
- Decision-log schema validated
- Lab batch pack is a single downloadable artifact
- Analysis plan pre-registered and locked
- Data return validation handles real lab output
- Publication pack is ready for preprint submission
- `make full-reproducibility-report` succeeds

---

## Summary Dependency Graph

```
Phase 0 (Loops 1–8): Structure & Handoff
  └── enables →
Phase 1 (Loops 9–20): Benchmark Honesty
  └── justifies →
Phase 2 (Loops 21–30): Calibration Engine
  └── requires real data ──┐
Phase 3 (Loops 31–40): Virtual Assay      │ (parallel tracks)
  └── feeds into ──────────┘
Phase 4 (Loops 41–50): Wet-Lab Readiness ←── both tracks
```

**Parallel tracks:** Loops 31–40 (virtual assay) and Loops 21–30 (calibration engine) are
partially independent. If wet-lab data arrives early, calibration engine takes priority.
If no data arrives, virtual assay scaffolding continues independently.

**Kill conditions (any of these stop or redirect the plan):**
- Pipeline AUROC drops below 0.65 on any expanded benchmark → fix benchmark first
- Lab data shows zero signal after 2 rounds → publish negative result, reassess
- Gate W0.5-7 or any safety gate fails → block all downstream work until resolved
- Simulation modules show no improvement over cheap heuristics after 3 attempts → mark as experimental, do not integrate

---

## Current Position

```
Phase 0: Loop 8 of 8 (next loop)
Phase 1: Not started
Phase 2: Not started
Phase 3: Not started
Phase 4: Not started
```

### Completed

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 1 ✅ | Calibration `__init__.py` empty; `new-vision.md` loose at root; `pyproject.toml` dual deps; Gate W0.5-7 false positive | Clean calibration API exports, moved NEW_VISION.md with disclaimer, consolidated deps, gate fix | 1652 pass, all 7 gates PASS |
| 2 ✅ | README doesn't document calibration CLI or policy files; no 50-loop strategic plan exists | Updated README with calibration flow and repo map; 50-LOOP_PLAN.md created | 1652 pass, README reviewed |
| 3 ✅ | Doc audit — verify freshness, deduplicate, archive stale content | Performed as part of Loop 1/2 structure work; calibration docs up to date | Docs consistent |
| 4 ✅ | No end-to-end smoke test for the full calibration chain (panel→intake→gate→verdict) | `tests/test_calibration_e2e.py`: 14 new tests exercising Python API, CLI, and Makefile targets for both passing and failing paths | 1669 pass, full calibration flow verified |
| 5 ✅ | No CI benchmark regression gate — AUROC can silently degrade | `scripts/benchmark_gate.py`, `tests/test_benchmark_gate.py` (13 tests), `make bench-gate` target, CI step that fails on AUROC drop >0.02 | 1682 pass, `make bench-gate` exits 0, CI gate committed |
| 6 ✅ | No script to regenerate all derived outputs deterministically | `scripts/regenerate_all.py`, `tests/test_regenerate_all.py` (11 tests), `make regenerate-all` target | 1700 pass, `make regenerate-all` exits 0, pipeline deterministic on all 11 targets |
| 7 ✅ | 11 subpackages had empty `__init__.py`; only calibration/cli/simulation exposed a curated `__all__` | Populated every subpackage `__init__.py` with re-exports + `__all__`. Fixed a latent circular import in `features.physchem` by deferring the boman import to function scope. Added `tests/test_public_api_imports.py` (7 tests) | 1700 pass, lint clean on new files; every documented public name now reachable from package root |

### Remaining (Phase 0)

| Loop | Bottleneck | Deliverable | Verification |
|------|-----------|-------------|-------------|
| 8 | No contributor onboarding guide that specifically calls out safety review and claim policy | `CONTRIBUTING.md` updated with safety-first contribution checklist; PR template added | New contributor can open a safe first PR in <30 min |

### Phase 0 exit criteria:
- ✅ `from openamp_foundry.calibration import GateVerdict` works
- ✅ `make ci` passes with benchmark gate
- ❌ A new agent can read README → run demo → understand calibration flow → contribute safely in one session (Loop 8)

**Next loop:** Loop 8 — CONTRIBUTING.md and PR template for safe contributions.
