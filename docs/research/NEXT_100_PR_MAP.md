# Next 100 PR Map

## Purpose

This document translates the OpenAMP vision into a concrete sequence of small, reviewable PRs.

The goal is to make the repo the obvious place where humans and agents can do useful work without needing private maintainer context.

Each PR should be narrow enough to review and strong enough to compound.

## Execution principle

```text
one PR = one bottleneck removed + evidence + docs + safety check
```

Do not use this map as permission for broad autonomous changes.

Safety-sensitive, wet-lab-facing, candidate-release, benchmark-threshold, calibration-policy, or claim-strengthening work requires human review.

## Phase A — First-run excellence

Make the repo easier to run, understand, and verify.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| A1 | Add a `make doctor` command that checks Python version, package install, expected folders, and key optional tools (complete). — scripts/doctor.py: checks Python ≥3.9, pip install, key modules, expected dirs; make doctor target in Makefile; comprehensive environment diagnostics. | New users fail less. | B |
| A2 | Add `openamp-foundry doctor` CLI equivalent (complete). — src/openamp_foundry/cli/commands/doctor.py: _run_doctor() CLI entry point, run_doctor() structured report dict, checks Python ≥3.9, required packages (numpy/scipy/pandas/pytest), openamp_foundry importable, expected dirs (src/tests/docs/schemas/scripts); 63 tests in tests/cli/test_doctor_command.py. | Agents can self-diagnose environment issues. | B |
| A3 | Generate a first-run report after `make demo` (complete). — src/openamp_foundry/cli/commands/first_run_report.py: build_first_run_report() reads demo_ranked.jsonl/evidence/demo_report.md/run_manifest.json; graceful when outputs missing; claim boundary notice enforced in every report; format_first_run_report() human-readable output; 58 tests in tests/cli/test_first_run_report.py. | New users understand outputs faster. | B |
| A4 | Add a `docs/getting-started/FIRST_RUN_WALKTHROUGH.md` with expected outputs and claim boundaries (complete). — docs/getting-started/FIRST_RUN_WALKTHROUGH.md: step-by-step first run guide, expected output shapes, claim boundary warnings, what output means vs doesn't mean. | Converts demo into onboarding. | A |
| A5 | Add test that README quickstart commands stay valid (complete). — tests/test_quickstart.py: validates key quickstart commands are importable and runnable; tests/test_arch_quickstart_batch.py covers batch entrypoints. | Prevents entrypoint drift. | B |
| A6 | Add link-check CI for internal docs (complete). — make doc-links-check: scans docs/ for internal links and verifies targets exist; included in make agent-check. | Prevents doc graph rot. | B |
| A7 | Add a `make docs-check` target (complete). — make docs-check: combined target running doc-links-check and docs-index-check; one-command docs validation for agents and maintainers. | Agents can verify doc-only PRs. | B |
| A8 | Add generated artifact examples with safe toy data (complete). — examples/toy_pipeline_output/: toy_ranked_example.jsonl (3 candidates, TOY- IDs, dry_lab_only=true), toy_certificate_example.json (TOY-CERT-0001, unsupported_claims enforced), README.md; 49 tests in tests/test_toy_examples.py. | Reviewers see what good output looks like. | B |
| A9 | Add `outputs/README.md` explaining generated outputs and ignored files (complete). — outputs/README.md: file pattern table, dry-lab-only notice, what is gitignored, how to regenerate examples; .gitignore updated with !outputs/README.md exception. | Reduces confusion. | A |
| A10 | Add troubleshooting table for install/test failures (complete). — docs/getting-started/TROUBLESHOOTING.md: 10 common failures with root causes and fixes; covers ModuleNotFoundError, BASELINE mismatch, claim violations, broken doc links, benchmark threshold freeze rule. | Faster onboarding. | A |

## Phase B — Evidence certificate hardening

Make candidate evidence packages impossible to confuse with biological proof.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| B1 | Add certificate field for `proof_ladder_level` (complete). | PLC- schema: 14 fields, 14 validation rules, dry_lab_only caps level at multi_signal_candidate_evidence, human_review_required enforced for levels ≥expert_reviewed_assay_proposal, unsupported_claims required as anti-overclaim guard; makes level claim machine-verifiable. | B |
| B2 | Add `unsupported_claims` field to certificates (complete). | CCB- schema: 10 fields, 13 validation rules, 8 claim class vocabulary, ≥3 classes required, dry_lab_only+all_listed_classes_unsupported enforced, no-duplicate check; negative complement of PLC- closes score-to-proof drift gap. | B |
| B3 | Add `baseline_caveat` field (complete). | Added to build_certificate(): auto-computes charge/length/hydrophobicity flags and warns when all three cheap baselines pass; forces cheap-explanation visibility at certificate issue time. 63 tests in tests/test_certificate_baseline_caveat.py. | B |
| B4 | Add `release_status` field. | Supports staged release. | C/D | DONE |
| B5 | Add certificate quality-tier validator (complete). | assess_certificate_quality() computes draft/internal_review/external_review_ready tier; missing-field detection, forbidden-claim violation check, external-review gate; 63 tests in tests/test_certificate_quality_validator.py. | B |
| B6 | Add human-readable certificate report (complete). | build_certificate_report() in certificate_report.py converts cert dict to formatted text with sections: identity, proof ladder, scores, cheap-explanation check, selection reason, failure modes, next steps, references, optional quality tier; 63 tests in tests/test_certificate_report.py. | B |
| B7 | Add candidate rejection certificate support (complete). | CRC- schema: 12 fields, 13 rules, VALID_REJECTION_GATES (10 values), VALID_REJECTION_REASONS (12 values), dry_lab_only enforced, proof-ladder cap at multi_signal; makes pipeline rejections first-class auditable artifacts; 63 tests. | B |
| B8 | Link certificates to run manifest hashes (complete). | Added run_id and run_manifest_hash optional params to build_certificate(); every certificate is now traceable to the exact pipeline run and manifest that produced it; backward-compatible (defaults to empty string); 63 tests in tests/test_certificate_run_link.py. | B |
| B9 | Add test that dry-lab certificates cannot include forbidden claims (complete). | CI gate: tests/test_certificate_claim_discipline.py scans all cert text fields against RISKY_PATTERNS and FORBIDDEN_CLAIM_PATTERNS; default cert proven clean; forbidden phrases confirmed detectable. 35 tests total. | B/C |
| B10 | Add external-review packet generator that bundles certificates (complete). — src/openamp_foundry/evidence/external_review_packet.py: ExternalReviewPacket dataclass, validate_external_review_packet(), format_external_review_packet(); scripts/generate_review_packet.py; 140+ tests across test_external_review_packet.py, test_external_review_packet_schema.py, test_example_external_review_packet.py. | Better partner review. | C/D |

## Phase C — Benchmark honesty expansion

Make OpenAMP the hardest repo to fool in AMP dry-lab selection.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| C1 | Create machine-readable benchmark cards (complete). | benchmark_registry.py: 5 BMC- cards (BMC-0001 to BMC-0005) for precision@k, charge-matched, calibration, family-stratified, cheap-enemy-comparison benchmarks; get_card()/validate_registry() API; 63 tests in tests/evidence/test_benchmark_registry.py. | B |
| C2 | Add benchmark-card schema (complete). | BMC- schema: 12 fields, 14 validation rules, VALID_MEASUREMENT_TARGETS (10), VALID_SPLIT_STRATEGIES (10), VALID_EVALUATION_METRICS (12), cheap_enemy_baselines required (≥1, warns if <2), known_limitations required (≥1), deprecated+notes dependency; 63 tests. | B |
| C3 | Add charge-distribution report for every benchmark (complete). | compute_charge_report(sequences, labels) in charge_distribution_report.py: charge stats for pos/neg groups, fraction_positive_high_charge, charge_ratio, charge_shortcut_likely flag and warning; SHORTCUT_WARNING_FRACTION=60%, SHORTCUT_RATIO_THRESHOLD=1.5; 63 tests. | B/C |
| C4 | Add similarity-neighbor distribution report (complete). | similarity_neighbor_report.py: detects novelty shortcut when >50% of positives have >=80% similarity to known AMPs; _sequence_similarity(), _nearest_neighbor_similarity(), SimilarityNeighborReport with novelty_shortcut_likely; compute_similarity_report(), format_similarity_report(); 63 tests. | B/C |
| C5 | Add `bench-length-matched` control (complete). | length_distribution_report.py: detects length shortcut (AMP_LENGTH_MIN=10, AMP_LENGTH_MAX=40), SHORTCUT_RATIO_THRESHOLD=1.5, SHORTCUT_FRACTION_THRESHOLD=0.60; LengthDistributionReport with length_shortcut_likely; 63 tests. | C |
| C6 | Add `bench-charge-length-matched` control (complete). | charge_length_report.py: combined charge+length shortcut (COMBINED_CHARGE_THRESHOLD=4, length 10-40), COMBINED_SHORTCUT_RATIO_THRESHOLD=1.5; ChargeLengthReport with combined_shortcut_likely; _net_charge_proxy(), _is_charge_length_match(); 63 tests. | C |
| C7 | Add family-stratified precision@k (complete). | family_stratified_report.py: detects family inflation (FAMILY_INFLATION_DOMINANCE_THRESHOLD=0.60); FamilyStratifiedReport with dominant_family, family_inflation_likely; _precision_at_k(), _family_counts_in_top_k(); 63 tests. | C |
| C8 | Add benchmark-deprecation banner system (complete). | benchmark_deprecation.py: get_deprecated_cards(), build_deprecation_banner(), check_no_deprecated_in_ranking() (raises DeprecatedBenchmarkError), deprecation_status_report(); 63 tests; main registry confirmed all-active. | B |
| C9 | Add command that compares all advanced scorers against declared cheap enemies (complete). | cheap_enemy_comparison.py: compute_cheap_enemy_comparison() enforces ranking_authority_granted=True only when ALL enemies beaten (strict >/<); EnemyResult, CheapEnemyComparisonReport; higher_is_better param for calibration_error; 63 tests. | C |
| C10 | Add benchmark governance CI that rejects missing benchmark cards for new benchmark scripts (complete). | benchmark_governance.py: GOVERNED_SCRIPTS frozenset, SCRIPT_TO_BMC_ID mapping, GovernanceReport, check_governance(), format_governance_report(); CI check that governed benchmark scripts have registered BMC- cards; 63 tests. | B/C |

## Phase D — Agent excellence

Make OpenAMP a gold-standard repo for safe agent contribution.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| D1 | Add `AGENT_TASKS.json` with machine-readable task categories and forbidden zones (complete). | Agents can self-classify tasks. | B |
| D2 | Add agent-safe issue examples (complete). — docs/operations/AGENT_SAFE_ISSUES.md: issue template with safety classification checklist, good vs bad examples. | Better issue creation. | A |
| D3 | Add agent PR self-check script that scans for forbidden claim language (complete). | pr_claim_checker.py: check_pr_claims() scans .md/.py/.rst/.txt for 11 forbidden patterns; PR_ALLOWLIST skips known-safe files; ClaimViolation, PRClaimReport; format_pr_claim_report(); 63 tests. | B |
| D4 | Add docs-only PR verifier (complete). | scripts/check_docs_only_pr.py: checks whether a PR only touches docs/. | B |
| D5 | Add `make agent-check` target combining doc links, claim scan, and safety phrase scan (complete). | agent-check: claim-check doc-links-check bench-deprecation-check in Makefile. | B |
| D6 | Add agent stop-condition examples (complete). — docs/operations/AGENT_STOP_CONDITIONS.md: 3 worked stop-condition examples with decision-log draft template. | Reduces scope creep. | A |
| D7 | Add maintainer prompts for assigning agent-safe tasks (complete). — docs/operations/MAINTAINER_AGENT_TASK_GUIDE.md: 3 dispatch prompt templates (schema, docs-only, map-update), issue labeling convention, agent failure signals, pre-assignment checklist. | Better human-agent coordination. | A |
| D8 | Add `docs/AGENT_FAILURE_MODES.md` (complete). | 10 failure modes (FM-01 to FM-10): claim escalation, scope creep, benchmark theater, safety weakening, certificate confusion, calibration self-service, hidden dependencies, novelty over-attribution, unsafe parallelism, stop-condition bypass; detection signals and mitigations for each. | A |
| D9 | Add CI warning for newly added top-level docs not in project index (complete). | scripts/check_docs_index_coverage.py: warns on docs/*.md files not referenced in PROJECT_INDEX.md; make docs-index-check target; allowlist for known exceptions. | B |
| D10 | Add structured agent contribution summary template (complete). | docs/operations/AGENT_CONTRIBUTION_SUMMARY_TEMPLATE.md: failure-mode self-check table (FM-01 to FM-10), disconfirming pass checklist, automated check results, stop-condition gate, test coverage, proof-ladder level, one-sentence verdict. | B |

## Phase E — Safe external review infrastructure

Make qualified external review easier and safer.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| E1 | Add external review packet schema (complete). — evidence/external_review_packet.py: ERP- schema with 14 fields, validation rules, dry_lab_only enforcement; tests/evidence/test_external_review_packet.py + test_external_review_packet_schema.py. | Packets become machine-checkable. | C/D |
| E2 | Add example external review packet using toy data (complete). — evidence/example_external_review_packet.py: toy-data example ERP with MOCK-/TOY- prefix enforcement and is_example_data=True; tests/evidence/test_example_external_review_packet.py. | Partners know what to expect. | C/D |
| E3 | Add reviewer questionnaire schema (complete). | Makes external review feedback machine-readable: Likert clarity ratings for activity/safety/novelty claims, synthesis recommendation, structured comments. | B/C |
| E4 | Add safety-release decision schema. | Release review becomes auditable. | D | DONE |
| E5 | Add non-protocol pilot pre-registration schema (complete). — evidence/pilot_preregistration.py: non-protocol pilot pre-registration schema (PPR-) freezing selection logic before batch release; tests/evidence/test_pilot_preregistration.py + test_pilot_preregistration_schema.py. | Freezes selection logic. | C/D |
| E6 | Add packet generator CLI (complete). — scripts/generate_review_packet.py: generates skeleton external review packet JSON; make generate-review-packet target; validates against schemas/external_review_packet.schema.json; dry_lab_only_attestation=True enforced. | Reduces manual packaging errors. | C/D |
| E7 | Add packet validator CLI (complete). — src/openamp_foundry/cli/commands/validate_packet.py: load_packet_from_json() reads ERP- JSON from disk; validate_packet_file() returns {valid, violations, packet_id, error}; _run_validate_packet() prints PASS/FAIL with violations; 45 tests in tests/cli/test_validate_packet.py. | Review readiness becomes testable. | C/D |
| E8 | Add release-summary generator that strips restricted fields. | Safer public summaries. | D | DONE |
| E9 | Add domain review outcome schema (complete). | Structured expert verdict on a PEP with controlled taxonomy of domains and outcomes; closes ESC→RVQ→DRO review chain. | B/C |
| E10 | Add expert-review example with mock/toy candidates only (complete). | ERP- schema: 14 fields, 16 validation rules, mock candidate ID prefix enforcement (MOCK-/TOY-/EXAMPLE-/DEMO-/TEST-), is_example_data=True and dry_lab_only=True enforced; CI-checkable template cannot accidentally leak real candidates. | B/C |

## Phase F — Negative-result infrastructure

Make failure useful.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| F1 | Add negative-result entry schema hardening (complete). | Atomic NRR- failure record: controlled vocabulary for stage/reason/confidence, foundation for NAS- and FCR- negative-result chain. | B/C |
| F2 | Add negative-result archive summary schema (complete). | Prevents incomplete archives: indexes NRR- entries, enforces completeness_confirmed and all_results_have_reason before batch is marked archived. | B |
| F3 | Add rejection reason entry schema (complete). | Enables analysis of failed candidates with controlled vocabulary of stages and reasons; feeds calibration loop with structured failure signal. | B |
| F4 | Add failed candidate batch report schema (complete). | Makes failed batches reviewable: links RJR- rejection reasons and NAS- archive into a validated batch-level report with failure rate consistency check. | B/C |
| F5 | Add safe-publication filter for negative results. | Supports openness without unsafe release. | D | DONE |
| F6 | Add examples of non-informative vs informative negative results (complete). — docs/evidence/NEGATIVE_RESULT_EXAMPLES.md: 5 worked examples (hemolysis rejection, module timeout, dual-use flag, ad-hoc removal, low-confidence borderline); summary table; agent MUST rules. | Better interpretation. | A |
| F7 | Add calibration link from negative-result entries to intake reports (complete). — evidence/negative_result_calibration_link.py: links NRR- rejection records to calibration intake reports for closed-loop learning; tests/evidence/test_negative_result_calibration_link.py. | Closes learning loop. | C |
| F8 | Add benchmark for whether rejected candidates resemble known failure modes (complete). — FMS- schema: 14 fields, 11 validation rules, PATTERN_REPEATED_THRESHOLD=0.80, pattern_repeated_flag enforcement, calibration_action_recommended; 63 tests. | Improves rejection logic. | C |
| F9 | Add negative-result dashboard schema (complete). | NRD- aggregates NRR- rejection statistics: rejection rate consistency check, all_rejections_have_nrr enforced, top stage/reason controlled vocabulary, 100% rejection warning. | B |
| F10 | Add policy that public claims must mention relevant negative results. | Prevents cherry-picking. | D | DONE |

## Phase G — Calibration and active-learning rigor

Make learning controlled rather than self-serving.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| G1 | Add machine-readable recalibration decision log examples (complete). | RDL- schema: 13 fields, 13 validation rules, 4 outcomes, 5 trigger types, deferred-requires-conditions enforced; closes governance audit trail for calibration decisions. | B |
| G2 | Add recalibration rejection examples (complete). | RRS- schema: 13 fields, 15 validation rules, refusal_rate consistency check (tol 0.01), all_refusals_have_rrf=True enforced, gate status controlled vocabulary; shows gate success by audit-ready refusal aggregation. | B |
| G3 | Add `make calibration-audit` (complete). — make calibration-audit: runs INTAKE/GATE/ENGINE/REPORT consistency checks; make calibration-audit-example also available; tests/calibration/test_calibration_audit.py. | Checks intake/gate/engine/report consistency. | C |
| G4 | Add active-learning strategy comparison report (complete). — active_learning/strategy_comparison.py: compares exploit/explore/diversity selector strategies; StrategyComparisonReport; 18 tests in tests/active_learning/test_strategy_comparison.py. | Prevents one-selector bias. | C |
| G5 | Add batch-2 rationale report explaining exploit/explore/diversity roles (complete). — active_learning/batch_rationale.py: BatchRationaleReport explaining exploit/explore/diversity composition; 19 tests in tests/active_learning/test_batch_rationale.py. | Reviewers understand next batch. | C |
| G6 | Add calibration-overfit warning when cohort is too small (complete). — calibration/overfit_warning.py: detects cohort-too-small condition and emits OverfitWarning; make calibration-overfit-check target; tests/calibration/test_overfit_warning.py. | Prevents false learning. | C |
| G7 | Add result-quality flag propagation into calibration engine (complete). — calibration/result_quality.py: flags low-quality outcomes before they enter calibration; make result-quality-filter target; tests/calibration/test_result_quality.py (27 tests). | Low-quality outcomes cannot drive updates. | C |
| G8 | Add policy that synthetic results cannot raise proof-ladder level (complete). | SBR- schema: 14 fields, 16 validation rules, synthetic-only evidence cannot propose level ≥4 without violations recorded, policy_enforced=True enforced, violation rate consistency check (tol 0.01); anti-overclaim boundary is now auditable artifact. | B/C |
| G9 | Add calibration decision review checklist (complete). — calibration/decision_checklist.py: CHECKLIST_ITEMS (12 items, 11 required), CalibrationDecisionChecklist (8 fields), build_checklist(), write_checklist_json(), write_checklist_markdown(); 14 tests in tests/calibration/test_decision_checklist.py. | Human review stronger. | C/D |
| G10 | Add recalibration rollback plan (complete). — calibration/rollback_plan.py: structured plan for rolling back a calibration update if quality degrades; make calibration-rollback-plan target; tests/calibration/test_rollback_plan.py. | Safer updates. | C |

## Phase H — Virtual assay discipline

Make simulation useful or harmless.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| H1 | Add simulation module registry (complete). — simulation/module_registry.py: registry of simulation modules with status and evidence level; make simulation-registry target; 28 tests in tests/simulation/test_module_registry.py. | Shows status and evidence level. | B |
| H2 | Add simulation-result schema (complete). — schemas/simulation_result.schema.json: JSON schema for simulation proxy outputs; simulation/result_validator.py validates against schema; make validate-simulation-result-schema target; tests/simulation/test_result_validator.py. | Prevents undocumented proxy output. | B/C |
| H3 | Add per-module cheapest-baseline declaration (complete). — simulation/baseline_registry.py: per-module cheapest-baseline scores for cheap-enemy comparison; make simulation-baseline-check target; tests/simulation/test_baseline_registry.py. | Forces enemy comparison. | C |
| H4 | Add fail-closed adapter integration tests (complete). — simulation/adapter_gate.py: fail-closed integration gate that blocks if adapter returns error or timeout; make adapter-gate-check target; tests/simulation/test_adapter_gate.py. | Avoids hidden external failures. | B/C |
| H5 | Add no-silent-network policy test for adapters. | Protects sequence privacy. | D | DONE |
| H6 | Add simulation uncertainty calibration report (complete). — SUC- schema: 14 fields, 10 validation rules, VALID_SIMULATION_MODULES (7 values), VALID_CALIBRATION_METHODS (6 values), OVERCONFIDENCE_THRESHOLD=0.15, MIN_SAMPLES_FOR_CALIBRATION=10; makes module confidence interval calibration machine-auditable; 63 tests. | Makes uncertainty inspectable. | C |
| H7 | Add documentation that failed simulation stays useful as negative evidence (complete). — docs/FAILED_SIMULATION_AS_NEGATIVE_EVIDENCE.md: cultural standard requiring NRR- record for every failure; agent MUST NOT rules; anti-selective-reporting enforcement. | Cultural standard. | A |
| H8 | Add `weighted` integration dry-run report, still blocked by gate (complete). — WDR- schema: 15 fields, 12 validation rules, results_applied_to_ranking=False enforcement, GATE_CLOSED_DISCLAIMER required, counterfactual-only; 63 tests. | Shows what would change without applying. | C |
| H9 | Add module deprecation mechanism for simulation theater (complete). — simulation/deprecation_enforcer.py: marks and enforces deprecation of simulation modules that produce theater (no real predictive value); make simulation-deprecation-check target; tests/simulation/test_deprecation_enforcer.py. | Cleanup discipline. | B/C |
| H10 | Add external-simulator review checklist. | Safer ecosystem bridges. | D | DONE |

## Phase I — Interoperability and adoption

Make OpenAMP artifacts useful even without OpenAMP scoring.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| I1 | Add FASTA export for final candidate set (complete). — export/fasta_export.py: exports final candidate set as FASTA with dry-lab-only header annotations; tests/export/test_fasta_export.py. | Standard format for partner labs. | B |
| I2 | Add JSON-LD context for evidence certificates (complete). — interop/jsonld_context.py: JSON-LD @context for evidence certificates enabling semantic web compatibility; tests/interop/test_jsonld_context.py. | Semantic web compatibility. | B |
| I3 | Add citation template for data consumers (complete). — docs/CITATION_TEMPLATE.md: APA, BibTeX, CFF, in-text, data-availability formats; dry-lab-only anti-overclaim embedded in every format. | Proper attribution. | A |
| I4 | Add OpenAMP output → external tool adapter stub (complete). — interop/adapter_stub.py: generic adapter stub for routing OpenAMP candidate outputs to external tools; tests/interop/test_adapter_stub.py. | Reduces integration friction. | B |
| I5 | Add cross-repo evidence traceability field (complete). — evidence/cross_repo_traceability.py: traceability record linking artifacts across repositories for multi-lab reproducibility; tests/evidence/test_cross_repo_traceability.py. | Multi-lab reproducibility. | C |
| I6 | Add versioned schema export (complete). — versioning/schema_export.py: exports schemas with version metadata for stable partner API; tests/versioning/test_schema_export.py. | Stable API for partners. | B |
| I7 | Add comparative summary across multiple candidate batches (complete). — BCS- schema: 14 fields, 12 validation rules, VALID_TREND_DIRECTIONS, VALID_QUALITY_TIERS, MIN_BATCHES_FOR_TREND=2; trend consistency enforced; 63 tests. | Shows trajectory, not just snapshots. | C |
| I8 | Add machine-readable release manifest (complete). — evidence/release_manifest.py: machine-readable manifest of what was released in each pipeline run; tests/evidence/test_release_manifest.py. | Downstream tools can parse what was released. | B |
| I9 | Add public API stub with rate-limit and privacy policy stubs. | Safety for eventual public access. | D | DONE |
| I10 | Add annotation layer for wet-lab-updated evidence. | Closes the wet-lab feedback loop. | D | DONE |

## Phase J — Long-term infrastructure

Make the repo survive contributors, updates, and time.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| J1 | Add changelog generator from PR titles (complete). — changelog/changelog_entry.py + changelog/artifact_changelog.py: generates changelog from PR titles and links to artifact versions; tests/changelog/test_changelog_entry.py + test_artifact_changelog.py. | History without manual maintenance. | B |
| J2 | Add schema version migration guide (complete). — docs/SCHEMA_MIGRATION_GUIDE.md: step-by-step guide for migrating artifacts when schemas change; backward-compatibility rules, deprecation policy. | Schema updates don't break old artifacts. | B |
| J3 | Add docs coverage report (complete). | Shows what is and isn't documented. | B |
| J4 | Add deprecation policy document (complete). | Makes obsolescence intentional. | A |
| J5 | Add long-term archival format specification (complete). — docs/ARCHIVAL_FORMAT_SPEC.md: 9 sections, directory layout, VERSION.txt format, checksums.sha256, anti-rot guarantees, agent MUST NOT rules. | Evidence survives software churn. | C |
| J6 | Add public license and reuse guide (complete). — docs/LICENSE_AND_REUSE_GUIDE.md: Apache 2.0 terms, artifact-specific constraints, dry-lab-only preservation requirement. | Community adoption enabled. | A |
| J7 | Add contributor covenant and attribution policy (complete). — docs/CONTRIBUTOR_COVENANT.md: overclaiming as explicit violation, AI attribution policy, artifact attribution rules. | Fair credit for future contributors. | A |
| J8 | Add automated stale-doc detector (complete). — checks/stale_doc_detector.py: detects docs that reference non-existent files, outdated schema names, or broken anchor links; tests/checks/test_stale_doc_detector.py. | Reduces doc rot over time. | B |
| J9 | Add cross-reference checker between schemas and tests (complete). — checks/schema_test_coverage.py: verifies each schema module has a corresponding test file; SchemaCoverageReport; tests/checks/test_schema_test_coverage.py. | Ensures tests stay coupled to schemas. | B |
| J10 | Add end-to-end dry-run test for full pipeline from sequences to evidence package (complete). — tests/test_pipeline_dry_run_e2e.py: 20 tests chaining fasta_export, scoring, evidence certificates, and pilot evidence package using TOY- sequences only; no external calls or disk I/O. | Smoke test for whole system. | B/C |

## Phase P — Pilot batch infrastructure

Prepare for the first real (non-toy) batch under dry-lab-only, human-reviewed conditions.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| P1 | Add batch selection proposal schema (complete). | BSP- schema: 14 fields, 17 validation rules, calibration_gate_passed enforcement, proposal_basis controlled vocabulary, all_sequences_dry_lab_only enforced, pre_selection_checklist required (≥3 items), funding_status required; calibration gate must pass before next batch release. | B/C |
| P2 | Add recalibration refusal record schema (complete). | RRF- schema: 14 fields, 14 validation rules, refusal_rate consistency check (tol 0.01), recalibration_baseline correction (4889→4784), corrects inflated BASELINE; auditable rejection of spurious recalibrations. | B/C |
| P3 | Add batch outcome summary schema (complete). | BOS- schema: 14 fields, 14 validation rules, synthetic/real boundary enforcement (all_outcomes_are_real requires dry_lab_only=False), hit_rate consistency check (tol 0.01), n_confirmed_hits ≤ n_total_outcomes enforced; closes BSP-to-outcomes feedback loop. | B/C |
| P4 | Add pilot batch safety clearance schema (complete). | PSC- schema: 14 fields, 15 validation rules, safety gate requiring all 4 screens (toxicity/hemolysis/off_target/dual_use) before wet-lab synthesis, blocks high-risk batches. | B/C |
| P5 | Add calibration cycle summary schema (complete). | CCS- schema: 14 fields, 15 validation rules, index record for complete BSP→PSC→BOS→CPS→CBA→CRG feedback loop; cycle_health controlled vocabulary; closes Phase P. | B/C |

## Phase Q — Wet-lab result intake and feedback loop

Close the loop between dry-lab nominations and actual experimental outcomes. First phase where real (non-synthetic) results enter the evidence trail.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| Q1 | Add pilot evidence package schema (complete). — src/openamp_foundry/evidence/pilot_evidence_package.py: PEP- schema linking CCS+BSP+PSC+PRE+BCM artifacts; completeness gate, safety enforcement, reference chain validation; docs/evidence/PILOT_EVIDENCE_PACKAGE_GUIDE.md; 63 tests. | External export bundle with full provenance. | B/C |
| Q2 | Add wet-lab hit record schema (WHR-) (complete). — src/openamp_foundry/evidence/wetlab_hit_record.py: WHR- 16-field schema; dry_lab_only=False enforced; VALID_EXPERIMENT_TYPES (10), VALID_INTERPRETATIONS (active/inactive/inconclusive), proof_ladder_level cap; 59 tests in tests/evidence/test_wetlab_hit_record.py. | First machine-readable record of actual experimental outcome; dry_lab_only must be False; closes nomination→experiment loop. | B/C |
| Q3 | Add post-experiment calibration update schema (complete). — src/openamp_foundry/evidence/post_experiment_calibration_update.py: PCU- 16-field schema; dry_lab_only=False enforced; human_reviewed=True required; VALID_UPDATE_DIRECTIONS (5), VALID_CALIBRATION_TRIGGER_TYPES (7); n_whr_records/whr_ids consistency check; 55 tests in tests/evidence/test_post_experiment_calibration_update.py. | Records how wet-lab results change score calibration; evidence trail for model improvement decisions. | B/C |
| Q4 | Add hit confirmation report generator (complete). — src/openamp_foundry/evidence/hit_confirmation_report.py: HCR- 16-field schema; VALID_CONFIRMATION_VERDICTS (4), VALID_DIVERGENCE_TYPES (7), VALID_PREDICTION_QUALITY_GRADES (A/B/C/D/N/A); dry_lab_only=False enforced; confirmed_hit requires n_confirmed≥1; not_confirmed requires n_inactive≥1; no_divergence exclusive with other divergence types; 70 tests in tests/evidence/test_hit_confirmation_report.py. | Bundles WHR- records with pre-registration for reproducibility check; flags prediction vs actual divergence. | B/C |
| Q5 | Add Phase Q completeness gate (closes Phase Q) (complete). — src/openamp_foundry/evidence/phase_q_completeness_gate.py: PQG- 12-field schema; REQUIRED_RECORD_TYPES (BSP/WHR/PCU/HCR), VALID_LOOP_VERDICTS (4); loop_complete enforces all four record types and no cross-link failures; dry_lab_only=False enforced; n_candidates_with_hcr ≤ n_candidates_with_whr enforced; 68 tests in tests/evidence/test_phase_q_completeness_gate.py. | Machine-verifiable that the full dry-lab→wet-lab→calibration loop has run for at least one candidate family. | C |

## Phase R — Scientific output readiness

Make the full pipeline auditable and reviewable by external scientists. First phase where the system produces outputs that could accompany a preprint or data release.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| R1 | Add candidate family clustering evidence schema (CFC-) (complete). — src/openamp_foundry/evidence/candidate_family_clustering.py: CFC- 15-field schema; VALID_NOVELTY_EVIDENCE_TYPES (6), VALID_CLUSTERING_METHODS (5), VALID_NOVELTY_VERDICTS (4); novel_family requires hard evidence (blast/hmm/structural/charge); variant_of_known requires known_family_hits; n_candidates≥2 enforced; dry_lab_only=True enforced; 66 tests in tests/evidence/test_candidate_family_clustering.py. | Machine-verifiable grouping of related candidates into a "novel family" claim; sequence similarity threshold, family size, novelty evidence type controlled vocabulary. | B/C |
| R2 | Add family novelty report schema (FNR-) (complete). — src/openamp_foundry/evidence/family_novelty_report.py: FNR- 13-field schema; VALID_BASELINE_COMPARISON_OUTCOMES (4), VALID_NOVELTY_STRENGTH_GRADES (4), VALID_CHEAP_BASELINES_CHECKED (5); strong grade requires outside_known_space; not_supported incompatible with outside_known_space; cheap_enemy_score/family_score in [0,1]; dry_lab_only=True enforced; 64 tests in tests/evidence/test_family_novelty_report.py. | Bundles CFC- clustering with cheap-baseline comparison; prevents "novel family" overclaim when candidates are merely sequence variants of known AMPs. | B/C |
| R3 | Add full audit trail report schema (ATR-) linking BSP→WHR→PCU→HCR→PQG for a complete dry-lab→wet-lab loop trace (complete). — src/openamp_foundry/evidence/audit_trail_report.py: ATR- 15-field schema; REQUIRED_ATR_STAGES (5: BSP/WHR/PCU/HCR/PQG), VALID_TRAIL_COMPLETENESS_STATUSES (4), VALID_CHAIN_INTEGRITY_GRADES (5); complete status enforces all 5 stages; grade D incompatible with complete; build() auto-computes n_stages_complete; dry_lab_only=True enforced; 70 tests in tests/evidence/test_audit_trail_report.py. | End-to-end chain of custody from nomination to confirmed hit; required for scientific reproducibility. | B/C |
| R4 | Add scientific review readiness gate schema (SRG-) (complete). — src/openamp_foundry/evidence/scientific_review_readiness_gate.py: SRG- 15-field schema; REQUIRED_SRG_ARTIFACT_TYPES (4: CFC/FNR/ATR/PQG), VALID_READINESS_VERDICTS (4), VALID_SAFETY_FLAG_TYPES (6), VALID_REVIEW_SCOPE_TYPES (4); ready_for_external_review blocks safety flags and failed_gates; open_preprint/peer_review blocked when not_ready/review_blocked_by_safety; dry_lab_only=True enforced; 63 tests in tests/evidence/test_scientific_review_readiness_gate.py. | Machine-verifiable checklist for when a candidate family has enough evidence for external scientific review; requires CFC+FNR+ATR+PQG records and no unresolved safety flags. PR #962. | C |
| R5 | Add preprint evidence bundle schema (PEB-) — read-only snapshot of all evidence for a run (complete). — src/openamp_foundry/evidence/preprint_evidence_bundle.py: PEB- 19-field schema; VALID_BUNDLE_STATUSES (5: draft/internal_review/approved/submitted/published), VALID_PREPRINT_SERVERS (7), VALID_CLAIM_STRENGTH_TIERS (4); DRY_LAB_ONLY_DISCLAIMER canonical text enforced; published requires DOI; submitted/published require real server; replicated_wet_lab requires n_confirmed_hits≥2; dry_lab_only=True enforced; 66 tests in tests/evidence/test_preprint_evidence_bundle.py. BASELINE: 9152→9215. PR #964. | External reviewers can verify every claim from a single self-contained artifact; closes Phase R. | C |

## Phase S — Score transparency and external credibility

Make it possible for an external reviewer to understand, in one artifact, why specific candidates were selected and how the pipeline's scores compare to cheap baselines. The bottleneck to external credibility is "Can the system help choose real experiments better than cheap baselines?" — every item here answers part of that question.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| S1 | Add score vs cheap-enemy gap report schema (SEG-) (complete). — src/openamp_foundry/evidence/score_enemy_gap_report.py: SEG- 16-field schema + CheapEnemyResult helper; VALID_GAP_VERDICTS (4: gap_meaningful/gap_marginal/gap_absent/comparison_not_run), VALID_CHEAP_ENEMY_TYPES (8), VALID_GAP_ASSESSMENT_METHODS (5); MINIMUM_MEANINGFUL_GAP=0.05; build() auto-computes verdict+best_enemy+gap; dry_lab_only=True enforced; 53 tests. BASELINE: 9215→9278. PR #966. | Flags when pipeline score margin over best cheap baseline is below a meaningful threshold; prevents advancing candidates that cheap baselines explain equally well. | C |
| S2 | Add selection transparency ledger schema (STL-) (complete). — src/openamp_foundry/evidence/selection_transparency_ledger.py: STL- 16-field schema + ArtifactReference helper; VALID_SELECTION_BASES (8), VALID_SELECTION_OUTCOME_TYPES (7), VALID_LEDGER_COMPLETENESS_GRADES (4); REQUIRED (BSP/SEG/SRG); not_specified blocked; complete grade requires all required; build() auto-computes completeness; dry_lab_only=True; 48 tests. BASELINE: 9278→9341. PR #968. | Per-candidate-family ledger of every evidence artifact that influenced selection; makes selection_basis auditable and traceable. | C |
| S3 | Add evidence completeness checker schema (ECC-) (complete). — src/openamp_foundry/evidence/evidence_completeness_checker.py: ECC- 17-field schema + ArtifactPresenceRecord helper; EXPECTED_ARTIFACT_TYPES (10: BSP/WHR/PCU/HCR/PQG/CFC/FNR/ATR/SRG/PEB), VALID_COMPLETENESS_GRADES (5: A-D/N/A); grade A=all present→ready_for_review; grade B=all dry+≥2 wet→ready_for_review; grade C=all dry,wet incomplete→dry_lab_review_only; grade D=dry missing→not_ready; build() auto-computes from present_artifact_ids dict; dry_lab_only=True; 63 tests. BASELINE: 9341→9404. PR #971. | Lists all expected artifact types (BSP/WHR/PCU/HCR/PQG/CFC/FNR/ATR/SRG/PEB) and which are present/absent for a candidate family; completeness_grade (A–D); closes "what's still needed for review?" question. | C |
| S4 | Add pipeline run stability report schema (RSR-) (complete). — src/openamp_foundry/evidence/pipeline_run_stability_report.py: RSR- schema; PipelineRunStabilityReport (18 fields) + RunRankRecord helper; VALID_STABILITY_VERDICTS (4: stable/borderline/unstable/single_run), VALID_COMPARISON_METHODS (5); DEFAULT_STABILITY_THRESHOLD=2.0; stable=rank_std<threshold; borderline=threshold to 2x; unstable≥2x; single_run blocked; build() auto-computes from run_records list; dry_lab_only=True; 63 tests. BASELINE: 9404→9467. PR #973. | Compares outputs across N pipeline runs; flags candidate families whose ranking is unstable across runs; prevents overconfident selection of borderline candidates. | C |
| S5 | Add prediction quality trend report schema (PQT-) (complete). — src/openamp_foundry/evidence/prediction_quality_trend_report.py: PQT- schema; PredictionQualityTrendReport (16 fields) + WHROutcomeRecord helper; VALID_TREND_VERDICTS (4: improving/stable/degrading/insufficient_data); DEFAULT_ROLLING_WINDOW=5, DEFAULT_ALERT_THRESHOLD=0.1; degrading triggers degradation_alert; Pearson score_hit_correlation; build() auto-computes rolling precision, trend, alert; dry_lab_only=True; 72 tests. BASELINE: 9467→9530. PR #975. Closes Phase S. | Tracks cumulative prediction quality across all confirmed WHR results; rolling precision/accuracy trend; degradation alerts; closes Phase S. | C |

## Phase T: Batch traceability and cross-batch audit (T1–T5)

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| T1 | Add batch traceability index schema (BTI-) (complete). — src/openamp_foundry/evidence/batch_traceability_index.py: BTI- schema; BatchTraceabilityIndex (14 fields) + FamilyArtifactEntry helper; REQUIRED_BATCH_ARTIFACT_TYPES (4: BSP/SEG/ECC/STL); VALID_FAMILY_COMPLETENESS_GRADES (3: complete/partial/empty); VALID_BATCH_COMPLETENESS_GRADES (4: full/majority/minority/none); build() auto-computes from family_artifact_dicts; dry_lab_only=True; 61 tests. BASELINE: 9530→9576. PR #977. | Per-batch index linking every candidate family in the batch to its evidence artifacts (BSP/SEG/ECC/STL/RSR/PQT); required_artifact_ids computed; completeness_grade (complete/partial/empty); enables cross-batch audit. | C |
| T2 | [x] Add cross-batch audit summary schema (CBA2-). (#980) | Aggregates BTI records across all batches; counts families per grade; flags batches with low completeness; required for multi-batch meta-analysis. | C |
| T3 | [x] Add batch evidence gap report schema (BEG-) (#983). | Per-batch listing of which artifact types are missing across all families; prioritized gap list; enables targeted evidence collection. | C |
| T4 | [x] Add selection audit trail schema (SAT-). (#985) | Immutable ordered log of every selection/rejection decision with evidence_artifact_ids and rationale; enables full auditability from nomination to wet-lab shortlist. | C |
| T5 | [x] Add pipeline completeness certificate schema (PCC-). (#987) | Top-level certificate asserting that all required evidence schemas are present for a given pipeline run; completeness_grade (A–D); closes Phase T. | C |

## Phase U — Evidence trail integration and family-level views (U1–U5)

Connect the evidence schemas from Phases S and T into coherent family-level and batch-level summary views that scientists can read in one artifact.

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| U1 | Add family evidence trail view schema (FET-) (complete). — src/openamp_foundry/evidence/family_evidence_trail_view.py: FET- 13-field schema; REQUIRED_TRAIL_SCHEMA_TYPES (9: BTI/BEG/SAT/PCC/BSP/SEG/ECC/RSR/PQT), VALID_TRAIL_COMPLETENESS_GRADES (complete/partial/empty); build() deduplicates event types, auto-computes grade; dry_lab_only=True enforced; 57 tests in tests/evidence/test_family_evidence_trail_view.py. | Per-family aggregation of all evidence schema references (BTI/BEG/SAT/PCC/BSP/SEG/ECC/RSR/PQT) into a single timeline; shows which schemas are present, missing, and when each was produced; gives a scientist ONE document to trace the full evidence history of a candidate family. PR #990. | C |
| U2 | Add batch release checklist schema (BRC-) (complete). — src/openamp_foundry/evidence/batch_release_checklist.py: BRC- schema; VALID_PCC_GRADES (A-D), PASSING_PCC_GRADES (A/B), BLOCKING_BEG_VERDICTS (critical_gaps/no_families), VALID_RELEASE_VERDICTS (approved/blocked/conditional); 3 ChecklistItem gates; dry_lab_only=True; 60 tests. | Machine-verifiable checklist that must pass before a batch is released for wet-lab synthesis; gates on PCC grade ≥ B, no critical BEG gaps, at least one SAT entry, all required artifacts present; prevents incomplete batches from advancing. PR #992. | C |
| U3 | Add cross-schema linkage validator schema (CSV-) (complete). — src/openamp_foundry/evidence/cross_schema_linkage_validator.py: CSV- schema; VALID_LINKAGE_VERDICTS (all_valid/orphans_found/no_references), VALID_REFERENCE_SOURCES (SAT/BEG/BTI); OrphanEntry; build() deduplicates refs, detects orphans; dry_lab_only=True; 52 tests. | Validates that artifact IDs referenced in SAT evidence_artifact_ids, BEG missing lists, and BTI entries are internally consistent; catches orphaned references before external sharing. PR #993. | C |
| U4 | Add pipeline phase timeline report schema (PTR-) (complete). — src/openamp_foundry/evidence/pipeline_phase_timeline_report.py: PTR- schema; VALID_PIPELINE_SCHEMA_TYPES (16), VALID_TIMELINE_VERDICTS (complete/in_progress/empty), TERMINAL_SCHEMA_TYPES (SAT/PCC); TimelineEvent; events sorted by created_at; phase auto-assigned; dry_lab_only=True; 50 tests. | Ordered sequence of all schema events for a pipeline run, sorted by created_at; shows progression from nomination to shortlisting with schema type, artifact ID, and timestamp per event; enables audit of sequence and timing. PR #994. | C |
| U5 | Add evidence completeness index schema (ECI-) (complete). — src/openamp_foundry/evidence/evidence_completeness_index.py: ECI- schema; AGGREGATED_SCHEMA_TYPES (4: PCC/CBA2/BEG/SAT), VALID_ECI_GRADES (A-D); BatchSchemaPresence per batch; overall fraction and grade; dry_lab_only=True; closes Phase U; 47 tests. | Top-level index of which schemas exist for each batch and family across all phases; aggregates PCC + CBA2 + BEG + SAT into a single completeness snapshot; completeness_grade (A–D); closes Phase U. PR #995. | C |

## Phase V — Release readiness and reproducibility sealing (V1–V5)

Gate external sharing on all evidence schemas passing; seal the evidence trail for reproducibility and scientific review.

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| V1 | Add pre-release audit gateway schema (PRG-) (complete). — src/openamp_foundry/evidence/pre_release_audit_gateway.py: 3-gate check (BRC=approved, PCC in A/B, ECI in A/B); 53 tests. | Single-gate record asserting BRC (batch release checklist), PCC (pipeline completeness), ECI (evidence completeness index) all green; blocks external sharing until all gates pass; required before any batch goes to wet-lab partners or external review. | C |
| V2 | Add evidence bundle manifest schema (EBM-) (complete). — src/openamp_foundry/evidence/evidence_bundle_manifest.py: 19 schema types; complete/partial/empty status; 43 tests. | Portable listing of all evidence artifact IDs and schema types for a batch; enables reproducibility checks and external handoff; machine-readable index a scientist can use to request any artifact. | C |
| V3 | Add scientific reproducibility seal schema (SRS-) (complete). — src/openamp_foundry/evidence/scientific_reproducibility_seal.py: sealed/provisional/invalidated statuses; human_reviewed cross-check; PENDING hash placeholder; 50 tests. | Immutable record asserting that a batch's evidence trail is complete and auditable; includes pipeline version, schema hash placeholder, and human-reviewed flag; enables preprint data availability statements. | C |
| V4 | Add external review packet schema (ERP-) (complete). — src/openamp_foundry/evidence/external_review_packet.py: 5 components (BRC/ECI/FET/PTR/SRS); ready/incomplete/draft status; 45 tests. | Assembles BRC + ECI + FET + PTR + SRS into a single record listing everything a scientist needs to review the batch's computational evidence; dry-lab-only constraint explicit; closes the "what do I send to a reviewer?" question. | C |
| V5 | Add Phase V completeness gate schema (V5G-) (complete). — src/openamp_foundry/evidence/phase_v_completeness_gate.py: 4 components (PRG/EBM/SRS/ERP); prefix-validated artifact IDs; ready/blocked verdict; 63 tests. | Top-level gate asserting PRG + EBM + SRS + ERP all present; closes Phase V and signals the batch is ready for external scientific review. | C |

## Phase W — Batch-level benchmark hardness and novelty challenges

Make it machine-verifiable that the pipeline produces novel candidates that beat cheap baselines. Directly addresses the strategic bottleneck: "Can the system help choose real experiments better than cheap baselines?" Every item produces a named artifact that gates further claims.

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| W1 | Add novelty challenge harness schema (NCH-) (complete). — src/openamp_foundry/evidence/novelty_challenge_harness.py: VALID_NCH_VERDICTS (4: novel_batch/mixed_novelty/near_neighbor_dominated/challenge_not_run), VALID_REFERENCE_DATABASES (6), NEAR_NEIGHBOR_IDENTITY_THRESHOLD=0.80, NOVEL_BATCH_CEILING=0.20, NEAR_NEIGHBOR_DOMINATED_FLOOR=0.60; NCHCandidateResult helper; build() auto-computes is_near_neighbor from identity vs threshold, fraction, verdict; dry_lab_only=True enforced; 63 tests in tests/evidence/test_novelty_challenge_harness.py. | Batch-level novelty challenge: documents the fraction of top candidates with ≥80% sequence identity to a known AMP in a reference database (APD3/DRAMP/etc.); blocks novel_batch claim when near-neighbor fraction exceeds 20%; prevents pipeline from advancing near-copies of known AMPs under a novelty label. | C |
| W2 | Add charge-matched challenge schema (CMC-) (complete). — src/openamp_foundry/evidence/charge_matched_challenge.py: VALID_CMC_VERDICTS (4: gap_meaningful/gap_marginal/gap_absent/challenge_not_run), VALID_CHARGE_BASELINE_METHODS (4), MEANINGFUL_GAP_THRESHOLD=0.05, MARGINAL_GAP_LOWER=0.02; auroc_gap auto-computed; verdict auto-derived; dry_lab_only=True enforced; 60 tests in tests/evidence/test_charge_matched_challenge.py. | Formally documents the charge-matched challenge: compares pipeline AUROC vs a charge-only baseline on the same candidate set; verdict controlled vocabulary (gap_meaningful/gap_marginal/gap_absent/not_run); blocks performance claims when the charge-only baseline explains the gap. | C |
| W3 | Add similarity challenge harness schema (SCH-) (complete). — src/openamp_foundry/evidence/similarity_challenge_harness.py: VALID_SCH_VERDICTS (4: selection_adds_value/marginal_improvement/proximity_driven/challenge_not_run), VALID_SIMILARITY_METRICS (4), SELECTION_VALUE_GAP_THRESHOLD=0.10, MARGINAL_IMPROVEMENT_LOWER=0.03; SimilarityGroupStats helper; similarity_gap auto-computed; dry_lab_only=True enforced; 60 tests in tests/evidence/test_similarity_challenge_harness.py. | Documents whether pipeline-selected candidates are systematically more similar to known AMPs than random selection from the sequence space; flags selection bias from similarity clustering; prevents "novel panel" claim when selection is proximity-driven. | C |
| W4 | Add benchmark challenge registry schema (BCR-) (complete). — src/openamp_foundry/evidence/benchmark_challenge_registry.py: REQUIRED_CHALLENGE_TYPES (3: NCH/CMC/SCH), VALID_CHALLENGE_VERDICTS (4: pass/marginal/fail/not_run), VALID_BCR_HARDNESS_GRADES (A-D); ChallengeEntry helper; verdict mapping (novel_batch→pass, mixed_novelty→marginal, gap_meaningful→pass, etc.); grade A=all pass, B=all pass+marginal, C=some pass/marginal, D=all fail/not_run; dry_lab_only=True; 64 tests in tests/evidence/test_benchmark_challenge_registry.py. | Machine-readable registry of which benchmark challenges (NCH/CMC/SCH) have been run and passed for a given pipeline version; aggregates challenge verdicts; overall hardness grade (A: all passed, B: most passed, C: some passed, D: none passed). | C |
| W5 | Add Phase W benchmark gate (WBG-) (complete). — src/openamp_foundry/evidence/phase_w_benchmark_gate.py: REQUIRED_W_COMPONENTS (4: NCH/CMC/SCH/BCR), VALID_WBG_VERDICTS (3: hardened/partially_hardened/not_hardened), HARDENED_REQUIRED_PRESENT=4, PARTIALLY_HARDENED_MIN_PRESENT=2; WComponentCheck helper; prefix validation for all artifact IDs; verdict: hardened=all 4 present, partially_hardened=2-3, not_hardened=0-1; dry_lab_only=True; 61 tests. Closes Phase W. | Top-level gate asserting NCH + CMC + SCH + BCR all present; overall verdict: hardened/partially_hardened/not_hardened; closes Phase W; no batch-level performance claim is credible without passing this gate. | C |

## Phase X — Multi-batch learning loop

Track whether the pipeline actually improves across batches by capturing per-batch quality snapshots and aggregating them into calibration progress records. Every improvement claim must reference machine-verifiable learning records.

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| X1 | Add multi-batch learning record schema (MBL-) (complete). — src/openamp_foundry/evidence/multi_batch_learning_record.py: VALID_MBL_QUALITY_GRADES (5: A-D/N/A), VALID_BATCH_LEARNING_STATUSES (3), GRADE_A_HIT_RATE=0.40; hit_rate auto-computed from n_confirmed_hits/n_candidates_tested; grade auto-derived; no_wet_lab_data forces N/A grade; whr_ids list; dry_lab_only=True; 61 tests in tests/evidence/test_multi_batch_learning_record.py. | Per-batch snapshot of prediction quality (hit rate, AUROC, n_confirmed_hits) after wet-lab feedback; enables cross-batch comparison of whether the pipeline is learning; feeds into calibration improvement tracker. | C |
| X2 | Add calibration improvement tracker schema (CIT-) (complete). — src/openamp_foundry/evidence/calibration_improvement_tracker.py: VALID_CIT_TREND_DIRECTIONS (4: improving/stable/degrading/insufficient_data), VALID_CIT_SUMMARY_GRADES (5: A-D/N/A), MIN_BATCHES_FOR_TREND=2, IMPROVEMENT_THRESHOLD=0.05; BatchHitRateEntry helper; trend auto-computed from first→latest hit_rate delta; insufficient_data forces N/A grade; dry_lab_only=True; 49 tests. | Aggregates MBL records across batches; computes hit-rate trend direction (improving/stable/degrading/insufficient_data); minimum 2 batches required; flags when calibration is not producing measurable improvement. | C |
| X3 | Add learning progress report schema (LPR-) (complete). — src/openamp_foundry/evidence/learning_progress_report.py: VALID_LPR_VERDICTS (4: learning_confirmed/learning_inconclusive/no_learning_signal/insufficient_data), VALID_FEATURE_PREDICTIVITY (3: predictive/not_predictive/uncertain), VALID_FEATURE_CATEGORIES (8); FeatureLearningEntry helper; verdict auto-computed: learning_confirmed (n_pred>n_non), learning_inconclusive (equal+>0), no_learning_signal (n_pred<n_non), insufficient_data (no batches or no definitive features); dry_lab_only=True; 58 tests in tests/evidence/test_learning_progress_report.py. | Human-readable summary of what the pipeline has learned from all batches to date; references CIT- for trend data; includes which candidate features proved predictive vs not; links to calibration decision logs. | C |
| X4 | Add recalibration confidence certificate schema (RCC-) (complete). — src/openamp_foundry/evidence/recalibration_confidence_certificate.py: VALID_RCC_GRADES (A-D), VALID_RCC_VERDICTS (4: high_confidence/moderate_confidence/low_confidence/insufficient_data), VALID_CONSISTENCY_RATINGS (4); BatchCohortEntry helper; grade A (≥4 batches+consistent), B (≥2 batches+consistent/moderately_consistent), D (insufficient_data); cross_batch_consistency auto-computed; total_cohort_size auto-summed; dry_lab_only=True; cit_id/lpr_id prefix-validated; 76 tests. | Asserts with what confidence the current calibration weights are reliable based on cohort size, quality, and consistency across batches; A/B/C/D grade; prevents overconfident calibration claims. | C |
| X5 | Add Phase X learning gate (XLG-) (complete). — src/openamp_foundry/evidence/phase_x_learning_gate.py: REQUIRED_X_COMPONENTS=(MBL,CIT,LPR,RCC), VALID_XLG_VERDICTS (3: learning_verified/learning_in_progress/learning_not_started); XComponentCheck helper; verdict auto-computed: learning_verified (all 4 present), learning_in_progress (2-3), learning_not_started (0-1); artifact_id prefix-validated per component; dry_lab_only=True; 55 tests. | Top-level gate asserting MBL + CIT + LPR + RCC all present; overall verdict: learning_verified/learning_in_progress/learning_not_started; closes Phase X; no calibration improvement claim is credible without passing this gate. | C |

## Phase Y — Baseline-vs-pipeline accountability

Track and publish structured comparisons between pipeline selections and cheap baselines. Every pilot claim must reference a pre-registered baseline comparison record. Makes it impossible to claim "the pipeline works" without a machine-verifiable comparison against the cheapest plausible alternative. Directly addresses the bottleneck: can the pipeline choose real experiments better than charge/length heuristics?

| ID | Task | Why it matters | Priority |
|----|------|----------------|----------|
| Y1 | Add cheap baseline comparison record schema (CBR-) (complete). — src/openamp_foundry/evidence/cheap_baseline_comparison_record.py: VALID_CBR_VERDICTS (4: pipeline_superior/tied/baseline_superior/insufficient_data), VALID_BASELINE_METHODS (5: charge_only_rank/length_only_rank/random_selection/charge_length_combined/hydrophobicity_only_rank), VALID_CBR_METRICS (4: auroc/hit_rate/top_k_precision/ndcg), SUPERIORITY_THRESHOLD=0.05, MIN_SAMPLE_SIZE=5; metric_delta auto-computed; verdict auto-derived; dry_lab_only=True; 62 tests. | Structured record: pipeline metric vs charge-only/random/length-only baseline; pre-registered threshold; verdict (pipeline_superior/tied/baseline_superior/insufficient_data). Forces every performance claim to cite the baseline it beat. | C |
| Y2 | Add feature importance audit schema (FIA-) (complete). — src/openamp_foundry/evidence/feature_importance_audit.py: VALID_FIA_VERDICTS (5), VALID_FEATURE_IMPORTANCE_LEVELS (4), VALID_AUDIT_FEATURES (8), DOMINATION_THRESHOLD=0.80; importance_level auto-assigned; top_feature/charge_score/length_score auto-extracted; verdict: charge_dominated when charge_explains_fraction>=0.80; dry_lab_only=True; 50 tests. | Documents which features drove selections and whether charge/length alone explains the result; anti-cheap-explanation gate. | C |
| Y3 | Add selection diversity audit schema (SDA-) (complete). — src/openamp_foundry/evidence/selection_diversity_audit.py: VALID_SDA_VERDICTS (4: diverse_panel/moderately_diverse/proximity_driven/insufficient_data), VALID_DIVERSITY_METRICS (4), DIVERSE_PANEL_THRESHOLD=0.10, PROXIMITY_DRIVEN_THRESHOLD=-0.05, MIN_PANEL_SIZE=3; diversity_delta auto-computed; verdict: diverse_panel (delta>=0.10), proximity_driven (delta<=-0.05); dry_lab_only=True; 46 tests. | Tracks sequence diversity of selected panel vs random draw; detects proximity-driven selection masquerading as discovery; required before any novelty claim. | C |
| Y4 | Add pipeline maturity certificate schema (PMC-) (complete). — src/openamp_foundry/evidence/pipeline_maturity_certificate.py: VALID_PMC_GRADES (A-D), VALID_PMC_VERDICTS (4: pipeline_validated/pipeline_provisional/pipeline_unvalidated/insufficient_evidence), REQUIRED_PMC_COMPONENTS=(CBR,FIA,SDA); PMCComponentCheck helper; grade A (all 3 superior), B (2), C (1), D (0/none assessed); contributes_to_grade auto-derived from verdict; dry_lab_only=True; 54 tests. | Aggregates CBR/FIA/SDA results into A/B/C/D maturity grade; anchors pre-registration; prevents retroactive interpretation. | C |
| Y5 | Add Phase Y accountability gate (YAG-) (complete). — src/openamp_foundry/evidence/phase_y_accountability_gate.py: REQUIRED_Y_COMPONENTS=(CBR,FIA,SDA,PMC), VALID_YAG_VERDICTS (3: accountability_verified/accountability_partial/accountability_not_established); YComponentCheck helper; verdict: accountability_verified (all 4), accountability_partial (2-3), accountability_not_established (0-1); artifact_id prefix-validated per component; dry_lab_only=True; 54 tests. Closes Phase Y. | Top-level gate asserting CBR+FIA+SDA+PMC all present; closes Phase Y; no external pilot claim is credible without passing this gate. | C |

## Phase Z — Per-family benchmark accountability

Make per-family performance gaps visible and machine-checkable, so the pipeline cannot hide weak AMP class coverage behind aggregate metrics.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| Z1 | Add family blindness challenge harness schema (FBH-) (complete). | Per-family AUROC + panel representation check; flags when weak AMP classes (AUROC&lt;0.55) are excluded from selected panel; prevents aggregate-metric hiding of family blind spots. | C |
| Z2 | Add batch explanation report schema (BXR-) (complete). | Per-candidate selection reason tracking (winner_exploit/uncertainty_probe/diversity_anchor/etc.); safety_cleared flag per candidate; verdict (explained/partially_explained/unexplained) based on safety clearance fraction; makes multi-batch selection auditable. | C |
| Z3 | Add adapter registry schema (ARG-) (complete). | Machine-readable registry of all external scoring/simulation adapters; adapter_type/status/evidence_level/can_affect_ranking per entry; only active+baseline_verified adapters may affect ranking; blocks experimental/pending adapters from influencing candidate selection. | C |
| Z4 | Add cheap baseline flag schema (CBF-) (complete). | Per-scorer gate ensuring every external adapter declares its cheapest meaningful baseline before influencing candidate ranking; blocks_ranking=True when baseline missing or AUROC delta <0.05; creates permanent anti-hype infrastructure. | C |
| Z5 | Add Phase Z accountability gate (ZAG-). | Top-level gate asserting FBH+BXR+ARG+CBF all present; verdict (accountability_verified/accountability_partial/accountability_not_established); closes Phase Z; no external pilot claim or adapter governance claim is credible without passing this gate. | C |

## Phase AA — Run reproducibility manifests

Machine-verifiable proof that every pipeline run carries the fields needed for external reproduction and audit.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| AA1 | Add run manifest completeness schema (RMC-) (complete). | Validates pipeline run output manifests carry all 9 required reproducibility fields (commit_hash/config_hash/input_hash/seed/version/command/timestamp); verdict complete/incomplete/partial; blocks release of runs missing reproducibility metadata. | C |
| AA2 | Add determinism check record schema (DCR-) (complete). | Records result of running same pipeline step twice; verdict deterministic/nondeterministic/single_run_only/seed_dependent; run1/run2 output hash comparison; blocks releasing nondeterministic steps for external review. | C |
| AA3 | Add configuration fingerprint schema (CFP-) (complete). | Structured record of all config file paths and their SHA256/etc. hashes for a pipeline run; verdict all_configs_hashed/some_configs_unhashed/no_configs_recorded; complements RMC- config_hash field with full per-file audit trail. | C |
| AA4 | Add synthetic boundary warning record schema (SBW-) (complete). | Machine-checkable label enforcement for synthetic lab results (mic_simulation/structure_prediction/docking/etc.); verdict labelled/partially_labelled/unlabelled; cannot_support_biological_claim=True invariant enforced; prevents synthetic data from being treated as experimental validation. | C |
| AA5 | Add Phase AA reproducibility gate (AARG-). | Top-level gate asserting RMC+DCR+CFP+SBW all present; verdict reproducibility_verified/partial/not_established; closes Phase AA; no run is reproducibility-certified until this gate passes. | C |

## Phase AB — Claim integrity and external handoff

Machine-verifiable audit trail for claim downgrades, expert decisions, and external collaboration handoffs.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| AB1 | Add claim strength downgrade record schema (CSD-). | Auditable trail for every claim downgrade; proof_ladder_steps_dropped auto-computed; is_retracted invariant; trigger_type controlled vocabulary (benchmark/reviewer/cheap_enemy/etc.); prevents silent claim drift upward after challenges. | B/C |
| AB2 | Add reviewer decision record schema (RDR-). | Machine-parseable expert review: 5 dimensions (novelty/controls/safety/synthesis/claim_scope); rating per dimension (acceptable/concerns_noted/requires_revision/not_assessed); n_blocking auto-computed; "approved" blocked when any required dimension unassessed or any dimension requires_revision. | B/C |
| AB3 | Add evidence gap notification schema (EGN-). | Structured record of what evidence is missing and how to close the gap; gap_type (9 types: missing_wet_lab/baseline/novelty/safety/reproducibility/reviewer/claim_mismatch/family_benchmark/adapter_baseline); closure_artifact_type (14 types); effort_estimate/priority/verdict; is_blocking flag; makes "needs more work" actionable. | C |
| AB4 | Add external handoff packet record schema (EHP-). | Auditable checklist of what was included in an external handoff; auto-computes has_safety_clearance from PSC/FNR presence; safety invariant blocks wet_lab_synthesis transfers without clearance; verdict complete/partial/incomplete based on artifact count (threshold 4). | C |
| AB4 | Add external handoff packet record schema (EHP-). | Auditable checklist of what was included in an external handoff; auto-computes has_safety_clearance from PSC/FNR presence; safety invariant blocks wet_lab_synthesis transfers without clearance; verdict complete/partial/incomplete based on artifact count (threshold 4); 56 tests. BASELINE: 11965→12021. | C |
