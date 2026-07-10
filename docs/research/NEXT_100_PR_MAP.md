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
| A1 | Add a `make doctor` command that checks Python version, package install, expected folders, and key optional tools. | New users fail less. | B |
| A2 | Add `openamp-foundry doctor` CLI equivalent. | Agents can self-diagnose environment issues. | B |
| A3 | Generate a first-run report after `make demo`. | New users understand outputs faster. | B |
| A4 | Add a `docs/getting-started/FIRST_RUN_WALKTHROUGH.md` with expected outputs and claim boundaries. | Converts demo into onboarding. | A |
| A5 | Add test that README quickstart commands stay valid. | Prevents entrypoint drift. | B |
| A6 | Add link-check CI for internal docs. | Prevents doc graph rot. | B |
| A7 | Add a `make docs-check` target. | Agents can verify doc-only PRs. | B |
| A8 | Add generated artifact examples with safe toy data. | Reviewers see what good output looks like. | B |
| A9 | Add `outputs/README.md` explaining generated outputs and ignored files. | Reduces confusion. | A |
| A10 | Add troubleshooting table for install/test failures. | Faster onboarding. | A |

## Phase B — Evidence certificate hardening

Make candidate evidence packages impossible to confuse with biological proof.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| B1 | Add certificate field for `proof_ladder_level` (complete). | PLC- schema: 14 fields, 14 validation rules, dry_lab_only caps level at multi_signal_candidate_evidence, human_review_required enforced for levels ≥expert_reviewed_assay_proposal, unsupported_claims required as anti-overclaim guard; makes level claim machine-verifiable. | B |
| B2 | Add `unsupported_claims` field to certificates (complete). | CCB- schema: 10 fields, 13 validation rules, 8 claim class vocabulary, ≥3 classes required, dry_lab_only+all_listed_classes_unsupported enforced, no-duplicate check; negative complement of PLC- closes score-to-proof drift gap. | B |
| B3 | Add `baseline_caveat` field (complete). | Added to build_certificate(): auto-computes charge/length/hydrophobicity flags and warns when all three cheap baselines pass; forces cheap-explanation visibility at certificate issue time. 63 tests in tests/test_certificate_baseline_caveat.py. | B |
| B4 | Add `release_status` field. | Supports staged release. | C/D |
| B5 | Add certificate quality-tier validator (complete). | assess_certificate_quality() computes draft/internal_review/external_review_ready tier; missing-field detection, forbidden-claim violation check, external-review gate; 63 tests in tests/test_certificate_quality_validator.py. | B |
| B6 | Add human-readable certificate report (complete). | build_certificate_report() in certificate_report.py converts cert dict to formatted text with sections: identity, proof ladder, scores, cheap-explanation check, selection reason, failure modes, next steps, references, optional quality tier; 63 tests in tests/test_certificate_report.py. | B |
| B7 | Add candidate rejection certificate support (complete). | CRC- schema: 12 fields, 13 rules, VALID_REJECTION_GATES (10 values), VALID_REJECTION_REASONS (12 values), dry_lab_only enforced, proof-ladder cap at multi_signal; makes pipeline rejections first-class auditable artifacts; 63 tests. | B |
| B8 | Link certificates to run manifest hashes (complete). | Added run_id and run_manifest_hash optional params to build_certificate(); every certificate is now traceable to the exact pipeline run and manifest that produced it; backward-compatible (defaults to empty string); 63 tests in tests/test_certificate_run_link.py. | B |
| B9 | Add test that dry-lab certificates cannot include forbidden claims (complete). | CI gate: tests/test_certificate_claim_discipline.py scans all cert text fields against RISKY_PATTERNS and FORBIDDEN_CLAIM_PATTERNS; default cert proven clean; forbidden phrases confirmed detectable. 35 tests total. | B/C |
| B10 | Add external-review packet generator that bundles certificates. | Better partner review. | C/D |

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
| D7 | Add maintainer prompts for assigning agent-safe tasks. | Better human-agent coordination. | A |
| D8 | Add `docs/AGENT_FAILURE_MODES.md` (complete). | 10 failure modes (FM-01 to FM-10): claim escalation, scope creep, benchmark theater, safety weakening, certificate confusion, calibration self-service, hidden dependencies, novelty over-attribution, unsafe parallelism, stop-condition bypass; detection signals and mitigations for each. | A |
| D9 | Add CI warning for newly added top-level docs not in project index (complete). | scripts/check_docs_index_coverage.py: warns on docs/*.md files not referenced in PROJECT_INDEX.md; make docs-index-check target; allowlist for known exceptions. | B |
| D10 | Add structured agent contribution summary template (complete). | docs/operations/AGENT_CONTRIBUTION_SUMMARY_TEMPLATE.md: failure-mode self-check table (FM-01 to FM-10), disconfirming pass checklist, automated check results, stop-condition gate, test coverage, proof-ladder level, one-sentence verdict. | B |

## Phase E — Safe external review infrastructure

Make qualified external review easier and safer.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| E1 | Add external review packet schema. | Packets become machine-checkable. | C/D |
| E2 | Add example external review packet using toy data. | Partners know what to expect. | C/D |
| E3 | Add reviewer questionnaire schema (complete). | Makes external review feedback machine-readable: Likert clarity ratings for activity/safety/novelty claims, synthesis recommendation, structured comments. | B/C |
| E4 | Add safety-release decision schema. | Release review becomes auditable. | D |
| E5 | Add non-protocol pilot pre-registration schema. | Freezes selection logic. | C/D |
| E6 | Add packet generator CLI. | Reduces manual packaging errors. | C/D |
| E7 | Add packet validator CLI. | Review readiness becomes testable. | C/D |
| E8 | Add release-summary generator that strips restricted fields. | Safer public summaries. | D |
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
| F5 | Add safe-publication filter for negative results. | Supports openness without unsafe release. | D |
| F6 | Add examples of non-informative vs informative negative results. | Better interpretation. | A |
| F7 | Add calibration link from negative-result entries to intake reports. | Closes learning loop. | C |
| F8 | Add benchmark for whether rejected candidates resemble known failure modes (complete). — FMS- schema: 14 fields, 11 validation rules, PATTERN_REPEATED_THRESHOLD=0.80, pattern_repeated_flag enforcement, calibration_action_recommended; 63 tests. | Improves rejection logic. | C |
| F9 | Add negative-result dashboard schema (complete). | NRD- aggregates NRR- rejection statistics: rejection rate consistency check, all_rejections_have_nrr enforced, top stage/reason controlled vocabulary, 100% rejection warning. | B |
| F10 | Add policy that public claims must mention relevant negative results. | Prevents cherry-picking. | D |

## Phase G — Calibration and active-learning rigor

Make learning controlled rather than self-serving.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| G1 | Add machine-readable recalibration decision log examples (complete). | RDL- schema: 13 fields, 13 validation rules, 4 outcomes, 5 trigger types, deferred-requires-conditions enforced; closes governance audit trail for calibration decisions. | B |
| G2 | Add recalibration rejection examples (complete). | RRS- schema: 13 fields, 15 validation rules, refusal_rate consistency check (tol 0.01), all_refusals_have_rrf=True enforced, gate status controlled vocabulary; shows gate success by audit-ready refusal aggregation. | B |
| G3 | Add `make calibration-audit`. | Checks intake/gate/engine/report consistency. | C |
| G4 | Add active-learning strategy comparison report. | Prevents one-selector bias. | C |
| G5 | Add batch-2 rationale report explaining exploit/explore/diversity roles. | Reviewers understand next batch. | C |
| G6 | Add calibration-overfit warning when cohort is too small. | Prevents false learning. | C |
| G7 | Add result-quality flag propagation into calibration engine. | Low-quality outcomes cannot drive updates. | C |
| G8 | Add policy that synthetic results cannot raise proof-ladder level (complete). | SBR- schema: 14 fields, 16 validation rules, synthetic-only evidence cannot propose level ≥4 without violations recorded, policy_enforced=True enforced, violation rate consistency check (tol 0.01); anti-overclaim boundary is now auditable artifact. | B/C |
| G9 | Add calibration decision review checklist. | Human review stronger. | C/D |
| G10 | Add recalibration rollback plan. | Safer updates. | C |

## Phase H — Virtual assay discipline

Make simulation useful or harmless.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| H1 | Add simulation module registry. | Shows status and evidence level. | B |
| H2 | Add simulation-result schema. | Prevents undocumented proxy output. | B/C |
| H3 | Add per-module cheapest-baseline declaration. | Forces enemy comparison. | C |
| H4 | Add fail-closed adapter integration tests. | Avoids hidden external failures. | B/C |
| H5 | Add no-silent-network policy test for adapters. | Protects sequence privacy. | D |
| H6 | Add simulation uncertainty calibration report (complete). — SUC- schema: 14 fields, 10 validation rules, VALID_SIMULATION_MODULES (7 values), VALID_CALIBRATION_METHODS (6 values), OVERCONFIDENCE_THRESHOLD=0.15, MIN_SAMPLES_FOR_CALIBRATION=10; makes module confidence interval calibration machine-auditable; 63 tests. | Makes uncertainty inspectable. | C |
| H7 | Add documentation that failed simulation stays useful as negative evidence (complete). — docs/FAILED_SIMULATION_AS_NEGATIVE_EVIDENCE.md: cultural standard requiring NRR- record for every failure; agent MUST NOT rules; anti-selective-reporting enforcement. | Cultural standard. | A |
| H8 | Add `weighted` integration dry-run report, still blocked by gate (complete). — WDR- schema: 15 fields, 12 validation rules, results_applied_to_ranking=False enforcement, GATE_CLOSED_DISCLAIMER required, counterfactual-only; 63 tests. | Shows what would change without applying. | C |
| H9 | Add module deprecation mechanism for simulation theater. | Cleanup discipline. | B/C |
| H10 | Add external-simulator review checklist. | Safer ecosystem bridges. | D |

## Phase I — Interoperability and adoption

Make OpenAMP artifacts useful even without OpenAMP scoring.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| I1 | Add FASTA export for final candidate set. | Standard format for partner labs. | B |
| I2 | Add JSON-LD context for evidence certificates. | Semantic web compatibility. | B |
| I3 | Add citation template for data consumers (complete). — docs/CITATION_TEMPLATE.md: APA, BibTeX, CFF, in-text, data-availability formats; dry-lab-only anti-overclaim embedded in every format. | Proper attribution. | A |
| I4 | Add OpenAMP output → external tool adapter stub. | Reduces integration friction. | B |
| I5 | Add cross-repo evidence traceability field. | Multi-lab reproducibility. | C |
| I6 | Add versioned schema export. | Stable API for partners. | B |
| I7 | Add comparative summary across multiple candidate batches (complete). — BCS- schema: 14 fields, 12 validation rules, VALID_TREND_DIRECTIONS, VALID_QUALITY_TIERS, MIN_BATCHES_FOR_TREND=2; trend consistency enforced; 63 tests. | Shows trajectory, not just snapshots. | C |
| I8 | Add machine-readable release manifest. | Downstream tools can parse what was released. | B |
| I9 | Add public API stub with rate-limit and privacy policy stubs. | Safety for eventual public access. | D |
| I10 | Add annotation layer for wet-lab-updated evidence. | Closes the wet-lab feedback loop. | D |

## Phase J — Long-term infrastructure

Make the repo survive contributors, updates, and time.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| J1 | Add changelog generator from PR titles. | History without manual maintenance. | B |
| J2 | Add schema version migration guide. | Schema updates don't break old artifacts. | B |
| J3 | Add docs coverage report (complete). | Shows what is and isn't documented. | B |
| J4 | Add deprecation policy document (complete). | Makes obsolescence intentional. | A |
| J5 | Add long-term archival format specification (complete). — docs/ARCHIVAL_FORMAT_SPEC.md: 9 sections, directory layout, VERSION.txt format, checksums.sha256, anti-rot guarantees, agent MUST NOT rules. | Evidence survives software churn. | C |
| J6 | Add public license and reuse guide (complete). — docs/LICENSE_AND_REUSE_GUIDE.md: Apache 2.0 terms, artifact-specific constraints, dry-lab-only preservation requirement. | Community adoption enabled. | A |
| J7 | Add contributor covenant and attribution policy (complete). — docs/CONTRIBUTOR_COVENANT.md: overclaiming as explicit violation, AI attribution policy, artifact attribution rules. | Fair credit for future contributors. | A |
| J8 | Add automated stale-doc detector. | Reduces doc rot over time. | B |
| J9 | Add cross-reference checker between schemas and tests. | Ensures tests stay coupled to schemas. | B |
| J10 | Add end-to-end dry-run test for full pipeline from sequences to evidence package. | Smoke test for whole system. | B/C |

## Phase P — Pilot batch infrastructure

Prepare for the first real (non-toy) batch under dry-lab-only, human-reviewed conditions.

| PR | Task | Why it matters | Review class |
|---:|---|---|---|
| P1 | Add batch selection proposal schema (complete). | BSP- schema: 14 fields, 17 validation rules, calibration_gate_passed enforcement, proposal_basis controlled vocabulary, all_sequences_dry_lab_only enforced, pre_selection_checklist required (≥3 items), funding_status required; calibration gate must pass before next batch release. | B/C |
| P2 | Add recalibration refusal record schema (complete). | RRF- schema: 14 fields, 14 validation rules, refusal_rate consistency check (tol 0.01), recalibration_baseline correction (4889→4784), corrects inflated BASELINE; auditable rejection of spurious recalibrations. | B/C |
| P3 | Add batch outcome summary schema (complete). | BOS- schema: 14 fields, 14 validation rules, synthetic/real boundary enforcement (all_outcomes_are_real requires dry_lab_only=False), hit_rate consistency check (tol 0.01), n_confirmed_hits ≤ n_total_outcomes enforced; closes BSP-to-outcomes feedback loop. | B/C |
| P4 | Add pilot batch safety clearance schema (complete). | PSC- schema: 14 fields, 15 validation rules, safety gate requiring all 4 screens (toxicity/hemolysis/off_target/dual_use) before wet-lab synthesis, blocks high-risk batches. | B/C |
| P5 | Add calibration cycle summary schema (complete). | CCS- schema: 14 fields, 15 validation rules, index record for complete BSP→PSC→BOS→CPS→CBA→CRG feedback loop; cycle_health controlled vocabulary; closes Phase P. | B/C |
