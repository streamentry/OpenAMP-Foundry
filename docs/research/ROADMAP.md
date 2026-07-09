# Roadmap

### v0.8.5
- Phase L L2: reproducibility manifest schema — captures exact software versions, data checksums, and random seeds for a pipeline run. ReproducibilityManifestEntry dataclass, validate_reproducibility_manifest(), CLI reproducibility-manifest-check.

### v0.8.4
- Phase L L1: preprint evidence bundle schema — ties K-phase artifacts into a submission-ready record for scientific preprints. PreprintBundleEntry dataclass, validate_preprint_bundle(), CLI preprint-bundle-check.

### v0.8.3
- Phase K K5: uncertainty quantification report schema — validates prediction intervals, confidence levels, and calibration source for dry-lab candidate recommendations. UncertaintyReportEntry dataclass, validate_uncertainty_report(), CLI uncertainty-report-check.

### v0.8.2
- Phase K K4: post-experiment calibration intake schema — captures structured comparison of pipeline dry-lab prediction against actual experimental outcome. CalibrationIntakeEntry dataclass (dry_lab_only=False enforced), validate_calibration_intake(), CLI calibration-intake-check.

## v0.8.1 — Loop 121: Phase K K3 — Pilot Package Completeness Checker

`docs/evidence/PILOT_PACKAGE_GUIDE.md` with purpose, required field table (11
fields), mandatory artifact types table (3 types: selection_rationale,
batch_priority, evidence_certificate), valid artifact types (8 types), warnings,
validation workflow, honest-use boundary.

`src/openamp_foundry/evidence/pilot_package.py` with `PilotPackageEntry`
dataclass (11 fields, dry_lab_only=True enforced), `PilotPackageResult`
dataclass (5 fields, dry_lab_only=True), `MINIMUM_REQUIRED_ARTIFACTS` (3),
`READINESS_SCORE_THRESHOLD` (0.80), `MANDATORY_ARTIFACT_TYPES` (3:
batch_priority, evidence_certificate, selection_rationale),
`VALID_ARTIFACT_TYPES` (8 types), `validate_pilot_package()` (11 checks, 3
warning conditions: missing artifacts, low completeness score, same
reviewer/approver), `validate_pilot_package_dict()` (10 required fields guard).

CLI: `openamp-foundry pilot-package-check`. `make pilot-package-check` target.
**v0.8.1 milestone** — every pilot submission is machine-validated for
completeness before external lab submission.

## v0.8.0 — Loop 120: Phase K K2 — Batch Experiment Priority Ranker ✓ (2026-07-09)

`docs/evidence/BATCH_PRIORITY_GUIDE.md` with field table and validation workflow
for batch synthesis wave priority entries.

`src/openamp_foundry/evidence/batch_priority.py` with `BatchPriorityEntry`
dataclass (12 fields, dry_lab_only=True enforced), `BatchPriorityResult`
dataclass (6 fields), `VALID_SYNTHESIS_COMPLEXITIES` (3: high/low/medium),
`VALID_NOVELTY_TIERS` (3: high/low/medium), `VALID_EVIDENCE_LEVELS` (1–6),
`validate_batch_priority()` (11 checks, 3 warning conditions: low evidence,
top-rank+high-complexity, low score), `validate_batch_priority_dict()`
(10 required fields guard).
CLI: `openamp-foundry batch-priority-check`. `make batch-priority-check` target.
**v0.8.0 milestone** — synthesis wave ranking is now machine-validated with
explicit evidence level and complexity signals.

## v0.7.9 — Loop 119: Phase K K1 — Selection Rationale Schema ✓ (2026-07-09)

`docs/evidence/SELECTION_RATIONALE_GUIDE.md` documenting what selection rationale
entries must contain, why they are needed for external review, and how evidence
levels map to `PROOF_LADDER.md`.

`src/openamp_foundry/evidence/selection_rationale.py` with `SelectionRationaleEntry`
dataclass (11 fields, dry_lab_only=True enforced), `SelectionRationaleResult`
dataclass (5 fields), `VALID_EVIDENCE_LEVELS` (1–6), `MINIMUM_SAFETY_FLAGS` (1),
`validate_selection_rationale()` (11 checks, 1 warning condition for low evidence
levels), `validate_selection_rationale_dict()` (10 required fields guard).
CLI: `openamp-foundry selection-rationale-check`. `make selection-rationale-check` target.
**Phase K milestone: v0.7.9** — every candidate selection now requires a
machine-validated rationale with evidence level and baseline comparison.

## v0.7.8 — Loop 118: Phase J J10 — Annual Safety and Benchmark Review Checklist ✓ (2026-07-09)

`docs/governance/ANNUAL_REVIEW_CHECKLIST.md` with 5-section structured annual
review checklist (safety_policy: 6 checks covering dual-use safeguards,
dry_lab_only enforcement, toxicity/hemolysis filter thresholds, evidence_level
guard; benchmark_thresholds: 6 checks covering threshold loosening guard,
easy-baseline requirement, selectivity benchmarks, deprecation check;
calibration_status: 4 checks covering recalibration gate, decision checklist,
rollback plan; governance_decisions: 4 checks covering active decisions,
COI disclosures, maintainer rotation; data_governance: 3 checks covering
proprietary data license flags, external source documentation).

`src/openamp_foundry/governance/annual_review.py` with `AnnualReviewEntry`
dataclass (10 fields: review_id, year, section, reviewer, finding_count,
action_items_count, status, notes, completion_date, dry_lab_only),
`AnnualReviewResult` dataclass (6 fields, dry_lab_only=True),
`VALID_REVIEW_SECTIONS` (5: benchmark_thresholds, calibration_status,
data_governance, governance_decisions, safety_policy),
`VALID_ENTRY_STATUSES` (5: completed, deferred, in_progress, not_applicable,
pending), `validate_annual_review_entry()` (9 checks: ANN- prefix, 4-digit year,
valid section, non-empty reviewer, non-negative finding_count,
non-negative action_items_count, valid status, completed requires YYYY-MM-DD
completion_date, dry_lab_only must be True; completed+no-notes warns, deferred
warns, findings+no-action-items warns), `validate_annual_review_dict()` (7
required fields guard). CLI (`openamp-foundry annual-review-check`) with
`--entry-json`, `--format text|json`. `make annual-review-check` target.
Long-term trust: annual review entries are now machine-validated.

## v0.7.7 — Loop 117: Phase J J9 — External Advisory Review Process ✓ (2026-07-09)

`docs/governance/EXTERNAL_ADVISORY_REVIEW_PROCESS.md` with reviewer eligibility
criteria (4 requirements), review scope table (5 review types with minimum
reviewer counts: candidate_review and safety_policy_review require ≥2 reviewers,
others ≥1), 5-step process (prepare packet, assign+disclose COI, receive+log,
respond to findings by severity, close and record), finding severity handling
(critical halts release, major resolves before release, minor defers, informational
notes), limitations section.

`src/openamp_foundry/governance/advisory_review.py` with `AdvisoryReview` dataclass
(11 fields: review_id, review_type, artifact_id, reviewer_handle, assigned_date,
deadline_date, status, finding_severity, finding_summary, resolved, dry_lab_only),
`AdvisoryReviewResult` dataclass (5 fields, dry_lab_only=True),
`VALID_REVIEW_TYPES` (5: benchmark_audit, candidate_review, evidence_review,
governance_review, safety_policy_review), `VALID_REVIEW_STATUSES` (5: assigned,
completed, deferred, in_progress, pending), `VALID_FINDING_SEVERITIES` (4:
critical, informational, major, minor), `MINIMUM_REVIEWER_COUNTS` (5 entries),
`validate_advisory_review()` (9 checks + 3 warning conditions),
`validate_advisory_review_dict()` (7 required fields guard).

CLI (`openamp-foundry advisory-review-check`) with `--review-json` (required),
`--format text|json`. Handler `_run_advisory_review_check` in reports.py.

`make advisory-review-check` target. 29 tests. **3653 total.**

Credibility: external advisory reviews now have a validated structure, documented
eligibility criteria, and a clear process from assignment to closure.

## v0.7.6 — Loop 116: Phase J J8 — Roadmap-to-Issue Sync Checklist ✓ (2026-07-09)

`docs/governance/ROADMAP_ISSUE_SYNC_CHECKLIST.md` with 5-section checklist:
roadmap items → issues (5 checks), issues → roadmap (3 checks), completed
items (4 checks), priority alignment (3 checks), version consistency (3 checks).

`src/openamp_foundry/governance/roadmap_sync.py` with `RoadmapSyncEntry`
dataclass (10 fields: item_id, phase, description, priority, sync_status,
issue_number, pr_number, completed, completion_date, dry_lab_only),
`RoadmapSyncResult` dataclass (5 fields, dry_lab_only=True),
`VALID_SYNC_STATUSES` (5: synced, missing_issue, orphaned_issue, stale,
completed), `VALID_PRIORITY_LEVELS` (4: A, B, C, D), `VALID_PHASES` (7:
E, F, G, H, I, J, K), `validate_roadmap_sync_entry()` (8 checks + 4 warning
conditions), `validate_roadmap_sync_dict()` (5 required fields guard).

CLI (`openamp-foundry roadmap-sync-check`) with `--entry-json` (required),
`--format text|json`. Handler `_run_roadmap_sync_check` in reports.py.

`make roadmap-sync-check` target. 24 tests. **3624 total.**

Keeps strategy actionable: roadmap sync entries are machine-validated,
priority A items without issues get an immediate warning, and stale or
orphaned items are flagged for cleanup.

## v0.7.5 — Loop 115: Phase J J7 — Citation and Reuse Guide ✓ (2026-07-09)

`docs/governance/CITATION_AND_REUSE_GUIDE.md` with citation formats (inline,
BibTeX), reuse table (4 artifact types with open/attribution_required/
contact_required/restricted classes), attribution requirements, honest-use
boundary (dry-lab outputs only), contact information, linked policies.

`src/openamp_foundry/governance/citation_policy.py` with
`CitationEntry` dataclass (11 fields: artifact_id, citation_type, title,
version, authors, year, license_identifier, reuse_class, url, bibtex_key,
dry_lab_only), `CitationValidationResult` dataclass (6 fields,
dry_lab_only=True), `VALID_CITATION_TYPES` (4: dataset, method, schema,
software), `VALID_REUSE_CLASSES` (4: attribution_required, contact_required,
open, restricted), `VALID_LICENSE_IDENTIFIERS` (5: Apache-2.0, CC-BY-4.0,
CC-BY-NC-4.0, MIT, Proprietary), `validate_citation_entry()` (9 checks
+ 3 warning conditions), `validate_citation_dict()` (8 required fields guard).

CLI (`openamp-foundry citation-check`) with `--citation-json` (required),
`--format text|json`. Handler `_run_citation_check` in reports.py.

`make citation-check` target. 24 tests. **3599 total.**

Ecosystem clarity: citation entries are machine-validated, reuse classes are
explicit, and the honest-use boundary is documented in the guide.

## v0.7.4 — Loop 114: Phase J J6 — Security Policy ✓ (2026-07-09)

`docs/governance/SECURITY_POLICY.md` with private vulnerability reporting
process, response timeline (48h acknowledgment, 30d patch), severity
classification (critical/high/medium/low), 5 vulnerability categories
(code_vulnerability, secret_leakage, dependency_vulnerability,
safety_guardrail_bypass, dual_use_risk), out-of-scope items, disclosure
process.

`src/openamp_foundry/governance/security_policy.py` with
`VulnerabilityReport` dataclass (9 fields: report_id, severity, category,
description, affected_version, reporter_handle, report_date, status,
dry_lab_only), `SecurityReportValidationResult` dataclass (6 fields:
report_id, severity, passed, errors, warnings, dry_lab_only=True),
`VALID_SEVERITY_LEVELS` (4: critical, high, medium, low),
`VALID_VULNERABILITY_CATEGORIES` (5: code_vulnerability, secret_leakage,
dependency_vulnerability, safety_guardrail_bypass, dual_use_risk),
`VALID_REPORT_STATUSES` (6: received, acknowledged, under_review, patched,
disclosed, not_applicable), `validate_vulnerability_report()` (9 checks:
report_id SEC- prefix, valid severity, valid category, non-empty
description, non-empty affected_version, non-empty reporter_handle,
YYYY-MM-DD date, valid status, dry_lab_only must be True; critical+received
warning, safety_guardrail_bypass warning), `validate_report_dict()` (dict
input with 8 required fields guard, missing fields returns passed=False
early).

CLI (`openamp-foundry security-report-check`) with `--report-json`
(required), `--format text|json`. Handler `_run_security_report_check` in
reports.py.

`make security-report-check` target. 18 tests. **3575 total.**

Private vulnerability reporting now has a validated structure and
documented process — security reporters have a clear channel and the
project has a documented response process.

Changes:
- `docs/governance/SECURITY_POLICY.md` (J6) — Private vulnerability
  reporting process with response timeline, severity classification
  (critical/high/medium/low), 5 vulnerability categories, out-of-scope
  items, disclosure process.
- `src/openamp_foundry/governance/security_policy.py` (J6) — Core module
  with `VulnerabilityReport` (9 fields), `SecurityReportValidationResult`
  (6 fields, dry_lab_only=True), `VALID_SEVERITY_LEVELS` (4),
  `VALID_VULNERABILITY_CATEGORIES` (5), `VALID_REPORT_STATUSES` (6),
  `validate_vulnerability_report()` (9 checks with critical+received
  warning and safety_guardrail_bypass warning),
  `validate_report_dict()` (dict input with 8 required fields guard).
- `tests/governance/test_security_policy.py` (J6) — 18 tests covering:
  valid report passes, report_id not SEC- fails, empty report_id fails,
  invalid severity fails, invalid category fails, empty description fails,
  empty affected_version fails, empty reporter_handle fails, invalid date
  fails, invalid status fails, dry_lab_only=False fails, critical+received
  warns, safety_guardrail_bypass warns, validate_report_dict passes,
  validate_report_dict missing fields fails, all results dry_lab_only=True,
  VALID_SEVERITY_LEVELS has 4, VALID_VULNERABILITY_CATEGORIES has 5.
- `src/openamp_foundry/cli/main.py` (J6) — Registered `security-report-check`
  subcommand with `--report-json`, `--format` flags. Added import and
  dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J6) — Added
  `_run_security_report_check()` CLI handler with JSON parsing,
  `validate_report_dict()` call, text and JSON output, exit code 3 on
  validation failure.
- `Makefile` (J6) — Added `security-report-check` target with demo
  invocation using dependency_vulnerability severity medium. Added to
  `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J6) — v0.7.4 J6 changelog. Pipeline
  version: v0.7.4. Test count: 3575.
- `tests/test_test_count_regression.py` — baseline updated to 3575.

Honest boundaries:
- Security policy validation checks structural and policy requirements
  only. It does not verify that the vulnerability actually exists, that
  the reporter has accurately described it, or that the severity
  assessment is correct.
- `dry_lab_only: true` is a const field on all dataclasses — security
  reports are governance artifacts, not biological findings.
- The validator checks that the report_date is in YYYY-MM-DD format but
  does not verify that the date is reasonable (e.g. not in the future).
- Critical severity with received status produces a warning but does not
  fail validation — the maintainer may have good reasons for delayed
  acknowledgment, but the warning ensures it is visible.
- Safety guardrail bypass reports always produce a warning to ensure
  immediate maintainer attention, regardless of other validation status.
- The security policy defines a process and timeline but does not
  guarantee that maintainers will actually meet those timelines.
- The policy covers code vulnerabilities, secret leakage, dependency
  vulnerabilities, safety guardrail bypass, and dual-use risks. It does
  not cover theoretical vulnerabilities without a reproducible PoC,
  social engineering, or upstream dependency issues without fixes.

## v0.7.3 — Loop 113: Phase J J5 — Maintainer Rotation Plan ✓ (2026-07-09)

`docs/governance/MAINTAINER_ROTATION_PLAN.md` with maintainer rotation and
bus-factor plan (purpose, current maintainers table with 3 entries covering
primary_maintainer, secondary_maintainer, external_advisor, role definitions
for 4 roles, bus-factor assessment with target >=2 per critical function,
rotation schedule every 6 months, onboarding and offboarding checklists,
linked policies).

`src/openamp_foundry/governance/maintainer_rotation.py` with `MaintainerEntry`
dataclass (6 fields: github_handle, role, backup_handle, responsibilities,
status, dry_lab_only), `RotationPlanValidationResult` dataclass (7 fields:
passed, errors, warnings, maintainer_count, critical_role_coverage,
bus_factor_sufficient, dry_lab_only), `VALID_ROLES` (4: primary_maintainer,
secondary_maintainer, external_advisor, contributor), `CRITICAL_ROLES` (2:
primary_maintainer, secondary_maintainer), `VALID_STATUSES` (4: active,
on_leave, emeritus, departing), `validate_maintainer_entry()` (6 checks:
non-empty github_handle, valid role, critical role requires backup_handle,
non-empty responsibilities, valid status, dry_lab_only=True),
`validate_rotation_plan()` (aggregates entry validation + bus-factor
coverage: missing critical role is error, single coverage is warning),
`validate_rotation_plan_dict()` (dict input with missing-fields guard).

CLI (`openamp-foundry rotation-plan-check`) with `--plan-json` (required),
`--format text|json`. Handler `_run_rotation_plan_check` in reports.py.

`make rotation-plan-check` target. 21 tests. **3557 total.**

Maintainer rotation and bus-factor coverage is now machine-validated — the
project can detect when critical roles lack backups.

Changes:
- `docs/governance/MAINTAINER_ROTATION_PLAN.md` (J5) — Maintainer rotation
  and bus-factor plan with purpose, current maintainers table (3 entries),
  role definitions (4 roles), bus-factor assessment, rotation schedule
  (every 6 months), onboarding checklist (11 items), offboarding checklist
  (7 items), linked policies.
- `src/openamp_foundry/governance/maintainer_rotation.py` (J5) — Core module
  with `MaintainerEntry` (6 fields), `RotationPlanValidationResult` (7 fields,
  dry_lab_only=True), `VALID_ROLES` (4), `CRITICAL_ROLES` (2),
  `VALID_STATUSES` (4), `validate_maintainer_entry()` (6 checks),
  `validate_rotation_plan()` (bus-factor coverage: missing critical role is
  error, single coverage is warning), `validate_rotation_plan_dict()` (dict
  input with missing-fields guard).
- `tests/governance/test_maintainer_rotation.py` (J5) — 21 tests covering:
  valid plan passes, empty entries fails, empty github_handle fails, invalid
  role fails, critical role without backup fails, empty responsibilities fails,
  invalid status fails, dry_lab_only=False fails, no active primary maintainer
  fails, no active secondary maintainer fails, single primary maintainer warns,
  single secondary maintainer warns, validate_rotation_plan_dict missing
  'entries' key fails, validate_rotation_plan_dict valid dict passes,
  validate_rotation_plan_dict missing entry fields fails, all results
  dry_lab_only=True, VALID_ROLES has 4 entries, CRITICAL_ROLES has 2 entries,
  contributor role valid, on_leave status valid, emeritus status valid.
- `src/openamp_foundry/cli/main.py` (J5) — Registered `rotation-plan-check`
  subcommand with `--plan-json`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J5) — Added
  `_run_rotation_plan_check()` CLI handler with JSON parsing,
  `validate_rotation_plan_dict()` call, text and JSON output, exit code 3 on
  validation failure.
- `Makefile` (J5) — Added `rotation-plan-check` target with demo invocation
  using maintainer and backup-maintainer. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J5) — v0.7.3 J5 changelog. Pipeline
  version: v0.7.3. Test count: 3557.
- `tests/test_test_count_regression.py` — baseline updated to 3557.

Honest boundaries:
- Maintainer rotation validation checks structural and policy requirements only.
  It does not verify that the listed maintainers actually have the skills or
  availability to perform their roles.
- `dry_lab_only: true` is a const field on all dataclasses — rotation plan
  validation is a governance artifact, not a legal determination.
- Bus-factor assessment is a project-durability estimate, not a security
  guarantee. A bus-factor of 2 means two named people can cover a function,
  but both might be unavailable simultaneously.
- The validator cannot detect unlisted critical dependencies (e.g., institutional
  knowledge, CI secrets, domain expertise held by only one person).
- The rotation schedule is a policy declaration; this validator does not track
  whether rotations actually occurred.
- Onboarding and offboarding checklists are documentation and guidance — they
  do not replace judgment about whether a new maintainer is ready.

## v0.7.2 — Loop 112: Phase J J4 — COI Disclosure Template ✓ (2026-07-09)

`docs/governance/COI_DISCLOSURE_TEMPLATE.md` with structured COI disclosure
template (purpose, fill-in-the-blank format with 10 fields: Disclosure ID
COI-YYYY-NNN, disclosure type reviewer|contributor|maintainer|external_advisor,
subject GitHub handle, related artifact or PR, relationship type
financial|institutional|competitive|personal|none, description (required unless
none), date YYYY-MM-DD, recusal_required true|false, reviewer GitHub handle,
review_status pending|acknowledged|resolved).

`src/openamp_foundry/governance/coi_disclosure.py` with `COIDisclosure`
dataclass (10 fields), `COIValidationResult` dataclass (6 fields,
dry_lab_only=True), `VALID_DISCLOSURE_TYPES` (4: contributor, external_advisor,
maintainer, reviewer), `VALID_RELATIONSHIP_TYPES` (5: competitive, financial,
institutional, none, personal), `VALID_REVIEW_STATUSES` (3: acknowledged,
pending, resolved), `validate_coi_disclosure()` (10 checks: disclosure_id
starts with COI-, valid disclosure_type, non-empty subject/related_artifact,
valid relationship_type, description required unless none, YYYY-MM-DD date,
non-empty reviewer, valid review_status, dry_lab_only must be True; financial
without recusal yields warning not error), `validate_coi_dict()` (dict input
with 10 required fields guard).

CLI (`openamp-foundry coi-check`) with `--disclosure-json` (required),
`--format text|json`. Handler `_run_coi_check` in reports.py.

`make coi-check` target. 20 tests. **3536 total.**

COI disclosures now have a validated structure that builds institutional trust.

Changes:
- `docs/governance/COI_DISCLOSURE_TEMPLATE.md` (J4) — Structured COI disclosure
  template with purpose, template (10 fields), when to disclose (financial,
  institutional, competitive, personal), process (5 steps with escalation).
- `src/openamp_foundry/governance/coi_disclosure.py` (J4) — Core module with
  `COIDisclosure` (10 fields), `COIValidationResult` (6 fields,
  dry_lab_only=True), `VALID_DISCLOSURE_TYPES` (4), `VALID_RELATIONSHIP_TYPES`
  (5), `VALID_REVIEW_STATUSES` (3), `validate_coi_disclosure()` (10 checks),
  `validate_coi_dict()` (dict input with 10 required fields guard).
- `tests/governance/test_coi_disclosure.py` (J4) — 20 tests covering: valid
  reviewer none relationship passes, valid contributor financial passes,
  disclosure_id not starting with COI- fails, empty disclosure_id fails, invalid
  disclosure_type fails, empty subject fails, empty related_artifact fails,
  invalid relationship_type fails, relationship not none with empty description
  fails, relationship none with empty description passes, invalid date format
  fails, empty reviewer fails, invalid review_status fails, dry_lab_only=False
  fails, financial without recusal warns, validate_coi_dict passes, validate_
  coi_dict with missing fields fails, all results dry_lab_only=True,
  VALID_DISCLOSURE_TYPES has 4, VALID_RELATIONSHIP_TYPES has 5.
- `src/openamp_foundry/cli/main.py` (J4) — Registered `coi-check` subcommand
  with `--disclosure-json`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J4) — Added `_run_coi_check()`
  CLI handler with JSON parsing, validate_coi_dict call, text and JSON output,
  exit code 3 on validation failure.
- `Makefile` (J4) — Added `coi-check` target. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J4) — v0.7.2 J4 changelog. Pipeline
  version: v0.7.2. Test count: 3536.
- `tests/test_test_count_regression.py` — baseline updated to 3536.

Honest boundaries:
- COI disclosure validation checks structural and policy requirements only.
  It does not verify that the disclosed information is true, complete, or
  accurate.
- Financial relationship without recusal produces a warning, not an error —
  the reviewer retains discretion to determine whether recusal is necessary.
- The validator cannot detect undisclosed conflicts — it only checks that
  disclosed conflicts are well-formed.
- `dry_lab_only: true` is a const field on all dataclasses — COI disclosures
  are governance artifacts, not legal determinations.
- The COI template is a transparency and governance tool — it does not replace
  the judgment of the human reviewer or governance team.

## v0.7.1 — Loop 111: Phase J J3 — Release Request Template ✓ (2026-07-09)

`docs/governance/RELEASE_REQUEST_TEMPLATE.md` with structured release request
template (purpose, fill-in-the-blank format with 17 fields: Release ID,
release type, artifact ID/version, requestor name/institution, request date,
evidence level 1-6, dry_lab_only, safety_review_status, benchmark_summary,
known_limitations, intended_use, data_license, human_reviewer, review_class
A-D, approval_status; review criteria with 8 checks; process with classes A-D
timelines and escalation path).

`src/openamp_foundry/governance/release_request.py` with `ReleaseRequest`
dataclass (17 fields), `ReleaseRequestValidationResult` dataclass (6 fields,
dry_lab_only=True), `VALID_RELEASE_TYPES` (5: candidate, model, dataset,
evidence_packet, schema), `VALID_SAFETY_STATUSES` (3: pending, approved,
not_required), `VALID_INTENDED_USES` (4: research, internal, external_partner,
public), `VALID_APPROVAL_STATUSES` (4: pending, approved, rejected, deferred),
`VALID_REVIEW_CLASSES` (4: A, B, C, D), `validate_release_request()` (17 checks:
release_id format, release_type valid, non-empty artifact_id/artifact_version/
requestor_name/requestor_institution, request_date YYYY-MM-DD, evidence_level
1-6, dry_lab_only must be True, safety_review_status valid, non-empty
benchmark_summary/known_limitations/data_license/human_reviewer, intended_use
valid, review_class valid, approval_status valid, dry_lab_only+evidence_level>4
error, public+safety_pending error, model+review_class warning).

`validate_request_dict()` (dict input with 17 required fields guard, missing
fields returns passed=False early).

CLI (`openamp-foundry release-request-check`) with `--request-json` (required),
`--format text|json`. Handler `_run_release_request_check` in reports.py.

`make release-request-check` target. 25 tests. **3516 total.**

Blocks public releases with pending safety review, blocks dry_lab_only
artifacts with evidence_level>4. Formal release requests now have a validated
structure before entering human review.

Changes:
- `docs/governance/RELEASE_REQUEST_TEMPLATE.md` (J3) — Structured release
  request template with purpose, template (17 fields), review criteria (8
  checks), process (5 steps with A-D timelines and escalation path).
- `src/openamp_foundry/governance/release_request.py` (J3) — Core module with
  `ReleaseRequest` (17 fields), `ReleaseRequestValidationResult` (6 fields,
  dry_lab_only=True), `VALID_RELEASE_TYPES` (5), `VALID_SAFETY_STATUSES` (3),
  `VALID_INTENDED_USES` (4), `VALID_APPROVAL_STATUSES` (4),
  `VALID_REVIEW_CLASSES` (4), `validate_release_request()` (17 checks),
  `validate_request_dict()` (dict input with missing-fields guard).
- `tests/governance/test_release_request.py` (J3) — 25 tests covering: valid
  candidate release request passes, release_id not starting with REL- fails,
  invalid release_type fails, empty artifact_id fails, empty requestor_name
  fails, invalid request_date format fails, evidence_level=0 fails,
  evidence_level=7 fails, dry_lab_only=False fails, invalid safety_review_status
  fails, empty benchmark_summary fails, empty known_limitations fails, invalid
  intended_use fails, public release with pending safety fails, dry_lab_only
  with evidence_level=5 fails, all results dry_lab_only=True, validate_request_
  dict passes, VALID_RELEASE_TYPES has 5, VALID_SAFETY_STATUSES has 3,
  VALID_INTENDED_USES has 4, VALID_APPROVAL_STATUSES has 4, VALID_REVIEW_CLASSES
  has 4, model review_class warning, dict missing fields fails.
- `src/openamp_foundry/cli/main.py` (J3) — Registered `release-request-check`
  subcommand with `--request-json`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J3) — Added
  `_run_release_request_check()` CLI handler with JSON parsing, validate_request
  _dict call, text and JSON output, exit code 3 on validation failure.
- `Makefile` (J3) — Added `release-request-check` target. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J3) — v0.7.1 J3 changelog. Pipeline
  version: v0.7.1. Test count: 3516.
- `tests/test_test_count_regression.py` — baseline updated to 3516.

Honest boundaries:
- Release request validation checks structural and policy requirements only.
  It does not verify that the artifact actually exists, that the evidence level
  claim is accurate, or that the safety review was thorough.
- `dry_lab_only: true` is a const field on all dataclasses — release requests
  are governance artifacts, not biological findings.
- The validator blocks public releases with pending safety review, but it cannot
  verify that the safety review was correctly performed or that the reviewer was
  qualified.
- Review classes are policy declarations — the validator checks that the class
  is valid (A-D) but not that the appropriate review process was followed.
- The release request template is a communication and governance tool — it does
  not replace the judgment of the human reviewer.

## v0.7.0 — Loop 110: Phase J J2 — Governance Decision Log ✓ (2026-07-09)

`docs/governance/DECISION_LOG.md` with structured governance decision log
(purpose, decision index with 8 entries GOV-001 through GOV-008 covering
safety/benchmark/release/evidence/data/adapter/contribution/docs scopes,
how to add entries, linked policies).

`src/openamp_foundry/governance/decision_log.py` with `VALID_SCOPES` (8:
safety, benchmark, release, evidence, data, adapter, contribution, docs),
`VALID_STATUSES` (4: active, superseded, under_review, proposed),
`VALID_REVIEW_CLASSES` (4: A, B, C, D), `GovernanceDecision` dataclass
(8 fields: decision_id, date, scope, decision, status, rationale,
review_class, dry_lab_only=True), `DecisionValidationResult` dataclass
(5 fields: decision_id, passed, errors, warnings, dry_lab_only=True),
`GOVERNANCE_DECISIONS` list (8 entries: GOV-001 through GOV-008),
`validate_governance_decision()` (9 checks: decision_id format, date
format, valid scope, non-empty decision, valid status, non-empty rationale,
valid review_class, dry_lab_only must be True, superseded warning),
`validate_all_decisions()` (aggregates total/passed/failed/all_passed/
results/dry_lab_only), `get_decisions_by_scope()` (filters by scope),
`get_decisions_by_status()` (filters by status).

CLI (`openamp-foundry decision-log`) with `--validate`, `--scope`,
`--format text|json`. Handler `_run_decision_log` in reports.py.

`make decision-log` target. 27 tests. **3491 total.**

**Phase J milestone: v0.7.0** — governance decisions are now discoverable
and machine-validated.

Changes:
- `docs/governance/DECISION_LOG.md` (J2) — Structured governance decision
  log with purpose, decision index (8 entries GOV-001 through GOV-008),
  how to add entries, linked policies.
- `src/openamp_foundry/governance/decision_log.py` (J2) — Core module with
  `VALID_SCOPES` (8), `VALID_STATUSES` (4), `VALID_REVIEW_CLASSES` (4),
  `GovernanceDecision` (8 fields, dry_lab_only=True default),
  `DecisionValidationResult` (5 fields, dry_lab_only=True default),
  `GOVERNANCE_DECISIONS` (8 entries: GOV-001 through GOV-008),
  `validate_governance_decision()` (9 checks),
  `validate_all_decisions()` (aggregates total/passed/failed/all_passed),
  `get_decisions_by_scope()`, `get_decisions_by_status()`.
- `tests/governance/test_decision_log.py` (J2) — 27 tests covering all
  8 GOV entries pass validation, empty/invalid decision_id, invalid date
  format, invalid scope (parametrized), empty decision text, invalid
  status (parametrized), empty rationale, invalid review_class
  (parametrized), dry_lab_only=False failure, superseded warning,
  validate_all_decisions passes, get_decisions_by_scope safety → GOV-001,
  get_decisions_by_status active → all 8, 8 entries constant check,
  all results dry_lab_only=True, valid set counts, DecisionValidationResult
  dataclass fields.
- `src/openamp_foundry/cli/main.py` (J2) — Registered `decision-log`
  subcommand with `--validate`, `--scope`, `--format` flags. Added import
  and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J2) — Added
  `_run_decision_log()` CLI handler with validate/scope filtering/list all
  modes, text and JSON output, exit code 3 on validation failure.
- `Makefile` (J2) — Added `decision-log` target. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J2) — v0.7.0 J2 changelog. Pipeline
  version: v0.7.0. Test count: 3491.
- `tests/test_test_count_regression.py` — baseline updated to 3491.

Honest boundaries:
- Decision log tracks governance decisions only — it does not measure
  biological activity, safety, or clinical value.
- `dry_lab_only: true` is a const field on all dataclasses — the decision
  log is a computational governance artifact, not a biological finding.
- The list of valid scopes and statuses is policy-defined and may need
  expansion as governance matures.
- Validation checks structural and policy requirements only — it does
  not verify that the decision was correctly implemented or enforced.
- Review classes are declarations stored on each decision; the validator
  does not verify that the declared review class was actually applied.
- The decision log is a documentation and validation tool — it does not
  replace human judgment about whether a decision is appropriate.

## v0.7.1 — Loop 111: Phase J J3 — Release Request Template ✓ (2026-07-09)

`docs/governance/RELEASE_REQUEST_TEMPLATE.md` with structured release
request template (purpose, fill-in template with 17 fields, review
criteria with 8 checks, process with classes A-D timelines and escalation).

`src/openamp_foundry/governance/release_request.py` with `ReleaseRequest`
dataclass (17 fields), `ReleaseRequestValidationResult` dataclass (6 fields,
dry_lab_only=True), `VALID_RELEASE_TYPES` (5), `VALID_SAFETY_STATUSES` (3),
`VALID_INTENDED_USES` (4), `VALID_APPROVAL_STATUSES` (4),
`VALID_REVIEW_CLASSES` (4), `validate_release_request()` (17 checks with
dry_lab_only+evidence_level>4 error, public+safety_pending error,
model+review_class warning), `validate_request_dict()` (dict input with
missing-fields guard).

CLI (`openamp-foundry release-request-check`) with `--request-json`,
`--format text|json`. Handler `_run_release_request_check` in reports.py.

`make release-request-check` target. 25 tests. **3516 total.**

Changes:
- `docs/governance/RELEASE_REQUEST_TEMPLATE.md` (J3) — Structured release
  request template with purpose, fill-in template (17 fields), review
  criteria (8 checks), process (submit→validate→review→decision→release),
  expected timelines per class A-D, escalation path.
- `src/openamp_foundry/governance/release_request.py` (J3) — Core module
  with `ReleaseRequest` (17 fields), `ReleaseRequestValidationResult`
  (6 fields, dry_lab_only=True), `VALID_RELEASE_TYPES` (5),
  `VALID_SAFETY_STATUSES` (3), `VALID_INTENDED_USES` (4),
  `VALID_APPROVAL_STATUSES` (4), `VALID_REVIEW_CLASSES` (4),
  `validate_release_request()` (17 checks including cross-field rules:
  dry_lab_only+evidence_level>4 error, public+safety_pending error,
  model+review_class C/D warning), `validate_request_dict()`.
- `tests/governance/test_release_request.py` (J3) — 25 tests covering:
  valid candidate passes, release_id must start with REL-, invalid type,
  empty artifact_id/requestor_name, invalid date format, evidence_level
  0/7, dry_lab_only=False, invalid safety_status, empty benchmark_summary/
  known_limitations, invalid intended_use, public+safety_pending fails,
  dry_lab_only+evidence_level 5 fails, dry_lab_only=True on results,
  valid dict passes, VALID_RELEASE_TYPES has 5 entries, VALID_SAFETY_STATUSES
  has 3, VALID_INTENDED_USES has 4, VALID_APPROVAL_STATUSES has 4,
  VALID_REVIEW_CLASSES has 4, model+low review_class warning, dict missing
  fields, invalid type via dict.
- `src/openamp_foundry/cli/main.py` (J3) — Registered `release-request-check`
  subcommand with `--request-json` (required), `--format` flags. Added import
  and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (J3) — Added
  `_run_release_request_check()` CLI handler with JSON parsing,
  `validate_request_dict()` call, text and JSON output, exit code 3
  on failure.
- `Makefile` (J3) — Added `release-request-check` target with demo invocation
  using schema release type with all fields valid. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J3) — v0.7.1 J3 changelog. Pipeline
  version: v0.7.1. Test count: 3516.
- `tests/test_test_count_regression.py` — baseline updated to 3516.

Honest boundaries:
- Release request validation checks structural and policy requirements only.
  It does not verify that the release was actually performed, that the
  artifact exists, or that the benchmark claims are biologically meaningful.
- `dry_lab_only: true` is a const field on all dataclasses — release requests
  are computational governance artifacts, not biological findings.
- The validator does not verify that the human reviewer has actually reviewed
  the request — it only checks that a GitHub handle was provided.
- Review class appropriateness is advisory: the validator warns about model
  releases with low review classes but does not block them.
- The template and process are governance tools — they do not replace human
  judgment about whether a release is appropriate or safe.

## v0.6.9 — Loop 109: Phase J J1 — Release Checklist ✓ (2026-07-09)

`docs/governance/RELEASE_CHECKLIST.md` with structured release checklist
cross-referencing `docs/trust/RELEASE_CHECKLIST.md`.

`src/openamp_foundry/governance/release_gate.py` with `RELEASE_TYPES` (5:
candidate, model, dataset, evidence_packet, schema), `UNIVERSAL_GATES` (7:
ci_tests_pass, agent_check_passes, no_critical_issues, dry_lab_only_confirmed,
safety_flags_reviewed, data_license_verified, no_hardcoded_secrets),
`EXTRA_GATES_BY_TYPE` (per-type additional gates), `ReleaseGateResult`
dataclass (8 fields, dry_lab_only=True), `validate_release_gate()` (validates
all required gates, treats missing gates as failed, raises CRITICAL error
on dry_lab_only_confirmed failure).

CLI (`openamp-foundry release-gate-check`) with `--release-type`,
`--artifact-id`, `--gates-json`, `--format text|json`.

`make release-gate-check` target. 18 tests. **3478 total.**

**Starts Phase J (Governance and release maturity)** — releases now require
all gates to pass before external release, preventing accidental bypass of
required checks.

Changes:
- `docs/governance/RELEASE_CHECKLIST.md` — Structured release checklist with
  pre-release gates, release-type gates (5 types), post-release checklist.
- `src/openamp_foundry/governance/__init__.py` — Empty package init.
- `src/openamp_foundry/governance/release_gate.py` (J1) — Core module with
  `RELEASE_TYPES` (5), `UNIVERSAL_GATES` (7), `EXTRA_GATES_BY_TYPE`,
  `ReleaseGateResult` (8 fields, dry_lab_only=True),
  `validate_release_gate()`.
- `tests/governance/__init__.py` — Empty package init.
- `tests/governance/test_release_gate.py` (J1) — 18 tests covering all
  release types, universal gate failure, missing gates, invalid release
  type, empty artifact_id, dry_lab_only_confirmed CRITICAL error, constant
  checks.
- `src/openamp_foundry/cli/commands/gates.py` (J1) — Added
  `_run_release_gate_check()` CLI handler with JSON parsing,
  `validate_release_gate()` call, text and JSON output.
- `src/openamp_foundry/cli/main.py` (J1) — Registered `release-gate-check`
  subcommand with `--release-type`, `--artifact-id`, `--gates-json`,
  `--format` flags. Added import and dispatch.
- `Makefile` (J1) — Added `release-gate-check` target with demo invocation
  using schema release type with all gates green. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (J1) — v0.6.9 J1 changelog. Pipeline
  version: v0.6.9. Test count: 3478. Phase J started note.
- `tests/test_test_count_regression.py` — baseline updated to 3478.

Honest boundaries:
- Release gate validator can only check what it is told via gate_statuses —
  if a gate status is incorrectly reported as passing, the validator cannot
  detect that.
- The checklist is documentation and automation — it does not replace human
  judgment about whether a release is appropriate.
- dry_lab_only flag is always True; the validator enforces this but cannot
  verify the actual status of external artifacts.
- No wet-lab validity implied. Gates are dry-lab governance only.

## v0.6.8 — Loop 108: Phase I I10 — Adoption Scorecard Dashboard ✓ (2026-07-09)

`src/openamp_foundry/adoption/scorecard.py` with `SCORECARD_DIMENSIONS`
(5 weighted dimensions summing to 1.0: integration_check 0.25,
license_compliance 0.20, adapter_validation 0.20, schema_compatibility 0.20,
contribution_readiness 0.15), `ADOPTION_TIERS` (4 tiers: not_ready 0.0-0.40,
emerging 0.40-0.65, established 0.65-0.85, mature 0.85-1.01),
`DimensionScore` dataclass (8 fields: dimension, weight, raw_score,
weighted_score, passed_checks, total_checks, notes, dry_lab_only=True),
`AdoptionScorecard` dataclass (6 fields: total_score, adoption_tier,
dimensions, summary, recommendations, dry_lab_only=True),
`build_scorecard()` (aggregates dimension inputs into weighted total score
with tier classification and actionable recommendations),
`compute_adoption_tier()` (maps float score 0.0-1.0 to tier string).

CLI (`openamp-foundry adoption-scorecard`) with `--scores-json` and
`--format text|json`. Handler `_run_adoption_scorecard` in reports.py.

`make adoption-scorecard` target. 17 tests. **3446 total.**

**Phase I (Interoperability and Adoption) is now fully complete** — all 10
items I1–I10 implemented (artifact versioning, candidate manifest, benchmark
card, artifact changelog, integration checker, adapter validator, data license
checker, schema compatibility, contribution intake, adoption scorecard).

Changes:
- `src/openamp_foundry/adoption/scorecard.py` (I10) — Core module with
  `SCORECARD_DIMENSIONS` (5 weighted dimensions summing to 1.0),
  `ADOPTION_TIERS` (4 tiers), `DimensionScore` (8 fields, dry_lab_only=True
  default), `AdoptionScorecard` (6 fields, dry_lab_only=True default),
  `build_scorecard()` (aggregates dimension inputs into weighted total score,
  tier, and per-dimension scores with recommendations),
  `compute_adoption_tier()` (maps float 0.0-1.0 to tier string).
- `tests/adoption/__init__.py` (I10) — Empty package init.
- `tests/adoption/test_scorecard.py` (I10) — 17 tests covering: perfect scores
  → mature, all zeros → not_ready, score 0.50 → emerging, score 0.75 →
  established, weights sum to 1.0, SCORECARD_DIMENSIONS has 5 entries,
  ADOPTION_TIERS has 4 entries, DimensionScore dry_lab_only=True default,
  AdoptionScorecard dry_lab_only=True default, recommendations empty when
  all pass, recommendations populated on failures, weighted sum correctness,
  missing dimension defaults to 0/0, compute_adoption_tier boundaries,
  build_scorecard returns correct fields.
- `src/openamp_foundry/cli/main.py` (I10) — Registered `adoption-scorecard`
  subcommand with `--scores-json` (required), `--format` flags. Added import
  and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I10) — Added
  `_run_adoption_scorecard()` CLI handler with JSON parsing, `build_scorecard`
  call, text and JSON output.
- `Makefile` (I10) — Added `adoption-scorecard` target with demo invocation
  using all 5 dimensions at perfect scores. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (I10) — v0.6.8 I10 changelog. Pipeline
  version: v0.6.8. Test count: 3446. Phase I complete note.
- `tests/test_test_count_regression.py` — baseline updated to 3446.

Honest boundaries:
- Scorecard measures adoption readiness only — whether the checks pass or fail.
  It does not measure actual downstream adoption, user satisfaction, or
  biological validity.
- Dimension weights are heuristic and may need adjustment as adoption data
  accumulates. The current weights (integration 0.25, license 0.20, adapter
  0.20, schema 0.20, contribution 0.15) are the initial guess.
- `dry_lab_only: true` is a const field on all dataclasses — the scorecard is
  a computational governance tool, not a biological assessment.
- The scorecard aggregates structural signals from other Phase I modules. If
  any of those modules have blind spots, the aggregation inherits them.
- Perfect scores mean all structural checks pass, not that real-world adoption
  is happening. Adoption is a social outcome, not a pipeline metric.

## v0.6.7 — Loop 107: Phase I I9 — Public-Good Contribution Guide ✓ (2026-07-09)

`docs/community/PUBLIC_GOOD_CONTRIBUTION_GUIDE.md` with 6 contribution types
(wet_lab_validation, dataset_donation, compute_sponsorship, expert_review,
governance_participation, algorithm_contribution), review classes A-D, minimum
requirements table, initiation process, data governance, and safety constraints.

`src/openamp_foundry/community/contribution_intake.py` with `ContributionIntake`
dataclass (7 fields: institution_name, contact_email, contribution_type,
proposed_scope, human_review_required, dry_lab_only, extra_fields),
`IntakeValidationResult` dataclass (7 fields: institution_name, contribution_type,
passed, errors, warnings, required_review_class, dry_lab_only),
`VALID_CONTRIBUTION_TYPES` set (6 entries), `VALID_REVIEW_CLASSES` set (4 entries),
`REQUIRED_FIELDS_BY_TYPE` dict (6 entries). `validate_contribution_intake()` checks
all top-level fields (institution_name, contact_email, contribution_type,
proposed_scope, dry_lab_only), type-specific required fields from
REQUIRED_FIELDS_BY_TYPE, and enforces human_review_required=True for
wet_lab_validation. `validate_intake_dict()` handles raw dict input with
missing-fields guard.

CLI (`openamp-foundry contribution-check`) with `--intake-json` and
`--format text|json`. Handler `_run_contribution_check` in reports.py.

`make contribution-check` target. 16 tests. **3429 total.**

Changes:
- `docs/community/PUBLIC_GOOD_CONTRIBUTION_GUIDE.md` (I9) — Full public-good
  contribution guide with purpose, who can contribute, 6 contribution types
  table, minimum requirements, initiation process, data governance, safety
  constraints, and contact information.
- `src/openamp_foundry/community/__init__.py` (I9) — Empty package init.
- `src/openamp_foundry/community/contribution_intake.py` (I9) — Core module
  with `ContributionIntake` (7 fields), `IntakeValidationResult` (7 fields),
  `VALID_CONTRIBUTION_TYPES` (6 entries), `VALID_REVIEW_CLASSES` (4 entries),
  `REQUIRED_FIELDS_BY_TYPE` (6 entries), `validate_contribution_intake()`,
  `validate_intake_dict()`. All dataclasses carry dry_lab_only=True.
- `tests/community/__init__.py` (I9) — Empty package init.
- `tests/community/test_contribution_intake.py` (I9) — 16 tests covering:
  valid dataset_donation passes, valid wet_lab_validation with human_review
  passes, empty institution_name fails, invalid email fails, invalid
  contribution_type fails, empty proposed_scope fails, dry_lab_only=False
  fails, wet_lab_validation without human_review fails, dataset_donation
  missing data_license fails, algorithm_contribution missing has_tests fails,
  all results have dry_lab_only=True, validate_intake_dict passes, dict
  missing field fails, VALID_CONTRIBUTION_TYPES has 6 entries,
  REQUIRED_FIELDS_BY_TYPE has 6 keys, wet_lab_validation gets review_class D.
- `src/openamp_foundry/cli/main.py` (I9) — Registered `contribution-check`
  subcommand with `--intake-json` (required), `--format` flags. Added import
  and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I9) — Added
  `_run_contribution_check()` CLI handler with JSON parsing, ContributionIntake
  creation, text and JSON output, and exit code 3 on failure.
- `Makefile` (I9) — Added `contribution-check` target with demo invocation
  using Example University dataset_donation. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (I9) — v0.6.7 I9 changelog. Pipeline
  version: v0.6.7. Test count: 3429.
- `tests/test_test_count_regression.py` — baseline updated to 3429.

Honest boundaries:
- Contribution validation checks structural and policy requirements only.
  It does not verify that the institution actually has the right to share
  the data or that the data is biologically meaningful.
- `dry_lab_only: true` is a const field on all dataclasses — contribution
  intake is inherently computational and must never be presented as
  biological proof.
- wet_lab_validation always requires human_review_required=True — this is
  a structural check that the flag is set, not verification that human
  review actually occurred.
- Data governance (DATA_GOVERNANCE.md, DATA_LICENSE_NOTICE.md) applies to
  all contributed datasets regardless of whether the intake check passes.
- The contribution guide is informational and aspirational. Actual
  acceptance and review outcomes depend on maintainer capacity and
  project priorities.

## v0.6.6 — Loop 106: Phase I I8 — Artifact Compatibility Tests ✓ (2026-07-09)

`src/openamp_foundry/compatibility/artifact_compatibility.py` with
`SchemaCompatibilityResult` dataclass (5 fields: schema_name, schema_path, passed,
errors, warnings, dry_lab_only=True). `UNIVERSAL_REQUIRED_FIELDS` (set: dry_lab_only,
version). `CONVENTION_CHECKS` (dict: dry_lab_only → boolean const true, version →
string matching MAJOR.MINOR.PATCH, evidence_level → integer in 1-6 when present).
`check_schema_conventions()` validates each schema against universal conventions.
`run_compatibility_check()` scans all schemas/*.schema.json and returns
total/passed/failed/all_passed/results/dry_lab_only.

CLI (`openamp-foundry artifact-compat-check`) with `--schemas-dir` (default:
schemas/) and `--format text|json`. Handler `_run_artifact_compat_check` in
reports.py.

`make artifact-compat-check` target. 20 tests. **3413 total.** Cross-artifact
schema compatibility is automatically checked across all schema files, preventing
drift between artifact versions.

Changes:
- `src/openamp_foundry/compatibility/__init__.py` (I8) — Empty package init.
- `src/openamp_foundry/compatibility/artifact_compatibility.py` (I8) — Core module
  with `SchemaCompatibilityResult` (5 fields, dry_lab_only=True default),
  `UNIVERSAL_REQUIRED_FIELDS`, `CONVENTION_CHECKS`, `check_schema_conventions()`,
  `run_compatibility_check()`.
- `tests/compatibility/__init__.py` (I8) — Empty package init.
- `tests/compatibility/test_artifact_compatibility.py` (I8) — 20 tests covering
  candidate_manifest/benchmark_card passes, simulation_result detected (known
  dry_lab_context convention difference), synthetic schemas with missing/misformed
  fields, run_compatibility_check dict shape, SchemaCompatibilityResult defaults,
  additionalProperties/$schema warnings.
- `src/openamp_foundry/cli/main.py` (I8) — Registered `artifact-compat-check`
  subcommand with `--schemas-dir`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I8) — Added
  `_run_artifact_compat_check()` CLI handler with text and JSON output, exit code 3
  on failure.
- `Makefile` (I8) — Added `artifact-compat-check` target. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` (I8) — Updated last updated, new in v0.6.6,
  pipeline version, test count (3393→3413).

## v0.6.5 — Loop 105: Phase I I7 — Data License Checker ✓ (2026-07-09)

`src/openamp_foundry/licensing/license_checker.py` with `DataLicenseDeclaration`
dataclass (11 fields: source_id, source_name, license_id, use_context,
attribution_required, commercial_use_allowed, redistribution_allowed,
modifications_allowed, human_review_required, notes, dry_lab_only).
`LicenseCheckResult` dataclass (8 fields: source_id, license_id, use_context,
passed, status, errors, warnings, dry_lab_only). `check_data_license()` validates
declarations against three license sets: `APPROVED_LICENSES` (11 entries: CC0-1.0,
CC-BY-4.0, CC-BY-SA-4.0, MIT, Apache-2.0, GPL-3.0, LGPL-2.1, BSD-2-Clause,
BSD-3-Clause, ODbL-1.0, PDDL-1.0), `RESTRICTED_LICENSES` (4 entries: CC-BY-NC-4.0,
CC-BY-NC-SA-4.0, custom, proprietary), `BLOCKED_LICENSES` (3 entries: unknown,
unlicensed, all-rights-reserved). Blocked licenses fail immediately; restricted
require human_review_required=True; unknown licenses require governance review.
`check_license_batch()` summarizes total/passed/failed/blocked/any_blocked/
all_passed with dry_lab_only=True. `VALID_USE_CONTEXTS` (6 entries: training,
scoring, benchmarking, reporting, publication, internal).

CLI (`openamp-foundry license-check`) with `--source-json` (required) and
`--format text|json`. Handler `_run_license_check` in reports.py.

`make license-check` target. 20 tests. **3393 total.** External data sources
used in pipeline outputs now require explicit license declarations, preventing
hidden legal risk. This is Loop 105 — the 105th PR in the NEXT_100_PR_MAP series.

Changes:
- `src/openamp_foundry/licensing/__init__.py` (I7) — Empty package init.
- `src/openamp_foundry/licensing/license_checker.py` (I7) — Core module with
  `DataLicenseDeclaration` (11 fields), `LicenseCheckResult` (8 fields),
  `check_data_license()` (validates against APPROVED_LICENSES 11 entries,
  RESTRICTED_LICENSES 4, BLOCKED_LICENSES 3, VALID_USE_CONTEXTS 6),
  `check_license_batch()` (summary with counts, any_blocked, all_passed,
  dry_lab_only=True). All dataclasses carry dry_lab_only=True.
- `tests/licensing/__init__.py` (I7) — Empty package init.
- `tests/licensing/test_license_checker.py` (I7) — 20 tests covering: valid CC0
  passes, valid MIT passes, blocked unknown/unlicensed/all-rights-reserved fail,
  restricted CC-BY-NC-4.0 without human_review fails, restricted with human_review
  passes, empty source_id/source_name/license_id fail, invalid use_context fails,
  dry_lab_only=False fails, publication without redistribution fails, unknown
  license gets status=unknown_license, batch counts correct, all results
  dry_lab_only, constant counts.
- `src/openamp_foundry/cli/main.py` (I7) — Registered `license-check` subcommand
  with `--source-json`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I7) — Added `_run_license_check()`
  CLI handler with JSON parsing, DataLicenseDeclaration creation, text and JSON
  output, and exit code 3 on failure.
- `Makefile` (I7) — Added `license-check` target with demo invocation using
  apd-v2 source and CC-BY-4.0 license. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.5 I7 changelog. Test count: 3393.
- `tests/test_test_count_regression.py` — baseline updated to 3393.

Honest boundaries:
- License validation checks declared license identifiers against known lists.
  It does not verify that the data source actually uses the declared license,
  that the license is legally enforceable in a given jurisdiction, or that the
  data was lawfully obtained.
- Approved and blocked lists are policy-defined and may need updating as the
  legal landscape evolves.
- `dry_lab_only: true` is a const field on all dataclasses — license checks
  are inherently computational and must never be presented as legal advice.
- External adapter authors who produce data from new sources must declare their
  licenses before those data can influence pipeline outputs.
- Restricted licenses require human_review_required=True — this is a structural
  check that the flag is set, not verification that human review actually occurred.

## v0.6.4 — Loop 104: Phase I I6 — Adapter Author Validator ✓ (2026-07-09)

`src/openamp_foundry/adapters/adapter_validator.py` with `AdapterDeclaration`
dataclass (14 fields: adapter_id, adapter_version, mode, output_status,
score_fields, uncertainty, warnings, failure_reason, release_status,
ranking_effect, has_baseline_comparison, makes_network_calls,
network_call_documented, dry_lab_only). `AdapterValidationResult` dataclass
(5 fields: adapter_id, passed, errors, warnings_list, dry_lab_only).
`validate_adapter_declaration()` with 10 checks covering all fields against
their valid value sets (VALID_ADAPTER_MODES, VALID_OUTPUT_STATUSES,
VALID_RANKING_EFFECTS, VALID_RELEASE_STATUSES) plus cross-field rules
(baseline comparison required for ranking_effect=proposed/active, network
call documentation required when makes_network_calls=True, deprecated mode
must not have active/proposed ranking_effect, uncertainty must be 0.0-1.0
or None, dry_lab_only must be True). Gated mode with ranking_effect=none
produces a warning. `validate_adapter_dict()` for raw dict validation with
missing-fields guard.

CLI (`openamp-foundry adapter-check`) with `--adapter-json` (required) and
`--format text|json`. Handler `_run_adapter_check` in reports.py.

`make adapter-author-check` target. 31 tests. **3387 total.** External adapter
authors can now validate their declarations against the ADAPTER_AUTHOR_GUIDE
contract before submitting. This is Loop 104 — the 104th PR in the
NEXT_100_PR_MAP series.

Changes:
- `src/openamp_foundry/adapters/__init__.py` (I6) — Empty package init.
- `src/openamp_foundry/adapters/adapter_validator.py` (I6) — Core module
  with AdapterDeclaration (14 fields), AdapterValidationResult (5 fields),
  validate_adapter_declaration (10 checks), validate_adapter_dict (dict
  input with missing-fields guard), 4 valid-value sets (VALID_ADAPTER_MODES,
  VALID_OUTPUT_STATUSES, VALID_RANKING_EFFECTS, VALID_RELEASE_STATUSES),
  REQUIRED_OUTPUT_CONTRACT_FIELDS (10 items). All dataclasses carry
  dry_lab_only=True.
- `tests/adapters/__init__.py` (I6) — Empty package init.
- `tests/adapters/test_adapter_validator.py` (I6) — 31 tests covering:
  valid minimal declaration, empty adapter_id/version, invalid mode/output_
  status/ranking_effect/release_status, dry_lab_only=False, ranking_effect
  active/proposed requires baseline, network calls require documentation,
  deprecated+active ranking, uncertainty range, None uncertainty passes,
  gated+none warning, all valid modes/output_statuses parametrized, result
  dry_lab_only, valid dict, missing fields in dict, constants counts.
- `src/openamp_foundry/cli/main.py` (I6) — Registered `adapter-check`
  subcommand with `--adapter-json`, `--format` flags. Added import and
  dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I6) — Added
  `_run_adapter_check()` CLI handler with JSON parsing, text and JSON
  output, adapter validation, and error handling.
- `Makefile` (I6) — Added `adapter-author-check` target with demo
  invocation using example-adapter. Added to `.PHONY`.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.4 I6 changelog. Fixed > >
  formatting bug on v0.6.2 line. Test count: 3387.
- `tests/test_test_count_regression.py` — baseline updated to 3373.

Honest boundaries:
- Adapter validation checks structural and policy requirements only. It
  does not verify that the adapter produces biologically meaningful outputs
  or that the adapter implementation is correct.
- Valid value sets are policy-defined and may need updating as the adapter
  ecosystem evolves.
- The validator accepts declarative metadata only — it does not run the
  adapter or verify its behavior at runtime.
- `dry_lab_only: true` is a const field on all dataclasses — adapters are
  inherently dry-lab and must never be presented as biological proof.
- Safety, toxicity, and dual-use safeguards are preserved — the validator
  enforces no-ranking-effect for deprecated adapters, baseline comparison
  for active adapters, and documentation for network calls.

## v0.6.3 — Loop 103: Phase I I5 — Downstream Project Template ✓ (2026-07-09)

`docs/adoption/DOWNSTREAM_PROJECT_TEMPLATE.md` with overview of OpenAMP
artifacts (candidate manifests, benchmark cards, evidence certificates,
simulation results — all dry-lab only), minimum viable integration steps
(consume candidate manifest, validate against schema, use Python library),
schema validation guide against `candidate_manifest.schema.json`, evidence
level interpretation table (L1-L6 with labels, meanings, and caveats),
safety flag conventions table (6 flags with meanings and suggested actions),
benchmark card consumption guide with comparison against baselines, explicit
dry-lab limitations section, and contact/contribution section.

`src/openamp_foundry/adoption/integration_checker.py` with
`REQUIRED_INTEGRATION_CHECKS` list (5 checks: manifest_schema_valid,
evidence_level_in_range, dry_lab_only_acknowledged, safety_flags_reviewed,
baseline_comparison_present). `IntegrationCheckResult` dataclass (4 fields:
check_name, passed, detail, dry_lab_only). `run_integration_checks()` that
validates a manifest dict against all 5 checks and returns checks list,
passed_count, failed_count, all_passed, dry_lab_only.

Exported from `src/openamp_foundry/adoption/__init__.py`.

CLI (`openamp-foundry integration-check`) with `--manifest-json` (required,
JSON of candidate manifest dict), `--format text|json`. `make integration-check`
target. Handler `_run_integration_check` in reports.py.

14 tests. **3356 total.** External researchers who want to use OpenAMP
artifacts in their own pipelines now have a guide that shows them the minimum
viable integration: how to consume a candidate manifest, validate it, and
produce their own evidence packet.

Changes:
- `docs/adoption/DOWNSTREAM_PROJECT_TEMPLATE.md` (I5) — Full downstream
  project guide with integration steps, schema validation, evidence table,
  safety flags, benchmark card consumption, dry-lab limitations.
- `src/openamp_foundry/adoption/__init__.py` (I5) — Package init, exports
  `REQUIRED_INTEGRATION_CHECKS`, `IntegrationCheckResult`,
  `run_integration_checks`.
- `src/openamp_foundry/adoption/integration_checker.py` (I5) — Core module
  with `REQUIRED_INTEGRATION_CHECKS` (5 items), `IntegrationCheckResult`
  dataclass (4 fields), `run_integration_checks()` (5 checks against
  manifest dict, returns dict with checks, counts, all_passed, dry_lab_only).
- `src/openamp_foundry/cli/main.py` (I5) — Registered `integration-check`
  subcommand with `--manifest-json`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I5) — Added
  `_run_integration_check()` CLI handler with JSON parsing, text and JSON
  output, integration check execution, and error handling.
- `Makefile` (I5) — Added `integration-check` target with demo invocation
  using AMP-001 manifest. Added to `.PHONY`.
- `tests/adoption/__init__.py` (I5) — Empty package init.
- `tests/adoption/test_integration_checker.py` (I5) — 14 tests covering:
  valid manifest all_passed=True, missing candidate_id fails, level=0 fails,
  level=7 fails, dry_lab_only=False fails, dry_lab_only key missing fails,
  safety_flags key missing fails, empty scores fails, all checks return
  dry_lab_only=True, REQUIRED_INTEGRATION_CHECKS has 5 entries,
  run_integration_checks returns dry_lab_only=True, passed+failed=5,
  valid manifest failed_count=0, IntegrationCheckResult dataclass
  constructor.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.3 I5 changelog. Test count: 3356.
- `tests/test_test_count_regression.py` — baseline updated to 3356.

Honest boundaries:
- The downstream project template is a guide for consuming dry-lab artifacts.
  It does not contain biological instructions, assay protocols, or safety
  procedures.
- The integration checker validates structural and policy requirements only.
  It does not verify that a downstream project actually consumes the artifacts
  correctly or that the candidate manifests are biologically meaningful.
- `dry_lab_only: true` is preserved throughout — all integration checks are
  computational safeguards, not biological proof.
- The evidence level table is a taxonomy, not a validation ladder. L1-L3
  outputs remain computational hypotheses regardless of integration status.
- Safety flag conventions are advisory. Downstream projects must conduct
  their own safety review.

## v0.6.2 — Loop 102: Phase I I4 — Evidence-Certificate Changelog ✓ (2026-07-09)

`docs/engineering/ARTIFACT_CHANGELOG.md` with structured changelog format
(version, date, artifact_name, change_type, description, breaking flag).
Unreleased section at top for pending changes. 5 entries covering recent
Phase H and I additions (candidate_manifest, benchmark_card,
simulation_result, simulation_module_registry, artifact_versioning_policy)
plus the changelog itself — all as "added", non-breaking, v1.0.0.

`src/openamp_foundry/versioning/artifact_changelog.py` with `CHANGE_TYPES`
set (6 values: added, changed, deprecated, removed, fixed, security),
`ChangelogEntry` dataclass (7 fields: version, date, artifact_name,
change_type, description, breaking, notes), `ARTIFACT_CHANGELOG` list
(6 entries), `get_changelog_entries()` (filters by artifact_name, version,
change_type, breaking_only), `validate_changelog()` (5 checks: version
MAJOR.MINOR.PATCH, date YYYY-MM-DD with dashes, artifact_name non-empty,
change_type in CHANGE_TYPES, description non-empty), `changelog_summary()`
(total, by_change_type, breaking_changes, artifacts_covered sorted,
dry_lab_only).

CLI (`openamp-foundry artifact-changelog`) with `--artifact`, `--version`,
`--change-type`, `--breaking-only`, `--format text|json`.
`make artifact-changelog` target.

13 tests. **3342 total.** External tools that consume OpenAMP artifacts
now have a machine-readable changelog to detect breaking changes and adapt
consumers. This is Loop 102 — the 102nd PR in the NEXT_100_PR_MAP series.

Changes:
- `docs/engineering/ARTIFACT_CHANGELOG.md` (I4) — Structured changelog
  document with versioned entries, Unreleased section, and dry-lab-only
  disclaimer.
- `src/openamp_foundry/versioning/artifact_changelog.py` (I4) — Core
  module with `CHANGE_TYPES`, `ChangelogEntry` dataclass,
  `ARTIFACT_CHANGELOG`, `get_changelog_entries()`, `validate_changelog()`,
  `changelog_summary()`.
- `src/openamp_foundry/versioning/__init__.py` (I4) — Exported
  `CHANGE_TYPES`, `ChangelogEntry`, `ARTIFACT_CHANGELOG`,
  `get_changelog_entries`, `validate_changelog`, `changelog_summary`.
- `src/openamp_foundry/cli/main.py` (I4) — Registered `artifact-changelog`
  subcommand with `--artifact`, `--version`, `--change-type`,
  `--breaking-only`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I4) — Added
  `_run_artifact_changelog()` CLI handler with JSON and text output,
  filtering, validation display, and summary.
- `Makefile` (I4) — Added `artifact-changelog` target with `.PHONY`.
- `tests/versioning/test_artifact_changelog.py` (I4) — 13 tests covering:
  at least 5 entries, all pass validation, no filter returns all, filter
  by artifact_name, breaking_only, change_type, catches empty artifact_name,
  invalid change_type, invalid version format, summary total, dry_lab_only,
  breaking_changes count, artifacts_covered sorted.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.2 I4 changelog. Test count: 3342.
- `tests/test_test_count_regression.py` — baseline updated to 3342.

Honest boundaries:
- Changelog entries describe schema and format changes only — they do not
  measure biological activity, safety, or clinical value.
- All current entries are "added" and non-breaking; breaking changes are
  expected in future major versions.
- The changelog is a computational artifact — it records version history,
  not biological findings.
- `dry_lab_only: true` applies to all entries — changelogs are inherently
  dry-lab and must never be presented as validated biological findings.

## v0.6.1 — Loop 101: Phase I I3 — Benchmark Card Schema ✓ (2026-07-09)

`schemas/benchmark_card.schema.json` (Draft 2020-12, 15 required fields:
benchmark_id, benchmark_name, version, date, metric, metric_value, baseline_name,
baseline_value, delta, beats_baseline, dataset, dataset_size, scope, caveats,
dry_lab_only). `$schema`, `$id`, `title`, `additionalProperties: false`.

`src/openamp_foundry/benchmarks/` module with `BenchmarkCard` dataclass
(15 fields), `make_benchmark_card()` (auto-computes delta, beats_baseline),
`validate_benchmark_card()` (10 checks: non-empty benchmark_id, non-empty
benchmark_name, non-empty metric, non-empty dataset, non-empty baseline_name,
dataset_size >= 1, delta matches metric_value - baseline_value within 1e-9,
beats_baseline matches delta > 0, dry_lab_only must be True),
`benchmark_card_summary()` (total, beats_baseline_count, fails_baseline_count,
dry_lab_only).

CLI (`openamp-foundry benchmark-card`) with `--benchmark-id`, `--benchmark-name`,
`--metric`, `--metric-value`, `--baseline-name`, `--baseline-value`, `--dataset`,
`--dataset-size`, `--validate`, `--format text|json`.
`make benchmark-card` target.

19 tests. **3329 total.** A benchmark card is the standard format for describing
external benchmark results — what was benchmarked, what the baseline was, what
the result was, and what claims are supported. This is Loop 101 — the 101st PR
in the NEXT_100_PR_MAP series.

Changes:
- `schemas/benchmark_card.schema.json` (I3) — Draft 2020-12 schema with
  15 required fields, `$id`, `title`, `additionalProperties: false`.
- `src/openamp_foundry/benchmarks/__init__.py` (I3) — Package init, exports
  `BenchmarkCard`, `make_benchmark_card`, `validate_benchmark_card`,
  `benchmark_card_summary`.
- `src/openamp_foundry/benchmarks/benchmark_card.py` (I3) — Core module
  with `BenchmarkCard` dataclass (15 fields), `make_benchmark_card()`,
  `validate_benchmark_card()`, `benchmark_card_summary()`.
- `src/openamp_foundry/cli/main.py` (I3) — Registered `benchmark-card`
  subcommand with `--benchmark-id`, `--benchmark-name`, `--metric`,
  `--metric-value`, `--baseline-name`, `--baseline-value`, `--dataset`,
  `--dataset-size`, `--validate`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I3) — Added
  `_run_benchmark_card()` CLI handler with JSON and text output,
  card creation, optional validation, and error handling.
- `Makefile` (I3) — Updated `benchmark-card` target with demo invocation
  using bench-auroc-001. Added to `.PHONY`.
- `tests/benchmarks/__init__.py` (I3) — Empty package init.
- `tests/benchmarks/test_benchmark_card.py` (I3) — 19 tests covering:
  make_benchmark_card returns BenchmarkCard, delta computed correctly,
  beats_baseline True/False, dry_lab_only always True, valid card passes
  validation, catches empty benchmark_id, empty benchmark_name, empty metric,
  empty dataset, empty baseline_name, dataset_size < 1, wrong delta,
  wrong beats_baseline, dry_lab_only=False, summary total, summary
  beats_baseline_count, dry_lab_only, schema file exists.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.1 I3 changelog. Test count: 3329.
- `tests/test_test_count_regression.py` — baseline updated to 3329.

Honest boundaries:
- Benchmark cards describe computational benchmark results only — they do not
  measure biological activity, safety, or clinical value.
- Delta and beats_baseline are computed from metric_value and baseline_value,
  not independently measured.
- The schema is versioned (currently 1.0.0) and should be updated when fields
  are added or changed.
- Validation checks structural correctness and internal consistency only — it
  does not verify that the benchmark was correctly designed or that the results
  generalize.
- `dry_lab_only: true` is a const field — all benchmark cards are inherently
  dry-lab and must never be presented as validated biological findings.

## v0.6.0 — Loop 100: Phase I I2 — Candidate Manifest Schema ✓ (2026-07-09)

`schemas/candidate_manifest.schema.json` (Draft 2020-12, 14 required fields:
candidate_id, sequence, evidence_level, scopes, scores, uncertainty,
source_modules, calibration_set, safety_flags, provenance_run_id, dry_lab_only,
version, created_at, notes). `$schema`, `$id`, `title`, `description`,
`additionalProperties: false`.

`src/openamp_foundry/manifests/` module with `CandidateManifest` dataclass
(14 fields), `make_candidate_manifest()`, `validate_candidate_manifest()`
(8 checks: non-empty candidate_id, non-empty sequence, evidence_level 1-6,
non-empty scopes, uncertainty 0.0-1.0, non-empty source_modules,
dry_lab_only must be True, version MAJOR.MINOR.PATCH), `manifest_to_dict()`,
`manifest_summary()` (total, by_evidence_level, with_safety_flags, dry_lab_only).

CLI (`openamp-foundry candidate-manifest`) with `--candidate-id`, `--sequence`,
`--evidence-level`, `--scopes`, `--scores-json`, `--uncertainty`,
`--source-modules`, `--validate`, `--format text|json`.
`make candidate-manifest` target.

19 tests. **3310 total.** A candidate manifest is the core interoperable
artifact — it describes a dry-lab candidate (sequence, scores, evidence level,
scopes, safety flags, provenance) in a machine-readable format that external
tools can consume without the full OpenAMP stack. This is Loop 100 — the
100th PR in the NEXT_100_PR_MAP series.

Changes:
- `schemas/candidate_manifest.schema.json` (I2) — Draft 2020-12 schema with
  14 required fields, `$id`, `title`, `description`, `additionalProperties: false`.
- `src/openamp_foundry/manifests/__init__.py` (I2) — Package init, exports
  `CandidateManifest`, `make_candidate_manifest`, `validate_candidate_manifest`,
  `manifest_to_dict`, `manifest_summary`.
- `src/openamp_foundry/manifests/candidate_manifest.py` (I2) — Core module
  with `CandidateManifest` dataclass (14 fields), `make_candidate_manifest()`,
  `validate_candidate_manifest()`, `manifest_to_dict()`, `manifest_summary()`.
- `src/openamp_foundry/cli/main.py` (I2) — Registered `candidate-manifest`
  subcommand with `--candidate-id`, `--sequence`, `--evidence-level`,
  `--scopes`, `--scores-json`, `--uncertainty`, `--source-modules`,
  `--validate`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` (I2) — Added
  `_run_candidate_manifest()` CLI handler with JSON and text output,
  manifest creation, optional validation, and error handling.
- `Makefile` (I2) — Added `candidate-manifest` target with demo invocation
  using AMP-001. Added to `.PHONY`.
- `tests/manifests/__init__.py` (I2) — Empty package init.
- `tests/manifests/test_candidate_manifest.py` (I2) — 19 tests covering:
  make_candidate_manifest returns CandidateManifest, dry_lab_only always True,
  valid manifest passes validation, empty candidate_id fails, empty sequence
  fails, evidence_level 0 or 7 fails, empty scopes fails, uncertainty out of
  range fails, empty source_modules fails, dry_lab_only=False fails,
  invalid version fails, manifest_to_dict returns all fields, manifest_summary
  total correct, with_safety_flags correct, dry_lab_only=True, by_evidence_level
  correct, schema file exists.
- `docs/evidence/METRICS_CURRENT.md` — v0.6.0 I2 changelog. Test count: 3310.
- `tests/test_test_count_regression.py` — baseline updated to 3310.

Honest boundaries:
- Candidate manifests describe dry-lab candidates only — they are computational
  artifacts, not biological proof.
- Scores and uncertainty are pipeline outputs, not measured biological properties.
- The manifest schema is versioned (currently 1.0.0) and should be updated when
  fields are added or changed.
- Validation checks structural correctness only — it does not verify biological
  plausibility, safety, or efficacy.
- `dry_lab_only: true` is a const field — all manifests are inherently dry-lab
  and must never be presented as validated wet-lab candidates.

## v0.5.95 — Loop 95: Phase H H7 — Simulation-Result Confidence Interval Reporter ✓ (2026-07-09)

`ScoreCI` dataclass (9 fields: module_id, score_key, point_estimate, uncertainty,
ci_lower, ci_upper, ci_width, overlaps_with, dry_lab_only).
`compute_score_ci()` builds CIs from SimulationResult.scores[score_key] ± uncertainty,
returns None if score_key missing. `compare_cis()` pairwise checks overlap condition
(a_lo <= b_hi and b_lo <= a_hi), returns new list with overlaps_with populated
(no in-place mutation). `ci_report()` produces full report with n_results, cis list,
any_overlap flag, and dry_lab_only=True.
CLI (`openamp-foundry simulation-ci-report`) with `--results-json`, `--score-key`,
`--format text|json`. `make simulation-ci-report` target with demo invocation.
Raw scores without uncertainty ranges make it impossible to judge whether two
candidates are distinguishable. The CI reporter makes uncertainty explicit and
auditable.

Changes:
- `src/openamp_foundry/simulation/ci_reporter.py` (H7) — Core module with
  `ScoreCI` dataclass (9 fields), `compute_score_ci()` with CI bounds from
  score ± uncertainty, `compare_cis()` with pairwise overlap detection,
  `ci_report()` with n_results, any_overlap, and dry_lab_only=True.
- `src/openamp_foundry/simulation/__init__.py` — Exports `ScoreCI`,
  `compute_score_ci`, `compare_cis`, `ci_report`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-ci-report`
  subcommand with `--results-json`, `--score-key`, `--format` flags.
  Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_ci_report()` CLI handler with JSON parsing,
  SimulationResult deserialization, text and JSON output.
- `Makefile` — Added `simulation-ci-report` target with demo invocation
  using membrane_proxy + structure_proxy. Added to `.PHONY`.
- `tests/simulation/test_ci_reporter.py` — 16 tests covering: compute_score_ci
  returns correct bounds, ci_width = 2*uncertainty, missing key returns None,
  dry_lab_only always True, non-overlapping CIs empty overlaps_with,
  overlapping CIs populated overlaps_with, no in-place mutation, 0 results,
  n_results correct, dry_lab_only=True, any_overlap false/true, overlapping
  example, non-overlapping example.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.95 H7 changelog. Test count: 3217.
- `tests/test_test_count_regression.py` — baseline updated to 3217.

Honest boundaries:
- Confidence intervals are computed from SimulationResult.uncertainty, which
  is self-reported by each simulation module and not independently verified.
- Overlap detection is a mathematical condition: two CIs overlapping means
  the scores are not statistically distinguishable at the stated uncertainty
  level. It does not mean the modules are biologically correct or incorrect.
- A CI with no overlaps may still be biologically meaningless — precision
  without accuracy is not useful.
- The any_overlap flag is a descriptive summary, not a gate. Overlap does
  not invalidate results; it highlights them for human review.
- All CI reports are dry-lab only and must not be presented as biological proof.

## v0.5.99 — Loop 99: Phase I I1 — Artifact Versioning Policy ✓ (2026-07-09)

`docs/engineering/ARTIFACT_VERSIONING_POLICY.md` with structured versioning
policy covering scope (schemas, evidence certificates, candidate manifests,
provenance records, benchmark cards, model cards), version format
(MAJOR.MINOR.PATCH), breaking/non-breaking change definitions, deprecation
timeline (at least one minor version warning), schema `$id` policy, changelog
requirement, and three stability tiers (Tier 1 stable, Tier 2 experimental,
Tier 3 internal). Dry-lab-only statement included.

`src/openamp_foundry/versioning/` module with `ArtifactVersionInfo` dataclass
(7 fields), `STABILITY_TIERS` dict (3 tiers), `VERSIONED_ARTIFACTS` list
(6 entries: candidate, lab_result, run_manifest, external_review_packet,
safety_release_decision, simulation_result — all at v1.0.0; 5 stable,
1 experimental). `get_artifact_version()`, `list_versioned_artifacts()` with
tier filtering, `validate_version_format()` (regex MAJOR.MINOR.PATCH),
`artifact_version_summary()` with total/by_tier/stable_count/experimental_count/
dry_lab_only.

CLI (`openamp-foundry artifact-version`) with `--list`, `--show <name>`,
`--tier <stable|experimental|internal>`, `--format text|json`.
`make artifact-version` target.

19 tests. **3291 total.** Starts Phase I (interoperability and adoption)
— external users now have stability guarantees for schemas, evidence
certificates, and candidate manifests.

Changes:
- `docs/engineering/ARTIFACT_VERSIONING_POLICY.md` (I1) — Full versioning
  policy document with scope, SemVer, breaking/non-breaking rules,
  deprecation timeline, $id policy, changelog requirement, stability tiers,
  dry-lab-only statement.
- `src/openamp_foundry/versioning/__init__.py` (I1) — Package init,
  exports all versioning symbols.
- `src/openamp_foundry/versioning/artifact_version.py` (I1) — Core module
  with `STABILITY_TIERS` dict, `ArtifactVersionInfo` dataclass,
  `VERSIONED_ARTIFACTS` list (6 entries), `get_artifact_version()`,
  `list_versioned_artifacts()`, `validate_version_format()`,
  `artifact_version_summary()`.
- `src/openamp_foundry/cli/main.py` — Registered `artifact-version`
  subcommand with `--list`, `--show`, `--tier`, `--format` flags.
  Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_artifact_version()` CLI handler with text and JSON output,
  artifact lookup, tier filtering, and error handling.
- `Makefile` — Added `artifact-version` target. Added to `.PHONY`.
- `tests/versioning/__init__.py` — Empty package init.
- `tests/versioning/test_artifact_version.py` — 19 tests covering:
  at least 5 entries, all valid versions, valid stability tiers, no duplicate
  names, get known/unknown, list all/filtered, validate valid/invalid
  versions, summary dry_lab_only, summary total, stable/experimental counts,
  by_tier sum.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.99 I1 changelog. Test count: 3291.
- `tests/test_test_count_regression.py` — baseline updated to 3291.

Honest boundaries:
- Artifact versioning describes schema and format compatibility, not
  biological validity, safety, or efficacy.
- The version registry is manually maintained; entries must be updated when
  schemas change.
- `validate_version_format()` checks structural validity only — it does not
  enforce semantic version ordering or compatibility rules.
- Stability tiers are policy declarations, not machine-enforced guarantees.
  A Tier 1 artifact may still have undiscovered bugs or incompatibilities.
- All artifacts remain dry-lab hypotheses requiring wet-lab validation
  regardless of version number.

## v0.5.98 — Loop 98: Phase H H10 — Simulation-Evidence Packet Assembler ✓ (2026-07-09)

`SimulationEvidencePacket` dataclass (12 fields: module_id, result,
requested_scopes, claimed_evidence_level, baseline_beaten, deprecation_check,
scope_check, baseline_check, adapter_gate, effective_evidence_level,
all_checks_passed, failure_reasons, dry_lab_only).
`assemble_evidence_packet()` runs all Phase H sub-checks (deprecation, scope,
baseline, adapter gate) and assembles into a single auditable packet with
all_checks_passed (True only if not deprecation_check["is_blocked"],
scope_check["is_fully_covered"], not baseline_check["capped"], and
adapter_gate["passed"]), failure_reasons (human-readable list of what failed),
and effective_evidence_level (from baseline_check).
`evidence_packet_summary()` returns compact dict with module_id,
claimed_evidence_level, effective_evidence_level, all_checks_passed,
failure_reasons, dry_lab_only.
CLI (`openamp-foundry simulation-evidence-packet`) with `--module-id`,
`--result-json`, `--requested-scopes`, `--claimed-level`, `--baseline-beaten`,
`--format text|json`. `make simulation-evidence-packet` target.
This is the capstone of Phase H — it assembles all the individual simulation
discipline checks into a single auditable evidence packet showing exactly why
a simulation result is trustworthy (or not) enough to support a given evidence
level claim.

Changes:
- `src/openamp_foundry/simulation/evidence_packet.py` (H10) — Core module
  with `SimulationEvidencePacket` dataclass (12+ fields),
  `assemble_evidence_packet()` orchestrating all 4 sub-checks with failure
  aggregation, `evidence_packet_summary()` compact dict builder.
- `src/openamp_foundry/simulation/__init__.py` — Exports
  `SimulationEvidencePacket`, `assemble_evidence_packet`,
  `evidence_packet_summary`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-evidence-packet`
  subcommand with `--module-id`, `--result-json`, `--requested-scopes`,
  `--claimed-level`, `--baseline-beaten`, `--format` flags.
  Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_evidence_packet()` CLI handler with JSON parsing,
  SimulationResult deserialization, text and JSON output, module-id validation.
- `Makefile` — Added `simulation-evidence-packet` target with demo invocation
  using membrane_proxy + bacterial_binding + baseline_beaten=false.
  Added to `.PHONY`.
- `tests/simulation/test_evidence_packet.py` — 16+ tests covering: returns
  packet dataclass, all_checks_passed=true/false for every sub-check,
  failure_reasons empty/non-empty, effective_evidence_level capped,
  dry_lab_only always True, summary keys and values, deprecated module,
  adapter timeout, membrane_proxy passes with correct scope, scope fail.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.98 H10 changelog. Test count: 3271.
- `tests/test_test_count_regression.py` — baseline updated to 3271.

Honest boundaries:
- The evidence packet aggregates computational sub-checks only. It does not
  measure biological activity, safety, or real-world performance.
- `all_checks_passed=True` means all computational discipline checks passed,
  not that the simulation result is biologically meaningful.
- The adapter gate uses failure signals provided by the caller; an adapter that
  returns plausible-looking but biologically meaningless results will pass.
- Baseline beating is a necessary condition for evidence, not a sufficient one.
- Scope coverage is based on the module registry's declared scopes, which may
  be incomplete relative to actual capabilities.
- All evidence packets are dry-lab only and must not be presented as biological
  proof.

## v0.5.97 — Loop 97: Phase H H9 — Simulation-Scope Coverage Checker ✓ (2026-07-09)

`ScopeCoverageResult` dataclass (8 fields: module_id, requested_scopes,
module_scopes, covered, uncovered, coverage_fraction, is_fully_covered,
dry_lab_only). `check_scope_coverage()` looks up module in registry, computes
covered (intersection) and uncovered (requested scopes not in module scopes),
coverage_fraction = len(covered)/len(requested_scopes) if requested else 1.0.
`check_result_scope()` uses conservative intersection of registry scopes and
result.scope as effective module_scopes. `scope_coverage_report()` returns
full dict.
CLI (`openamp-foundry simulation-scope-check`) with `--module-id`,
`--requested-scopes`, `--format text|json`.
`make simulation-scope-check` target with demo invocation.
A simulation module may cover only some biological scopes. If a candidate is
evaluated for a scope the module does not cover, that result must be flagged
as out-of-scope rather than silently trusted.

Changes:
- `src/openamp_foundry/simulation/scope_checker.py` (H9) — Core module with
  `ScopeCoverageResult` dataclass (8 fields), `check_scope_coverage()` with
  registry lookup and set intersection, `check_result_scope()` with conservative
  intersection of registry and result scopes, `scope_coverage_report()` dict
  builder.
- `src/openamp_foundry/simulation/__init__.py` — Exports `ScopeCoverageResult`,
  `check_scope_coverage`, `check_result_scope`, `scope_coverage_report`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-scope-check`
  subcommand with `--module-id`, `--requested-scopes`, `--format` flags.
  Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_scope_check()` CLI handler with text and JSON output.
- `Makefile` — Added `simulation-scope-check` target. Added to `.PHONY`.
- `tests/simulation/test_scope_checker.py` — 17 tests covering: fully covered,
  partially covered, no scopes requested, unknown module, dry_lab_only always
  True, covered/uncovered lists correct, coverage_fraction half/full/zero,
  check_result_scope intersection, scope_coverage_report keys and dry_lab_only,
  membrane_proxy covers bacterial, membrane_proxy does not cover fungal, empty
  module scopes all uncovered.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.97 H9 changelog. Test count: 3255.
- `tests/test_test_count_regression.py` — baseline updated to 3255.

Honest boundaries:
- Scope coverage is based on the module registry's declared scopes, which may
  be incomplete or outdated relative to a module's actual capabilities.
- `check_result_scope` is conservative: it only trusts scopes that both the
  registry and the result agree on. This may undercount coverage if result
  metadata is sparse.
- A fully covered scope does not mean the simulation is accurate or biologically
  meaningful — only that the module claims to cover the requested scope.
- All outputs are dry-lab only and must not be presented as biological proof.

## v0.5.96 — Loop 96: Phase H H8 — Simulation-Module Deprecation Enforcer ✓ (2026-07-09)

`DeprecationCheckResult` dataclass (5 fields: module_id, status, is_blocked,
block_reason, dry_lab_only). `BLOCKED_STATUSES = {"deprecated", "unavailable"}`.
`check_module_deprecation()` looks up module in registry: not-found returns
is_blocked=True status="unknown"; deprecated/unavailable returns is_blocked=True
with reason; active/experimental returns is_blocked=False.
`enforce_deprecation()` filters list[SimulationResult] to only non-blocked
modules, returns dict with total_input/passed/blocked/blocked_modules/
passed_results/checks/dry_lab_only. `run_deprecation_check_batch()` bulk-checks
module_ids with total/blocked/allowed/any_blocked/results/dry_lab_only.
CLI (`openamp-foundry simulation-deprecation-check`) with `--module-ids`,
`--format text|json`. `make simulation-deprecation-check` target with demo
invocation. Deprecated simulation modules must not be used in production
scoring — the enforcer prevents stale or unreliable modules from tainting
evidence packets.

Changes:
- `src/openamp_foundry/simulation/deprecation_enforcer.py` (H8) — Core
  module with `DeprecationCheckResult` dataclass, `check_module_deprecation()`,
  `enforce_deprecation()`, `run_deprecation_check_batch()`.
- `src/openamp_foundry/simulation/__init__.py` — Exports `BLOCKED_STATUSES`,
  `DeprecationCheckResult`, `check_module_deprecation`, `enforce_deprecation`,
  `run_deprecation_check_batch`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-deprecation-check`
  subcommand with `--module-ids`, `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_deprecation_check()` CLI handler.
- `Makefile` — Added `simulation-deprecation-check` target. Added to `.PHONY`.
- `tests/simulation/test_deprecation_enforcer.py` — 21 tests covering: active
  module not blocked, deprecated/unavailable blocked, unknown blocked with
  status="unknown", dry_lab_only always True, enforce_deprecation filters
  results, passed count, blocked_modules sorted/deduplicated, dry_lab_only flag,
  all-allowed blocked=0, batch total/any_blocked/not blocked.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.96 H8 changelog. Test count: 3238.
- `tests/test_test_count_regression.py` — baseline updated to 3238.

Honest boundaries:
- Deprecation checks are based on registry status, not biological validity.
  A module may be "active" in the registry but still produce unreliable scores.
- Blocking removes results from evidence packets but does not invalidate them
  as research data — blocked results may still be useful for internal analysis.
- The enforcer does not evaluate whether a module's underlying science is sound;
  it enforces the pipeline's declared module lifecycle policy.
- All outputs are dry-lab only and must not be presented as biological proof.

## v0.5.94 — Loop 94: Phase H H6 — Simulation-Ensemble Agreement Checker ✓ (2026-07-09)

`EnsembleAgreementResult` dataclass (9 fields: sequence, modules_checked,
agreement_level, agreement_description, mean_score, score_range, scores_by_module,
threshold, dry_lab_only). `AGREEMENT_LEVELS` dict (5 levels: strong/moderate/
weak/conflict/insufficient). `check_ensemble_agreement()` extracts score_key from
each SimulationResult's scores dict, computes score_range, classifies agreement:
strong (≥3 modules within threshold), moderate (2 modules within threshold),
weak (1 module), conflict (beyond threshold), or insufficient (no results).
`run_ensemble_check_batch()` aggregates multiple calls with counts and any_conflict
flag. CLI (`openamp-foundry simulation-ensemble-check`) with `--sequence`,
`--results-json`, `--score-key`, `--threshold`, `--format text|json`.
`make simulation-ensemble-check` target with demo invocation. When multiple
simulation modules independently agree on a candidate, that agreement is stronger
evidence than a single module alone. The ensemble checker makes this agreement
explicit and auditable.

Changes:
- `src/openamp_foundry/simulation/ensemble_checker.py` (H6) — Core module with
  `AGREEMENT_LEVELS` dict (5 entries), `EnsembleAgreementResult` dataclass
  (9 fields), `check_ensemble_agreement()` with 5-path classification logic,
  `run_ensemble_check_batch()` with per-level counts and any_conflict flag.
- `src/openamp_foundry/simulation/__init__.py` — Exports `AGREEMENT_LEVELS`,
  `EnsembleAgreementResult`, `check_ensemble_agreement`, `run_ensemble_check_batch`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-ensemble-check`
  subcommand with `--sequence`, `--results-json`, `--score-key`, `--threshold`,
  `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_ensemble_check()` CLI handler with JSON parsing,
  SimulationResult deserialization, text and JSON output.
- `Makefile` — Added `simulation-ensemble-check` target with demo invocation
  using AKLWKR + two module results. Added to `.PHONY`.
- `tests/simulation/test_ensemble_checker.py` — 20 tests covering: empty
  results, 1 result weak, 2 results moderate, 3+ results strong, conflict,
  missing score_key skipped, mean_score, score_range, dry_lab_only always True,
  scores_by_module, threshold parameter, modules_checked, agreement_description,
  to_dict fields, batch counts, batch any_conflict, batch dry_lab_only.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.94 H6 changelog. Test count: 3201.
- `tests/test_test_count_regression.py` — baseline updated to 3201.

Honest boundaries:
- Agreement is a computational measure: when N modules agree within threshold,
  it means their scores are numerically close, not that they are biologically
  correct.
- The threshold is a user-parameterized float; different thresholds produce
  different agreement levels for the same data.
- A "strong" agreement from three weak modules is still weak evidence. The
  checker measures consistency, not quality.
- Missing score_key entries are silently skipped — the checker does not validate
  that the score_key is meaningful or calibrated.
- The dry_lab_only flag is a safety constraint, not a technical guarantee.
- Ensemble agreement does not constitute biological proof. All simulation
  outputs remain dry-lab hypotheses requiring wet-lab validation.

## v0.5.93 — Loop 93: Phase H H5 — Simulation-Result Provenance Chain ✓ (2026-07-09)

`SimulationProvenanceRecord` dataclass with run_id, module_id, module_version,
timestamp_utc, input_hash (SHA-256 of input sequence), result_hash (SHA-256 of
sorted scores dict), calibration_set, notes, and dry_lab_only.
`make_provenance_record()` computes hashes deterministically (sort_keys=True for
result_hash). `validate_provenance_record()` checks non-empty fields, ISO 8601
timestamp, 64-char hex hashes, and dry_lab_only=True. `provenance_summary()`
aggregates total, unique modules, run_ids, and dry_lab_only flag. Every simulation
result carries a traceable provenance chain so results can be audited, reproduced,
or invalidated later without relying on memory.

Changes:
- `src/openamp_foundry/simulation/provenance.py` (H5) — Core module with
  `SimulationProvenanceRecord` dataclass (9 fields), `make_provenance_record()`
  computing SHA-256 input_hash and sorted result_hash, `validate_provenance_record()`
  with 7 integrity checks, `provenance_summary()` with aggregation.
- `src/openamp_foundry/simulation/__init__.py` — Exports `SimulationProvenanceRecord`,
  `make_provenance_record`, `validate_provenance_record`, `provenance_summary`.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-provenance` subcommand
  with `--run-id`, `--module-id`, `--module-version`, `--timestamp-utc`,
  `--input-sequence`, `--scores-json`, `--calibration-set`, `--format` flags.
  Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added `_run_simulation_provenance()`
  CLI handler with JSON parsing, validation, text and JSON output, exit code 3 on
  validation error.
- `Makefile` — Added `simulation-provenance` target with demo invocation using
  `test-run-001`. Added to `.PHONY`.
- `tests/simulation/test_provenance.py` — 19 tests covering: record creation,
  deterministic hashes, dry_lab_only always True, all validation checks
  (empty fields, bad timestamp, wrong-length hash, dry_lab_only=False),
  provenance_summary with 0 and N records.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.93 H5 changelog. Test count: 3181.
- `tests/test_test_count_regression.py` — baseline updated to 3181.

Honest boundaries:
- SHA-256 hashes prove content integrity, not biological activity.
- The provenance record attests that a simulation ran, not that the result
  is biologically meaningful.
- `input_hash` covers the input sequence only; other input parameters
  (e.g., engine settings) are not hashed.
- `result_hash` uses JSON serialisation with sort_keys=True; any future
  change to the serialisation format will change the hash for identical data.
- Timestamps are self-reported by the caller and not independently verified.
- Provenance records are dry-lab only and must not be presented as
  biological proof.

## v0.5.92 — Loop 92: Phase H H4 — Fail-Closed Adapter Integration Tests ✓ (2026-07-09)

`FAIL_CLOSED_REASONS` dict (6 keys) enumerates known adapter failure reasons.
`AdapterGateResult` dataclass with module_id, passed, failure_reason, failure_detail,
dry_lab_only. `evaluate_adapter_gate()` fail-closed: returns passed=False on ANY
failure signal with strict priority ordering (timeout > connection_refused >
invalid_response > schema_violation > module_unavailable > baseline_not_beaten).
`run_adapter_gate_batch()` aggregates multiple adapter calls with total/passed/failed/
any_failed/results/dry_lab_only. Avoids hidden external failures — when the adapter
to an external simulation service is down or misbehaves, the pipeline must fail
loudly rather than silently passing garbage through.

Changes:
- `src/openamp_foundry/simulation/adapter_gate.py` (H4) — Core module with
  `FAIL_CLOSED_REASONS` dict (6 entries), `AdapterGateResult` dataclass (5 fields:
  module_id, passed, failure_reason, failure_detail, dry_lab_only),
  `evaluate_adapter_gate()` with 7-path priority logic,
  `run_adapter_gate_batch()` aggregating results with counts and any_failed flag.
- `src/openamp_foundry/simulation/__init__.py` — Exports `AdapterGateResult`,
  `FAIL_CLOSED_REASONS`, `evaluate_adapter_gate`, `run_adapter_gate_batch`.
- `src/openamp_foundry/cli/main.py` — Registered `adapter-gate-check` subcommand
  with `--module-id`, `--timeout`, `--connection-refused`, `--schema-errors`,
  `--module-unavailable`, `--baseline-beaten`, `--format` flags. Added import
  and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added `_run_adapter_gate_check()`
  CLI handler with text and JSON output, JSON parsing for schema errors,
  exit code 3 on failure.
- `Makefile` — Added `adapter-gate-check` target with default `membrane_proxy`
  check. Added to `.PHONY`.
- `tests/simulation/test_adapter_gate.py` — 20 tests covering: all 6 failure
  reasons, all-clear pass, dry_lab_only always True, priority ordering (timeout
  beats connection_refused, connection_refused beats result=None, schema_errors
  beat module_unavailable), baseline_beaten=True passes, baseline_beaten=None
  does not trigger, batch counts, batch any_failed, batch dry_lab_only.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.92 H4 changelog. Test count: 3161.
- `tests/test_test_count_regression.py` — baseline updated to 3161.

Honest boundaries:
- The adapter gate checks for known failure signals only. An adapter that
  returns plausible-looking but biologically meaningless results will pass.
- Failure detection depends on the caller correctly setting the failure
  flags. An adapter that silently hangs (neither timeout nor connection
  refused) may not be caught.
- Schema validation errors detect structural contract violations, not
  biological correctness. A schema-valid response can still be biologically
  meaningless.
- The `baseline_not_beaten` check requires the caller to run the baseline
  comparison externally; the gate does not compute it.
- All adapter gate checks are dry-lab only and must not be presented as
  biological proof.

## v0.5.91 — Loop 91: Phase H H3 — Per-Module Cheapest-Baseline Declaration ✓ (2026-07-09)

`BaselineDeclaration` dataclass with module_id, module_name, baseline_description,
baseline_type, evidence_level_ceiling, and notes. `BASELINE_DECLARATIONS` list
(4 entries: membrane_proxy, structure_proxy, dummy_membrane_proxy,
external_adapter_placeholder). `get_baseline_declaration()` and
`list_baseline_declarations()` for lookup. `check_baseline_requirement()` caps
effective_evidence_level to ceiling when baseline not beaten.
`validate_baseline_declarations()` checks module_id, baseline_description,
baseline_type, evidence_level_ceiling, and duplicate detection. Forces honest
enemy comparison — every simulation module must declare the simplest baseline
it must beat, making it easy to detect "simulation theater."

Changes:
- `src/openamp_foundry/simulation/baseline_registry.py` (H3) — Core module with
  `BaselineDeclaration` dataclass (6 fields), `BASELINE_DECLARATIONS` list
  (4 entries), `get_baseline_declaration()`, `list_baseline_declarations()`,
  `check_baseline_requirement()` with ceiling logic,
  `validate_baseline_declarations()` with 5 checks.
- `src/openamp_foundry/simulation/__init__.py` — Exports all baseline registry
  symbols.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-baseline-check`
  subcommand with `--module-id`, `--claimed-level`, `--baseline-beaten`,
  `--format` flags. Added import and dispatch.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_baseline_check()` CLI handler with text and JSON output,
  error handling for unknown module IDs, exit code 3 if capped.
- `Makefile` — Added `simulation-baseline-check` target with default
  `membrane_proxy` check. Added to `.PHONY`.
- `tests/simulation/test_baseline_registry.py` — 16 tests covering: at least
  4 entries, validation passes, get/list lookup, required field presence,
  baseline type validity, check logic (beaten/not beaten/capped/uncapped),
  dry_lab_only always True, unknown module handling, duplicate detection,
  invalid baseline type detection.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.91 H3 changelog. Test count: 3141.
- `tests/test_test_count_regression.py` — baseline updated to 3141.

Honest boundaries:
- Baseline declarations are self-reported by module maintainers and must be
  manually kept in sync with the module registry.
- `check_baseline_requirement()` caps evidence levels based on declared
  ceilings, not on independent biological validation.
- A module that beats its cheapest baseline may still produce biologically
  meaningless results — beating a heuristic baseline is a necessary condition
  for evidence, not a sufficient one.
- Baseline types are categorical labels; a "heuristic" baseline and a "length"
  baseline are not directly comparable in difficulty.
- The evidence_level_ceiling is a policy rule, not a biological guarantee.
  Higher ceilings should be justified by actual benchmark performance.
- All baseline comparisons are dry-lab only and must not be presented as
  biological proof.

## v0.5.90 — Loop 90: Phase H H2 — Simulation-Result Schema and Validator ✓ (2026-07-09)

`schemas/simulation_result.schema.json` (Draft 2020-12) validates SimulationResult
outputs with uncertainty 0.0–1.0 range and all required fields.
`validate_simulation_result()` checks module, version, scope, scores, uncertainty,
validated_against, notes. Strict mode rejects dummy/stub modules, uncertainty=1.0,
and empty validated_against. `validate_simulation_result_batch()` aggregates
results with counts and `any_invalid` flag. CLI (`openamp-foundry
validate-simulation-result`) with `--results-json`, `--strict`, `--out-json`.
Prevents undocumented proxy output — every SimulationResult is now
machine-checkable against a formal JSON schema.

Changes:
- `schemas/simulation_result.schema.json` (H2) — JSON Schema Draft 2020-12
  for SimulationResult outputs. Required fields: module, version, scope, scores,
  uncertainty (min 0.0, max 1.0), calibration_set (string or null),
  validated_against, notes. Optional `dry_lab_context` const "dry-lab-only".
- `src/openamp_foundry/simulation/result_validator.py` (H2) —
  `validate_simulation_result()` with 6 always-checked rules and 3 strict-mode
  rules. `validate_simulation_result_batch()` with checked/valid/invalid/
  errors_by_module/any_invalid/dry_lab_only keys.
- `src/openamp_foundry/simulation/__init__.py` — Exports
  `validate_simulation_result`, `validate_simulation_result_batch`.
- `src/openamp_foundry/cli/main.py` — Registered `validate-simulation-result`
  subcommand with `--results-json`, `--strict`, `--out-json` flags.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_validate_simulation_result()` CLI handler with JSON loading,
  SimulationResult deserialization, batch validation, and output.
- `Makefile` — Added `validate-simulation-result-schema` target to `.PHONY`.
  Fixed duplicate `.PHONY` entry for `simulation-registry`.
- `tests/simulation/test_result_validator.py` — 19 tests covering: valid
  result, empty module/version, uncertainty bounds, strict mode rules,
  batch validation, and non-finite scores.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.90 H2 changelog. Test count: 3125.
- `tests/test_test_count_regression.py` — baseline updated to 3125.

Honest boundaries:
- Schema validation checks structural correctness, not biological truth.
- A schema-valid SimulationResult may still be biologically meaningless.
- Uncertainties are self-reported by simulation modules and not independently
  verified by this validation layer.
- Strict mode is an additional policy layer; it does not guarantee that a
  passing result is biologically meaningful.
- All simulation results are dry-lab only and must not be presented as
  biological proof.

## v0.5.89 — Loop 89: Phase H H1 — Simulation Module Registry ✓ (2026-07-09)

`SIMULATION_MODULE_REGISTRY` with 4 entries (membrane_proxy, structure_proxy,
dummy_membrane_proxy, external_adapter_placeholder). `SimulationModuleEntry`
dataclass tracks module_id, name, description, status, evidence_level,
baseline_comparison, scope, maintainer, and notes. Lookup functions:
`get_module_entry()`, `list_module_entries()` with status/min_evidence
filtering, `get_active_modules()`, `registry_summary()` with
total/by_status/by_evidence_level/active_module_ids keys.
`validate_registry()` checks module_id, name, baseline_comparison,
evidence_level 1-6, valid status, duplicate detection.
CLI (`openamp-foundry simulation-registry`) with `--list`, `--show`,
`--status`, `--min-evidence`, `--format text|json`.
Schema (`schemas/simulation_module_registry.schema.json`).
`make simulation-registry` target. 28 tests. 3106 total.
Starts Phase H (virtual assay discipline).

Changes:
- `src/openamp_foundry/simulation/module_registry.py` (H1) — Core module with
  `SimulationModuleStatus` literal type, `SimulationModuleEntry` dataclass
  (9 fields), `SIMULATION_MODULE_REGISTRY` list (4 entries),
  `get_module_entry()`, `list_module_entries()`, `get_active_modules()`,
  `registry_summary()` with aggregation, `validate_registry()` with 6 checks.
  Imports `PROOF_LADDER_LEVELS` from `evidence/synthetic_result_policy.py`.
- `schemas/simulation_module_registry.schema.json` (H1) — JSON Schema Draft
  2020-12 for the registry_summary() output. Validates total, by_status
  (all 4 status keys), by_evidence_level, active_module_ids.
- `src/openamp_foundry/simulation/__init__.py` — Exports all module registry
  symbols.
- `src/openamp_foundry/cli/main.py` — Registered `simulation-registry`
  subcommand with `--list`, `--show`, `--status`, `--min-evidence`,
  `--format` flags.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_simulation_registry()` CLI handler with text and JSON output,
  per-module details, status/evidence filtering, and validation.
- `Makefile` — Added `simulation-registry` target with `--list` default.
  Added to `.PHONY`.
- `tests/simulation/test_module_registry.py` — 28 tests covering: registry
  size ≥ 4, all entries pass validation, required field presence, evidence
  level range 1-6, valid status values, get_module_entry known/unknown,
  list_module_entries no filter/status filter/min_evidence filter,
  get_active_modules returns only active, registry_summary keys and totals,
  validate_registry detection of empty fields, invalid level, invalid
  status, duplicate ids, PROOF_LADDER_LEVELS completeness.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.89 H1 changelog. Test count: 3106.
- `tests/test_test_count_regression.py` — baseline updated to 3106.

Honest boundaries:
- The registry lists module status and evidence level for informational
  purposes only. It does not measure biological activity, safety, or
  real-world performance.
- Registry validation checks structural correctness, not scientific validity.
  A valid entry may still produce biologically meaningless results.
- The PROOF_LADDER_LEVELS mapping is a claim-level taxonomy. An evidence_level
  of 2 ("virtual-assay support") means the module supports computational
  exploration — it does not constitute biological proof.
- The registry is dry-lab only. All module entries carry dry-lab caveats
  regardless of their status or evidence_level.
- "active" status means the module is available for use, not that it has
  been biologically validated.

## v0.5.88 — Loop 88: Phase G G10 — Recalibration Rollback Plan ✓ (2026-07-09)

`build_rollback_plan()` produces a structured `RollbackPlan` with 5 rollback
triggers (RT-01 through RT-05) and 6 default rollback steps covering halt,
document, restore, verify, root-cause, and log. `RollbackPlan` dataclass with
plan_id, version, triggered_by, steps, notes, dry_lab_only, and to_dict().
`RollbackStep` dataclass with step_number, action, responsible, detail, and
dry_lab_only. CLI (`openamp-foundry calibration-rollback-plan`).
JSON + Markdown output. Schema (`schemas/calibration_rollback_plan.schema.json`).
`make calibration-rollback-plan` target. 15 tests. 3078 total.
This completes Phase G (G1-G10 — calibration and active-learning rigor).

Changes:
- `src/openamp_foundry/calibration/rollback_plan.py` (G10) — Core module with
  `ROLLBACK_TRIGGERS` list (5 triggers: RT-01 through RT-05), `RollbackStep`
  dataclass (5 fields: step_number, action, responsible, detail, dry_lab_only),
  `RollbackPlan` dataclass (6 fields: plan_id, version, triggered_by, steps,
  notes, dry_lab_only), `DEFAULT_ROLLBACK_STEPS` list (6 steps),
  `build_rollback_plan()` with trigger ID validation, `write_rollback_plan_json()`
  and `write_rollback_plan_markdown()` for structured output.
- `schemas/calibration_rollback_plan.schema.json` (G10) — JSON Schema Draft
  2020-12 for the rollback plan. Validates all 6 required fields including
  plan_id, version, triggered_by with RT-NN pattern, steps with ordered
  actions, and dry_lab_only const=true.
- `src/openamp_foundry/calibration/__init__.py` — Exports all rollback plan
  symbols.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_calibration_rollback_plan()` CLI handler with `--plan-id`, `--version`,
  `--triggered-by`, `--notes`, `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `calibration-rollback-plan`
  subcommand with all argument flags and dispatch to handler.
- `Makefile` — Added `calibration-rollback-plan` target with default example
  writing to `/tmp/rollback_plan.json` and `/tmp/rollback_plan.md`.
  Added to `.PHONY`.
- `tests/calibration/test_rollback_plan.py` — 18 tests covering: valid triggers
  pass, unknown trigger raises ValueError, triggered_by stored correctly, steps
  include all default steps, extra_steps appended correctly, dry_lab_only always
  True, ROLLBACK_TRIGGERS count and required fields, plan_id stored correctly,
  version stored correctly, to_dict has required keys, notes stored correctly,
  default steps have correct responsible parties, JSON writer, Markdown writer.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.88 G10 changelog. Test count: 3081.
- `tests/test_test_count_regression.py` — baseline updated to 3081.

Honest boundaries:
- The rollback plan restores weight configurations only. It does not undo
  candidate selections, synthesis decisions, or code-level regressions.
- Rollback triggers are detection rules, not guarantees. A regression that
  does not match any trigger may still be harmful.
- All rollback steps require human review (steps 2, 5, 6 explicitly).
  Automated rollback without documented human oversight is not permitted.
- The plan is a procedural framework. Actual rollback execution may require
  additional context-specific steps.
- Dry-lab only. Rollback affects computational scoring, not biological
  activity, safety, or real-world outcomes.

## v0.5.87 — Loop 87: Phase G G9 — Calibration Decision Review Checklist ✓ (2026-07-09)

`build_checklist()` produces a structured `CalibrationDecisionChecklist` with 12
checklist items (10 required) covering data quality, statistical validity, safety
consistency, approval, and documentation. Each item has an id, category, question,
rationale, and required flag. `CalibrationDecisionChecklist` dataclass tracks
responses, notes, overall_pass, and missing_required. JSON + Markdown output.
Schema (`schemas/calibration_decision_checklist.schema.json`).
CLI (`openamp-foundry calibration-decision-checklist`).
`make calibration-decision-checklist` target. 14 tests. 3063 total.
Makes human review structured and auditable.

Changes:
- `src/openamp_foundry/calibration/decision_checklist.py` (G9) — Core module with
  `CHECKLIST_ITEMS` list (12 items), `CalibrationDecisionChecklist` dataclass
  (8 fields: checklist_id, date, reviewer, responses, notes, overall_pass,
  missing_required, dry_lab_only), `build_checklist()` applying response validation
  and missing-required analysis, `write_checklist_json()` and
  `write_checklist_markdown()` for structured output.
- `schemas/calibration_decision_checklist.schema.json` (G9) — JSON Schema Draft
  2020-12 for the decision checklist. Validates all 8 required fields including
  date pattern, responses object, and dry_lab_only const=true.
- `src/openamp_foundry/calibration/__init__.py` — Exports all decision checklist
  symbols.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_calibration_decision_checklist()` CLI handler with `--checklist-id`,
  `--date`, `--reviewer`, `--responses-json`, `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `calibration-decision-checklist`
  subcommand with all argument flags and dispatch to handler.
- `Makefile` — Added `calibration-decision-checklist` target with default example
  data writing to `/tmp/checklist_output.json` and `/tmp/checklist_output.md`.
  Added to `.PHONY`.
- `tests/calibration/test_decision_checklist.py` — 14 tests covering: all required
  pass → overall_pass=True, missing required → overall_pass=False, missing_required
  list correct, unknown response id raises ValueError, dry_lab_only always True,
  notes stored correctly, checklist_id stored correctly, reviewer stored correctly,
  date stored correctly, CHECKLIST_ITEMS minimum count, required items have
  required=True attribute, all items have required fields, JSON writer, Markdown
  writer with table and icons.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.87 G9 changelog. Test count: 3063.
- `tests/test_test_count_regression.py` — baseline updated to 3063.

Honest boundaries:
- The checklist validates structured human-review completion, not biological
  correctness. A passing checklist does not confirm biological activity or safety.
- Required items are policy-defined. Missing or false required items block the
  overall_pass, but a pass does not guarantee that human review was thorough.
- All calibration decisions require qualified human review regardless of checklist
  results.
- The dry_lab_only=True constraint is an attestation, not a technical proof.

## v0.5.86 — Loop 86: Phase G G8 — Synthetic-Result Policy (Anti-Overclaim) ✓ (2026-07-09)

`check_synthetic_result_policy()` and `run_policy_batch()` enforce that synthetic/
simulation results cannot raise the proof-ladder level of a candidate. Levels 4+
require wet-lab evidence; synthetic or unknown sources are blocked for such proposals.
CLI (`openamp-foundry synthetic-result-policy-check`). Schema
(`schemas/synthetic_result_policy_check.schema.json`). `make synthetic-result-policy-check`
target. 27 tests. 3049 total. Anti-overclaim safeguard.

## v0.5.86 — Loop 86: Phase G G8 — Synthetic Result Policy — Anti-Overclaim ✓ (2026-07-09)

`check_synthetic_result_policy()` enforces that synthetic/simulation outputs cannot
raise a candidate's proof-ladder level. Simulation outputs are anti-overclaim —
they must not be used as evidence to move a candidate up the proof ladder.

Changes:
- `src/openamp_foundry/evidence/synthetic_result_policy.py` (G8) — Core module with
  `PROOF_LADDER_LEVELS` dictionary (1–6 mapping to descriptions),
  `SyntheticResultPolicyCheck` dataclass (8 fields: candidate_id, current_level,
  proposed_level, evidence_source, policy_pass, violation, recommendation,
  dry_lab_only), `check_synthetic_result_policy()` applying multi-tier rules
  (synthetic cannot raise, synthetic cannot lower, levels 4+ require wet-lab
  evidence, invalid level raises ValueError), `run_policy_batch()` aggregating
  results with summary counts and any_violation flag,
  `write_policy_check_json()` and `write_policy_check_markdown()` for output.
- `schemas/synthetic_result_policy_check.schema.json` (G8) — JSON Schema Draft 07
  for single or batch policy check results. Validates all 8 required fields
  including evidence_source enum constraint and dry_lab_only const=true.
- `src/openamp_foundry/evidence/__init__.py` — Exports all synthetic result policy
  symbols.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_synthetic_result_policy_check()` CLI handler with `--proposals-json`,
  `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `synthetic-result-policy-check`
  subcommand with all argument flags and dispatch to handler.
- `Makefile` — Added `synthetic-result-policy-check` target with default example
  data writing to `/tmp/srp_output.json` and `/tmp/srp_output.md`. Added to
  `.PHONY`.
- `tests/evidence/test_synthetic_result_policy.py` — 27 tests covering: synthetic
  raising level, synthetic maintaining level, synthetic lowering level, lab raising
  level, literature raising level, proposed_level > 3 with synthetic/unknown source
  violation, proposed_level > 3 with lab/literature pass, invalid current_level,
  invalid proposed_level, unknown source normalization, unknown source + level 4
  violation, dry_lab_only always True, run_policy_batch summary counts, all-pass
  batch, any_violation flag, to_dict output, PROOF_LADDER_LEVELS completeness,
  JSON writer (single + batch), Markdown writer (single + batch), recommendation
  non-empty for violation, recommendation for pass, empty batch list.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.86 G8 changelog. Test count: 3049.
- `tests/test_test_count_regression.py` — baseline updated to 3049.

Honest boundaries:
- This policy check validates evidence-source discipline, not biological truth.
  A PASS does not confirm biological activity or safety.
- Synthetic evidence can still be useful for negative-result documentation and
  exploratory research — the policy restricts proof-ladder movement, not usage.
- Level 4+ wet-lab evidence requirement is a policy rule, not a biological
  guarantee. Wet-lab evidence can be wrong, inconclusive, or non-reproducible.
- The evidence_source classification relies on the submitter's honest labeling.
  A "lab" source may still be noisy or erroneous.
- All proof-ladder determinations require qualified human review regardless of
  policy check results.

## v0.5.85 — Loop 85: Phase G G7 — Result-Quality Flag Propagation into Calibration Engine ✓ (2026-07-09)

`assess_result_quality()` and `filter_results_for_calibration()` propagate
result-quality flags into the calibration engine. Low-quality outcomes cannot
drive updates — garbage results must not update the scoring model.

Changes:
- `src/openamp_foundry/calibration/result_quality.py` (G7) — Core module with
  `QUALITY_FLAGS` dictionary (8 standard flags), `EXCLUDED_FLAGS` set
  (contamination, assay_interference), `ResultQualityReport` dataclass (7 fields:
  candidate_id, flags, quality_level, can_drive_update, propagation_action,
  explanation, dry_lab_only), `assess_result_quality()` applying multi-tier rules
  (excluded flags → excluded, 2+ minor flags → low/excluded, 1 flag → acceptable,
  0 flags → high), `filter_results_for_calibration()` grouping results into
  included/included_with_caution/excluded with summary counts,
  `write_result_quality_json()` and `write_result_quality_markdown()` for output.
- `schemas/result_quality_report.schema.json` (G7) — JSON Schema Draft 07 for
  per-candidate or aggregate result quality reports. Validates all 7 required
  fields including flag enum constraint and dry_lab_only const=true.
- `src/openamp_foundry/calibration/__init__.py` — Exports all result-quality
  symbols.
- `src/openamp_foundry/cli/commands/reports.py` — Added `_run_result_quality_filter()`
  CLI handler with `--results-json`, `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `result-quality-filter` subcommand
  with all argument flags and dispatch to handler.
- `Makefile` — Added `result-quality-filter` target with default example data writing
  to `/tmp/rq_output.json` and `/tmp/rq_output.md`. Added to `.PHONY`.
- `tests/calibration/test_result_quality.py` — 27 tests covering: high quality (no
  flags), contamination excluded, assay_interference excluded, 2 minor flags excluded
  (low quality), 1 minor flag include_with_caution, can_drive_update True/False for
  all quality levels, dry_lab_only always True, unknown flag raises ValueError,
  explanation non-empty, to_dict output, contamination+other flags still excluded,
  assay_interference+other flags still excluded, filter_results_for_calibration
  empty/summary counts/per-action grouping/can_drive_update_count, missing flags
  handling, EXCLUDED_FLAGS set, QUALITY_FLAGS descriptions and count.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.85 G7 changelog. Test count: 3022.
- `tests/test_test_count_regression.py` — baseline updated to 3022.

Honest boundaries:
- Quality assessment is a computational filter on structural and metadata criteria.
  A "high quality" result does not confirm biological activity.
- Flag-based classification uses a pre-defined rule set. Edge cases (e.g.,
  borderline_threshold with ambiguous_activity) are treated the same as any
  other 2-flag combination — excluded for caution.
- Excluded results may still contain useful scientific information and should
  remain available for expert review.
- The `dry_lab_only=True` constraint is an attestation, not a technical proof.
- All calibration decisions require qualified human review regardless of
  result quality assessment.

## v0.5.84 — Loop 84: Phase G G6 — Calibration-Overfit Warning for Small Cohorts ✓ (2026-07-09)

`check_cohort_overfit_risk()` and `run_overfit_check()` flag when a calibration
cohort is too small relative to model parameters. Prevents false learning from
under-powered cohorts. Warns at three severity levels (critical/warning/caution)
with human-readable messages and actionable recommendations.

Changes:
- `src/openamp_foundry/calibration/overfit_warning.py` (G6) —
  `check_cohort_overfit_risk()` assesses a single cohort's overfit risk from
  cohort_size, model_params, n_features, and min_recommended threshold. Returns
  warning_level (none/caution/warning/critical), ratio, message, and
  recommendation. `run_overfit_check()` accepts a list of cohort sizes and
  aggregates per-cohort results with worst_level, any_critical, any_warning flags.
  `write_overfit_check_json()` and `write_overfit_check_markdown()` produce
  structured output.
- `schemas/calibration_overfit_check.schema.json` (G6) — JSON Schema Draft
  2020-12 for the overfit check report. Validates per_cohort array, worst_level,
  any_critical, any_warning, recommendation, dry_lab_only constraint.
- `src/openamp_foundry/calibration/__init__.py` — Exports
  `check_cohort_overfit_risk`, `run_overfit_check`, `write_overfit_check_json`,
  `write_overfit_check_markdown`.
- `src/openamp_foundry/cli/commands/reports.py` — Added
  `_run_calibration_overfit_check()` CLI handler with `--cohort-sizes`,
  `--model-params`, `--n-features`, `--min-recommended`, `--out-json`,
  `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `calibration-overfit-check`
  subcommand with all argument flags and dispatch to handler.
- `Makefile` — Added `calibration-overfit-check` target with default params
  writing to `/tmp/overfit_check.json` and `/tmp/overfit_check.md`.
- `tests/calibration/test_overfit_warning.py` — 21 tests covering: critical
  threshold (<10), warning threshold (size < min_recommended AND ratio < 3.0),
  caution (size < min_recommended OR ratio < 5.0), none level, run_overfit_check
  mixed severity/all-none/all-critical, ratio calculation, message non-empty,
  dry_lab_only=True everywhere, worst_level logic, any_critical/any_warning
  flags, empty cohort list, single-cohort matching, ratio zero-division edge,
  JSON writer, Markdown writer.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.84 G6 changelog. Test count: 2995.
- `tests/test_test_count_regression.py` — baseline updated to 2995.

Honest boundaries:
- This check evaluates **statistical overfit risk** only. A passing check does
  not confirm biological validity, safety, or real-world performance.
- Small cohorts can produce spurious correlations that appear significant in
  dry-lab benchmarks. The warning is a computational safeguard, not a
  biological guarantee.
- The severity thresholds (min_recommended=30, ratio<3.0 for warning, ratio<5.0
  for caution) are heuristic rules of thumb. Specific domains may require
  stricter or looser thresholds.
- All calibration decisions require qualified human review regardless of
  overfit check results.

## v0.5.83 — Loop 83: Phase G G5 — Batch-2 Selection Rationale Report ✓ (2026-07-09)

CLI (`openamp-foundry batch-rationale`) that generates a synthetic candidate pool,
runs the batch-2 selector with configurable weights, and produces a per-candidate
rationale report classifying each selected candidate into exploit / explore /
diversity / combined roles. Report includes weight configuration, role breakdown
summary, per-candidate contribution detail (ensemble×weight, uncertainty×weight,
diversity×weight), safety gate impact, and caveats. Enables reviewers to
understand why each candidate was selected in terms of the three active-learning
roles.

Changes:
- `src/openamp_foundry/active_learning/batch_rationale.py` (G5) —
  `build_batch_rationale_report()` generates a synthetic pool, runs
  `select_batch_2` with configurable weights, classifies each selected candidate
  into exploit/explore/diversity/combined roles based on which weight
  contribution dominates (threshold: > 0.05 above second-place), and produces a
  `BatchRationaleReport` with per-candidate rationales, role summary, and
  selector metadata. `PerCandidateRationale` dataclass tracks scores,
  contributions, safety gate status, and human-readable explanation.
  `write_rationale_json()` and `write_rationale_markdown()` produce structured
  output.
- `schemas/batch_rationale_report.schema.json` (G5) — JSON Schema Draft 2020-12
  for the batch-2 rationale report. Validates all required fields including
  per-candidate rationales, role summary, role descriptions, selected IDs,
  and notes.
- `src/openamp_foundry/active_learning/__init__.py` — Exports
  `BatchRationaleReport`, `PerCandidateRationale`, `build_batch_rationale_report`,
  `write_rationale_json`, `write_rationale_markdown`.
- `src/openamp_foundry/cli/main.py` — Registered `batch-rationale` subcommand
  with all argument flags and dispatch to `_run_batch_rationale`.
- `src/openamp_foundry/cli/commands/selection.py` — Added
  `_run_batch_rationale()` CLI handler with `--n-total`, `--n-active`,
  `--batch-size`, `--safety-threshold`, `--selectivity-threshold`,
  `--ensemble-weight`, `--uncertainty-weight`, `--diversity-weight`,
  `--min-uncertainty-probes`, `--rng-seed`, `--out-json`, `--out-md` flags.
- `Makefile` — Added `batch-rationale` target with default params writing to
  `outputs/batch_rationale_report.json` and `outputs/batch_rationale_report.md`.
- `tests/active_learning/test_batch_rationale.py` — 19 tests covering: all
  required top-level fields, candidates selected, per-candidate required fields,
  valid role (exploit/explore/diversity/combined), scores in [0,1], role summary
  counts match candidates, selected IDs match candidate IDs, probes non-negative,
  notes present, weight config matches input, JSON and Markdown output writing,
  CLI exit 0, CLI writes files, JSON Schema conformance, high exploitation weight
  produces more exploit roles, all candidates have explanations with role mention,
  role descriptions present for all roles, empty roles not in summary.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.83 G5 changelog. Test count: 2974.
- `tests/test_test_count_regression.py` — baseline updated to 2974.

Honest boundaries:
- This report uses **synthetic data** with known labels. Results reflect
  code-path integrity, not biological performance.
- Role classification is based solely on weight contributions. A candidate
  classified as "exploit" may also have meaningful uncertainty or diversity
  signal — the role label is the dominant contribution, not an exclusive
  category.
- The threshold (> 0.05 above second-place) is an arbitrary cutoff; candidates
  near the boundary are classified as "combined" to avoid false precision.
- The production selector optimises for multiple objectives (activity, safety,
  diversity) that a single-role label does not fully capture.
- This report is informational and requires qualified human review before
  influencing selection decisions.

## v0.5.82 — Loop 82: Phase G G4 — Active-Learning Strategy Comparison Report ✓ (2026-07-09)

CLI (`openamp-foundry bench strategy-compare`) that compares 5 selection strategies
(exploitation, exploration, diversity, combined, random) on the same synthetic pool
with identical hidden active candidates. Each strategy runs multi-round recovery of
hidden actives using the same batch-2 selector with different weights. The report
ranks strategies by recall, compares the production selector vs pure strategies and
random baseline, and produces structured JSON + Markdown output with caveats.
Prevents one-selector bias by making strategy performance transparent.

Changes:
- `src/openamp_foundry/active_learning/strategy_comparison.py` (G4) —
  `run_strategy_comparison()` generates a synthetic pool, hides N active candidates,
  runs 5 strategies (exploitation, exploration, diversity, combined, random) via
  multi-round selection, and produces a `StrategyComparisonReport` with per-strategy
  recovery metrics, ranking by recall, best strategy identification, and production
  selector comparison (vs random, exploitation, exploration, diversity).
  `STRATEGY_WEIGHTS` dict defines the weight tuples for each strategy.
  `write_comparison_json()` and `write_comparison_markdown()` produce structured output.
- `schemas/active_learning_strategy_comparison.schema.json` (G4) — JSON Schema
  Draft 2020-12 for the strategy comparison report. Validates all required fields
  including per-strategy results, ranking, production comparisons, and notes.
- `src/openamp_foundry/active_learning/__init__.py` — Exports `STRATEGY_WEIGHTS`,
  `StrategyComparisonReport`, `StrategyResult`, `run_strategy_comparison`,
  `write_comparison_json`, `write_comparison_markdown`.
- `src/openamp_foundry/cli/commands/benchmark.py` — Added
  `_run_active_learning_strategy_compare()` CLI handler with `--n-total`, `--n-active`,
  `--n-hidden`, `--batch-size`, `--max-rounds`, `--rng-seed`, `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `strategy-compare` subcommand under
  `bench` with all argument flags and dispatch to handler.
- `Makefile` — Added `bench-strategy-compare` target with default params writing to
  `outputs/strategy_comparison.json` and `outputs/strategy_comparison.md`.
- `tests/active_learning/test_strategy_comparison.py` — 18 tests covering: all 5
  strategies present, required fields (top-level + per-result), valid recall range,
  ranking order, production strategy name, best strategy not null, exploitation
  recovers actives, random baseline notes, production vs comparison fields, notes
  presence, JSON and Markdown output writing, CLI exit 0, CLI writes files, random
  baseline ranges, JSON Schema conformance, and production_outperforms_random type.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.82 G4 changelog. Test count: 2955.
- `tests/test_test_count_regression.py` — baseline updated to 2955.

Honest boundaries:
- This report uses **synthetic data** with known active/inactive labels. Results
  reflect code-path integrity, not biological performance.
- All strategies run with safety/selectivity gates disabled to isolate strategy
  effects. Real performance may differ with gates enabled.
- Random baseline is averaged over 20 Monte Carlo trials; deterministic strategies
  use a single run per config.
- The production selector optimizes for multiple objectives (activity, safety,
  diversity) that this recall-based benchmark does not fully measure.
- A strategy that ranks highest on recall may not be the best choice for real
  candidate selection — domain-specific constraints, safety requirements, and
  material constraints matter.
- This comparison is informational and requires qualified human review before
  influencing selection decisions.

## v0.5.81 — Loop 81: Phase G G3 — Calibration Pipeline Consistency Audit ✓ (2026-07-09)

CLI (`openamp-foundry calibration-audit`) that checks consistency across the
calibration pipeline artifacts — intake report, gate verdict, engine proposal,
and combined recalibration report. Ensures a human reviewer inspecting the
calibration pipeline output can verify that all stages agree on candidate
counts, gate verdicts, weight proposals, and timestamps.

Changes:
- `src/openamp_foundry/calibration/audit.py` (G3) — `run_calibration_audit()`
  accepts file paths or pre-loaded dicts for any combination of the four
  artifacts. Runs 12 consistency checks: artifact path existence, intake↔gate
  count matching, engine↔gate verdict agreement, engine L1 budget compliance,
  engine intake-link match, report↔gate verdict match, report↔engine proposal
  match, timestamp sanity, and intake cohort-metrics warnings. Each check has
  check_id, description, pass/fail, observed, expected, and severity (error/
  warning/info). Returns structured dict with overall_pass, checks array, and
  summary.
- `schemas/calibration_audit.schema.json` (G3) — JSON Schema Draft 2020-12 for
  the calibration audit report. Validates report_type, schema_version, timestamp,
  artifacts_checked, overall_pass, checks array, and summary.
- `src/openamp_foundry/cli/commands/reports.py` — Added `_run_calibration_audit`
  CLI handler with `--intake-report`, `--gate-verdict`, `--engine-proposal`,
  `--recalibration-report`, `--out-json`, `--out-md` flags.
- `src/openamp_foundry/cli/main.py` — Registered `calibration-audit` subcommand
  with all argument flags and dispatch to `_run_calibration_audit`.
- `Makefile` — Added `calibration-audit-example` and `calibration-audit` targets.
  Example target runs on synthetic intake + gate outputs.
- `tests/calibration/test_calibration_audit.py` — 18 tests covering: no
  artifact edge case, single artifact, intake↔gate count match/mismatch,
  engine↔gate verdict match/mismatch, L1 budget within/exceeds, report↔gate
  match, report↔engine match, future timestamp detection, cohort-metrics
  warning, JSON schema conformance, Markdown output, synthetic example
  consistency, synthetic path existence, engine without gate_passed, and
  nonexistent path handling.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.81 G3 changelog. Test count: 2937.
- `tests/test_test_count_regression.py` — baseline updated to 2937.

Honest boundaries:
- This audit checks **consistency** between pipeline artifacts, not biological
  validity. A passing audit means the pipeline stages agreed with each other,
  not that calibration decisions are correct.
- All tests use synthetic dict fixtures, not real wet-lab data.
- Timestamp checks detect future timestamps but do not validate chronological
  ordering between artifacts (e.g., gate must precede engine). This is a known
  limitation for a future iteration.
- The audit does not validate artifact schema conformance (each artifact's
  schema validity is tested separately). It focuses on cross-artifact
  consistency.

## v0.5.80 — Loop 80: Phase F F10 — Negative-Result Archive Completeness Checker ✓ (2026-07-09)

CLI that reads a JSON archive of negative-result entries and checks each entry
against completeness criteria: required fields, duplicate candidate_ids, content
field presence, date format validity, and intake_report_id format. Prevents
cherry-picking by ensuring incomplete or poorly documented entries are detected
before analysis or reporting.

Changes:
- `scripts/check_negative_archive_completeness.py` (F10) — Standalone CLI that
  loads negative-result entries (list or dict with `entries` key), checks each
  entry for: required fields present, no duplicate candidate_ids, at least one
  content field (assay_result, score_safety, reviewer_notes, or reason_detail),
  valid YYYY-MM-DD date format, and well-formed intake_report_id (INT-YYYY-NNN).
  Produces structured JSON + Markdown report with per-check and per-entry pass/fail.
  Exit 0 on all pass, 1 on any failure, 2 on input errors.
- `schemas/negative_result_archive_completeness.schema.json` (F10) — JSON Schema
  Draft 2020-12 for the completeness report output. Validates report_metadata,
  summary (total_entries, pass/fail count, pass_rate), 5 checks (required_fields,
  duplicate_candidate_ids, has_content_fields, date_format,
  intake_report_id_references) each with pass boolean and details array,
  per_entry_results array, and _caveat.
- `examples/negative_result_archive_example.json` (F10) — Toy example with 4
  entries (lab_inactive, lab_toxic, control_failure, synthesis_failure) across
  4 pipeline versions, including one entry with intake_report_id reference.
  Clearly marked EXAMPLE — NOT REAL DATA.
- `tests/evidence/test_negative_archive_completeness.py` — 35 tests covering:
  valid entries pass all checks, missing required field, duplicate candidate_id,
  missing content fields, invalid date format, invalid calendar date, invalid
  intake_report_id format, valid intake_report_id, mixed good/bad entries, empty
  string required field, reason_detail as content, report structure (5 keys),
  per-entry results matching count, empty entry handling, missing file, markdown
  sections (title, summary, check results, caveat, errors), example file loading
  and round-trip, all load_entries error modes, CLI exit codes (0, 1, 2), and
  JSON/Markdown output writing.
- `Makefile` — Added `check-negative-archive-completeness` target.
- `docs/evidence/METRICS_CURRENT.md` — v0.5.80 F10 changelog. Test count: 2919.
- `tests/test_test_count_regression.py` — baseline updated to 2919.

Honest boundaries:
- Checks structural and formatting criteria only — a PASS does not confirm
  biological accuracy, pipeline correctness, or data authenticity.
- Missing content fields may reflect genuine data absence (e.g., unreviewed
  entries) rather than record-keeping errors.
- The intake_report_id format check validates pattern, not referential
  integrity — a well-formed ID may reference a non-existent intake report.
- Duplicate candidate_id detection flags structural duplicates; it cannot
  distinguish accidental duplicates from intentional re-entry of the same
  candidate under different conditions.
- All conclusions about entry quality require qualified human review.


## Archived Loop History (Loop 79 and earlier)

*Full details available in git history. One-line summaries below.*

- Loop 79: Phase F F9 — Negative-Result Dashboard (v0.5.79)
- Loop 78: Phase F F8 — Bulk Rejection-Event Validator (v0.5.79)
- Loop 77: Phase F F7 — Calibration Link from Negative-Result Entries (v0.5.78)
- Loop 76: Phase F F6 — Negative-Result Informativeness Guide (v0.5.77)
- Loop 75: Phase F F5 — Safe-Publication Filter (v0.5.76)
- Loop 74: Phase F F4 — Failed-Candidate Report Generator (v0.5.75)
- Loop 73: Phase F F3 — Rejection Reason Taxonomy Schema (v0.5.74)
- Loop 72: Phase E E4-E6 — Safety Release, Preregistration, Packet CLI (v0.5.73)
- Loop 71: Phase E E1-E3 — External Review Packet Schemas (v0.5.72)
- Loop 70: Chain-of-Custody Hashing (v0.5.65)
- Loop 69: Active-Learning Recovery Benchmark (v0.5.46)
- Loop 68: Active-Learning Batch-2 Selector (v0.5.45)
- Loop 67: Recalibration Report (v0.5.44)
- Loop 66: Per-Family Benchmark Breakdown (v0.5.37)
- Loop 65: Recalibration Engine (v0.5.36)
- Loop 64: Cross-Dataset Generalization Benchmark (v0.5.35)
- Loop 63: Benchmark Card Consolidation (v0.5.34)
- Loop 62: Expert Ablation Re-run on Expanded Benchmark (v0.5.33)
- Loop 61: Precision@k Calibration (v0.5.32)
- Loop 60: Order-Dependent Features Benchmark (v0.5.31)
- Loop 59: Easy Baseline Benchmark (v0.5.30)
- Loop 58: Expanded 500-AMP Benchmark (v0.5.29)
- Loop 57: Multi-Negative-Set Benchmark (v0.5.28)
- Loop 56: Subpackage Public API (v0.5.25)
- Loop 55: Benchmark Regression Gate for CI (v0.5.24)
- Loop 54: Recalibration Policy + Gate (v0.5.20)
- Loop 53: Calibration Intake Module (v0.5.19)
- Loop 52: Two-Gate Triage Composite (v0.5.18)
- Loop 51: Rich Selectivity Integrated into Production Pipeline (v0.5.17)
- Loop 50: Rich Selectivity Scorer (v0.5.16)
- Loop 49: Charge-Matched Decoy Benchmark (v0.5.39)
- Loop 48: Bias-Aware Pilot Panel Floor (v0.5.38)
- Loop 47: Feature Decomposition Benchmark (v0.5.15) — feature_decomp.py; hydrophobic_fraction and amphipathicity decomposition; AUROC per feature.
- Loop 46: Wave 0.5 External Screen (v0.5.15) — Wave 0.5 complete; generic future-panel Gate 6 remains panel-specific.
- Loop 45: Chain-of-Custody Hashing (v0.5.65) — chain_of_custody.json added; --verify-pack CLI flag. These hashes verify identity and archive integrity only. Does not verify synthesis, biological activity, safety, or experimental provenance after receipt.
- Loops 1-44: Foundation phases (v0.1–v0.5.14) — see git log for details.
