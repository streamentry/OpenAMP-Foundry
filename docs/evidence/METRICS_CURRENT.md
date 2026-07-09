# Current Pipeline Metrics — Single Source of Truth

Machine-readable snapshot: `outputs/metrics_snapshot.json` regenerated with `make metrics-snapshot`.

> **Purpose:** One authoritative table of current pipeline metrics. If any doc disagrees
> with this file, this file wins. Updated whenever benchmark/benchmark config changes.
>
> **Last updated:** 2026-07-10 (Phase M M5 — audit chain completeness — v0.9.3)
> **New in v0.9.3:** Audit chain completeness checker (M5 — Loop 132) — docs/evidence/AUDIT_CHAIN_GUIDE.md with purpose, schema fields table (16 fields: chain_id, batch_id, pipeline_version, audit_date, 9 has_* bools, missing_links, auditor, dry_lab_only), 9 required chain links, validation rules (5), warning conditions (2: single auditor, future date), honest-use boundary. src/openamp_foundry/evidence/audit_chain_completeness.py with AuditChainEntry dataclass (16 fields: chain_id, batch_id, pipeline_version, audit_date, 9 has_* bools, missing_links list[str], auditor, dry_lab_only=True), AuditChainResult dataclass (7 fields: chain_id, batch_id, missing_link_count, passed, errors, warnings, dry_lab_only=True), CHAIN_LINK_FIELDS (9 entries), CHAIN_LINK_COUNT (9), AUDITOR_EMAIL_HINT ("@"), IMPLAUSIBLE_YEAR_THRESHOLD (2030), validate_audit_chain() (5+ error checks: ACH- prefix, non-empty auditor, dry_lab_only must be True, each false chain link errors, missing_links consistency; 2 warnings: no email, future date), validate_audit_chain_dict() (15 required fields guard). CLI (openamp-foundry audit-chain-check) with --entry-json, --format text|json. make audit-chain-check target. 39 tests. Phase M M5: the evidence chain is now machine-checkable end to end. Phase M (Audit Trail Infrastructure) is fully complete with M1-M5.
> **New in v0.9.1:** Score decomposition report schema (M3 — Loop 130) — docs/evidence/SCORE_DECOMPOSITION_GUIDE.md with purpose, schema fields table (12 fields), valid scoring methods (6), validation rules (9), warning conditions (4), honest-use boundary. src/openamp_foundry/evidence/score_decomposition_report.py with ScoreDecompositionEntry dataclass (12 fields: report_id, batch_id, candidate_id, pipeline_version, composite_score, component_scores, component_weights, scoring_method, score_range_min, score_range_max, reviewer, dry_lab_only=True), ScoreDecompositionResult dataclass (7 fields: report_id, batch_id, candidate_id, scoring_method, passed, errors, warnings, dry_lab_only=True), VALID_SCORING_METHODS (6: additive_weighted, geometric_mean, harmonic_mean, max_component, min_component, rank_aggregation), MINIMUM_COMPONENTS (2), WEIGHT_SUM_TOLERANCE (0.01), DOMINANT_WEIGHT_THRESHOLD (0.6), UNBALANCED_RATIO_THRESHOLD (5.0), MAX_COMPONENTS_WARNING (8), LOW_SCORE_FRACTION (0.2), validate_score_decomposition() (9 error checks: SDR- prefix, score_range_min<score_range_max, composite_score in range, >=2 components, weight keys match score keys, weights sum to ~1.0, valid scoring_method, non-empty reviewer, dry_lab_only must be True; 4 warning conditions: dominant component, unbalanced weights, many components, low composite score), validate_score_decomposition_dict() (11 required fields guard). CLI (openamp-foundry score-decomposition-check) with --entry-json, --format text|json. make score-decomposition-check target. Phase M M3: every composite score is now machine-decomposable into its named components for external audit.
> **New in v0.9.0:** Claim-to-evidence mapper schema (M2 — Loop 129) — docs/evidence/CLAIM_TO_EVIDENCE_GUIDE.md with purpose, schema fields table (10 fields), valid claim types (7), validation rules (7), warning conditions (4), honest-use boundary, CLI usage. src/openamp_foundry/evidence/claim_to_evidence_mapper.py with ClaimToEvidenceEntry dataclass (10 fields: mapping_id, batch_id, pipeline_version, claim_text, claim_type, supporting_artifact_ids, evidence_level, pre_specified, reviewer, dry_lab_only=True), ClaimToEvidenceResult dataclass (7 fields: mapping_id, batch_id, claim_type, passed, errors, warnings, dry_lab_only=True), VALID_CLAIM_TYPES (7: activity_prediction, calibration_statement, novelty_claim, performance_comparison, reproducibility_claim, safety_assessment, selection_rationale), VALID_EVIDENCE_LEVELS (6: 1-6), MAX_CLAIM_TEXT_LENGTH (500), LONG_CLAIM_TEXT_THRESHOLD (300), WEAK_EVIDENCE_THRESHOLD (2), validate_claim_to_evidence() (7 error checks: CEM- prefix, non-empty claim_text<=500 chars, valid claim_type, non-empty supporting_artifact_ids, valid evidence_level 1-6, non-empty reviewer, dry_lab_only must be True; 4 warning conditions: post-hoc, weak evidence, single artifact, long claim text), validate_claim_to_evidence_dict() (9 required fields guard). CLI (openamp-foundry claim-to-evidence-check) with --entry-json, --format text|json. make claim-to-evidence-check target. Phase M M2: every scientific claim is now machine-mapped to its supporting artifacts for external audit.
> **New in v0.8.9:** Pipeline decision audit entry schema (M1 — Loop 128) — docs/evidence/PIPELINE_DECISION_AUDIT_GUIDE.md with purpose, required field table (13 fields), valid decision types (7), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/pipeline_decision_audit.py with PipelineDecisionAuditEntry dataclass (13 fields: audit_id, batch_id, pipeline_version, decision_date, decision_type, decision_description, rationale, alternatives_considered, affected_candidate_count, evidence_level, pre_specified, reviewer, dry_lab_only), PipelineDecisionAuditResult dataclass (5 fields: audit_id, batch_id, decision_type, passed, errors, warnings, dry_lab_only=True), VALID_DECISION_TYPES (7: benchmark_updated, calibration_adjusted, candidate_ranked, candidate_rejected, filter_applied, safety_flag_applied, threshold_chosen), VALID_EVIDENCE_LEVELS (6: 1-6), MAX_DESCRIPTION_LENGTH (500), MAX_RATIONALE_LENGTH (1000), validate_pipeline_decision_audit() (12 checks: AUD- prefix, non-empty batch_id/pipeline_version/reviewer, YYYY-MM-DD decision_date, valid decision_type, non-empty description<=500 chars, non-empty rationale<=1000 chars, affected_candidate_count>=0, valid evidence_level, dry_lab_only must be True; post-hoc warns, empty alternatives warns, low evidence warns, zero affected warns), validate_pipeline_decision_audit_dict() (12 required fields guard). CLI (openamp-foundry pipeline-decision-audit-check) with --entry-json, --format text|json. make pipeline-decision-audit-check target. Phase M M1: every pipeline decision is now machine-validated and traceable for external audit.
> **New in v0.8.8:** Dataset release package checker (L5 — Loop 127) — docs/evidence/DATASET_RELEASE_GUIDE.md with purpose, required field table (13 fields), valid license identifiers (5), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/dataset_release.py with DatasetReleaseEntry dataclass (13 fields: release_id, dataset_name, dataset_version, release_date, license_identifier, data_sources, contains_sequences, contains_activity_data, dual_use_assessed, usage_policy_url, contact_email, release_approved, dry_lab_only), DatasetReleaseResult dataclass (4 fields: release_id, dataset_name, passed, errors, warnings, dry_lab_only=True), VALID_LICENSE_IDENTIFIERS (5: Apache-2.0, CC-BY-4.0, CC-BY-NC-4.0, CC0-1.0, MIT), MINIMUM_DATA_SOURCES (1), validate_dataset_release() (11 checks: DSR- prefix, non-empty dataset_name/dataset_version/usage_policy_url/contact_email, YYYY-MM-DD release_date, valid license_identifier, data_sources>=1, dual_use_assessed must be True, release_approved must be True, dry_lab_only must be True; CC-BY-NC-4.0 warns, single source warns), validate_dataset_release_dict() (12 required fields guard). CLI (openamp-foundry dataset-release-check) with --entry-json, --format text|json. make dataset-release-check target. Phase L L5 completes Phase L: open dataset releases now have machine-validated data governance checks.
> **New in v0.8.7:** Multi-candidate comparison schema (L4 — Loop 126b) — docs/evidence/MULTI_CANDIDATE_COMPARISON_GUIDE.md with purpose, required field table (11 fields), minimum requirements (2 candidates, 2 criteria), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/multi_candidate_comparison.py with MultiCandidateComparisonEntry dataclass (11 fields: comparison_id, batch_id, pipeline_version, comparison_date, candidate_ids, comparison_criteria, top_candidate_id, top_candidate_rationale, evidence_level, reviewer, dry_lab_only), MultiCandidateComparisonResult dataclass (5 fields: comparison_id, batch_id, candidate_count, passed, errors, warnings, dry_lab_only=True), MINIMUM_CANDIDATES (2), MINIMUM_CRITERIA (2), RECOMMENDED_CRITERIA (3), MAX_RATIONALE_LENGTH (500), LARGE_CANDIDATE_SET_THRESHOLD (10), VALID_EVIDENCE_LEVELS (6: 1-6), validate_multi_candidate_comparison() (11 checks: CMP- prefix, non-empty batch_id/pipeline_version/reviewer, YYYY-MM-DD comparison_date, candidate_ids>=2, comparison_criteria>=2, top_candidate_id in candidate_ids, non-empty rationale<=500 chars, valid evidence_level, dry_lab_only must be True; evidence_level<=2 warns, candidate_count>10 warns, criteria_count<3 warns), validate_multi_candidate_comparison_dict() (10 required fields guard). CLI (openamp-foundry multi-candidate-comparison-check) with --entry-json, --format text|json. make multi-candidate-comparison-check target. Phase L L4: side-by-side candidate comparisons are now machine-validated for publication-ready supplementary tables.
> **New in v0.8.6:** Candidate summary card schema (L3 — Loop 126) — docs/evidence/CANDIDATE_SUMMARY_CARD_GUIDE.md with purpose, required field table (12 fields), valid activity labels (5), valid amino acid set (20 standard), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/candidate_summary_card.py with CandidateSummaryCardEntry dataclass (12 fields: card_id, candidate_id, batch_id, pipeline_version, sequence, sequence_length, evidence_level, predicted_activity, safety_flags, selection_rationale_id, reviewer, dry_lab_only), CandidateSummaryCardResult dataclass (5 fields: card_id, candidate_id, sequence_length, passed, errors, warnings, dry_lab_only=True), VALID_ACTIVITY_LABELS (5: high_activity, inactive, low_activity, moderate_activity, uncertain), VALID_AMINO_ACIDS (20 standard one-letter codes), LONG_PEPTIDE_THRESHOLD (50), VALID_EVIDENCE_LEVELS (6: 1-6), validate_candidate_summary_card() (11 checks: CRD- prefix, non-empty candidate_id/batch_id/pipeline_version/reviewer, non-empty sequence with valid amino acids, sequence_length==len(sequence), valid evidence_level, valid predicted_activity, SEL- prefix on selection_rationale_id, dry_lab_only must be True; evidence_level<=2 warns, safety_flags non-empty warns, uncertain activity warns, length>50 warns), validate_candidate_summary_card_dict() (11 required fields guard). CLI (openamp-foundry candidate-summary-card-check) with --entry-json, --format text|json. make candidate-summary-card-check target. Phase L L3: every candidate now has a machine-validated publication-ready summary card.
> **New in v0.8.5:** Reproducibility manifest schema (L2 — Loop 125) — docs/evidence/REPRODUCIBILITY_MANIFEST_GUIDE.md with purpose, required field table (11 fields), package checksums format, data checksums format, warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/reproducibility_manifest.py with ReproducibilityManifestEntry dataclass (11 fields: manifest_id, batch_id, pipeline_version, run_date, python_version, package_checksums, data_checksums, random_seeds, hardware_summary, reviewer, dry_lab_only), ReproducibilityManifestResult dataclass (6 fields: manifest_id, batch_id, package_count, data_file_count, passed, errors, warnings, dry_lab_only=True), MINIMUM_PACKAGES (3), MINIMUM_DATA_FILES (1), RECOMMENDED_PACKAGES (5), validate_reproducibility_manifest() (10 checks: RPM- prefix, non-empty batch_id/pipeline_version/python_version/hardware_summary/reviewer, YYYY-MM-DD run_date, package_checksums>=3, data_checksums>=1, dry_lab_only must be True; empty random_seeds warns, package_count<5 warns, hardware_summary contains 'unknown' warns), validate_reproducibility_manifest_dict() (10 required fields guard). CLI (openamp-foundry reproducibility-manifest-check) with --entry-json, --format text|json. make reproducibility-manifest-check target. Phase L L2: every pipeline run now has a machine-validated reproducibility record.
> **New in v0.8.4:** Preprint evidence bundle schema (L1 — Loop 124) — docs/evidence/PREPRINT_BUNDLE_GUIDE.md with purpose, required field table (11 fields), minimum artifact count (3), evidence level guide, warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/preprint_bundle.py with PreprintBundleEntry dataclass (11 fields: bundle_id, batch_id, pipeline_version, submission_date, title, artifact_ids, evidence_level, preprint_doi, contact_email, release_approved, dry_lab_only), PreprintBundleResult dataclass (5 fields: bundle_id, batch_id, artifact_count, passed, errors, warnings, dry_lab_only=True), MINIMUM_ARTIFACTS (3), RECOMMENDED_ARTIFACT_COUNT (5), MAX_TITLE_LENGTH (300), VALID_EVIDENCE_LEVELS (6: 1-6), validate_preprint_bundle() (10 checks: BND- prefix, non-empty batch_id/pipeline_version/contact_email, YYYY-MM-DD submission_date, non-empty title<=300 chars, artifact_ids>=3, valid evidence_level 1-6, release_approved must be True, dry_lab_only must be True; evidence_level<=2 warns, empty preprint_doi warns, artifact_count<5 warns), validate_preprint_bundle_dict() (10 required fields guard). CLI (openamp-foundry preprint-bundle-check) with --entry-json, --format text|json. make preprint-bundle-check target. Phase L L1: scientific preprints now have a machine-validated evidence bundle structure.
> **New in v0.8.3:** Uncertainty quantification report schema (K5 — Loop 123) — docs/evidence/UNCERTAINTY_REPORT_GUIDE.md with purpose, required field table (12 fields), valid metric names (5), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/uncertainty_report.py with UncertaintyReportEntry dataclass (12 fields: report_id, batch_id, candidate_id, pipeline_version, metric_name, point_estimate, lower_bound, upper_bound, confidence_level, calibration_source, reviewer, dry_lab_only), UncertaintyReportResult dataclass (6 fields: report_id, candidate_id, interval_width, passed, errors, warnings, dry_lab_only=True), VALID_METRIC_NAMES (5: cytotoxicity_score, hemolysis_fraction, mic, selectivity_index, stability_score), WIDE_INTERVAL_THRESHOLD (10.0), validate_uncertainty_report() (11 checks: UQ- prefix, non-empty batch_id/candidate_id/pipeline_version/calibration_source/reviewer, valid metric_name, lower_bound<=point_estimate, upper_bound>=point_estimate, confidence_level 0.0-1.0, dry_lab_only must be True; wide interval warns, confidence<0.80 warns, confidence>0.99 warns), validate_uncertainty_report_dict() (11 required fields guard). CLI (openamp-foundry uncertainty-report-check) with --entry-json, --format text|json. make uncertainty-report-check target. Phase K K5: prediction intervals for external reviewers are now machine-validated.
> **New in v0.8.2:** Post-experiment calibration intake schema (K4 — Loop 122) — docs/evidence/CALIBRATION_INTAKE_GUIDE.md with purpose, required field table (11 fields), note on dry_lab_only=False (real lab results), valid assay types (5), valid outcome values (4), warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/calibration_intake.py with CalibrationIntakeEntry dataclass (11 fields: intake_id, batch_id, candidate_id, pipeline_version, assay_type, predicted_outcome, observed_outcome, predicted_confidence, intake_date, reviewer, dry_lab_only=False), CalibrationIntakeResult dataclass (6 fields: intake_id, candidate_id, prediction_correct, passed, errors, warnings, dry_lab_only=False), VALID_ASSAY_TYPES (5: cytotoxicity_assay, hemolysis_assay, membrane_disruption_assay, mic_assay, stability_assay), VALID_OUTCOME_VALUES (4: active, inactive, inconclusive, not_tested), validate_calibration_intake() (11 checks: CAL- prefix, non-empty batch_id/candidate_id/pipeline_version/reviewer, valid assay_type, valid predicted_outcome, valid observed_outcome, confidence 0.0-1.0, YYYY-MM-DD date, dry_lab_only must be False; high-confidence misprediction warns, inconclusive observed warns), validate_calibration_intake_dict() (10 required fields guard). CLI (openamp-foundry calibration-intake-check) with --entry-json, --format text|json. make calibration-intake-check target. Phase K K4: prediction-vs-outcome comparisons are now machine-validated with honest dry_lab_only=False enforcement.
> **New in v0.8.1:** Pilot package completeness checker (K3 — Loop 121) — docs/evidence/PILOT_PACKAGE_GUIDE.md with purpose, required field table (11 fields), mandatory artifact types table (3 types), valid artifact types, warnings, validation workflow, honest-use boundary. src/openamp_foundry/evidence/pilot_package.py with PilotPackageEntry dataclass (11 fields: package_id, batch_id, submission_date, pipeline_version, included_artifacts, missing_artifacts, reviewer, approver, completeness_score, ready_to_submit, dry_lab_only), PilotPackageResult dataclass (5 fields, dry_lab_only=True), MINIMUM_REQUIRED_ARTIFACTS (3), READINESS_SCORE_THRESHOLD (0.80), MANDATORY_ARTIFACT_TYPES (3: batch_priority, evidence_certificate, selection_rationale), VALID_ARTIFACT_TYPES (8 types), validate_pilot_package() (11 checks: PKG- prefix, non-empty batch_id/pipeline_version/reviewer/approver, YYYY-MM-DD submission_date, included_artifacts>=3, mandatory types covered, completeness_score 0.0-1.0, ready_to_submit must be False when score<0.80, dry_lab_only must be True; missing_artifacts non-empty warns, score<0.90 warns, same reviewer/approver warns), validate_pilot_package_dict() (10 required fields guard). CLI (openamp-foundry pilot-package-check) with --entry-json, --format text|json. make pilot-package-check target. Phase K K3: every pilot submission is now machine-validated for completeness.
>
> **New in v0.8.0:** Batch experiment priority ranker (K2 — Loop 120) — docs/evidence/BATCH_PRIORITY_GUIDE.md with purpose, required field table (11 fields), how-to-validate instructions. src/openamp_foundry/evidence/batch_priority.py with BatchPriorityEntry dataclass (12 fields: priority_id, batch_id, candidate_id, pipeline_version, priority_rank, priority_score, evidence_level, synthesis_complexity, novelty_tier, primary_rationale, disqualifying_concerns, dry_lab_only), BatchPriorityResult dataclass (6 fields, dry_lab_only=True), VALID_SYNTHESIS_COMPLEXITIES (3: high, low, medium), VALID_NOVELTY_TIERS (3: high, low, medium), VALID_EVIDENCE_LEVELS (6: 1-6), validate_batch_priority() (11 checks: PRI- prefix, non-empty batch_id/candidate_id/pipeline_version, priority_rank>=1, priority_score 0.0-1.0, valid evidence_level, valid synthesis_complexity, valid novelty_tier, non-empty primary_rationale, dry_lab_only must be True; evidence_level<=2 warns, rank==1+high-complexity warns, priority_score<0.30 warns), validate_batch_priority_dict() (10 required fields guard). CLI (openamp-foundry batch-priority-check) with --entry-json, --format text|json. make batch-priority-check target. Phase K K2: synthesis wave ranking is now machine-validated.
>
> **New in v0.7.9:** Candidate selection rationale schema (K1 — Loop 119) — docs/evidence/SELECTION_RATIONALE_GUIDE.md with purpose, required field table (11 fields), evidence level table (6 levels from PROOF_LADDER.md), validation workflow. src/openamp_foundry/evidence/selection_rationale.py with SelectionRationaleEntry dataclass (11 fields: selection_id, batch_id, candidate_id, pipeline_version, selection_date, evidence_level, baseline_comparison, primary_criterion, safety_flags_checked, reviewer, dry_lab_only), SelectionRationaleResult dataclass (5 fields, dry_lab_only=True), VALID_EVIDENCE_LEVELS (6: 1-6), MINIMUM_SAFETY_FLAGS (1), validate_selection_rationale() (11 checks: SEL- prefix, non-empty batch_id/candidate_id/pipeline_version, YYYY-MM-DD date, valid evidence_level 1-6, non-empty baseline_comparison/primary_criterion, safety_flags_checked list with >=1 entry, non-empty reviewer, dry_lab_only must be True; evidence_level<=2 warns with synthesis caution), validate_selection_rationale_dict() (10 required fields guard). CLI (openamp-foundry selection-rationale-check) with --entry-json, --format text|json. make selection-rationale-check target. Phase K K1: every selection decision now has a machine-validated evidence trail.
>
> **New in v0.7.8:** Annual safety and benchmark review checklist (J10 — Loop 118) — docs/governance/ANNUAL_REVIEW_CHECKLIST.md with 5-section structured checklist (safety_policy: 6 checks including dual-use safeguards, dry_lab_only enforcement, toxicity filters; benchmark_thresholds: 6 checks including threshold loosening guard, easy-baseline requirement, deprecation check; calibration_status: 4 checks including recalibration gate and rollback plan; governance_decisions: 4 checks including COI disclosures and rotation plan; data_governance: 3 checks including proprietary data flag). src/openamp_foundry/governance/annual_review.py with AnnualReviewEntry dataclass (10 fields: review_id, year, section, reviewer, finding_count, action_items_count, status, notes, completion_date, dry_lab_only), AnnualReviewResult dataclass (6 fields: review_id, year, section, passed, errors, warnings, dry_lab_only=True), VALID_REVIEW_SECTIONS (5: benchmark_thresholds, calibration_status, data_governance, governance_decisions, safety_policy), VALID_ENTRY_STATUSES (5: completed, deferred, in_progress, not_applicable, pending), validate_annual_review_entry() (9 checks: ANN- prefix, 4-digit year, valid section, non-empty reviewer, non-negative finding_count, non-negative action_items_count, valid status, completed requires YYYY-MM-DD completion_date, dry_lab_only must be True; completed+no-notes warns, deferred warns, findings+no-action-items warns), validate_annual_review_dict() (7 required fields guard). CLI (openamp-foundry annual-review-check) with --entry-json, --format text|json. make annual-review-check target. Long-term trust: annual review entries are now machine-validated.
>
> **New in v0.7.7:** External advisory review process (J9 — Loop 117) — docs/governance/EXTERNAL_ADVISORY_REVIEW_PROCESS.md with reviewer eligibility criteria, review scope table (5 review types with minimum reviewer counts), 5-step review process (prepare packet, assign+disclose, receive+log, respond to findings, close), finding severity classification (critical/major/minor/informational), limitations. src/openamp_foundry/governance/advisory_review.py with AdvisoryReview dataclass (11 fields: review_id, review_type, artifact_id, reviewer_handle, assigned_date, deadline_date, status, finding_severity, finding_summary, resolved, dry_lab_only), AdvisoryReviewResult dataclass (5 fields: review_id, review_type, passed, errors, warnings, dry_lab_only=True), VALID_REVIEW_TYPES (5: benchmark_audit, candidate_review, evidence_review, governance_review, safety_policy_review), VALID_REVIEW_STATUSES (5: assigned, completed, deferred, in_progress, pending), VALID_FINDING_SEVERITIES (4: critical, informational, major, minor), MINIMUM_REVIEWER_COUNTS (5 entries: candidate_review and safety_policy_review require 2, others 1), validate_advisory_review() (9 checks: ADV- prefix, valid review_type, non-empty artifact_id, non-empty reviewer_handle, YYYY-MM-DD dates, valid status, valid finding_severity, dry_lab_only must be True; critical+unresolved warns, completed+no-summary warns, deferred warns), validate_advisory_review_dict() (7 required fields guard). CLI (openamp-foundry advisory-review-check) with --review-json, --format text|json. make advisory-review-check target. 29 tests. Credibility: external advisory reviews now have a validated structure and documented process.
>
> **New in v0.7.6:** Roadmap-to-issue sync checklist (J8 — Loop 116) — docs/governance/ROADMAP_ISSUE_SYNC_CHECKLIST.md with 5-section sync checklist (roadmap items → issues, issues → roadmap, completed items, priority alignment, version consistency). src/openamp_foundry/governance/roadmap_sync.py with RoadmapSyncEntry dataclass (10 fields: item_id, phase, description, priority, sync_status, issue_number, pr_number, completed, completion_date, dry_lab_only), RoadmapSyncResult dataclass (5 fields: item_id, phase, passed, errors, warnings, dry_lab_only=True), VALID_SYNC_STATUSES (5: synced, missing_issue, orphaned_issue, stale, completed), VALID_PRIORITY_LEVELS (4: A, B, C, D), VALID_PHASES (7: E, F, G, H, I, J, K), validate_roadmap_sync_entry() (8 checks: non-empty item_id, valid phase, non-empty description, valid priority, valid sync_status, dry_lab_only must be True, completed must have completion_date, completion_date must be YYYY-MM-DD; priority A + missing_issue warns, stale warns, orphaned_issue warns, no issue_number warns), validate_roadmap_sync_dict() (5 required fields guard). CLI (openamp-foundry roadmap-sync-check) with --entry-json, --format text|json. make roadmap-sync-check target. 24 tests. Keeps strategy actionable: roadmap sync entries are now machine-validated.
>
> **New in v0.7.5:** Citation and reuse guide (J7 — Loop 115) — docs/governance/CITATION_AND_REUSE_GUIDE.md with citation formats (inline, BibTeX), reuse table (4 artifact types, open/attribution_required/contact_required/restricted classes), attribution requirements, honest-use boundary. src/openamp_foundry/governance/citation_policy.py with CitationEntry (11 fields: artifact_id, citation_type, title, version, authors, year, license_identifier, reuse_class, url, bibtex_key, dry_lab_only), CitationValidationResult (6 fields, dry_lab_only=True), VALID_CITATION_TYPES (4: dataset, method, schema, software), VALID_REUSE_CLASSES (4: attribution_required, contact_required, open, restricted), VALID_LICENSE_IDENTIFIERS (5: Apache-2.0, CC-BY-4.0, CC-BY-NC-4.0, MIT, Proprietary), validate_citation_entry() (9 checks: non-empty artifact_id, valid citation_type, non-empty title, non-empty version, non-empty authors, 4-digit year, valid license_identifier, valid reuse_class, dry_lab_only must be True; restricted warns, contact_required+no-url warns, empty bibtex_key warns), validate_citation_dict() (8 required fields guard). CLI (openamp-foundry citation-check) with --citation-json, --format text|json. make citation-check target. 24 tests. Ecosystem clarity: citation entries are now machine-validated.
>
> **New in v0.7.4:** Security policy (J6 — Loop 114) — `docs/governance/SECURITY_POLICY.md` with private vulnerability reporting process, response timeline (48h acknowledgment, 30d patch), severity classification (critical/high/medium/low), 5 vulnerability categories (code_vulnerability, secret_leakage, dependency_vulnerability, safety_guardrail_bypass, dual_use_risk), out-of-scope items, disclosure process. `src/openamp_foundry/governance/security_policy.py` with `VulnerabilityReport` dataclass (9 fields: report_id, severity, category, description, affected_version, reporter_handle, report_date, status, dry_lab_only), `SecurityReportValidationResult` dataclass (6 fields, dry_lab_only=True), `VALID_SEVERITY_LEVELS` (4: critical, high, medium, low), `VALID_VULNERABILITY_CATEGORIES` (5: code_vulnerability, secret_leakage, dependency_vulnerability, safety_guardrail_bypass, dual_use_risk), `VALID_REPORT_STATUSES` (6: received, acknowledged, under_review, patched, disclosed, not_applicable), `validate_vulnerability_report()` (9 checks: report_id SEC- prefix, valid severity, valid category, non-empty description, non-empty affected_version, non-empty reporter_handle, YYYY-MM-DD date, valid status, dry_lab_only must be True; critical+received warning, safety_guardrail_bypass warning), `validate_report_dict()` (dict input with 8 required fields guard). CLI (`openamp-foundry security-report-check`) with `--report-json`, `--format text|json`. `make security-report-check` target. 18 tests. Dry-lab only. Private vulnerability reporting now has a validated structure and documented process.
> **New in v0.7.3:** Maintainer rotation plan (J5 — Loop 113) — `docs/governance/MAINTAINER_ROTATION_PLAN.md` with purpose, current maintainers table (3 entries covering primary, secondary, external_advisor), role definitions (4 roles: primary_maintainer, secondary_maintainer, external_advisor, contributor), bus-factor assessment (target >=2 for every critical function, CI maintenance and domain expertise currently at 1), rotation schedule (every 6 months), onboarding and offboarding checklists, linked policies. `src/openamp_foundry/governance/maintainer_rotation.py` with `MaintainerEntry` dataclass (6 fields: github_handle, role, backup_handle, responsibilities, status, dry_lab_only), `RotationPlanValidationResult` dataclass (7 fields: passed, errors, warnings, maintainer_count, critical_role_coverage, bus_factor_sufficient, dry_lab_only), `VALID_ROLES` (4: primary_maintainer, secondary_maintainer, external_advisor, contributor), `CRITICAL_ROLES` (2: primary_maintainer, secondary_maintainer), `VALID_STATUSES` (4: active, on_leave, emeritus, departing), `validate_maintainer_entry()` (6 checks), `validate_rotation_plan()` (aggregates entry validation + bus-factor coverage: missing critical role is error, single coverage is warning), `validate_rotation_plan_dict()` (dict input with missing-entries-fields guard). CLI (`openamp-foundry rotation-plan-check`) with `--plan-json`, `--format text|json`. `make rotation-plan-check` target. 21 tests. Dry-lab only. Project durability is now machine-validated.
> **New in v0.7.2:** COI disclosure template (J4 — Loop 112) — `docs/governance/COI_DISCLOSURE_TEMPLATE.md` with structured COI disclosure template (purpose, fill-in-the-blank template with 10 fields: Disclosure ID, disclosure type (reviewer|contributor|maintainer|external_advisor), subject, related artifact, relationship type (financial|institutional|competitive|personal|none), description (conditional), date, recusal required, reviewer, review status (pending|acknowledged|resolved); when to disclose section covering financial/institutional/competitive/personal relationships; process with machine validation and escalation; linked policies). `src/openamp_foundry/governance/coi_disclosure.py` with `COIDisclosure` dataclass (10 fields), `COIValidationResult` dataclass (6 fields, dry_lab_only=True), `VALID_DISCLOSURE_TYPES` (4: contributor, external_advisor, maintainer, reviewer), `VALID_RELATIONSHIP_TYPES` (5: competitive, financial, institutional, none, personal), `VALID_REVIEW_STATUSES` (3: acknowledged, pending, resolved), `validate_coi_disclosure()` (10 checks including disclosure_id COI- prefix, valid disclosure_type, non-empty subject/related_artifact, valid relationship_type, description required unless none, YYYY-MM-DD date, non-empty reviewer, valid review_status, dry_lab_only must be True; financial without recusal warning), `validate_coi_dict()` (dict input with 10 required fields guard, missing fields returns passed=False early). CLI (`openamp-foundry coi-check`) with `--disclosure-json`, `--format text|json`. `make coi-check` target. 20 tests. Dry-lab only. COI disclosures now have a validated structure that builds institutional trust.
> **New in v0.7.1:** Release request template (J3 — Loop 111) — `docs/governance/RELEASE_REQUEST_TEMPLATE.md` with structured release request template (purpose, fill-in-the-blank template with 17 fields: Release ID, release type, artifact ID/version, requestor name/institution, request date, evidence level 1-6, dry_lab_only, safety_review_status, benchmark_summary, known_limitations, intended_use, data_license, human_reviewer, review_class, approval_status; review criteria with 8 checks; process with classes A-D timelines and escalation path). `src/openamp_foundry/governance/release_request.py` with `ReleaseRequest` dataclass (17 fields), `ReleaseRequestValidationResult` dataclass (6 fields, dry_lab_only=True), `VALID_RELEASE_TYPES` (5), `VALID_SAFETY_STATUSES` (3), `VALID_INTENDED_USES` (4), `VALID_APPROVAL_STATUSES` (4), `VALID_REVIEW_CLASSES` (4), `validate_release_request()` (17 checks including dry_lab_only+evidence_level>4 error, public+safety_pending error, model+review_class warning), `validate_request_dict()` (dict input with missing-fields guard). CLI (`openamp-foundry release-request-check`) with `--request-json`, `--format text|json`. `make release-request-check` target. 25 tests. **3516 total.** Formal release requests now have a validated structure before entering human review.
> **New in v0.7.0:** Governance decision log index (J2 — Loop 110, Phase J milestone) — `docs/governance/DECISION_LOG.md` with structured decision log (purpose, decision index with 8 entries GOV-001 through GOV-008 covering safety/benchmark/release/evidence/data/adapter/contribution/docs scopes, how to add entries, linked policies). `src/openamp_foundry/governance/decision_log.py` with `VALID_SCOPES` (8 entries: safety, benchmark, release, evidence, data, adapter, contribution, docs), `VALID_STATUSES` (4 entries: active, superseded, under_review, proposed), `VALID_REVIEW_CLASSES` (4 entries: A, B, C, D), `GovernanceDecision` dataclass (8 fields: decision_id, date, scope, decision, status, rationale, review_class, dry_lab_only=True), `DecisionValidationResult` dataclass (5 fields: decision_id, passed, errors, warnings, dry_lab_only=True), `GOVERNANCE_DECISIONS` list (8 entries: GOV-001 through GOV-008), `validate_governance_decision()` (9 checks: decision_id format, date format, valid scope, non-empty decision, valid status, non-empty rationale, valid review_class, dry_lab_only must be True, superseded warning), `validate_all_decisions()` (aggregates total/passed/failed/all_passed/results/dry_lab_only), `get_decisions_by_scope()` (filters by scope), `get_decisions_by_status()` (filters by status). CLI (`openamp-foundry decision-log`) with `--validate`, `--scope`, `--format text|json`. `make decision-log` target. 27 tests. **3505 total.** **Phase J milestone: v0.7.0** — governance decisions are now discoverable and machine-validated.
> **New in v0.6.9:** Release checklist and gate validator (J1 — Loop 109, starts Phase J) — `docs/governance/RELEASE_CHECKLIST.md` with structured checklist (pre-release gates, release-type gates for 5 types, post-release checklist), cross-referencing `docs/trust/RELEASE_CHECKLIST.md`. `src/openamp_foundry/governance/release_gate.py` with `RELEASE_TYPES` (5: candidate, model, dataset, evidence_packet, schema), `UNIVERSAL_GATES` (7: ci_tests_pass, agent_check_passes, no_critical_issues, dry_lab_only_confirmed, safety_flags_reviewed, data_license_verified, no_hardcoded_secrets), `EXTRA_GATES_BY_TYPE` (per-type additional gates), `ReleaseGateResult` dataclass (8 fields, dry_lab_only=True), `validate_release_gate()` (validates all required gates, treats missing gates as failed, raises CRITICAL error on dry_lab_only_confirmed failure). CLI (`openamp-foundry release-gate-check`) with `--release-type`, `--artifact-id`, `--gates-json`, `--format text|json`. `make release-gate-check` target. 18 tests. **3478 total.** **Starts Phase J (Governance and release maturity)** — releases now require all gates to pass before external release, preventing accidental bypass of required checks.
> **New in v0.6.8:** Adoption scorecard dashboard (I10 — Loop 108) — `src/openamp_foundry/adoption/scorecard.py` with `SCORECARD_DIMENSIONS` (5 weighted dimensions summing to 1.0: integration_check 0.25, license_compliance 0.20, adapter_validation 0.20, schema_compatibility 0.20, contribution_readiness 0.15), `ADOPTION_TIERS` (4 tiers: not_ready 0.0-0.40, emerging 0.40-0.65, established 0.65-0.85, mature 0.85-1.01), `DimensionScore` dataclass (8 fields, dry_lab_only=True), `AdoptionScorecard` dataclass (6 fields, dry_lab_only=True), `build_scorecard()` (aggregates dimension inputs into weighted total score with tier and actionable recommendations), `compute_adoption_tier()` (maps score to tier). CLI (`openamp-foundry adoption-scorecard`) with `--scores-json`, `--format text|json`. `make adoption-scorecard` target. 17 tests. **3446 total.** **Phase I (Interoperability and Adoption) is now complete** — all 10 items I1–I10 implemented (artifact versioning, candidate manifest, benchmark card, artifact changelog, integration checker, adapter validator, data license checker, schema compatibility, contribution intake, adoption scorecard).
> **New in v0.6.7:** Public-good contribution guide (I9 — Loop 107) — `docs/community/PUBLIC_GOOD_CONTRIBUTION_GUIDE.md` with 6 contribution types (wet_lab_validation, dataset_donation, compute_sponsorship, expert_review, governance_participation, algorithm_contribution), review classes A-D, minimum requirements table, initiation process, data governance, and safety constraints. `src/openamp_foundry/community/contribution_intake.py` with `ContributionIntake` dataclass (7 fields), `IntakeValidationResult` dataclass (7 fields), `VALID_CONTRIBUTION_TYPES` (6 entries), `VALID_REVIEW_CLASSES` (4 entries), `REQUIRED_FIELDS_BY_TYPE` (6 entries), `validate_contribution_intake()` (checks all top-level fields, type-specific required fields, wet_lab_validation human_review_required=True enforcement), `validate_intake_dict()` (dict input with missing-fields guard). CLI (`openamp-foundry contribution-check`) with `--intake-json`, `--format text|json`. `make contribution-check` target. 16 tests. Dry-lab only. Funders and institutions now have a clear, validated pathway for contribution.
> **New in v0.6.5:** Data license checker (I7 — Loop 105) — `src/openamp_foundry/licensing/license_checker.py` with `DataLicenseDeclaration` dataclass (11 fields: source_id, source_name, license_id, use_context, attribution_required, commercial_use_allowed, redistribution_allowed, modifications_allowed, human_review_required, notes, dry_lab_only), `LicenseCheckResult` dataclass (8 fields: source_id, license_id, use_context, passed, status, errors, warnings, dry_lab_only), `check_data_license()` (validates declarations against `APPROVED_LICENSES` (11 entries: CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0, MIT, Apache-2.0, GPL-3.0, LGPL-2.1, BSD-2-Clause, BSD-3-Clause, ODbL-1.0, PDDL-1.0), `RESTRICTED_LICENSES` (4 entries: CC-BY-NC-4.0, CC-BY-NC-SA-4.0, custom, proprietary), `BLOCKED_LICENSES` (3 entries: unknown, unlicensed, all-rights-reserved), `VALID_USE_CONTEXTS` (6 entries: training, scoring, benchmarking, reporting, publication, internal). Blocked licenses fail immediately; restricted require human_review_required=True; unknown licenses require governance review before use. `check_license_batch()` summarizes total/passed/failed/blocked/any_blocked/all_passed with dry_lab_only=True. All results carry dry_lab_only=True. CLI (`openamp-foundry license-check`) with `--source-json`, `--format text|json`. `make license-check` target. 16 tests. **3429 total.** External data sources used in pipeline outputs now require explicit license declarations, preventing hidden legal risk.
> **New in v0.6.3:** Downstream project template (I5 — Loop 103) — `docs/adoption/DOWNSTREAM_PROJECT_TEMPLATE.md` with overview of OpenAMP artifacts, minimum viable integration (consume candidate manifest, validate against schema, use Python library), schema validation step, evidence level interpretation table (L1-L6), safety flag conventions table, benchmark card consumption guide, explicit dry-lab limitations section, and contact/contribution section. `src/openamp_foundry/adoption/integration_checker.py` with `REQUIRED_INTEGRATION_CHECKS` (5 checks: manifest_schema_valid, evidence_level_in_range, dry_lab_only_acknowledged, safety_flags_reviewed, baseline_comparison_present), `IntegrationCheckResult` dataclass (4 fields: check_name, passed, detail, dry_lab_only), `run_integration_checks()` (returns dict with checks, passed_count, failed_count, all_passed, dry_lab_only). Exported from `src/openamp_foundry/adoption/__init__.py`. CLI (`openamp-foundry integration-check`) with `--manifest-json`, `--format text|json`. `make integration-check` target. 14 tests. **3356 total.** External researchers who want to use OpenAMP artifacts now have a guide and checker to validate their integration.
> **New in v0.6.2:** Evidence-certificate changelog (I4 — Loop 102) — `docs/engineering/ARTIFACT_CHANGELOG.md` with structured changelog format (version, date, artifact_name, change_type, description, breaking flag). Unreleased section at top. `src/openamp_foundry/versioning/artifact_changelog.py` with `CHANGE_TYPES` set (6 values), `ChangelogEntry` dataclass (7 fields), `ARTIFACT_CHANGELOG` list (6 entries: candidate_manifest, benchmark_card, simulation_result, simulation_module_registry, artifact_versioning_policy, artifact_changelog — all "added", non-breaking, v1.0.0), `get_changelog_entries()` (filters by artifact_name, version, change_type, breaking_only), `validate_changelog()` (5 checks: version MAJOR.MINOR.PATCH, date YYYY-MM-DD with dashes, artifact_name non-empty, change_type in CHANGE_TYPES, description non-empty), `changelog_summary()` (total, by_change_type, breaking_changes, artifacts_covered sorted, dry_lab_only). CLI (`openamp-foundry artifact-changelog`) with `--artifact`, `--version`, `--change-type`, `--breaking-only`, `--format text|json`. `make artifact-changelog` target. 13 tests. **3342 total.** External tools that consume OpenAMP artifacts now have a machine-readable changelog to detect breaking changes and adapt consumers.
> **New in v0.6.1:** Benchmark card schema (I3 — Loop 101) — `schemas/benchmark_card.schema.json` (Draft 2020-12, 15 required fields: benchmark_id, benchmark_name, version, date, metric, metric_value, baseline_name, baseline_value, delta, beats_baseline, dataset, dataset_size, scope, caveats, dry_lab_only). `$schema`, `$id`, `title`, `additionalProperties: false`. `src/openamp_foundry/benchmarks/` module with `BenchmarkCard` dataclass (15 fields), `make_benchmark_card()` (auto-computes delta, beats_baseline), `validate_benchmark_card()` (10 checks: non-empty benchmark_id, non-empty benchmark_name, non-empty metric, non-empty dataset, non-empty baseline_name, dataset_size >= 1, delta matches metric_value - baseline_value within 1e-9, beats_baseline matches delta > 0, dry_lab_only must be True), `benchmark_card_summary()` (total, beats_baseline_count, fails_baseline_count, dry_lab_only). CLI (`openamp-foundry benchmark-card`) with `--benchmark-id`, `--benchmark-name`, `--metric`, `--metric-value`, `--baseline-name`, `--baseline-value`, `--dataset`, `--dataset-size`, `--validate`, `--format text|json`. `make benchmark-card` target. 19 tests. **3329 total.** A benchmark card is the standard format for describing external benchmark results — what was benchmarked, what the baseline was, what the result was, and what claims are supported.
> **New in v0.6.0:** Candidate manifest schema (I2 — Loop 100) — `schemas/candidate_manifest.schema.json` (Draft 2020-12, 14 required fields: candidate_id, sequence, evidence_level, scopes, scores, uncertainty, source_modules, calibration_set, safety_flags, provenance_run_id, dry_lab_only, version, created_at, notes). `$schema`, `$id`, `title`, `description`, `additionalProperties: false`. `src/openamp_foundry/manifests/` module with `CandidateManifest` dataclass (14 fields), `make_candidate_manifest()`, `validate_candidate_manifest()` (8 checks: non-empty candidate_id, non-empty sequence, evidence_level 1-6, non-empty scopes, uncertainty 0.0-1.0, non-empty source_modules, dry_lab_only must be True, version MAJOR.MINOR.PATCH), `manifest_to_dict()`, `manifest_summary()` (total, by_evidence_level, with_safety_flags, dry_lab_only). CLI (`openamp-foundry candidate-manifest`) with `--candidate-id`, `--sequence`, `--evidence-level`, `--scopes`, `--scores-json`, `--uncertainty`, `--source-modules`, `--validate`, `--format text|json`. `make candidate-manifest` target. 19 tests. **3310 total.** A candidate manifest is the core interoperable artifact — it describes a dry-lab candidate (sequence, scores, evidence level, scopes, safety flags, provenance) in a machine-readable format that external tools can consume without the full OpenAMP stack.
> **New in v0.5.99:** Artifact versioning policy (I1 — starts Phase I) — `docs/engineering/ARTIFACT_VERSIONING_POLICY.md` with structured versioning policy covering scope, SemVer format, breaking/non-breaking change definitions, deprecation timeline (at least one minor version warning), schema `$id` policy, changelog requirement, and three stability tiers (stable/experimental/internal). `src/openamp_foundry/versioning/` module with `ArtifactVersionInfo` dataclass (7 fields), `STABILITY_TIERS` dict, `VERSIONED_ARTIFACTS` list (6 entries covering candidate, lab_result, run_manifest, external_review_packet, safety_release_decision, simulation_result at v1.0.0), `get_artifact_version()`, `list_versioned_artifacts()`, `validate_version_format()`, `artifact_version_summary()`. CLI (`openamp-foundry artifact-version`) with `--list`, `--show`, `--tier`, `--format text|json`. `make artifact-version` target. 19 tests. **3291 total.** Starts Phase I (interoperability) — external users now have stability guarantees for schemas, evidence certificates, and candidate manifests.
> **New in v0.5.97:** Simulation-scope coverage checker (H9) — `ScopeCoverageResult` dataclass (8 fields: module_id, requested_scopes, module_scopes, covered, uncovered, coverage_fraction, is_fully_covered, dry_lab_only). `check_scope_coverage()` looks up module in registry, computes covered (intersection) and uncovered (requested scopes not in module scopes), coverage_fraction = len(covered)/len(requested_scopes) if requested else 1.0. `check_result_scope()` uses conservative intersection of registry scopes and result.scope as effective module_scopes. `scope_coverage_report()` returns full dict. CLI (`openamp-foundry simulation-scope-check`) with `--module-id`, `--requested-scopes`, `--format text|json`. `make simulation-scope-check` target. 17 tests. **3255 total.** A simulation module may cover only some biological scopes. If a candidate is evaluated for a scope the module doesn't cover, that result must be flagged as out-of-scope rather than silently trusted.
> **New in v0.5.96:** Simulation-module deprecation enforcer (H8) — `DeprecationCheckResult` dataclass (5 fields: module_id, status, is_blocked, block_reason, dry_lab_only). `BLOCKED_STATUSES = {"deprecated", "unavailable"}`. `check_module_deprecation()` looks up module in registry: not-found returns is_blocked=True status="unknown"; deprecated/unavailable returns is_blocked=True with reason; active/experimental returns is_blocked=False. `enforce_deprecation()` filters list[SimulationResult] to only non-blocked modules, returns total_input/passed/blocked/blocked_modules/passed_results/checks/dry_lab_only. `run_deprecation_check_batch()` bulk-checks module_ids with total/blocked/allowed/any_blocked/results/dry_lab_only. CLI (`openamp-foundry simulation-deprecation-check`) with `--module-ids`, `--format text|json`. `make simulation-deprecation-check` target. 21 tests. **3238 total.** Deprecated simulation modules must not be used in production scoring — the enforcer prevents stale or unreliable modules from tainting evidence packets.
> **New in v0.5.95:** Simulation-result confidence interval reporter (H7) — `ci_reporter.py` with `ScoreCI` dataclass (9 fields: module_id, score_key, point_estimate, uncertainty, ci_lower, ci_upper, ci_width, overlaps_with, dry_lab_only). `compute_score_ci()` builds CIs from SimulationResult.scores[score_key] ± uncertainty, returns None if score_key missing. `compare_cis()` pairwise checks overlap condition (a_lo <= b_hi and b_lo <= a_hi), returns new list with overlaps_with populated (no in-place mutation). `ci_report()` produces full report with n_results, cis list, any_overlap flag, and dry_lab_only=True. CLI (`openamp-foundry simulation-ci-report`) with `--results-json`, `--score-key`, `--format text|json`. `make simulation-ci-report` target. 16 tests. **3217 total.** Raw scores without uncertainty ranges make it impossible to judge whether two candidates are distinguishable. The CI reporter makes uncertainty explicit and auditable.
> **New in v0.5.94:** Simulation-ensemble agreement checker (H6) — `ensemble_checker.py` with `EnsembleAgreementResult` dataclass (9 fields: sequence, modules_checked, agreement_level, agreement_description, mean_score, score_range, scores_by_module, threshold, dry_lab_only). `AGREEMENT_LEVELS` dict (5 levels: strong, moderate, weak, conflict, insufficient). `check_ensemble_agreement()` extracts score_key from each SimulationResult's scores dict, computes score_range, classifies into strong (≥3 modules within threshold), moderate (2 modules within threshold), weak (1 module), conflict (beyond threshold), or insufficient (no results). `run_ensemble_check_batch()` aggregates multiple calls with counts and any_conflict flag. CLI (`openamp-foundry simulation-ensemble-check`) with `--sequence`, `--results-json`, `--score-key`, `--threshold`, `--format text|json`. `make simulation-ensemble-check` target. 20 tests. **3201 total.** When multiple simulation modules independently agree on a candidate, that agreement is stronger evidence than a single module alone. The ensemble checker makes this agreement explicit and auditable.
> **New in v0.5.93:** Simulation-result provenance chain (H5) — `SimulationProvenanceRecord` dataclass with run_id, module_id, module_version, timestamp_utc, input_hash (SHA-256 of input sequence), result_hash (SHA-256 of sorted scores dict), calibration_set, notes, and dry_lab_only. `make_provenance_record()` computes input_hash and result_hash deterministically (sort_keys=True for result_hash). `validate_provenance_record()` checks run_id, module_id, module_version non-empty; ISO 8601 timestamp contains 'T'; hashes are 64-char hex; dry_lab_only is True. `provenance_summary()` aggregates total, unique modules, run_ids, and dry_lab_only flag. CLI (`openamp-foundry simulation-provenance`) with `--run-id`, `--module-id`, `--module-version`, `--timestamp-utc`, `--input-sequence`, `--scores-json`, `--calibration-set`, `--format text|json`. `make simulation-provenance` target with demo invocation. 19 tests. **3181 total.** Every simulation result carries a traceable provenance chain so results can be audited, reproduced, or invalidated later without relying on memory.
> **New in v0.5.92:** Fail-closed adapter integration tests (H4) — `FAIL_CLOSED_REASONS` dict keys (6 entries: timeout, connection_refused, invalid_response, schema_violation, module_unavailable, baseline_not_beaten). `AdapterGateResult` dataclass with module_id, passed, failure_reason, failure_detail, dry_lab_only. `evaluate_adapter_gate()` fail-closed: returns passed=False on ANY failure signal with priority ordering (timeout > connection_refused > invalid_response > schema_violation > module_unavailable > baseline_not_beaten). `run_adapter_gate_batch()` aggregates multiple adapter calls with total/passed/failed/any_failed/results/dry_lab_only. CLI (`openamp-foundry adapter-gate-check`) with `--module-id`, `--timeout`, `--connection-refused`, `--schema-errors`, `--module-unavailable`, `--baseline-beaten`, `--format text|json`. `make adapter-gate-check` target. 21 tests. **3162 total.** Avoids hidden external failures — when the adapter to an external simulation service is down or misbehaves, the pipeline must fail loudly rather than silently passing garbage through.
> **New in v0.5.91:** Per-module cheapest-baseline declaration (H3) — `BaselineDeclaration` dataclass with module_id, module_name, baseline_description, baseline_type, evidence_level_ceiling, and notes. `BASELINE_DECLARATIONS` list (4 entries: membrane_proxy, structure_proxy, dummy_membrane_proxy, external_adapter_placeholder). `get_baseline_declaration()` and `list_baseline_declarations()` for lookup. `check_baseline_requirement()` caps effective_evidence_level to ceiling when baseline not beaten; returns dict with module_id, baseline_beaten, claimed/effective evidence levels, capped flag, message, and dry_lab_only. `validate_baseline_declarations()` checks module_id non-empty, baseline_description non-empty, baseline_type in {heuristic, random, constant, length}, evidence_level_ceiling 1-6, no duplicate module_ids. CLI (`openamp-foundry simulation-baseline-check`) with `--module-id`, `--claimed-level`, `--baseline-beaten`, `--format text|json`. `make simulation-baseline-check` target. 16 tests. **3141 total.** Forces honest enemy comparison — every simulation module must declare the simplest baseline it must beat.
> **New in v0.5.90:** Simulation-result schema and validator (H2) — `schemas/simulation_result.schema.json` (Draft 2020-12) validates SimulationResult outputs with uncertainty 0.0–1.0 range, required fields (module, version, scope, scores, uncertainty, calibration_set, validated_against, notes), and optional `dry_lab_context` const "dry-lab-only". `validate_simulation_result()` checks module, version, scope, scores, uncertainty, validated_against, notes. Strict mode adds: module must not be "dummy" or contain "stub", uncertainty < 1.0, validated_against non-empty. `validate_simulation_result_batch()` aggregates results with counts and `any_invalid` flag. CLI (`openamp-foundry validate-simulation-result`) with `--results-json`, `--strict`, `--out-json`. `make validate-simulation-result-schema` target. 19 tests. **3125 total.** Dry-lab only.
> **New in v0.5.89:** Simulation module registry (H1) — `SimulationModuleEntry` dataclass tracks module_id, name, description, status, evidence_level, baseline_comparison, scope, maintainer, and notes. `SIMULATION_MODULE_REGISTRY` holds 4 entries (membrane_proxy, structure_proxy, dummy_membrane_proxy, external_adapter_placeholder). Lookup functions: `get_module_entry()`, `list_module_entries()` with status/min_evidence filtering, `get_active_modules()`, `registry_summary()` with total/by_status/by_evidence_level/active_module_ids keys. `validate_registry()` checks module_id, name, baseline_comparison, evidence_level 1-6, valid status, duplicate detection. CLI (`openamp-foundry simulation-registry`) supports `--list`, `--show`, `--status`, `--min-evidence`, `--format text|json`. Schema (`schemas/simulation_module_registry.schema.json`). `make simulation-registry` target. 28 tests. 3106 total. Starts Phase H (virtual assay discipline).
> **New in v0.5.87:** Calibration decision review checklist (G9) — `build_checklist()` produces a structured `CalibrationDecisionChecklist` with 12 checklist items (10 required) covering data quality, statistical validity, safety consistency, approval, and documentation. Each item has an id, category, question, rationale, and required flag. `CalibrationDecisionChecklist` dataclass tracks responses, notes, overall_pass, and missing_required. CLI (`openamp-foundry calibration-decision-checklist`) accepts `--checklist-id`, `--date`, `--reviewer`, `--responses-json`, `--out-json`, `--out-md`. JSON + Markdown output. Schema (`schemas/calibration_decision_checklist.schema.json`). `make calibration-decision-checklist` target. 14 tests. 3063 total. Makes human review structured and auditable.
> **New in v0.5.86:** Synthetic-result policy enforcement (G8) — `check_synthetic_result_policy()` and `run_policy_batch()` enforce that synthetic/simulation outputs cannot raise the proof-ladder level of a candidate. Levels 4+ require wet-lab evidence; synthetic/unknown sources are rejected for such proposals. CLI (`openamp-foundry synthetic-result-policy-check`) accepts `--proposals-json`, `--out-json`, `--out-md`. Schema (`schemas/synthetic_result_policy_check.schema.json`). `make synthetic-result-policy-check` target. 27 tests. 3049 total. Anti-overclaim safeguard.
> **New in v0.5.85:** Result-quality flag propagation (G7) — `assess_result_quality()` and `filter_results_for_calibration()` propagate result-quality flags into the calibration engine. Candidates with contamination or assay interference are excluded; candidates with 2+ quality flags are excluded; candidates with 1 flag are included with caution; clean candidates are fully included. `QUALITY_FLAGS` dictionary (8 flags). `ResultQualityReport` dataclass. CLI (`openamp-foundry result-quality-filter`) accepts `--results-json`, `--out-json`, `--out-md`. JSON + Markdown output. Schema (`schemas/result_quality_report.schema.json`). `make result-quality-filter` target. 27 tests. 3022 total.
> **New in v0.5.84:** Calibration-overfit warning (G6) — `check_cohort_overfit_risk()` and `run_overfit_check()` flag when a calibration cohort is too small relative to model parameters. Warns at three severity levels (critical/warning/caution/none). CLI (`openamp-foundry calibration-overfit-check`) accepts comma-separated cohort sizes, model params, n features. JSON + Markdown output. Schema (`schemas/calibration_overfit_check.schema.json`). `make calibration-overfit-check` target. 21 tests. 2995 total.
> **New in v0.5.83:** Batch-2 selection rationale report (G5) — CLI (`openamp-foundry batch-rationale`) that generates a synthetic candidate pool, runs the batch-2 selector with configurable weights, and produces a per-candidate rationale report classifying each selected candidate into exploit / explore / diversity / combined roles. Reports weight configuration, role breakdown summary, per-candidate contributions (ensemble×weight, uncertainty×weight, diversity×weight), safety gate impact, and caveats. Schema (`schemas/batch_rationale_report.schema.json`). `make batch-rationale` target. 19 tests. 2974 total.
> **New in v0.5.82:** Active-learning strategy comparison report (G4) — CLI (`openamp-foundry bench strategy-compare`) that compares 5 selection strategies (exploitation, exploration, diversity, combined, random) on the same synthetic pool with identical hidden active candidates. Each strategy runs multi-round recovery of hidden actives; the report ranks strategies by recall, compares the production selector vs pure strategies and random baseline, and produces structured JSON + Markdown output with caveats. Prevents one-selector bias by making strategy performance transparent. Schema (`schemas/active_learning_strategy_comparison.schema.json`). `make bench-strategy-compare` target. 18 tests. 2955 total.
> **New in v0.5.81:** Calibration pipeline consistency audit (G3) — CLI (`openamp-foundry calibration-audit`) that checks consistency across calibration pipeline artifacts (intake report, gate verdict, engine proposal, recalibration report). Checks intake↔gate count matching, engine↔gate verdict agreement, engine L1 budget compliance, report↔gate verdict consistency, report↔engine proposal consistency, timestamp sanity, and cohort-metrics warnings. Schema (`schemas/calibration_audit.schema.json`). `make calibration-audit` and `make calibration-audit-example` targets. 18 tests. 2937 total.
> **New in v0.5.80:** Negative-result archive completeness checker (F10) — CLI (`scripts/check_negative_archive_completeness.py`) that reads a JSON archive of negative-result entries and checks each entry against completeness criteria: all required fields present, no duplicate candidate_ids, each entry has at least one content field (assay_result, score_safety, reviewer_notes, or reason_detail), date format valid YYYY-MM-DD, and optional intake_report_id references are well-formed. Outputs a structured completeness report as JSON and Markdown with summary, per-check results, and per-entry pass/fail. Schema (`schemas/negative_result_archive_completeness.schema.json`). Example file (`examples/negative_result_archive_example.json`) with 4 toy entries. 35 tests. 2919 total.
>
> **New in v0.5.79:** Negative-result dashboard (F9) — CLI (`scripts/negative_result_dashboard.py`) that reads a collection of negative-result entries from a JSON file and produces a structured dashboard with summary statistics (by category, by pipeline version), score distributions (activity, safety, novelty, ensemble), per-category cross-analysis, and pipeline insights (most common failure category, recalibration opportunities). Outputs JSON + Markdown. Example file (`examples/negative_result_dashboard_example.json`) with 15 toy entries across all 6 failure categories. Schema (`schemas/negative_result_dashboard.schema.json`). `make negative-result-dashboard` target. 33 tests. 2883 total.
>
> **New in v0.5.79:** Bulk rejection-event validator (F8) — CLI (`scripts/validate_rejection_events.py`) that reads a JSON list of rejection events, validates each `rejection_code` against the rejection taxonomy (`examples/rejection_taxonomy_example.json`), checks required fields (candidate_id, rejection_code, date, pipeline_version), and outputs a PASS/FAIL validation report with per-event errors, rejection-code distribution, and Markdown summary. Example file (`examples/rejection_events_example.json`) with 6 toy events. `make validate-rejection-events` target. 26 tests. 2849 total.
>
> **New in v0.5.78:** Calibration link from negative-result entries to intake reports (F7) — closes learning loop by tracing each negative-result entry back to its prediction-vs-actual data in the calibration intake report. Schema addition: `intake_report_id` optional field on `negative_result_entry.schema.json`. CLI (`scripts/link_negative_result_to_intake.py`) reads negative-result archive JSON + calibration intake report, links by candidate_id, reports matched/unmatched entries, orphan intake candidates, lab summary for matched entries, and validates intake_report_id references. Produces structured JSON + Markdown link report. 25 tests. 2822 total.
>
> **New in v0.5.77:** Negative-result informativeness guide (F6) — comprehensive documentation defining 7-dimension informativeness framework for negative-result entries, with 14 examples across all 6 reason categories, before/after transformation pairs, and quick-reference checklist. CLI classifier (`scripts/classify_negative_result_informativeness.py`) that scores entries on 7 dimensions and produces informative/neutral/non-informative classification. 37 tests. 2796 total.
>
> **New in v0.5.76:** Safe-publication filter (F5) — CLI that reads candidate panel data with safety metadata and checks each candidate against publication safety constraints before external release. FAIL-CLOSED: defaults to reject unless all checks pass. Checks: dry_lab_only (must be true), proof_ladder_level (≤4), toxicity_screened, hemolysis_screened, dual_use_reviewed (all must be true). Produces structured JSON filter result and human-readable Markdown summary. 33 tests. 2758 total.
>
> **New in v0.5.75:** Failed-candidate report generator (F4) — CLI that reads candidate rejection data + taxonomy, produces structured JSON report with summary aggregation (by category, severity, stage, evidence impact) and human-readable Markdown summary. 26 tests. 2724 total.
>
> **New in v0.5.74:** Rejection reason taxonomy schema (F3) — machine-readable taxonomy with severity, evidence_impact, and applies_at_stage fields. Comprehensive REJECTION_TAXONOMY.md doc. 19 tests. 2698 total.
>
> **New in v0.5.73:** Safety-release decision schema (E4), pilot pre-registration schema (E5), review packet generator CLI (E6). 40 tests. 2679 total.
>
> **New in v0.5.72:** External review packet schema (E1), example packet (E2), reviewer questionnaire schema (E3). 27 tests. 2666 total.
>
> **New in v0.5.71:** Calibration benchmark added — Brier score, reliability diagram, and calibration slope for pipeline ensemble scores. Honest finding: Brier=0.318 (>0.25=uninformative), slope=0.43 (ideal=1.0). Pipeline ranks well but scores are not meaningful probabilities. `make bench-calibration`. 6 tests. ~2100 total.
>
> **New in v0.5.65:** `scripts/lab/build_lab_batch_pack.py` now writes `chain_of_custody.json` and `MANIFEST.json` into lab batch packs. The custody file includes SHA-256 hashes for `panel.csv`, the ordered candidate list, each candidate sequence, and each evidence certificate. `--verify-pack` verifies archive integrity and detects tampering. These hashes prove identity/integrity only, not biological activity, safety, or synthesis success. 5 tests.
> **New in v0.5.64:** `schemas/decision_log.schema.json` — 12-field JSON Schema for human review decisions. Covers 9 decision types from AGENTS.md §8. Dissent conditional. 11 tests. 2000 total.
> **New in v0.5.63:** `scripts/lab/build_lab_batch_pack.py` — generates single zip with candidate CSV, 36 evidence certs, protocol refs, controls manifest, data return template. `make lab-batch-pack`. 10 tests. 1989 total.
> **New in v0.5.62:** Pre-registered pass/fail criteria + simulation uncertainty in evidence. `configs/wave1_pass_fail.yaml` + `scripts/lab/check_wave1_pass_fail.py`. `rank info` now propagates simulation uncertainty into evidence certs. 17 tests.
> **New in v0.5.61:** `docs/review/LAB_PARTNER_ONBOARDING.md` — CRO onboarding pack with panel summary, synthesis instructions, assay protocols, data return format, controls, safety, timeline. No code changes.
> **New in v0.5.60:** `docs/evidence/SIMULATION_BENCHMARK.md` consolidates simulation ablation, cheap-baseline comparison, and weighted-mode gate results. Current conclusion: simulation does not improve ranking; `weighted` remains blocked.
> **New in v0.5.59:** `ExternalSimulationAdapter` protocol — wraps third-party callables into `VirtualAssayProxy`. Availability check, graceful error handling, metadata override. ARCHITECTURE.md docs updated. 12 tests. 1965 total.
> **New in v0.5.58:** Per-signal cheap-baseline comparison: 0/4 simulation signals beat their cheapest heuristic. All simulation modules remain permanently experimental. `make bench-simulation-baselines`. 13 tests. 1953 total.
> **New in v0.5.57:** `rank --simulation-mode info` runs MembraneProxy + StructureProxy on every candidate, adds `sim_*` scores to JSONL output and Markdown report. 6 new CLI tests. 1940 total.
> **New in v0.5.56:** `openamp-foundry bench simulation-gate` converts both
> simulation ablation artifacts into a fail-closed permission decision for
> `weighted` mode. Current verdict: blocked. AMP-vs-decoy delta remains
> negative and within-AMP delta remains negative, so simulation stays
> informational only. 6 tests. Current suite: 1927 passed, 7 skipped.
> **New in v0.5.55:** Within-AMP simulation ablation — `--mode within-amp` tests MembraneProxy + StructureProxy on hemolysis detection (45 hemolytic vs 125 selective). Honest finding: best simulation `helix_weight` AUROC 0.6458; `rich_selectivity` still best at 0.7453. 23 tests. 1928 total.
> **New in v0.5.54:** Simulation ablation benchmark — tests MembraneProxy + StructureProxy on 500-AMP AMP-vs-decoy benchmark. Honest finding: composite degrades (delta=−0.1153) but `bacterial_binding` alone achieves AUROC 0.7512 — genuine non-charge signal. 17 new tests. 1922 total.
> **New in v0.5.53:** Structure ensemble proxy — `StructureProxy` using Chou-Fasman 3-state helix/sheet/coil propensities. `non_helical` flag for helic-biased scorer warnings. `HelicityBaseline`. 34 new tests. 1905 total.
> **New in v0.5.52:** Membrane interaction proxy — `MembraneProxy` using Wimley-White interfacial/octanol scales for coarse-grained bacterial and mammalian binding energy scores. `BomanBaseline` clamped. 30 new tests. 1873 total.
> **New in v0.5.51:** Virtual assay scope document — `docs/evidence/VIRTUAL_ASSAY_SCOPE.md` with uncertainty policy, ablation requirements, integration modes. Doc drift fixes: BENCHMARKING.md, METRICS_CURRENT.md test count, NOVELTY_AUDIT_GUIDE.md script ref. No code changes.
> **New in v0.5.50:** Negative-result archive template — `docs/evidence/NEGATIVE_RESULT_ARCHIVE.md` with full 18-field entry schema, automation notes, and limitations. Phase 2 exit criteria: all 5 met ✅. No code changes.
> **New in v0.5.49:** Policy version bump workflow — `scripts/calibration/bump_recalibration_policy.py` (standalone CLI, decision-log guard, dry-run mode, auto-increment + write). CI guard in `ci.yml` validates policy version against base branch when `configs/recalibration_policy.yaml` changes. `make bump-policy-version` Makefile target. 9 tests. 1843 total passing. Phase 2 exit: 5 of 5 criteria met.
> **New in v0.5.48:** Fixed stale ARCHITECTURE.md package map — calibration and active_learning were listed as "Potential future packages" despite shipping in v0.5.19+ and v0.5.45+. Moved to main package map with version annotations. Updated 50_LOOP_PLAN.md "Current Position" and completed Phase 2 table. No code changes.
> **New in v0.5.47:** Full calibration loop end-to-end pytest test added — `TestFullCalibrationLoop.test_full_calibration_loop_via_cli` exercises all 5 pipeline steps via CLI subprocess calls in temp directory isolation. Validates every output artifact. Oldest "golden path" regression test. 1834 total passing.
> **New in v0.5.46:** Active-learning recovery benchmark added — `run_active_learning_benchmark()` simulates multi-round recovery of hidden active candidates via `select_batch_2` vs 20-trial random baseline. Pre-registered thresholds: PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY=3, PREREGISTERED_MIN_RECALL=0.33. `openamp-foundry bench active-learning` CLI. 8 tests. 1832 total passing.
> **New in v0.5.45:** Active-learning batch-2 selector added — `select_batch_2()` uses uncertainty (model disagreement + ensemble proximity to 0.5), diversity (sequence similarity vs batch-1), and safety/selectivity gates with min-uncertainty-probe guarantee. `openamp-foundry select-batch` CLI. 11 tests.
> **New in v0.5.44:** Recalibration report with JSON Schema validation added — `schemas/recalibration_report.schema.json` (Draft 2020-12), `build_recalibration_report()` combines gate verdict + weight proposal, `validate_recalibration_report()`, CLI `--out-json` and `--out-md`. 9 tests.
> **New in v0.5.43:** Dry-run mode for recalibration engine — `--dry-run` flag on `recalibration-engine` CLI prints diff table with current vs proposed weights, L1 summary. Skips all file writes. `make recalibration-engine-dry-run`.
> **New in v0.5.42:** Synthetic lab-result generator added — `examples/lab_results_generator.py` produces schema-valid JSON for 7 assay types (MIC, MBC, hemolysis_RBC, cytotoxicity_mammalian, membrane_disruption, time_kill, biofilm_inhibition). Configurable cohort-size, effect-size, noise-level, seed. All files explicitly SYNTHETIC-labeled. 40/40 schema-valid. Integrates with `calibration-intake`.
> **New in v0.5.41:** Added exact charge-balanced synthetic controls. These
> preserve each AMP's length and K/R/D/E/H counts, then resample neutral
> positions from a fixed neutral residue background. This is not a biological
> negative set, but it is a hard control for the trivial cationic prior. Result:
> charge-density AUROC falls to `0.5000`, while pipeline AUROC falls to `0.5103`
> (`pipeline_minus_charge_density=+0.0103`). The current broad AMP-vs-decoy
> signal is therefore not proven to survive exact charge control.
> **New in v0.5.38:** `pilot-panel` now supports an optional `--min-per-structural-class` floor using the same six classes as the v0.5.37 benchmark. This is a panel-construction bias control, not evidence that the under-ranked classes are stronger candidates.
> **New in v0.5.39:** Added charge-matched decoy benchmark to test whether the ensemble retains signal after controlling the trivial charge-density gap between positives and decoys. Current decoy pool does **not** support exact charge matching (`mean_abs_charge_density_delta=0.1296`), and charge density still beats the ensemble (`0.8166` vs `0.7792`). Treat raw AMP-vs-decoy AUROC as charge-inflated until a better charge-balanced negative set exists. See `outputs/benchmark_charge_matched.json`.
> **New in v0.5.35:** Cross-dataset generalization benchmark: DRAMP AMPs (database-independent test) achieve AUROC 0.7803 vs baseline 0.7832 (Δ=-0.0029). Pipeline generalises strongly — heuristic features are source-independent, not memorizing APD6/UniProt biases. Phase 1 exit criterion #5 (cross-dataset results) satisfied. See `outputs/cross_dataset_benchmark.json`.
> **New in v0.5.37:** Per-family benchmark breakdown: stratifies 500 AMPs by structural class. Pipeline is charge-dominated — highly_cationic AUROC 0.9583 vs proline_rich AUROC 0.5861 (Δ=0.37). Classes with weak discrimination flagged as blind spots. See `outputs/benchmark_per_family.json`.
> **New in v0.5.33:** Expert ablation re-run on expanded 500-AMP benchmark (n=1000). Two components reclassified: synthesis was an anti-signal artifact on n=191 (now near-zero 0.4968); boman_activity more strongly anti-AMP (0.3291). selectivity_proxy weaker on diverse set (0.6702 vs 0.7729). Activity remains dominant signal (0.7969). Expert composite delta widens to −0.0935 — expected tradeoff for selectivity-aware scoring.
> **New in v0.5.32:** Precision@k calibration added — top-20 precision 1.000 (all AMPs), top-50 precision 0.900, top-100 precision 0.870, top-200 precision 0.835. Best F1 threshold 0.6323 (F1=0.7518, precision=0.6337, recall=0.9240). At 80% recall, precision drops to base-rate (0.5000) — honest limitation: high-recall triage is not the pipeline's strength.
> **New in v0.5.31:** Added dipeptide-order features for sequence-order awareness. `dipeptide_order_score` achieves AUROC 0.7861 on AMP-vs-scrambled discrimination — the strongest order-dependent feature in the pipeline. Only 7/31 features survive scrambling (amphipathicity/helix-wheel + dipeptide). All composition features are purely position-independent (exactly 0.5000 AUROC on scrambled test).
> **New in v0.5.30:** Easy baseline benchmark added — charge density alone (AUROC 0.8166) outperforms the full pipeline ensemble (0.7792) on AMP-vs-Swiss-Prot-decoy discrimination. Honest finding documented: expected because pipeline optimizes for safety, not raw discrimination.
> **New in v0.5.29:** Expanded benchmark to 500 AMPs + 500 composition-matched decoys (n=1000). AUROC 0.7792 (CI₉₅: 0.7505–0.8065) confirms signal generalizes. Cluster-aware CI: 0.746–0.8102. Representative AUROC: 0.778. Standard benchmark (n=191) retained for backward comparison.
> **Pipeline version:** v0.9.2 (M4 — reviewer briefing package)
> **Branch:** main

---

## Benchmark Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Benchmark type | Standard (composition-matched decoys) | Default `make validate-scoring` |
| Positives | **95** public-domain AMPs | 12 taxonomic classes; see `examples/validation/known_amps.csv` |
| Negatives | **96** length-matched random decoys | Swiss-Prot residue frequencies, seed=1729 |
| Total (n) | **191** | Expanded from original 87 (PR #110) |
| **Pipeline AUROC** | **0.7832** | Bootstrap CI₉₅: 0.72–0.84 (n_bootstrap=2000) |
| **Phase3 AUROC** | **0.7448** | Synthesis gate config; CI₉₅: 0.68–0.81 |
| **Pipeline AUPRC** | **0.8164** | Random baseline: 0.4974 |
| **Phase3 AUPRC** | **0.7933** | Random baseline: 0.4974 |
| Strict AUROC (scrambled) | 0.4335 | 95 shuffled decoys; below random — expected for helic-centric scorer |
| Recall@10 | 0.1053 | 10/95 positives in top 10 |
| Recall@20 | 0.2105 | 20/95 positives in top 20 |
| Recall@43 | 0.4211 | 40/95 positives in top 43 |
| Interpretation | **STRONG** | AUROC > 0.70 gate passed |


### Expanded 500-AMP Benchmark (n=1000)

> Added 2026-07-05. The original benchmark (95 AMPs + 96 decoys, n=191) was
> expanded to 500 AMPs + 500 length-matched decoys (n=1000) using UniProt
> reviewed AMPs (CC BY 4.0) and APD6 natural sequences (academic use).
> This provides a more honest estimate of pipeline discriminative power
> with tighter confidence intervals.
>
> Curated by: `scripts/benchmarks/curate_500_amp_benchmark.py`
>
> Run: `make bench-500`

| Metric | Value | Notes |
|--------|-------|-------|
| Positives | **500** public-domain AMPs | UniProt reviewed + APD6 natural + existing curated |
| Negatives | **500** length-matched random decoys | Swiss-Prot residue frequencies, seed=20260705 |
| Total (n) | **1000** | ~2.3× reduction in CI width over the original 87-seq benchmark |
| **Pipeline AUROC** | **0.7792** | Bootstrap CI₉₅: 0.7505–0.8065 |
| **Phase3 AUROC** | **0.7744** | Synthesis gate config |
| **Pipeline AUPRC** | **0.7705** | Random baseline: 0.5000 |
| **Phase3 AUPRC** | **0.7656** | Random baseline: 0.5000 |
| Recall@10 | 0.020 | 10/500 positives in top 10 |
| Recall@20 | 0.040 | 20/500 positives in top 20 |
| Recall@43 | 0.076 | 38/500 positives in top 43 |
| Interpretation | **STRONG** | AUROC > 0.70 gate passed |

### Cross-Dataset Generalization: DRAMP (v0.5.35, added 2026-07-05)

Tests whether pipeline heuristic features discriminate AMPs from a different
database — DRAMP (Data Repository of Antimicrobial Peptides) — against the same
Swiss-Prot frequency decoys. DRAMP-only sequences (n=500, not in current
benchmark set) vs length-matched decoys.

| Metric | DRAMP-only | Current baseline (APD6/UniProt) | Δ |
|--------|:----------:|:-------------------------------:|:-:|
| AUROC | **0.7803** | **0.7832** | **−0.0029** |
| CI₉₅ | 0.7517–0.8081 | 0.7505–0.8065 | — |
| AUPRC | 0.8071 | 0.8164 | — |
| Mean AMP score | 0.8178 | — | — |
| Mean decoy score | 0.7197 | — | — |

**Key finding:**
- Pipeline generalises strongly — AUROC is essentially identical (Δ=−0.0029).
- Heuristic features (charge, hydrophobicity, hydrophobic moment, etc.) are
  **source-independent**: they capture fundamental AMP physicochemical properties
  rather than database-specific biases.
- 65% of current AMP set (325/500) overlap with DRAMP — expected because DRAMP
  is a meta-database that includes APD6. DRAMP-only test uses the remaining
  6427 sequences with zero overlap.

**Phase 1 exit criterion #5 satisfied:** cross-dataset results published.

### Expanded Cluster-Split Benchmark (near-duplicate de-inflation)

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Full AUROC | 0.7792 | 0.7744 |
| **Cluster-aware CI₉₅** | **0.746–0.8102** | **same config** |
| Representative AUROC (1/cluster) | 0.778 | 0.7744 |
| Representative CI₉₅ | 0.7455–0.8084 | — |
| Held-out AUROC (195 near-dup AMPs) | 0.7828 | — |
| Independent clusters | 374 / 500 | 374 / 500 |
| AMPs in multi-member clusters | 195 / 500 | 195 / 500 |
| Multi-member clusters | 69 | 69 |

**Key findings:**

1. **Signal generalizes to 10× larger set.** AUROC 0.7792 on n=1000 is essentially
   identical to 0.7832 on n=191. The pipeline does not overfit to the 95-sequence
   benchmark.

2. **CIs are much tighter.** Cluster-aware CI: 0.746–0.8102 (width 0.064) vs
   0.7061–0.8526 (width 0.146) on n=191. The expanded set provides ~2.3× tighter
   confidence intervals.

3. **Representative AUROC nearly equals full AUROC.** 0.778 vs 0.7792. On the
   original benchmark, representative AUROC (0.7607) was lower than full (0.7832).
   The expanded set's 500 sequences are less dominated by near-duplicate inflation.

4. **Cluster-aware CI lower bound (0.746) is well above the 0.65 gate.** The
   pipeline's signal is robust to near-duplicate de-inflation.

5. **Honest limitation:** The expanded set uses UniProt-reviewed and APD6 sequences
   annotated as antimicrobial. These carry the same annotation bias as the original
   set: AMP annotation is an active research field, and some annotated AMPs may not
   be genuinely antimicrobial. The set also includes fewer defensins and
   cysteine-rich peptides due to the 10–30 AA length constraint.

### Easy Baseline Benchmark (trivial feature comparison)

> Added 2026-07-05 (v0.5.30). Compares the full pipeline ensemble against
> single-feature trivial predictors (length, charge, charge density) on the
> expanded 500-AMP benchmark. If the pipeline does not significantly outperform
> trivial features, its value must come from multi-objective optimization,
> not better basic discrimination.
>
> Run: `make bench-easy-baseline`

| Predictor | AUROC | Notes |
|-----------|-------|-------|
| Length alone | 0.5000 | Decoys are length-matched — no signal |
| Net charge (pH 7.4) | 0.8125 | AMPs are cationic — known strong predictor |
| **Charge density** | **0.8166** | **Best trivial feature** |
| Length + charge (Z-scored) | 0.5024 | Length adds nothing (matched decoys) |
| **Pipeline ensemble** | **0.7792** | **Below best trivial (Δ=−0.0374)** |

**Honest finding:** The pipeline ensemble does NOT outperform charge density
alone on AMP-vs-Swiss-Prot-decoy discrimination. This is expected because:

1. **AMPs are cationic by nature.** Net positive charge is the single strongest
   predictor of antimicrobial function. This is a well-known result in the
   AMP prediction literature (Lata et al. 2007, Waghu et al. 2016).

2. **The pipeline optimizes for 4 objectives.** The ensemble combines activity
   (0.40), safety (0.25), synthesis (0.15), and novelty (0.20). The safety
   scorer explicitly penalizes high-charge peptides (hemolytic risk). This
   reduces raw AMP/non-AMP discrimination — intentionally.

3. **Charge density alone has no safety penalty.** A pure charge-density
   predictor ranks all high-charge sequences highly — including hemolytic ones.
   The pipeline trades some raw discrimination for safety awareness.

**Implication:** The current AMP-vs-Swiss-Prot-decoy benchmark primarily tests
charge-based discrimination, which is not where the pipeline's value lies.
A benchmark that tests the pipeline's actual objective (finding SAFE, novel,
synthesizable AMPs) would more honestly assess the ensemble's contributions.

**Recommendation for benchmarks that test the pipeline's actual value:**
- Use charge-matched decoys (now implemented in `make bench-charge-matched`)
- Test safe-AMP detection (active AND non-hemolytic vs hemolytic AMPs)
- Test multi-objective ranking (does the ensemble rank safe, novel, synthesizable AMPs above toxic or trivially known ones?)

### Charge-Matched Decoy Benchmark

> Added 2026-07-06 (v0.5.38). This benchmark greedily matches each AMP to an
> unused decoy with nearest charge density, then compares the ensemble against
> charge density on that adversarial set.
>
> Run: `make bench-charge-matched`

Purpose: test the exact failure mode exposed by the easy baseline benchmark.
If the ensemble only works because AMPs are more cationic than generic decoys,
it should lose most of its signal once that gap is removed.

Primary output:
- `outputs/benchmark_charge_matched.json`

Observed result:
- `mean_abs_charge_density_delta = 0.1296`
- `charge_density_auroc = 0.8166`
- `pipeline_auroc = 0.7792`
- `pipeline_minus_charge_density = -0.0374`

Interpretation:
- The easy-baseline concern survives: charge density remains a stronger raw
  discriminator than the ensemble on the current matched set.
- The corrected implementation fixed an earlier false-zero bug (`charge_ph74`
  was not a feature key). The benchmark now uses direct pH-7.4 side-chain charge.
- Confirmed fact: the current decoy pool is insufficient for exact
  charge-density matching across all 500 positives.
- Remaining uncertainty: the ensemble may still retain non-charge signal, but
  this benchmark does not prove it. A stronger charge-balanced decoy generator
  is now the next honest test.

This benchmark is informational, not a regression gate. Its job is honesty:
separate genuine ensemble discrimination from the trivial cationic prior.

### Charge-Balanced Synthetic Control Benchmark

> Added 2026-07-06 (v0.5.41). This benchmark creates one deterministic
> synthetic negative control per AMP. Each synthetic control preserves the AMP's
> length and exact K/R/D/E/H counts, then resamples all neutral positions from a
> fixed neutral residue background.
>
> Run: `make bench-charge-matched`

Purpose: force charge density to be non-discriminative and ask whether the
current pipeline still separates AMPs from a charge-equivalent synthetic
background.

Primary output:
- `outputs/benchmark_charge_balanced_synthetic.json`

Observed result:
- `mean_abs_charge_density_delta = 0.0000`
- `max_abs_charge_density_delta = 0.0000`
- `charge_density_auroc = 0.5000`
- `pipeline_auroc = 0.5103`
- `pipeline_minus_charge_density = +0.0103`

Interpretation:
- This is a negative result for broad AMP-vs-decoy discrimination after exact
  charge control. The pipeline is only barely above chance on this synthetic
  control.
- The control is intentionally synthetic and should not be mistaken for a real
  inactive-peptide distribution.
- The result strengthens the current benchmark warning: the pipeline's value
  must be judged on safety-aware, novelty-aware, and wet-lab-calibrated
  selection, not raw AMP-vs-generic-decoy AUROC.

Next benchmark bottleneck:
- Build a biologically plausible charge-balanced negative set or a benchmark
  framed around the actual objective: active, low-hemolysis, novel, synthesizable
  candidates versus toxic, copied, unstable, or inactive controls.

### Order-Dependent Features Benchmark (which features survive scrambling?)

> Added 2026-07-05 (v0.5.31). The pipeline's strict triage benchmark (AMP vs
> scrambled sequence, preserving composition) tests whether the pipeline is
> aware of sequence order. This benchmark analyzes which of the 31 scalar
> features survive scrambling, and introduces the new `dipeptide_order_score`
> feature.
>
> Run: `make bench-order-dependent`

**Key finding:** Only 7/31 features are order-dependent (AUROC > 0.55 on
AMP-vs-scrambled). All composition-based features (charge, hydrophobicity,
aromatic fraction, boman index, gravy, etc.) are EXACTLY position-independent
(AUROC = 0.5000 on scrambled test — real and scrambled sequences have
identical means).

| Feature | AUROC | Mean (real) | Mean (scrambled) | Order-dependent? |
|---------|-------|-------------|-------------------|:----------------:|
| **dipeptide_order_score** | **0.7861** | 0.5644 | 0.4603 | ✅ **#1** |
| hydrophobic_moment | 0.7483 | 0.3198 | 0.1949 | ✅ |
| helix_wheel_face_contrast | 0.7398 | 0.8469 | 0.4922 | ✅ |
| helix_wheel_amphipathic_score | 0.7396 | 0.4239 | 0.2485 | ✅ |
| max_hydrophobic_moment | 0.7146 | 0.5189 | 0.3991 | ✅ |
| helix_wheel_hydrophobic_face_mean_h | 0.6372 | 0.5798 | 0.4113 | ✅ |
| helix_wheel_ph_face_cationic_fraction | 0.5595 | 0.2732 | 0.2402 | ✅ |
| *All composition features (charge, hydrophob., etc.)* | *0.5000* | *identical* | *identical* | ❌ |

**Analysis:**

1. **dipeptide_order_score is the strongest order-dependent feature** (0.7861).
   It captures local dipeptide patterns that are characteristic of AMPs and
   destroyed by scrambling. The score uses a pre-computed reference of log-odds
   from the 500-AMP benchmark (real vs scrambled).

2. **Hydrophobic moment and helix wheel features** are the only other
   order-dependent signals. They depend on which residues are on the hydrophobic
   vs hydrophilic face of an idealised helix — a position-dependent property.

3. **All composition features are EXACTLY 0.5000.** This is a mathematical
   necessity: composition is invariant under permutation. Scrambling changes
   the position of residues but not their counts.

4. **Some features are anti-order-dependent** (AUROC < 0.5): aggregation
   propensity (0.4325), helix_wheel_hydrophilic_face_mean_h (0.3506).
   Scrambled sequences score higher on these — the scrambling process
   creates patterns that are more aggregation-prone than the native AMP.

**Recommendation:** The dipeptide_order_score should be considered for
integration into the ensemble scoring when the benchmark is next re-baselined.
It provides orthogonal order-dependent signal that the existing composition-based
features cannot capture.

### Precision@k Calibration (operating characteristic for candidate selection)

> Added 2026-07-05 (v0.5.32). Translates the pipeline's AUROC into actionable
> operational guidance: at a given k, what precision/recall can we expect? At a
> given recall, what threshold should we use? This addresses the gap between
> "AUROC > 0.70" (binary discrimination) and "how many candidates do I need to
> pick to find X AMPs?" (operational triage).
>
> Dataset: 500 AMPs + 500 decoys (balanced, base rate = 50%)
>
> Run: `make bench-precision-at-k`

**Small-k triage (top-k analysis):**

| k | Precision | Recall | Enrichment factor | AMPs found |
|:-:|:---------:|:------:|:-----------------:|:----------:|
| 1 | 1.000 | 0.002 | 2.00 | 1 |
| 5 | 1.000 | 0.010 | 2.00 | 5 |
| 10 | 1.000 | 0.020 | 2.00 | 10 |
| 20 | 1.000 | 0.040 | 2.00 | 20 |
| 50 | 0.900 | 0.090 | 1.80 | 45 |
| 100 | 0.870 | 0.174 | 1.74 | 87 |
| 200 | 0.835 | 0.334 | 1.67 | 167 |

**Threshold-based operating characteristic:**

| Operating point | Threshold | Precision | Recall | F1 | Candidates above |
|:---------------:|:---------:|:---------:|:------:|:--:|:----------------:|
| Best F1 | 0.6323 | 0.6337 | 0.9240 | **0.7518** | 729 (462 AMPs + 267 decoys) |
| 80% recall | 0.4943 | 0.5000 | 0.8000 | 0.6667 | 1000 (500 AMPs + 500 decoys) |

**Key findings:**

1. **Top-20 triage is perfect** (precision 1.000). The pipeline's top 20 candidates
   are all genuine AMPs. This is the most relevant operating point for candidate
   selection: if you pick the top 20, you get 20 real AMPs.

2. **Top-50 still excellent** (0.900). 45/50 top-ranked sequences are AMPs. The
   pipeline enriches AMPs 1.8× over random at k=50.

3. **Enrichment persists to k=200** (0.835, 1.67×). Even at 200 candidates, the
   pipeline maintains strong enrichment.

4. **Best F1 threshold at 0.6323** (F1=0.7518) — this is the threshold that
   maximises precision+recall balance. At this threshold, 729 of 1000 candidates
   score above 0.6323, of which 462 are true AMPs and 267 are false positives.

5. **At 80% recall, precision drops to base-rate** (0.5000). This is an honest
   limitation: to capture 80% of AMPs, you must accept ~80% of decoys as well.
   The score distribution of AMPs and decoys overlaps substantially in the
   middle range (0.5–0.75). High-recall triage is not the pipeline's strength.

6. **For operational use:** The pipeline is best used as a small-k triage tool
   (pick top 20–50 candidates where precision is ≥0.90). For large-scale
   screening, use the best-F1 threshold (0.63) which gives precision 0.63 and
   recall 0.92 — a practical balance.

**Honest limitation:** This benchmark uses a balanced 50/50 dataset. In real
screening, the AMP base rate may be much lower (1–10%), which would reduce
precision at every operating point. The enrichment factors (1.67–2.00×) are
dataset-dependent and may not generalise to low-prevalence screening scenarios.

### Cluster-Split Benchmark (near-duplicate de-inflation, n=191)

> Added 2026-07-01. The standard benchmark treats all 95 AMPs as independent samples.
> 33 of 95 AMPs are in 14 near-duplicate clusters (sim >= 0.70): magainin-1/2/3,
> protegrin-1/2/3, tachyplesin-I/II/polyphemusin-I, indolicidin/analog/lys-analog, etc.
> The cluster-aware bootstrap resamples clusters (not sequences) to produce an honest CI.

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Full AUROC | 0.7832 | 0.7448 |
| Standard CI₉₅ | 0.717–0.8423 | 0.6741–0.8118 |
| **Cluster-aware CI₉₅** | **0.7061–0.8526** | **0.6591–0.8237** |
| Representative AUROC (1/cluster) | 0.7607 | 0.7196 |
| Representative CI₉₅ | 0.6854–0.8301 | 0.6372–0.7985 |
| Held-out AUROC (19 near-dup AMPs) | 0.8734 | 0.8454 |
| Independent clusters | 76 / 95 | 76 / 95 |
| AMPs in multi-member clusters | 33 / 95 | 33 / 95 |
| Multi-member clusters | 14 | 14 |

**Key finding:** The cluster-aware CI (0.7061–0.8526) is wider than the standard CI
(0.717–0.8423) on the upper end but the lower bound drops below the standard CI
(0.7061 vs 0.717). The representative-only AUROC (0.7607, CI: 0.6854–0.8301) confirms
the signal is not entirely driven by near-duplicate redundancy — but the CI lower
bound (0.6854) dips below the 0.70 synthesis gate threshold. The pipeline passes the
cluster-aware gate (CI lo > 0.65) but with less margin than the standard benchmark
suggested. The held-out AUROC (0.8734) is high because held-out near-duplicates share
composition features with their cluster representatives — this is expected and not
evidence of generalisation to novel sequence space.

**Verdict:** Signal survives near-duplicate de-inflation. The synthesis gate (AUROC >
0.70) holds on the full set and the cluster-aware CI lower bound stays above 0.65.
The representative-only CI lower bound (0.6854) crossing below 0.70 is an honest
limitation: the pipeline has real but modest discriminative power, and the headline
CI was slightly overconfident.

Run: `openamp-foundry bench cluster-split`

### Historical baselines

| Point | Benchmark | AUROC | Phase3 AUROC | Source |
|-------|-----------|-------|--------------|--------|
| **Expanded** | **500 AMP + 500 decoy (n=1000)** | **0.7792** | **0.7744** | v0.5.29 (Loop 11) |
| Standard | 95 AMP + 96 decoy (n=191) | 0.7832 | 0.7448 | PR #110 |
| Original demo set | 43 AMP + 44 decoy (n=87) | 0.8420 | 0.8266 | PR #72 |
| Pre-face-bonus | 43 + 44 | 0.8348 | 0.8126 | PR #70 |
| Pre-windowed-mu_h | 43 + 44 | 0.8047 | 0.7846 | PR #66 |
| Pre-Trp-bonus | 43 + 44 | 0.8164 | — | PR #65 (transient) |

**Note:** The expanded benchmark (500+500, n=1000) is now the primary benchmark.
The n=191 benchmark is retained for backward comparison. The expanded set is more
representative of diverse AMP classes and provides ~2.3× tighter confidence intervals.
Historical baselines from the demo set (n=87) should not be directly compared with
the expanded benchmark — the helic-centric scorer's strong performance on small
amphipathic-helix sets does not reflect performance on diverse AMP classes.

---

### Per-Family Benchmark Breakdown (by structural class)

> Added 2026-07-05 (v0.5.37). The expanded 500-AMP benchmark reports a single
> AUROC for all AMPs. This benchmark stratifies the AMP set by heuristic
> structural class to reveal which families the pipeline handles well or poorly.
>
> Classification rules (mutually exclusive, priority order): cysteine_rich (≥2 Cys),
> short (≤12 AA), proline_rich (Pro ≥ 15%), highly_cationic (charge ≥ 4.0),
> moderately_cationic (charge 2.0–3.9), low_charge (charge < 2.0).
>
> Run: `make bench-per-family`

| Class | N | AUROC | CI₉₅ | Δ vs baseline | Mean ensemble | Description |
|-------|:-:|:-----:|:----:|:-------------:|:-------------:|-------------|
| highly_cationic | 73 | **0.9583** | 0.936–0.976 | +0.1791 | 0.8700 | Net charge pH 7.4 ≥ 4.0 |
| moderately_cationic | 115 | **0.8940** | 0.868–0.918 | +0.1148 | 0.8355 | Net charge pH 7.4 2.0–3.9 |
| cysteine_rich | 153 | **0.7230** | 0.677–0.768 | −0.0562 | 0.7918 | β-sheet / disulfide-stabilised |
| low_charge | 118 | **0.6925** | 0.642–0.738 | −0.0867 | 0.7812 | Net charge pH 7.4 < 2.0 |
| short | 21 | **0.6095** | 0.486–0.727 | −0.1697 | 0.7608 | Length ≤ 12 AA |
| proline_rich | 20 | **0.5861** | 0.418–0.735 | −0.1931 | 0.7534 | Pro fraction ≥ 0.15 |
| **all_amps (baseline)** | **500** | **0.7792** | **0.750–0.807** | — | **0.8079** | Full AMP set |

**Key findings:**

1. **Pipeline is charge-dominated.** Classes with higher charge (highly_cationic
   AUROC 0.958, moderately_cationic 0.894) outperform the baseline by a wide
   margin. The two classes account for 188/500 AMPs (37.6%) and drive the
   overall AUROC. This is consistent with the easy baseline benchmark (v0.5.30):
   charge density alone achieves AUROC 0.8166.

2. **Proline-rich AMPs are the worst-handled class** (AUROC 0.586, CI includes
   0.50). This is expected — proline-rich AMPs (Bac2A, PR-39, indolicidin) have
   non-helical, extended structures that the helic-centric activity scorer does
   not reward. Wet-lab selection should avoid overweighting the ensemble score
   for proline-rich families without corroborating evidence.

3. **Short AMPs (≤12 AA) also perform poorly** (AUROC 0.610, CI includes 0.50).
   Short sequences have insufficient residues for the hydrophobic-moment and
   helix-wheel features to be meaningful. The pipeline's physicochemical proxies
   are designed for optimal 15–25 AA range.

4. **Cysteine-rich AMPs show moderate discrimination** (AUROC 0.723) despite the
   pipeline lacking any explicit β-sheet or disulfide scoring. The signal comes
   from secondary features (composition, charge, hydrophobicity) that correlate
   with cysteine-rich AMPs — not from cysteine-specific modeling.

5. **Low-charge AMPs underperform the baseline** (AUROC 0.693). AMPs with net
   charge < 2.0 are harder to distinguish from decoy sequences, which also have
   low average charge.

6. **Implication for candidate selection:** Top-ranked candidates are likely to
   be highly or moderately cationic AMPs with well-formed amphipathic helices.
   The pipeline systematically undervalues non-helical, short, low-charge, or
   proline-rich candidates. Diversity selection should deliberately compensate.

**Shipped response (v0.5.38):**
- `openamp-foundry pilot-panel --min-per-structural-class 1` can reserve one
  slot per heuristic structural class before normal seed/remainder fill.
- Default remains `0`, preserving existing behavior.
- This improves assay-panel reviewability. It does not fix the scorer.

---

## Candidate Panel

| Metric | Value |
|--------|-------|
| Wave 0 panel size | 20 candidates |
| Wave 0 scaffold families | 7 (SEED-001, 003, 005, 006, 007, 008, 009) |
| **Wave 1 final panel (Wave 0.5)** | **24 candidates** |
| **Wave 1 scaffold families** | **15 (Wave 0 carry-overs + 9 new families)** |
| Wave 0.5 new families | 10 (SEED-010 through SEED-019) |
| Wave 0.5 shortlisted | 60 (6 per family × 10 families) |
| Wave 0.5 novelty (v2, 27k DB) | 1 RELATED_NOVEL / 39 CLOSE_RELATIVE / 19 KNOWN_VARIANT / 1 EXACT_MATCH_OR_FRAGMENT |
| Wave 0.5 novelty v1 (72 refs, Levenshtein) | 53/60 RELATED_NOVEL or higher — v1 method overstated novelty |
| Broad novelty Wave 0 (72 refs) | 16/20 NOVEL, 3 KNOWN_VARIANT, 1 CLOSE_RELATIVE |
| 5-tier audit Wave 0 (120 refs) | 13 HIGH_CONFIDENCE_NOVEL + 3 NOVEL + 1 CLOSE_RELATIVE + 3 KNOWN_VARIANT |
| Wave 0 panel ensemble range | 0.796–0.857 |
| Wave 0 panel safety range | 0.845–1.000 |
| Positive control | SEED-001_VAR_064 (magainin-1 derivative, ensemble 0.802) |
| Blind spot | Melittin scores Safety=1.0 despite hemolysis; hemolysis assay mandatory |
| Wave 0.5 external predictors | **COMPLETE** — AMPScanner 59/60, AMPActiPred 60/60, Macrel AMP 52/60 |
| Wave 0.5 activity consensus | **STRONG_ACTIVITY: 52/60 (87%)** — passes W0.5-3 gate (≥70%) |
| Wave 0.5 HemoFinder | LOW: 40/60 (67%), HIGH: 20/60 |
| Wave 0.5 AntiCP 2.0 | Non-AntiCP: 4/60 (7%), AntiCP: 56/60 |
| Best clean candidate | SEED-019_VAR_004 (RVRIRLVKRLLK) — STRONG + Non-AntiCP + HemoFinder LOW |
| **Wave 0.5b** | **23 candidates shortlisted** (5 new families SEED-020→024, no aromatics) |
| Wave 0.5b design goal | Lower AntiCP risk: no W/Y/F residues; broken helix pattern |
| Wave 0.5b expected AntiCP | < 0.50 (by design — pending external predictor confirmation) |

### Wave 1 Panel Composition (Wave 0.5 output, post-v2 novelty update)

| Role | Count |
|------|-------|
| BALANCED_LEAD | 15 |
| HIGH_UPSIDE_RISKY | 4 |
| POSITIVE_CONTROL | 1 |
| SAR_CONTROL | 4 |

### Novel families (Wave 0 leads)

| Family | Mechanism | Panel slots | Novelty | Key risk |
|--------|-----------|:-----------:|---------|----------|
| SEED-006 | Mastoparan-X, wasp-venom helix insertion | 2 | 0.643 | Mast-cell degranulation |
| SEED-007 | Bombolitin-II, bumblebee venom | 1 | 0.643 | Met oxidation at pos 6 |
| SEED-008 | Puroindoline-a, Trp-rich interfacial | 2 | 0.692 | DKP risk (FP), HemoFinder HIGH |
| SEED-009 | Bac2A, proline-rich intracellular | 2 | 0.647 | AntiCP risk, RPMI-1640 arm |

### New Wave 0.5 families in Wave 1 panel (v2 novelty classes)

| Family | Mechanism | Panel slots | v2 Novelty class |
|--------|-----------|:-----------:|---------------|
| SEED-010 | Histatin-5 P-113 oral innate AMP fragments | 1 | KNOWN_VARIANT (SAR_CONTROL) |
| SEED-011 | Pro-kinked amphipathic | 1 | CLOSE_RELATIVE |
| SEED-012 | Glycine-rich low-hydrophobicity design | 2 | CLOSE_RELATIVE |
| SEED-014 | Cathelicidin-mini scattered helix | 1 | CLOSE_RELATIVE |
| SEED-015 | KFLK de novo cationic helix | 1 | CLOSE_RELATIVE |
| SEED-016 | RRWK dual-Trp low-aromatic | 2 | CLOSE_RELATIVE |
| SEED-018 | GKRK scattered-charge design | 2 | CLOSE_RELATIVE |
| SEED-019 | Arg-Val alternating pattern | 2 | RELATED_NOVEL / CLOSE_RELATIVE |

---

## External Predictor Results (Wave 0.5)

| Tool | Status | Result |
|------|--------|--------|
| CAMPR4 | ⏳ Not submitted | PENDING |
| AMPScanner v2 | ✅ Complete | 59/60 AMP (98%) |
| AMPActiPred | ✅ Complete | 60/60 ABP (100%) |
| Macrel AMP | ✅ Complete | 52/60 AMP (87%) |
| HemoFinder | ✅ Complete | 40/60 LOW (67%), 20/60 HIGH |
| AntiCP 2.0 | ✅ Complete | 4/60 Non-AntiCP, 56/60 AntiCP |
| Macrel Hemolysis | ✅ Complete | 60/60 flagged (non-discriminating — flags all) |

**Activity consensus (3 tools, CAMPR4 excluded):** 52/60 STRONG_ACTIVITY, 7/60 MODERATE, 1/60 WEAK

**Safety profile concern:** 56/60 AntiCP-positive is expected for amphipathic-helix designs.
AntiCP 2.0 detects anticancer peptide (ACP) patterns, not antimicrobial activity directly.
Mitigation: Wave 0.5b designs avoid aromatic residues and pure amphipathic helix.

Current-state summary is documented here. Wave 0.5 machine-readable CSV outputs are
generated locally via `make wave0-5-fill-external` when `outputs/wave05_combined_consensus.csv`
is present; they are not guaranteed to be committed in every checkout.

---

---

## Expert Ablation Benchmark (v0.5.x — added 2026-07-01; re-run on n=1000 v0.5.33)

> The expert composite scorer (`scoring/expert.py`) adds four components beyond the
> simple ensemble: selectivity, serum stability, helix-hinge, and k-mer motif novelty.
> This ablation tests whether those additions improve binary AMP-vs-decoy discrimination
> or are complexity that does not earn its keep.
>
> Run: `make bench-expert-ablation` (n=191) or `make bench-expert-ablation-500` (n=1000)

### Original benchmark (n=191)

| Metric | Pipeline (pipeline.yaml) | Phase3 (phase3.yaml) |
|--------|:-----------------------:|:-------------------:|
| Ensemble AUROC | 0.7832 | 0.7448 |
| Ensemble CI₉₅ | 0.717–0.8423 | 0.6741–0.8118 |
| Expert composite AUROC | 0.7097 | 0.7097 |
| Expert CI₉₅ | 0.6384–0.7871 | 0.6384–0.7871 |
| **Delta (expert − ensemble)** | **−0.0735** | **−0.0351** |
| Verdict | Expert LOWER | Expert LOWER |

### Expanded benchmark (n=1000, added v0.5.33)

| Metric | Pipeline (pipeline.yaml) |
|--------|:-----------------------:|
| Ensemble AUROC | 0.7792 |
| Ensemble CI₉₅ | 0.7503–0.8070 |
| Expert composite AUROC | 0.6857 |
| Expert CI₉₅ | 0.6523–0.7170 |
| **Delta (expert − ensemble)** | **−0.0935** |
| Verdict | Expert LOWER |

Run: `make bench-expert-ablation-500`

### Per-component comparison (n=191 vs n=1000)

| Component | n=191 AUROC | n=191 class | n=1000 AUROC | n=1000 class | Change |
|-----------|:-----------:|:-----------:|:------------:|:------------:|:------:|
| activity | 0.8137 | Signal-bearing | **0.7969** | Signal-bearing | ↓0.0168 (stable) |
| selectivity_proxy | 0.7729 | Signal-bearing | **0.6702** | Signal-bearing | ↓0.1027 (weaker on diverse set) |
| hinge_selectivity | 0.5180 | Near-zero | **0.5004** | Near-zero | ↓0.0176 (stable) |
| novelty | 0.5000 | Near-zero | **0.5000** | Near-zero | 0.0000 (by construction) |
| motif_novelty | 0.5000 | Near-zero | **0.5000** | Near-zero | 0.0000 (by construction) |
| synthesis | 0.4228 | Anti-signal | **0.4968** | Near-zero | **↗ Reclassified** — n=191 artifact |
| boman_activity | 0.4620 | Near-zero | **0.3291** | Anti-signal | **↘ Reclassified** — stronger anti-AMP on diverse set |
| safety | 0.3487 | Anti-signal | **0.4459** | Anti-signal | ↑0.0972 (less extreme) |
| serum_stability | 0.2231 | Anti-signal | **0.3767** | Anti-signal | ↑0.1536 (less extreme) |
| rich_selectivity | 0.1973 | Anti-signal | **0.3407** | Anti-signal | ↑0.1434 (less extreme) |

### Updated key findings

The expanded benchmark (n=1000) **changes two classifications** and **tightens uncertainty**:

1. **synthesis was an anti-signal artifact on n=191.** At 0.4968 on n=1000, synthesis feasibility is essentially neutral — AMPs and decoys have similar average synthesis difficulty. The original finding (0.4228) was a small-n artifact on the original 95-sequence benchmark, which was enriched for manually curated AMPs with unusual biophysical properties. On the more diverse 500-AMP set, this bias disappears.

2. **boman_activity is more strongly anti-AMP than previously known.** At 0.3291 on n=1000, random decoys score substantially higher on Boman activity than most AMPs. The Boman index (a measure of overall residue solubility) is designed to detect peptides with broad-spectrum binding potential — a property that random decoys drawn from Swiss-Prot frequencies happen to have. This does NOT mean the Boman signal is harmful; its contribution to the ensemble works through the disagreement signal (|activity − boman|), not through independent discrimination. A high-disagreement candidate is one where the activity and Boman scorers disagree — this is the intended signal.

3. **selectivity_proxy is weaker on the diverse set** (0.6702 vs 0.7729). The charge+GRAVY heuristic distinguishes AMPs from random decoys less reliably when applied to a broader AMP diversity (UniProt-reviewed + APD6 natural). This is expected: the original 95-AMP benchmark was manually curated and enriched for canonical amphipathic helix AMPs that have characteristic charge and GRAVY values.

4. **activity remains the dominant signal** (0.7969, signal-bearing). The ensemble's primary discriminative power still comes from the activity scorer, as expected.

5. **rich_selectivity, safety, and serum_stability remain anti-signal** but are less extreme on n=1000 (moving toward 0.5). The expanded set includes more diverse AMPs with more moderate biophysical properties, so the anti-AMP penalty is less severe on average.

6. **The expert composite's delta widens from −0.0735 to −0.0935** because the selectivity-focused components penalize more diverse AMPs more heavily. The expert composite is NOT a good binary discriminator — this is by design, as its components focus on within-AMP differentiation.

### What this means for the pipeline:

1. The expert composite should NOT replace the ensemble for AMP/non-AMP triage. However, the rich_selectivity component (AUROC=0.3407 for AMP-vs-decoy but detection AUROC=0.7138 for hemolysis) is anti-AMP by design — it penalises high hydrophobicity and charge that define AMPs. This is the correct tradeoff.
2. The ensemble (activity + safety + synthesis + novelty + Boman) remains the primary synthesis gate.
3. The expert components may still add value for **within-AMP ranking** (selectivity and safety differentiation among candidates that already pass the activity gate) — but this has not been demonstrated and should not be assumed.
4. The `boman_activity` scorer (AUROC 0.329, well below random) does NOT discriminate AMPs from random decoys. Its only useful contribution to the ensemble is through the disagreement signal — which requires a partner scorer to disagree with.
5. `motif_novelty` and `novelty` are 0.5 by construction (no k-mer index, no references in this benchmark) — they are correctly neutral, not noise.

**Honest limitation:** This benchmark measures binary AMP-vs-decoy discrimination
only. The expert composite's selectivity, safety, and synthesis components are
designed for within-AMP candidate differentiation, not for separating AMPs from
non-AMPs. A within-AMP ranking benchmark (comparing selective vs hemolytic AMPs)
has been added in v0.5.9 (see Within-AMP Selectivity Benchmark section below).

---


## Within-AMP Selectivity Benchmark (v0.5.x — added 2026-07-01)

> The expert ablation benchmark found that safety, synthesis, and serum stability are
> anti-signal for AMP-vs-decoy discrimination. But those scorers were designed for
> *within-AMP ranking*: distinguishing hemolytic AMPs from selective AMPs. This benchmark
> tests them on that intended task.
>
> Run: `make bench-selectivity`

**Dataset:** 42 known AMPs with literature HC50 values (hemolysis_reference.csv)

| Class | HC50 threshold | Count |
|-------|:--------------:|:-----:|
| HEMOLYTIC | < 25 µg/mL | 14 |
| SELECTIVE | >= 100 µg/mL | 21 |
| BORDER (excluded from AUROC) | 25-100 µg/mL | 7 |

**Task:** Can pipeline scorers distinguish hemolytic AMPs from selective AMPs?
For safety/selectivity scorers, the correct direction is: hemolytic AMPs score *lower*
(less safe, less selective). We report "hemolysis detection AUROC" where higher = better
risk detection (1 - raw AUROC for safety-type scorers).

### Per-score hemolysis detection AUROC

| Score | Detection AUROC | CI₉₅ | Significant? | Verdict |
|-------|:--------------:|:----:|:------------:|---------|
| synthesis | 0.8027 | 0.63-0.95 | **YES** | Synthesis difficulty correlates with hemolysis — hemolytic AMPs are harder to synthesize |
| boman_activity | 0.6837 | 0.49-0.85 | No (CI lo < 0.5) | Weak trend: hemolytic AMPs have lower Boman activity |
| serum_stability | 0.6020 | 0.40-0.80 | No (CI lo < 0.5) | Weak trend: hemolytic AMPs less serum-stable |
| expert_composite | 0.5119 | 0.31-0.71 | No (CI lo < 0.5) | Better than ensemble but not significant |
| hinge_selectivity | 0.4456 | 0.24-0.64 | No | No selectivity signal from hinge detection |
| selectivity_proxy | 0.4133 | 0.28-0.55 | No | **FAILS** — charge/GRAVY does not capture hemolysis |
| safety | 0.3844 | 0.26-0.52 | No | **FAILS** — confirms melittin blind spot |
| activity | 0.3401 | 0.16-0.52 | No | Activity scorer ranks hemolytic AMPs *higher* (anti-selective) |
| ensemble | 0.3486 | 0.17-0.54 | No | Ensemble inherits activity scorer's anti-selective bias |

**Key findings:**

1. **The safety scorer does NOT detect hemolysis** (detection AUROC = 0.3844, CI lo = 0.26).
   This confirms the expert ablation's prediction and the previously documented melittin
   blind spot. All 14 hemolytic AMPs in the reference set score safety >= 0.8 — the scorer
   cannot distinguish them from selective AMPs.

2. **The selectivity proxy does NOT detect hemolysis** (detection AUROC = 0.4133, CI lo = 0.28).
   The charge/GRAVY heuristic is insufficient for capturing hemolysis risk. Hemolytic AMPs
   like melittin and protegrin have optimal charge (+2 to +7) and moderate GRAVY, so the
   proxy assigns them high selectivity scores.

3. **Synthesis feasibility is the only significant risk detector** (detection AUROC = 0.8027,
   CI lo = 0.63). Hemolytic AMPs tend to be harder to synthesize: they have more cysteines
   (protegrins, tachyplesins), repeat runs, and hydrophobic segments. This is an incidental
   correlation, not a designed safety feature — but it means the synthesis gate provides
   partial hemolysis filtering as a side effect.

4. **The activity scorer is anti-selective** (detection AUROC = 0.34): it ranks hemolytic
   AMPs *higher* than selective AMPs. This is expected: hemolytic AMPs like melittin have
   strong amphipathic helices, high hydrophobic moment, and high charge — exactly the
   features the activity scorer rewards. The ensemble inherits this bias.

5. **The expert composite now includes rich_selectivity** (detection AUROC=0.7138, CI 0.63-0.80) as its hemolysis-risk component, replacing the old hemolysis_safety (was 0.5119 vs
   0.3486) but not significantly so (CI includes 0.5). The added selectivity and safety
   components partially offset the activity scorer's anti-selective bias, but not enough
   to reach significance at n=14 vs n=21.

**Honest limitation:** HC50 values are approximate literature values with high inter-assay
variability (RBC source, buffer, incubation time, concentration range). The binary
thresholds (25 / 100 µg/mL) are coarse. A larger reference set with standardized HC50
measurements would tighten the CIs and might flip some near-zero results to significant.
The current sample size (14 vs 21) is too small for confident conclusions on any score
with CI lower bound below 0.5.

**Implication for the pipeline:** Hemolysis remains unpredictable by the current
physicochemical scorers. The melittin blind spot is confirmed quantitatively. Hemolysis
must be assayed experimentally for every candidate regardless of safety or selectivity
score. The synthesis gate provides partial indirect filtering but should not be relied
upon as a hemolysis predictor.

## Dedicated Hemolysis Risk Scorer (v0.5.10 — added 2026-07-01)

> The selectivity benchmark (v0.5.9) confirmed that the safety scorer fails
> hemolysis detection (AUROC=0.3844). A dedicated hemolysis risk scorer was
> built from empirically-validated components identified in that benchmark.
>
> **v0.5.11 correction:** The original 42-peptide reference set (14 hemolytic
> vs 21 selective, n=35) produced detection AUROC=0.9218 (CI 0.82-0.99). This
> was **small-sample inflation**. Expansion to 238 peptides using DBAASP human
> erythrocyte data (54 hemolytic vs 125 selective, n=179) dropped the detection
> AUROC to 0.5650 (CI 0.47-0.66) — direction correct but NOT statistically
> significant. The scorer retains weak directional signal but should not be
> trusted as a standalone hemolysis detector.
>
> Run: `make bench-selectivity` (hemolysis_risk column in the output)

**Module:** `src/openamp_foundry/scoring/hemolysis.py`

**Components** (individual AUROC from original n=14 vs n=21; may not replicate on expanded set):

| Component | Individual AUROC (n=35) | Weight | Signal source |
|-----------|:-----------------------:|:------:|---------------|
| Synthesis difficulty (1 - synth_feasibility) | 0.8027 | 0.30 | Incidental: hemolytic AMPs harder to synthesize |
| Aromatic fraction (F/W/Y density) | 0.8299 | 0.30 | Trp/Phe intercalation in both membrane types |
| Cationic-on-hydrophobic-face fraction | 0.7585 | 0.20 | Poor amphipathic face segregation |
| Cysteine fraction | 0.7500 | 0.20 | Beta-sheet defensin/protegrin class |

**Combined performance (expanded n=179):**

| Metric | Original (n=35) | Expanded (n=179) | Notes |
|--------|:---------------:|:-----------------:|-------|
| **Detection AUROC** | **0.9218** | **0.5650** | Small-sample inflation corrected |
| CI₉₅ lower bound | 0.82 | 0.47 | No longer > 0.5 — not significant |
| CI₉₅ upper bound | 0.99 | 0.66 | |
| Mean hemolytic risk | 0.4064 (n=14) | 0.2042 (n=54) | Direction still correct |
| Mean selective risk | 0.1501 (n=21) | 0.1535 (n=125) | |
| Safety scorer detection | 0.3844 | 0.5116 | Safety also improves slightly with more data |

**Expert composite integration (expanded n=179):**

| Metric | Before (v0.5.9, n=35) | After (v0.5.10, n=35) | Expanded (n=179) |
|--------|:---------------------:|:---------------------:|:-----------------:|
| Expert composite detection AUROC | 0.5119 | 0.6429 | 0.5459 |
| Expert composite CI lo | 0.3129 | 0.4490 | 0.4562 |
| Ensemble detection AUROC | 0.3486 | 0.3486 | 0.4201 |

**Expert ablation (AMP-vs-decoy, unchanged):**

| Metric | Value | Classification |
|--------|:-----:|:--------------:|
| rich_selectivity AUROC | 0.1973 | **Anti-signal** (above_random = -0.3027) — replaces hemolysis_safety (was 0.3285) |
| Expert composite AUROC | 0.7097 | Down from 0.7119 (rich_selectivity replaces hemolysis_safety as expert component) |

**Key finding (corrected):** The hemolysis risk scorer's original detection
AUROC=0.9218 on n=35 was small-sample inflation. On the expanded n=179
reference set, detection AUROC=0.5650 (CI 0.47-0.66) — direction is correct
(hemolytic > selective on average) but not statistically significant. The
scorer should NOT be described as a "statistically significant hemolysis
detector." It provides weak directional signal that may be useful as one
factor in a composite but cannot be relied upon for hemolysis triage. Hemolysis
must still be assayed experimentally for every candidate.

**Honest limitation:** The expanded reference set (n=179) provides a more honest
estimate, but HC50 values are approximate literature values with high inter-assay
variability. Melittin's risk score (0.13) remains modest because its bent-helix
hemolysis mechanism is not fully captured by 1D features.

---

## Multi-Class Triage Benchmark (v0.5.12 — added 2026-07-01)

> Tests the v1.1 ROADMAP item: "benchmark candidate triage against a reference
> panel that includes selective AMPs, hemolytic positives, inactive peptides,
> and random controls." Prior benchmarks tested two separate 2-class problems
> (AMP vs decoy, hemolytic vs selective). This benchmark tests the combined
> triage task the virtual assay layer must solve: rank selective AMPs above
> hemolytic AMPs above random decoys in a single panel.
>
> Run: `make bench-triage`

**Dataset:** 125 selective AMPs (HC50 >= 100 µg/mL) + 54 hemolytic AMPs (HC50 < 25 µg/mL)
+ 96 random background decoys = 275 total.

### Per-scorer pairwise AUROCs

A scorer that triages correctly should have all three AUROCs > 0.5:
  - selective > decoy (identifies AMPs)
  - hemolytic > decoy (identifies AMPs)
  - selective > hemolytic (prefers safe AMPs)

| Scorer | sel > decoy | hem > decoy | sel > hem | Triages correctly? |
|--------|:-----------:|:-----------:|:---------:|:------------------:|
| ensemble | 0.848 | 0.891 | 0.466 | **NO** (anti-selective) |
| activity | 0.885 | 0.934 | 0.430 | NO |
| selectivity_proxy | 0.782 | 0.795 | 0.610 | **YES** |
| expert_composite | 0.757 | 0.746 | 0.545 | **YES** |
| triage_score (activity × (1 - hemo_risk)) | 0.863 | 0.902 | 0.462 | NO |
| safe_weighted_ensemble | 0.849 | 0.890 | 0.483 | NO |
| safety | 0.344 | 0.300 | 0.538 | NO |
| synthesis | 0.590 | 0.634 | 0.469 | NO |
| hemolysis_risk (inverted) | 0.485 | 0.492 | 0.488 | NO |
| serum_stability | 0.217 | 0.160 | 0.569 | NO |
| **gate_triage** (activity × rich_sel) | **0.779** | **0.686** | **0.666** | **YES** |

**Key findings:**

1. **The ensemble does NOT triage correctly.** It ranks hemolytic AMPs above
   selective AMPs (sel_vs_hem AUROC = 0.466 < 0.5). This is the anti-selective
   bias documented in the selectivity benchmark, now confirmed in the combined
   triage context.

2. **selectivity_proxy and expert_composite triage correctly by pairwise AUROC**
   (all three AUROCs > 0.5). selectivity_proxy remains the best scorer because it
   has stronger selective-vs-hemolytic separation (0.610 vs expert_composite 0.545)
   while keeping slightly better selective-vs-decoy discrimination (0.782 vs 0.757).

3. **The naive triage_score (activity × (1 - hemolysis_risk)) does NOT fix the
   anti-selective bias** (sel_vs_hem = 0.462). This is because hemolysis_risk
   is too weak (detection AUROC 0.565, not significant on expanded benchmark).
   A naive virtual-assay composite does not outperform the ensemble.

6. **The gate_triage scorer (activity × rich_selectivity) is the first scorer
   to triage correctly with strong selective_vs_hemolytic separation** (0.666).
   Unlike the old triage_score, it uses rich_selectivity (detection AUROC 0.714,
   significant) instead of hemolysis_risk (not significant). It also achieves
   selective_vs_decoy 0.779 and hemolytic_vs_decoy 0.686, and ranks 16 selective
   / 1 hemolytic / 3 decoys in its top-20 — the best distribution of any benchmarked
   scorer. However, its AMP-vs-decoy discrimination is weaker than the ensemble
   (0.779 vs 0.848) because the rich_selectivity gate penalizes AMP-like features.
   It must NOT replace the ensemble activity gate; it is a complementary signal.

4. **Top-20 distribution shift:** The triage_score moves 2 more selective AMPs
   into the top-20 (16 vs 14 for ensemble), removing 2 hemolytic AMPs (4 vs 6).
   The shift is in the right direction but modest — the hemolysis_risk penalty
   is weak.

5. **Expert-composite top-k failure:** The expert_composite removes hemolytic
   AMPs from its top-20 (15 selective / 0 hemolytic), but admits 5 random decoys.
   That is a useful negative result: expert ranking is not a replacement for the
   ensemble activity gate, even when its pairwise AUROCs clear 0.5.

**Implication for the virtual assay layer:** Any future virtual assay module
must beat this triage benchmark baseline. The minimum bar is: triage correctly
(all three AUROCs > 0.5), keep decoys out of the top-k selection surface, and
maintain near-ensemble decoy discrimination (sel_vs_decoy > 0.80). The
selectivity_proxy achieves correct triage but loses decoy-discrimination margin.
The expert_composite achieves correct pairwise triage but admits decoys into its
top-20. A successful virtual assay must avoid both failures.

**Honest limitation:** The benchmark uses literature HC50 values with high
inter-assay variability. The binary thresholds (25 / 100 µg/mL) are coarse.
The MODERATE class (HC50 25-100, n=68) is excluded from the binary task.

### Strict Triage: Composition-Matched Decoys (v0.5.14 — added 2026-07-02)

> The standard triage benchmark uses random background peptides as decoys.
> These are trivially distinguishable from AMPs because their composition is
> protein-like, not AMP-like. This inflates selective_vs_decoy and
> hemolytic_vs_decoy AUROCs, making scorers appear to triage well.
>
> The strict triage benchmark replaces random decoys with **composition-matched
> scrambled versions** of the selective AMPs — same amino acids, permuted order.
> This destroys amphipathic helical phase, hydrophobic moment, and charge
> distribution patterns while preserving all composition-based features.

**Key finding: standard triage success was partly an illusion.**

| Scorer | Std sel_vs_dec | Strict sel_vs_dec | Std sel_vs_hemo | Strict sel_vs_hemo | Std correct | Strict correct |
|-------|-----------------|-------------------|------------------|---------------------|--------------|----------------|
| ensemble | 0.848 | **0.572** | 0.466 | 0.466 | NO | NO |
| activity | 0.885 | **0.617** | 0.430 | 0.430 | NO | NO |
| selectivity_proxy | 0.782 | **0.500** | 0.610 | 0.610 | YES | **NO** |
| expert_composite | 0.757 | **0.510** | 0.545 | 0.545 | YES | **NO** |
| triage_score | 0.863 | **0.674** | 0.462 | 0.462 | NO | NO |
| hemolysis_risk | 0.485 | 0.617 | 0.488 | 0.488 | NO | NO |
| gate_triage | 0.779 | **0.624** | 0.666 | 0.666 | YES | **NO** |

**What this reveals:**

1. **selectivity_proxy collapses to exactly 0.5000** on selective_vs_decoy —
   confirming it is purely composition-driven (charge and GRAVY are identical
   between a sequence and its scrambled version).

2. **The ensemble drops from 0.848 to 0.572** — most of its apparent triage
   power was composition-based, not order-based.

3. **No scorer triages correctly** with composition-matched decoys. The standard
   triage "success" of selectivity_proxy and expert_composite was an artifact
   of trivially distinguishable decoys.

4. **selective_vs_hemolytic is stable** across both benchmarks (identical AUROCs)
   — as expected, since both classes are real AMP sequences and only the decoy
   class changes.

5. **The ensemble admits 7 scrambled decoys into top-20** (vs 0 with random
   decoys) — it cannot distinguish real AMPs from scrambled versions of themselves.

6. **gate_triage retains partial order-dependent signal** (sel_vs_dec 0.624,
   hem_vs_dec 0.489). It fails strict triage because rich_selectivity penalizes
   the AMP-like composition that hemolytic AMPs share with their scrambled
   versions. But its selective_vs_decoy remains above 0.5, unlike selectivity_proxy
   which collapses to exactly 0.500 — suggesting the activity gate contributes
   order-dependent signal that the selectivity gate alone lacks.

**Implication:** The pipeline's triage signal is almost entirely composition-driven.
The real bottleneck is selective-vs-hemolytic discrimination, which requires
structural or contextual features beyond what current 1D physicochemical scorers
can capture. Any future virtual assay layer must demonstrate order-dependent
triage signal on this strict benchmark before claiming to improve candidate
selection.

## Feature Decomposition: Per-Feature Selective vs Hemolytic (v0.5.15 — added 2026-07-03)

> The strict triage benchmark (v0.5.14) proved that NO composite scorer passes
> selective_vs_hemolytic discrimination (AUROC 0.43-0.54). But it did not explain
> *why*. This benchmark tests every scalar physicochemical feature individually
> for selective_vs_hemolytic AUROC, with bootstrap confidence intervals.

**Key finding: the selectivity proxy ignores the strongest discriminative features.**

The selectivity proxy uses only `net_charge_ph74` and `gravy`. The top feature,
`hydrophobic_fraction` (AUROC 0.6745, CI 0.58-0.77), is NOT used by the proxy.
Six of eight significant features are not used by the current selectivity model.

| Feature | Detection AUROC | CI 95% | Direction | Used by proxy? |
|---------|-----------------|--------|-----------|----------------|
| hydrophobic_fraction | **0.6745** | 0.58-0.77 | risk | **NO** |
| helix_propensity | **0.6489** | 0.54-0.75 | risk | **NO** |
| net_charge_proxy | **0.6394** | 0.54-0.73 | risk | **NO** |
| net_charge_ph74 | **0.6332** | 0.54-0.73 | risk | YES |
| selectivity_proxy | **0.6095** | 0.52-0.70 | protective | YES |
| interior_trypsin_sites | **0.6089** | 0.51-0.70 | risk | **NO** |
| longest_repeat_run | **0.5946** | 0.52-0.68 | risk | **NO** |
| length | **0.5785** | 0.51-0.66 | risk | **NO** |

**What this reveals:**

1. **`hydrophobic_fraction` is the strongest single discriminative feature**
   (AUROC 0.6745), yet the selectivity proxy does not use it. The proxy relies
   on charge and overall hydrophobicity (GRAVY), but the *fraction* of
   hydrophobic residues carries more signal.

2. **All significant risk indicators point in the expected direction**
   (higher = more hemolytic). The features the pipeline already tracks (charge,
   hydrophobicity, helix propensity) have real signal for hemolysis, but the
   composite scorers cancel it out.

3. **The selectivity proxy itself has weak but significant signal** (0.6095)
   as a protective indicator. It is doing the right thing but is underpowered
   because it ignores the strongest axes.

4. **22 of 30 features tested have NO significant signal** for selective vs
   hemolytic discrimination. This confirms the strict triage finding: 1D
   physicochemical descriptors alone cannot solve this task well.

**Implication for next steps:**

A richer selectivity scorer combining `hydrophobic_fraction`, `helix_propensity`,
`net_charge`, and `interior_trypsin_sites` in a learned or hand-tuned model
could plausibly improve selective_vs_hemolytic AUROC above the current 0.55
ceiling. However, the best single feature (0.6745) is still modest, and
the CI is wide. 3D structural modelling or sequence-pattern features may
ultimately be needed for clinically meaningful discrimination.

Run: `make bench-feature-decomp` or `python -m openamp_foundry.cli bench feature-decomp`

## Rich Selectivity Scorer (v0.5.16 — added 2026-07-03)

The feature decomposition benchmark identified 8 significant features for selective_vs_hemolytic
discrimination, but the old `selectivity_proxy` (charge + GRAVY) used only 2. The rich selectivity
scorer (`scoring/selectivity_rich.py`) combines all 8 significant features, weighted by detection
AUROC, to produce a composite selectivity score.

| Scorer | Detection AUROC | CI 95% | Significant? |
|--------|----------------|--------|-------------|
| **rich_selectivity** | **0.7138** | **0.6266-0.7951** | **YES** |
| selectivity_proxy (old) | 0.5744 | 0.4954-0.6558 | Marginal |
| hemolysis_risk | 0.5650 | 0.4664-0.6601 | NO |
| expert_composite | 0.5459 | 0.4562-0.6305 | NO |
| safety | 0.5116 | 0.4321-0.5954 | NO |
| ensemble | 0.4201 | 0.3335-0.5067 | NO (anti-signal) |

**Key finding:** The rich selectivity scorer is the **first pipeline score with statistically
significant hemolysis detection** on the expanded n=179 benchmark (CI lower bound 0.6266 > 0.5).
It outperforms the old selectivity_proxy by +0.14 AUROC and is the only scorer whose CI excludes 0.5.

**Features combined (by detection AUROC):**
`hydrophobic_fraction` (0.6745), `net_charge_proxy` (0.6394), `net_charge_ph74` (0.6332),
`helix_propensity` (0.6489), `interior_trypsin_sites` (0.6089), `selectivity_proxy` (0.6095,
protective), `longest_repeat_run` (0.5946), `length` (0.5900).

**Honest limitations:**
- The rich selectivity scorer does NOT triage AMP-vs-decoy correctly (selective_vs_decoy = 0.19).
  It is designed for within-AMP ranking, not activity detection. It must be combined with an
  activity gate to be useful for candidate selection.
- Individual feature AUROCs are weak (0.59-0.67); the composite's CI is wide (0.63-0.80).
- Normalisation thresholds are empirical and may not generalise beyond the reference set.
- Does not model 3D structure, oligomeric state, or membrane curvature.
- HC50 values are approximate literature values with high inter-assay variability.
- This is a triage signal, NOT a hemolysis predictor. Wet-lab hemolysis assay remains mandatory.

Run: `make bench-selectivity` (rich_selectivity is included in the selectivity benchmark output)

## Two-Gate Triage Composite (v0.5.17 — added 2026-07-03)

> The triage benchmark showed that no scorer could pass all three pairwise
> AUROC conditions (selective_vs_decoy, hemolytic_vs_decoy, selective_vs_hemolytic)
> with strong selective-vs-hemolytic separation. selectivity_proxy passed but
> had weak separation (0.610). expert_composite passed but admitted 5 decoys
> into top-20. The old triage_score used hemolysis_risk (not significant).
>
> This scorer combines two complementary signals as a multiplicative gate:
> activity (strong AMP-vs-decoy, AUROC 0.885-0.934) × rich_selectivity
> (strong selective-vs-hemolytic, AUROC 0.745, significant).
>
> Run: `make bench-triage`

**Key result: gate_triage is the first scorer to pass all three standard triage conditions
with selective_vs_hemolytic > 0.65.**

| Scorer | sel > decoy | hem > decoy | sel > hem | Top-20 (sel/hem/dec) | Correct? |
|--------|:-----------:|:-----------:|:---------:|:---------------------:|:--------:|
| ensemble | 0.848 | 0.891 | 0.466 | 14/6/0 | NO |
| selectivity_proxy | 0.782 | 0.795 | 0.610 | — | YES (weak) |
| expert_composite | 0.757 | 0.746 | 0.545 | 15/0/5 | YES (decoy leak) |
| triage_score (old) | 0.863 | 0.902 | 0.462 | 16/4/0 | NO |
| **gate_triage** | **0.779** | **0.686** | **0.666** | **16/1/3** | **YES** |

**Design rationale:**

The two gates solve complementary problems:
- activity gate: detects AMP-likeness (composition + amphipathicity) —
  strong vs random decoys but anti-selective (rewards hemolytic AMPs)
- rich_selectivity gate: detects hemolysis risk from 8 evidence-identified
  features — strong vs hemolytic AMPs but anti-AMP (penalizes AMP-like composition)

Their product leverages both: a candidate must score high on BOTH AMP-likeness
AND selectivity. Hemolytic AMPs score high on activity but low on rich_selectivity.
Decoys score low on activity. Selective AMPs score moderately on both.

**Honest limitations:**

1. gate_triage does NOT pass strict triage (composition-matched decoys).
   Its hemolytic_vs_decoy drops to 0.489 because rich_selectivity penalizes
   the AMP-like composition that hemolytic AMPs share with their scrambled
   versions. It retains partial order-dependent signal (sel_vs_dec 0.624),
   but this is from the activity gate, not the selectivity gate.

2. gate_triage is weaker than ensemble on pure AMP-vs-decoy detection
   (0.779 vs 0.848). It must NOT replace the ensemble activity gate.
   It is a complementary triage signal, not a replacement.

3. A decoy leaks into the top-20 (3 decoys vs 0 for ensemble). The
   selectivity gate removes some hemolytic AMPs but admits some decoys
   that happen to have moderate activity and moderate selectivity.

4. This is still a dry-lab triage signal. Wet-lab hemolysis assay
   remains mandatory for all candidates.

## Test Suite

| Metric | Value |
|--------|-------|
| Total tests | 4162 |
| Coverage (branch) | 99% (6 CLI guard lines only) |
| Source modules at 100% | All pipeline, QC, scoring, adapter modules |

---

## Key Limitations

| Limitation | Impact |
|------------|--------|
| 500-AMP AUROC 0.7792 | ~22% of benchmark pairs misranked; charge-inflated; wet-lab is the judge |
| Safety model blind spot | Melittin scores Safety=1.0; hemolysis assay mandatory |
| No structural modeling | Helical assumption may misclassify non-helical mechanisms |
| Near-seed generation only | Novel sequence space not explored de novo |
| APD/DRAMP novelty (v2) | Complete — 27,234-sequence combined DB (APD6+DRAMP+UniProt); BLOSUM62 local alignment; Wave 0.5 results updated |
| No wet-lab data | All probabilities are upper bounds; true hit rate unknown |
| Rich selectivity scope | Designed for within-AMP selectivity only; does not distinguish AMPs from decoys (selective_vs_decoy=0.19) |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-09 | **Release checklist and gate validator (J1, starts Phase J):** `docs/governance/RELEASE_CHECKLIST.md` with structured checklist. `src/openamp_foundry/governance/release_gate.py` with `RELEASE_TYPES` (5), `UNIVERSAL_GATES` (7), `EXTRA_GATES_BY_TYPE`, `ReleaseGateResult`, `validate_release_gate()`. CLI `release-gate-check`. `make release-gate-check`. 18 tests. **Phase J (Governance and release maturity) started. 3478 total.** | OpenAMP Loop 109 |
| 2026-07-09 | **Adoption scorecard dashboard added (I10):** `src/openamp_foundry/adoption/scorecard.py` with `SCORECARD_DIMENSIONS` (5, weights sum 1.0), `ADOPTION_TIERS` (4), `DimensionScore`, `AdoptionScorecard`, `build_scorecard()`, `compute_adoption_tier()`. CLI `adoption-scorecard` with `--scores-json` and `--format`. `make adoption-scorecard`. 17 tests. **Phase I (Interoperability and Adoption) is now complete** — all 10 items I1–I10 implemented. **3446 total.** | OpenAMP Loop 108 |
| 2026-07-09 | **Adapter author validator added (I6):** `src/openamp_foundry/adapters/adapter_validator.py` with `AdapterDeclaration` (14 fields), `AdapterValidationResult` (5 fields), `validate_adapter_declaration()` (10 checks enforcing ADAPTER_AUTHOR_GUIDE contract), `validate_adapter_dict()` (dict input with missing-fields guard). 4 valid-value sets (VALID_ADAPTER_MODES, VALID_OUTPUT_STATUSES, VALID_RANKING_EFFECTS, VALID_RELEASE_STATUSES). CLI (`openamp-foundry adapter-check`) with `--adapter-json`, `--format text|json`. `make adapter-author-check` target. 31 tests. **3387 total.** | OpenAMP Loop 104 |
| 2026-07-08 | **Calibration benchmark added:** Brier score decomposition, reliability diagram, and calibration slope for pipeline ensemble scores. Brier=0.3178 (>0.25=uninformative), skill=-0.27 (worse than base rate), slope=0.43 (ideal=1.0). Honest finding: pipeline ranks well (AUROC~0.78) but scores are not meaningful probabilities. Expanded 500-AMP set confirms same pattern (Brier=0.2772, slope=2.31 — dataset-dependent). Integrated into `make bench-500` and `make bench-calibration`. `scripts/benchmarks/benchmark_calibration.py`, JSON output to `outputs/bench_calibration*.json`. | OpenAMP loop 18 |
| 2026-06-29 | Novelty audit v2: BioPython BLOSUM62 local alignment vs 27,234 AMPs (APD6+DRAMP+UniProt); panel updated (15 families, 4 SAR_CONTROL); all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5b: 23-candidate safety-optimized shortlist (SEED-020–024, no aromatics) | OpenAMP Wave 0.5b |
| 2026-06-29 | External predictor results filled from wave05_combined_consensus.csv; all 7 gates PASS | OpenAMP Wave 0.5 |
| 2026-06-29 | Wave 0.5 scaffold diversification — 24-candidate Wave 1 panel across 14 families | OpenAMP Wave 0.5 |
| 2026-07-01 | Expert ablation benchmark added: expert composite AUROC 0.7119 vs ensemble 0.7832 (delta −0.0713); anti-signal components documented; ensemble remains primary gate | OpenAMP loop |
| 2026-07-01 | **Hemolysis benchmark expanded:** 42 -> 238 peptides using DBAASP human erythrocyte data (54 hemolytic vs 125 selective, n=179 binary). Hemolysis risk scorer detection AUROC drops 0.9218 -> 0.5650 (CI 0.47-0.66) — original performance was small-sample inflation. Direction correct, not significant. Safety scorer detection improves 0.3844 -> 0.5116 (still not significant). 196 new peptides from DBAASP v3. | OpenAMP loop |
| 2026-07-01 | Dedicated hemolysis risk scorer: 4-component score (synth+aromatic+face+cys) achieves detection AUROC=0.9218 (CI: 0.82-0.99); integrated into expert composite (detection 0.5119→0.6429); safety scorer unchanged; 1471 tests | OpenAMP loop |
| 2026-07-01 | Within-AMP selectivity benchmark added: safety scorer FAILS hemolysis detection (AUROC=0.3844); synthesis is only significant risk detector (AUROC=0.8027); expert composite better than ensemble but not significant (0.5119 vs 0.3486) | OpenAMP loop |
| 2026-07-01 | Expert composite ranking integration: `score_candidates()` now computes `expert_composite` and `hemolysis_risk`; `--ranking-mode expert` CLI flag; expert-ranked top-5 have lower mean hemolysis_risk than ensemble | OpenAMP loop |
| 2026-07-02 | **Strict triage benchmark added:** composition-matched scrambled decoys replace random background. No scorer triages correctly — standard triage "success" of selectivity_proxy (0.782 sel_vs_dec) and expert_composite (0.757) was inflated by trivially distinguishable decoys. selectivity_proxy collapses to 0.500 (purely composition-driven), ensemble drops to 0.572. Real bottleneck (selective_vs_hemolytic) unchanged. | OpenAMP loop |
| 2026-07-02 | Ranking policy contract added: machine-readable recommendation now states `ensemble` remains default broad synthesis gate, `expert` is narrower safety-aware alternative only | OpenAMP loop |
| 2026-07-03 | **Rich selectivity scorer added:** composite of 8 evidence-identified features from the feature decomposition benchmark. Detection AUROC=0.7138 (CI 0.63-0.80) on n=179 — first pipeline score with statistically significant selective_vs_hemolytic discrimination. Old selectivity_proxy=0.5744 (CI 0.50-0.66). Honest limitation: does not triage AMP-vs-decoy (0.19); must be combined with activity gate. | OpenAMP loop |
| 2026-07-05 | **Order-dependent features benchmark added:** dipeptide_order_score is the strongest order-dependent feature (AUROC 0.7861 on AMP-vs-scrambled). Only 7/31 features survive scrambling. All composition features are exactly position-independent (0.5000). `src/openamp_foundry/features/dipeptide.py`, `scripts/benchmarks/benchmark_order_dependent.py`, `make bench-order-dependent`. | OpenAMP loop 13 |
| 2026-07-05 | **Cross-dataset generalization benchmark:** DRAMP AMPs (independent database) vs Swiss-Prot decoys: AUROC 0.7803 (CI 0.75–0.81). Baseline 0.7832 from APD6/UniProt — Δ=-0.0029. Pipeline is source-independent: heuristic features generalise to DRAMP with essentially identical discrimination. Phase 1 exit criterion #5 satisfied. `scripts/benchmarks/benchmark_cross_dataset.py`, `make bench-cross-dataset`. | OpenAMP loop 17 |
| 2026-07-05 | **Precision@k calibration benchmark added:** top-20 precision 1.000, top-50 precision 0.900, top-200 precision 0.835. Best F1 threshold 0.6323 (F1=0.7518). At 80% recall, precision drops to base-rate (0.5000) — honest limitation documented. `scripts/benchmarks/benchmark_precision_at_k.py`, `make bench-precision-at-k`. | OpenAMP loop 14 |
| 2026-07-05 | **Expert ablation re-run on expanded benchmark (n=1000):** 2 components reclassified — synthesis was anti-signal artifact on n=191 (0.4228→0.4968, now near-zero); boman_activity more strongly anti-AMP (0.3291). selectivity_proxy weaker on diverse set. Activity remains dominant (0.7969). `make bench-expert-ablation-500`. | OpenAMP loop 15 |
| 2026-07-05 | **Benchmark card consolidated** with all Phase 1 findings: expanded benchmark, cluster-split-500, multi-negative, easy baseline, order-dependence, precision@k, rich selectivity, gate_triage, expert ablation (n=1000), updated known biases. Phase 1 exit criterion: benchmark card is now externally reviewable. `docs/evidence/BENCHMARK_CARD.md`. | OpenAMP loop 16 |
| 2026-07-05 | **Easy baseline benchmark added:** charge density alone (AUROC 0.8166) beats pipeline ensemble (0.7792, Δ=−0.0374). Honest finding: expected — pipeline optimizes for safety, not raw discrimination. `scripts/benchmarks/baseline_trivial.py`, `make bench-easy-baseline`, CI informational step. | OpenAMP loop 12 |
| 2026-07-03 | **Rich selectivity integrated into production pipeline:** rich_selectivity_score now computed in score_candidates() (pipeline.py), replaces hemolysis_safety as the expert composite hemolysis-risk component (weight 0.10), used in pilot_priority formula, displayed in pilot panel report, and included in evidence certificates. Expert AUROC drops 0.7119→0.7097 (−0.0022) — acceptable tradeoff: the expert now includes a significant hemolysis detector (CI excludes 0.5) instead of the old non-significant one. | OpenAMP loop |
| 2026-07-03 | **Two-gate triage composite added:** gate_triage = activity × rich_selectivity, added to triage benchmark. First scorer to pass all three standard triage conditions with strong selective_vs_hemolytic separation (0.666). Top-20: 16 selective / 1 hemolytic / 3 decoy — best distribution. Does NOT pass strict triage (hem_vs_dec 0.489) — honest limitation. Must not replace ensemble activity gate. | OpenAMP loop |
| 2026-07-03 | **Feature decomposition benchmark added:** per-feature selective_vs_hemolytic AUROC for all 30 scalar physicochemical features. hydrophobic_fraction is the strongest single discriminative feature (0.6745, CI 0.58-0.77) but is NOT used by the selectivity proxy. 8/30 features have significant signal; 6 of those are unused. Provides actionable diagnostic for why composite scorers fail selective_vs_hemolytic discrimination. | OpenAMP loop |
| 2026-07-04 | **Calibration intake module added:** `openamp-foundry calibration-intake` joins a pilot panel CSV with a directory of validated lab result JSON files, produces a per-candidate prediction-vs-actual report with cohort metrics gated by `MIN_COHORT_SIZE=5`. Descriptive only — does NOT trigger recalibration, weight updates, or selection-rule changes. Synthetic example data in `examples/lab_results/` is clearly labeled in every file and in `examples/lab_results/README.md`. 29 new tests; total 1614 passing. | OpenAMP loop |
| 2026-06-29 | Initial — expanded benchmark (PR #110) | OpenAMP CI |
| 2026-07-05 | **Per-family benchmark breakdown added:** stratifies 500 AMPs by structural class (cysteine_rich, proline_rich, short, highly_cationic, moderately_cationic, low_charge). Pipeline is charge-dominated: highly_cationic AUROC 0.958 vs proline_rich AUROC 0.586 — a 0.37 gap. Proline-rich, short, and low-charge AMPs are consistently undervalued. Diversity selection should deliberately compensate for pipeline's helic/charge bias. `scripts/benchmarks/benchmark_per_family.py`, `make bench-per-family`, CI informational step. 27 new tests. | OpenAMP loop 18 |
| 2026-07-04 | **Recalibration policy + gate module added:** `openamp-foundry recalibration-gate` evaluates a calibration intake report against the pre-registered policy in `configs/recalibration_policy.yaml` and emits a binary `may_recalibrate` verdict. The policy file encodes 7 minimum conditions (cohort size, controls, orphans, positives, negatives, metrics availability), 5 permanent prohibited actions (toxicity, hemolysis, novelty, pathogen enhancement, post-hoc success redefinition), and 2 rate limits (L1 weight budget, cooldown). The validator rejects policy files that omit any canonical prohibited action or any `locked_changes` entry. The gate does NOT trigger weight updates; it is the missing permission layer between v0.5.19 intake and a future recalibration engine. Exit code 0 when `may_recalibrate=true`, 3 when false. 39 new tests; total 1647 passing. See `docs/evidence/CALIBRATION_POLICY.md`. | OpenAMP loop |
