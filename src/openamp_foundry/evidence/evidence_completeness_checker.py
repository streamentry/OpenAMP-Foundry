from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict


EXPECTED_ARTIFACT_TYPES = frozenset({
    "BSP",  # batch selection proposal
    "WHR",  # wet-lab hit record
    "PCU",  # post-experiment calibration update
    "HCR",  # hit confirmation report
    "PQG",  # phase Q completeness gate
    "CFC",  # candidate family clustering
    "FNR",  # family novelty report
    "ATR",  # audit trail report
    "SRG",  # scientific review readiness gate
    "PEB",  # preprint evidence bundle
})

DRY_LAB_ONLY_TYPES = frozenset({
    "BSP", "CFC", "FNR", "ATR", "SRG", "PEB",
})

WET_LAB_TYPES = frozenset({
    "WHR", "PCU", "HCR", "PQG",
})

VALID_COMPLETENESS_GRADES = frozenset({
    "A",  # all 10 artifact types present
    "B",  # all dry-lab types + at least 2 wet-lab types
    "C",  # all dry-lab types present, wet-lab incomplete
    "D",  # some dry-lab types missing
    "N/A",  # completeness not assessed
})

VALID_REVIEW_READINESS_VERDICTS = frozenset({
    "ready_for_review",         # grade A or B; can accompany external review
    "dry_lab_review_only",      # grade C; only dry-lab review possible
    "not_ready",                # grade D; major artifacts missing
    "assessment_pending",       # grade N/A; not yet checked
})


@dataclass
class ArtifactPresenceRecord:
    artifact_type: str
    is_present: bool
    artifact_id: Optional[str] = None


@dataclass
class EvidenceCompletenessChecker:
    ecc_id: str
    run_id: str
    candidate_family_id: str
    completeness_grade: str
    review_readiness_verdict: str
    artifact_presence_records: List[ArtifactPresenceRecord]
    n_artifacts_present: int
    n_artifacts_expected: int
    n_dry_lab_present: int
    n_wet_lab_present: int
    missing_artifact_types: List[str]
    dry_lab_only: bool
    limitations: str
    notes: str = ""
    peb_id: Optional[str] = None
    srg_id: Optional[str] = None


@dataclass
class ECCValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_evidence_completeness_checker(checker: EvidenceCompletenessChecker) -> ECCValidationResult:
    violations = []

    if not checker.ecc_id.startswith("ECC-"):
        violations.append("ecc_id must start with 'ECC-'")

    if not checker.run_id:
        violations.append("run_id is required")

    if not checker.candidate_family_id:
        violations.append("candidate_family_id is required")

    if checker.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real ECC- records")

    if checker.completeness_grade not in VALID_COMPLETENESS_GRADES:
        violations.append(
            f"completeness_grade '{checker.completeness_grade}' must be one of {sorted(VALID_COMPLETENESS_GRADES)}"
        )

    if checker.review_readiness_verdict not in VALID_REVIEW_READINESS_VERDICTS:
        violations.append(
            f"review_readiness_verdict '{checker.review_readiness_verdict}' must be one of {sorted(VALID_REVIEW_READINESS_VERDICTS)}"
        )

    if checker.n_artifacts_expected != len(EXPECTED_ARTIFACT_TYPES):
        violations.append(
            f"n_artifacts_expected must be {len(EXPECTED_ARTIFACT_TYPES)} (all EXPECTED_ARTIFACT_TYPES), got {checker.n_artifacts_expected}"
        )

    if checker.n_artifacts_present < 0 or checker.n_artifacts_present > checker.n_artifacts_expected:
        violations.append(
            f"n_artifacts_present ({checker.n_artifacts_present}) must be in [0, {checker.n_artifacts_expected}]"
        )

    # Validate each presence record
    present_types = set()
    for i, rec in enumerate(checker.artifact_presence_records):
        if rec.artifact_type not in EXPECTED_ARTIFACT_TYPES:
            violations.append(f"artifact_presence_records[{i}].artifact_type '{rec.artifact_type}' not in EXPECTED_ARTIFACT_TYPES")
        if rec.is_present:
            present_types.add(rec.artifact_type)

    # Cross-check n_artifacts_present
    computed_present = sum(1 for r in checker.artifact_presence_records if r.is_present)
    if checker.n_artifacts_present != computed_present:
        violations.append(
            f"n_artifacts_present ({checker.n_artifacts_present}) inconsistent with records (computed {computed_present})"
        )

    # Cross-check missing types
    computed_missing = sorted(EXPECTED_ARTIFACT_TYPES - present_types)
    if sorted(checker.missing_artifact_types) != computed_missing:
        violations.append(
            f"missing_artifact_types {sorted(checker.missing_artifact_types)} does not match computed {computed_missing}"
        )

    # Cross-check dry_lab count
    computed_dry = sum(1 for r in checker.artifact_presence_records if r.is_present and r.artifact_type in DRY_LAB_ONLY_TYPES)
    if checker.n_dry_lab_present != computed_dry:
        violations.append(
            f"n_dry_lab_present ({checker.n_dry_lab_present}) inconsistent with records (computed {computed_dry})"
        )

    # Cross-check wet_lab count
    computed_wet = sum(1 for r in checker.artifact_presence_records if r.is_present and r.artifact_type in WET_LAB_TYPES)
    if checker.n_wet_lab_present != computed_wet:
        violations.append(
            f"n_wet_lab_present ({checker.n_wet_lab_present}) inconsistent with records (computed {computed_wet})"
        )

    # Grade A requires all artifacts
    if checker.completeness_grade == "A" and checker.n_artifacts_present != len(EXPECTED_ARTIFACT_TYPES):
        violations.append(
            f"completeness_grade='A' requires all {len(EXPECTED_ARTIFACT_TYPES)} artifacts present"
        )

    # Grade B requires all dry-lab + at least 2 wet-lab
    if checker.completeness_grade == "B":
        if checker.n_dry_lab_present != len(DRY_LAB_ONLY_TYPES):
            violations.append(
                f"completeness_grade='B' requires all {len(DRY_LAB_ONLY_TYPES)} dry-lab artifacts present"
            )
        if checker.n_wet_lab_present < 2:
            violations.append(
                "completeness_grade='B' requires at least 2 wet-lab artifacts present"
            )

    # Grade C requires all dry-lab types
    if checker.completeness_grade == "C" and checker.n_dry_lab_present != len(DRY_LAB_ONLY_TYPES):
        violations.append(
            f"completeness_grade='C' requires all {len(DRY_LAB_ONLY_TYPES)} dry-lab artifacts present"
        )

    # Grade D must have some missing dry-lab types
    if checker.completeness_grade == "D" and checker.n_dry_lab_present == len(DRY_LAB_ONLY_TYPES) and checker.n_wet_lab_present >= 2:
        violations.append(
            "completeness_grade='D' should not have all dry-lab and 2+ wet-lab artifacts present"
        )

    # Verdict consistency
    if checker.completeness_grade == "A" and checker.review_readiness_verdict not in ("ready_for_review",):
        violations.append(
            "completeness_grade='A' requires review_readiness_verdict='ready_for_review'"
        )

    if checker.completeness_grade == "D" and checker.review_readiness_verdict not in ("not_ready",):
        violations.append(
            "completeness_grade='D' requires review_readiness_verdict='not_ready'"
        )

    if checker.completeness_grade == "N/A" and checker.review_readiness_verdict not in ("assessment_pending",):
        violations.append(
            "completeness_grade='N/A' requires review_readiness_verdict='assessment_pending'"
        )

    # ID prefix checks
    if checker.peb_id is not None and not checker.peb_id.startswith("PEB-"):
        violations.append("peb_id must start with 'PEB-' when provided")

    if checker.srg_id is not None and not checker.srg_id.startswith("SRG-"):
        violations.append("srg_id must start with 'SRG-' when provided")

    if not checker.dry_lab_only:
        violations.append("dry_lab_only must be True for ECC- records")

    if not checker.limitations or len(checker.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return ECCValidationResult(valid=len(violations) == 0, violations=violations)


def _compute_grade(n_dry: int, n_wet: int, n_total: int) -> str:
    if n_total == len(EXPECTED_ARTIFACT_TYPES):
        return "A"
    elif n_dry == len(DRY_LAB_ONLY_TYPES) and n_wet >= 2:
        return "B"
    elif n_dry == len(DRY_LAB_ONLY_TYPES):
        return "C"
    else:
        return "D"


def _compute_verdict(grade: str) -> str:
    mapping = {
        "A": "ready_for_review",
        "B": "ready_for_review",
        "C": "dry_lab_review_only",
        "D": "not_ready",
        "N/A": "assessment_pending",
    }
    return mapping[grade]


def build_evidence_completeness_checker(
    ecc_id: str,
    run_id: str,
    candidate_family_id: str,
    present_artifact_ids: Dict[str, str],
    limitations: str,
    notes: str = "",
    peb_id: Optional[str] = None,
    srg_id: Optional[str] = None,
) -> EvidenceCompletenessChecker:
    records = []
    for atype in sorted(EXPECTED_ARTIFACT_TYPES):
        artifact_id = present_artifact_ids.get(atype)
        records.append(ArtifactPresenceRecord(
            artifact_type=atype,
            is_present=artifact_id is not None,
            artifact_id=artifact_id,
        ))

    n_present = sum(1 for r in records if r.is_present)
    present_types = {r.artifact_type for r in records if r.is_present}
    missing = sorted(EXPECTED_ARTIFACT_TYPES - present_types)
    n_dry = sum(1 for r in records if r.is_present and r.artifact_type in DRY_LAB_ONLY_TYPES)
    n_wet = sum(1 for r in records if r.is_present and r.artifact_type in WET_LAB_TYPES)
    grade = _compute_grade(n_dry, n_wet, n_present)
    verdict = _compute_verdict(grade)

    checker = EvidenceCompletenessChecker(
        ecc_id=ecc_id,
        run_id=run_id,
        candidate_family_id=candidate_family_id,
        completeness_grade=grade,
        review_readiness_verdict=verdict,
        artifact_presence_records=records,
        n_artifacts_present=n_present,
        n_artifacts_expected=len(EXPECTED_ARTIFACT_TYPES),
        n_dry_lab_present=n_dry,
        n_wet_lab_present=n_wet,
        missing_artifact_types=missing,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
        peb_id=peb_id,
        srg_id=srg_id,
    )
    result = validate_evidence_completeness_checker(checker)
    if not result.valid:
        raise ValueError(f"Invalid ECC: {result.violations}")
    return checker


def format_evidence_completeness_checker(checker: EvidenceCompletenessChecker) -> str:
    lines = [
        f"Evidence Completeness Checker — {checker.ecc_id}",
        f"Run: {checker.run_id}  |  Family: {checker.candidate_family_id}",
        f"Completeness Grade: {checker.completeness_grade}  |  Review Readiness: {checker.review_readiness_verdict}",
        f"Artifacts Present: {checker.n_artifacts_present}/{checker.n_artifacts_expected}",
        f"  Dry-lab: {checker.n_dry_lab_present}/{len(DRY_LAB_ONLY_TYPES)}  |  Wet-lab: {checker.n_wet_lab_present}/{len(WET_LAB_TYPES)}",
    ]
    if checker.missing_artifact_types:
        lines.append(f"Missing: {', '.join(checker.missing_artifact_types)}")
    for rec in checker.artifact_presence_records:
        status = "PRESENT" if rec.is_present else "MISSING"
        id_str = f" ({rec.artifact_id})" if rec.artifact_id else ""
        lines.append(f"  [{rec.artifact_type}] {status}{id_str}")
    if checker.peb_id:
        lines.append(f"PEB Link: {checker.peb_id}")
    if checker.srg_id:
        lines.append(f"SRG Link: {checker.srg_id}")
    lines.append(f"Limitations: {checker.limitations}")
    if checker.notes:
        lines.append(f"Notes: {checker.notes}")
    lines.append("dry_lab_only: True")
    return "\n".join(lines)
