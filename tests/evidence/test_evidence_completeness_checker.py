"""Tests for evidence_completeness_checker module — Phase S S3 (ECC-)."""
import pytest
from openamp_foundry.evidence.evidence_completeness_checker import (
    EvidenceCompletenessChecker, ArtifactPresenceRecord,
    EXPECTED_ARTIFACT_TYPES, VALID_COMPLETENESS_GRADES,
    VALID_REVIEW_READINESS_VERDICTS, DRY_LAB_ONLY_TYPES, WET_LAB_TYPES,
    validate_evidence_completeness_checker,
    build_evidence_completeness_checker,
    format_evidence_completeness_checker,
)

ALL_IDS = {"BSP":"BSP-001","WHR":"WHR-001","PCU":"PCU-001","HCR":"HCR-001","PQG":"PQG-001",
           "CFC":"CFC-001","FNR":"FNR-001","ATR":"ATR-001","SRG":"SRG-001","PEB":"PEB-001"}
DRY_IDS = {k:v for k,v in ALL_IDS.items() if k in DRY_LAB_ONLY_TYPES}
WET_IDS = {k:v for k,v in ALL_IDS.items() if k in WET_LAB_TYPES}


def _all_records(present=None):
    if present is None: present = set(EXPECTED_ARTIFACT_TYPES)
    return [ArtifactPresenceRecord(t, t in present, ALL_IDS.get(t) if t in present else None)
            for t in sorted(EXPECTED_ARTIFACT_TYPES)]


def _make(**kw):
    records = _all_records()
    defaults = dict(
        ecc_id="ECC-001", run_id="RUN-001", candidate_family_id="FAM-001",
        completeness_grade="A", review_readiness_verdict="ready_for_review",
        artifact_presence_records=records, n_artifacts_present=10,
        n_artifacts_expected=10, n_dry_lab_present=6, n_wet_lab_present=4,
        missing_artifact_types=[], dry_lab_only=True,
        limitations="Dry-lab assessment only. Wet-lab not validated.",
        notes="", peb_id=None, srg_id=None,
    )
    defaults.update(kw)
    return EvidenceCompletenessChecker(**defaults)


class TestECCIDValidation:
    def test_valid_ecc_id(self): assert validate_evidence_completeness_checker(_make(ecc_id="ECC-001")).valid
    def test_invalid_ecc_id(self):
        r = validate_evidence_completeness_checker(_make(ecc_id="001"))
        assert not r.valid and any("ecc_id" in v for v in r.violations)
    def test_wrong_prefix(self): assert not validate_evidence_completeness_checker(_make(ecc_id="SEG-001")).valid
    def test_toy_family_blocked(self):
        r = validate_evidence_completeness_checker(_make(candidate_family_id="TOY-001"))
        assert not r.valid and any("TOY-" in v for v in r.violations)
    def test_run_id_required(self):
        r = validate_evidence_completeness_checker(_make(run_id=""))
        assert not r.valid and any("run_id" in v for v in r.violations)
    def test_family_id_required(self): assert not validate_evidence_completeness_checker(_make(candidate_family_id="")).valid
    def test_peb_id_prefix_required(self):
        r = validate_evidence_completeness_checker(_make(peb_id="001"))
        assert not r.valid and any("peb_id" in v for v in r.violations)
    def test_srg_id_prefix_required(self):
        r = validate_evidence_completeness_checker(_make(srg_id="001"))
        assert not r.valid and any("srg_id" in v for v in r.violations)
    def test_valid_optional_ids(self): assert validate_evidence_completeness_checker(_make(peb_id="PEB-001", srg_id="SRG-001")).valid


class TestCompletenessGradeValidation:
    def test_grade_A_all_present(self): assert validate_evidence_completeness_checker(_make(completeness_grade="A")).valid
    def test_grade_A_requires_all_artifacts(self):
        records = _all_records(set(EXPECTED_ARTIFACT_TYPES) - {"WHR"})
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="A", artifact_presence_records=records,
            n_artifacts_present=9, n_wet_lab_present=3, missing_artifact_types=["WHR"]
        ))
        assert not r.valid and any("grade='A'" in v or "grade=\\'A\\'" in v or "'A'" in v for v in r.violations)
    def test_grade_B_all_dry_plus_2_wet(self):
        present = set(DRY_LAB_ONLY_TYPES) | {"WHR","PCU"}
        records = _all_records(present)
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="B", review_readiness_verdict="ready_for_review",
            artifact_presence_records=records, n_artifacts_present=8,
            n_dry_lab_present=6, n_wet_lab_present=2, missing_artifact_types=["HCR","PQG"]
        ))
        assert r.valid
    def test_grade_B_requires_all_dry(self):
        present = set(DRY_LAB_ONLY_TYPES) - {"CFC"} | {"WHR","PCU"}
        records = _all_records(present)
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="B", review_readiness_verdict="ready_for_review",
            artifact_presence_records=records, n_artifacts_present=7,
            n_dry_lab_present=5, n_wet_lab_present=2, missing_artifact_types=["CFC","HCR","PQG"]
        ))
        assert not r.valid and any("'B'" in v for v in r.violations)
    def test_grade_C_all_dry_no_wet(self):
        records = _all_records(set(DRY_LAB_ONLY_TYPES))
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="C", review_readiness_verdict="dry_lab_review_only",
            artifact_presence_records=records, n_artifacts_present=6,
            n_dry_lab_present=6, n_wet_lab_present=0, missing_artifact_types=["HCR","PCU","PQG","WHR"]
        ))
        assert r.valid
    def test_grade_D_missing_dry(self):
        present = set(DRY_LAB_ONLY_TYPES) - {"CFC","FNR"}
        records = _all_records(present)
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="D", review_readiness_verdict="not_ready",
            artifact_presence_records=records, n_artifacts_present=4,
            n_dry_lab_present=4, n_wet_lab_present=0, missing_artifact_types=["CFC","FNR","HCR","PCU","PQG","WHR"]
        ))
        assert r.valid
    def test_invalid_grade(self):
        r = validate_evidence_completeness_checker(_make(completeness_grade="E"))
        assert not r.valid and any("completeness_grade" in v for v in r.violations)
    def test_grades_count(self): assert len(VALID_COMPLETENESS_GRADES) == 5


class TestVerdictConsistency:
    def test_grade_A_requires_ready_verdict(self):
        r = validate_evidence_completeness_checker(_make(completeness_grade="A", review_readiness_verdict="not_ready"))
        assert not r.valid and any("'A'" in v and "ready_for_review" in v for v in r.violations)
    def test_grade_D_requires_not_ready_verdict(self):
        present = set(DRY_LAB_ONLY_TYPES) - {"CFC"}
        records = _all_records(present)
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="D", review_readiness_verdict="ready_for_review",
            artifact_presence_records=records, n_artifacts_present=5,
            n_dry_lab_present=5, n_wet_lab_present=0, missing_artifact_types=["CFC","HCR","PCU","PQG","WHR"]
        ))
        assert not r.valid and any("'D'" in v and "not_ready" in v for v in r.violations)
    def test_grade_na_requires_assessment_pending(self):
        r = validate_evidence_completeness_checker(_make(
            completeness_grade="N/A", review_readiness_verdict="ready_for_review",
            n_artifacts_present=10, n_dry_lab_present=6, n_wet_lab_present=4, missing_artifact_types=[]
        ))
        assert not r.valid
    def test_verdicts_count(self): assert len(VALID_REVIEW_READINESS_VERDICTS) == 4
    def test_invalid_verdict(self):
        r = validate_evidence_completeness_checker(_make(review_readiness_verdict="partial_ready"))
        assert not r.valid and any("review_readiness_verdict" in v for v in r.violations)


class TestCountConsistency:
    def test_n_expected_must_be_10(self):
        r = validate_evidence_completeness_checker(_make(n_artifacts_expected=9))
        assert not r.valid and any("n_artifacts_expected" in v for v in r.violations)
    def test_n_present_inconsistency_rejected(self):
        r = validate_evidence_completeness_checker(_make(n_artifacts_present=5))
        assert not r.valid and any("n_artifacts_present" in v and "inconsistent" in v for v in r.violations)
    def test_n_dry_inconsistency_rejected(self):
        r = validate_evidence_completeness_checker(_make(n_dry_lab_present=3))
        assert not r.valid and any("n_dry_lab_present" in v for v in r.violations)
    def test_n_wet_inconsistency_rejected(self):
        r = validate_evidence_completeness_checker(_make(n_wet_lab_present=2))
        assert not r.valid and any("n_wet_lab_present" in v for v in r.violations)
    def test_missing_types_inconsistency_rejected(self):
        r = validate_evidence_completeness_checker(_make(missing_artifact_types=["WHR"]))
        assert not r.valid and any("missing_artifact_types" in v for v in r.violations)
    def test_expected_artifact_types_count(self): assert len(EXPECTED_ARTIFACT_TYPES) == 10
    def test_dry_lab_types_count(self): assert len(DRY_LAB_ONLY_TYPES) == 6
    def test_wet_lab_types_count(self): assert len(WET_LAB_TYPES) == 4


class TestArtifactRecordValidation:
    def test_invalid_artifact_type_in_records(self):
        records = _all_records()
        records[0] = ArtifactPresenceRecord("XYZ", True, "XYZ-001")
        r = validate_evidence_completeness_checker(_make(artifact_presence_records=records))
        assert not r.valid and any("XYZ" in v for v in r.violations)


class TestDryLabAndLimitations:
    def test_dry_lab_false_rejected(self):
        r = validate_evidence_completeness_checker(_make(dry_lab_only=False))
        assert not r.valid and any("dry_lab_only" in v for v in r.violations)
    def test_limitations_required(self):
        r = validate_evidence_completeness_checker(_make(limitations=""))
        assert not r.valid and any("limitations" in v for v in r.violations)
    def test_limitations_short_rejected(self): assert not validate_evidence_completeness_checker(_make(limitations="Too short")).valid
    def test_limitations_sufficient_valid(self): assert validate_evidence_completeness_checker(_make(limitations="Dry-lab assessment only. Wet-lab not validated.")).valid


class TestBuildAndFormat:
    def test_build_grade_A_all_present(self):
        c = build_evidence_completeness_checker("ECC-001","RUN-001","FAM-001",
            ALL_IDS, "Dry-lab assessment only. Wet-lab not validated.")
        assert c.completeness_grade == "A" and c.review_readiness_verdict == "ready_for_review"
        assert c.n_artifacts_present == 10 and c.dry_lab_only is True

    def test_build_grade_C_dry_only(self):
        c = build_evidence_completeness_checker("ECC-001","RUN-001","FAM-001",
            DRY_IDS, "Dry-lab assessment only. Wet-lab not validated.")
        assert c.completeness_grade == "C" and c.review_readiness_verdict == "dry_lab_review_only"
        assert c.n_dry_lab_present == 6 and c.n_wet_lab_present == 0

    def test_build_grade_D_partial_dry(self):
        partial = {k:v for k,v in DRY_IDS.items() if k not in ("CFC","FNR")}
        c = build_evidence_completeness_checker("ECC-001","RUN-001","FAM-001",
            partial, "Dry-lab assessment only. Wet-lab not validated.")
        assert c.completeness_grade == "D" and c.review_readiness_verdict == "not_ready"

    def test_build_raises_invalid(self):
        with pytest.raises(ValueError):
            build_evidence_completeness_checker("INVALID","RUN-001","FAM-001",
                ALL_IDS, "Dry-lab assessment only. Wet-lab not validated.")

    def test_format_includes_ecc_id(self): assert "ECC-001" in format_evidence_completeness_checker(_make())
    def test_format_includes_grade(self): assert "A" in format_evidence_completeness_checker(_make())
    def test_format_includes_verdict(self): assert "ready_for_review" in format_evidence_completeness_checker(_make())
    def test_format_includes_artifact_counts(self): assert "10/10" in format_evidence_completeness_checker(_make())
    def test_format_includes_peb_link(self): assert "PEB-001" in format_evidence_completeness_checker(_make(peb_id="PEB-001"))
    def test_format_is_multiline(self): assert "\n" in format_evidence_completeness_checker(_make())
    def test_valid_checker_passes(self):
        r = validate_evidence_completeness_checker(_make())
        assert r.valid and r.violations == []
    def test_multiple_violations(self):
        r = validate_evidence_completeness_checker(_make(ecc_id="INVALID", completeness_grade="Z"))
        assert not r.valid and len(r.violations) >= 2
    def test_build_grade_B(self):
        partial = dict(**DRY_IDS)
        partial["WHR"] = "WHR-001"
        partial["PCU"] = "PCU-001"
        c = build_evidence_completeness_checker("ECC-001","RUN-001","FAM-001",
            partial, "Dry-lab assessment only. Wet-lab not validated.")
        assert c.completeness_grade == "B" and c.n_wet_lab_present == 2
