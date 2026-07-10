"""Tests for pilot evidence package schema — Phase Q Q1."""

import pytest
from openamp_foundry.evidence.pilot_evidence_package import (
    PilotEvidencePackageEntry,
    validate_pilot_evidence_package,
    validate_pilot_evidence_package_dict,
    PEP_PREFIX,
    CCS_PREFIX,
    BSP_PREFIX,
    PSC_PREFIX,
    PRE_PREFIX,
    BCM_PREFIX,
    PACKAGE_NOTES_MAX_LENGTH,
    MIN_CANDIDATES,
)


def _valid_entry(**kwargs) -> PilotEvidencePackageEntry:
    defaults = dict(
        pep_id="PEP-001",
        pipeline_version="v1.0.0",
        ccs_id="CCS-001",
        bsp_id="BSP-001",
        psc_id="PSC-001",
        pre_registration_id="PRE-001",
        baseline_comparison_id="BCM-001",
        candidate_count=5,
        cleared_for_synthesis=True,
        is_complete=True,
        missing_artifacts=[],
        package_notes="Complete pilot package for external review.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PilotEvidencePackageEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_pilot_evidence_package(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_pilot_evidence_package(_valid_entry())
        assert r.pep_id == "PEP-001"
        assert r.ccs_id == "CCS-001"
        assert r.bsp_id == "BSP-001"
        assert r.psc_id == "PSC-001"
        assert r.candidate_count == 5
        assert r.cleared_for_synthesis is True
        assert r.is_complete is True
        assert r.missing_artifact_count == 0
        assert r.dry_lab_only is True

    def test_dry_lab_complete_warns(self):
        r = validate_pilot_evidence_package(_valid_entry(dry_lab_only=True))
        assert r.passed
        assert any("computational screening" in w or "dry_lab_only" in w for w in r.warnings)

    def test_real_package_no_dry_lab_warning(self):
        r = validate_pilot_evidence_package(_valid_entry(dry_lab_only=False))
        assert r.passed
        assert not any("computational screening" in w for w in r.warnings)

    def test_single_candidate_warns(self):
        r = validate_pilot_evidence_package(_valid_entry(candidate_count=1))
        assert r.passed
        assert any("single-candidate" in w or "1" in w for w in r.warnings)

    def test_incomplete_package_with_missing_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                is_complete=False,
                missing_artifacts=["cps_id", "cba_id"],
            )
        )
        assert r.passed
        assert r.missing_artifact_count == 2

    def test_empty_package_notes(self):
        r = validate_pilot_evidence_package(_valid_entry(package_notes=""))
        assert r.passed

    def test_max_length_notes(self):
        notes = "p" * PACKAGE_NOTES_MAX_LENGTH
        r = validate_pilot_evidence_package(_valid_entry(package_notes=notes))
        assert r.passed

    def test_large_candidate_count(self):
        r = validate_pilot_evidence_package(_valid_entry(candidate_count=100))
        assert r.passed
        assert r.candidate_count == 100

    def test_missing_artifact_count_computed(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                is_complete=False,
                missing_artifacts=["x", "y", "z"],
            )
        )
        assert r.passed
        assert r.missing_artifact_count == 3


class TestPepIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(pep_id="001"))
        assert not r.passed
        assert any("pep_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(pep_id="CCS-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(pep_id="pep-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_pilot_evidence_package(_valid_entry(pep_id="PEP-"))
        assert r.passed


class TestArtifactIdValidation:
    def test_invalid_ccs_id_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(ccs_id="001"))
        assert not r.passed
        assert any("ccs_id" in e for e in r.errors)

    def test_invalid_bsp_id_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(bsp_id="001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_invalid_psc_id_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(psc_id="001"))
        assert not r.passed
        assert any("psc_id" in e for e in r.errors)

    def test_invalid_pre_registration_id_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(pre_registration_id="001"))
        assert not r.passed
        assert any("pre_registration_id" in e for e in r.errors)

    def test_invalid_baseline_comparison_id_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(baseline_comparison_id="001"))
        assert not r.passed
        assert any("baseline_comparison_id" in e for e in r.errors)

    def test_correct_pre_prefix_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(pre_registration_id="PRE-999")
        )
        assert r.passed

    def test_correct_bcm_prefix_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(baseline_comparison_id="BCM-999")
        )
        assert r.passed

    def test_wrong_prefix_pre_fails(self):
        r = validate_pilot_evidence_package(
            _valid_entry(pre_registration_id="PEP-001")
        )
        assert not r.passed


class TestCandidateCountValidation:
    def test_zero_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(candidate_count=0))
        assert not r.passed
        assert any("candidate_count" in e for e in r.errors)

    def test_negative_fails(self):
        r = validate_pilot_evidence_package(_valid_entry(candidate_count=-1))
        assert not r.passed

    def test_one_passes_with_warning(self):
        r = validate_pilot_evidence_package(_valid_entry(candidate_count=1))
        assert r.passed
        assert r.warnings


class TestClearedForSynthesisValidation:
    def test_not_cleared_fails(self):
        r = validate_pilot_evidence_package(
            _valid_entry(cleared_for_synthesis=False)
        )
        assert not r.passed
        assert any("cleared_for_synthesis" in e for e in r.errors)

    def test_cleared_true_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(cleared_for_synthesis=True)
        )
        assert r.passed


class TestCompletenessValidation:
    def test_complete_with_missing_fails(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                is_complete=True,
                missing_artifacts=["cps_id"],
            )
        )
        assert not r.passed
        assert any("is_complete" in e for e in r.errors)

    def test_incomplete_without_missing_fails(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                is_complete=False,
                missing_artifacts=[],
            )
        )
        assert not r.passed
        assert any("is_complete" in e for e in r.errors)

    def test_complete_without_missing_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(is_complete=True, missing_artifacts=[])
        )
        assert r.passed

    def test_incomplete_with_missing_passes(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                is_complete=False,
                missing_artifacts=["cba_id"],
            )
        )
        assert r.passed


class TestPackageNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "p" * (PACKAGE_NOTES_MAX_LENGTH + 1)
        r = validate_pilot_evidence_package(_valid_entry(package_notes=notes))
        assert not r.passed
        assert any("package_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "p" * PACKAGE_NOTES_MAX_LENGTH
        r = validate_pilot_evidence_package(_valid_entry(package_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            pep_id="PEP-001",
            pipeline_version="v1.0.0",
            ccs_id="CCS-001",
            bsp_id="BSP-001",
            psc_id="PSC-001",
            pre_registration_id="PRE-001",
            baseline_comparison_id="BCM-001",
            candidate_count=5,
            cleared_for_synthesis=True,
            is_complete=True,
            missing_artifacts=[],
            package_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_pilot_evidence_package_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["ccs_id"]
        r = validate_pilot_evidence_package_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields(self):
        d = self._valid_dict()
        del d["ccs_id"]
        del d["pre_registration_id"]
        r = validate_pilot_evidence_package_dict(d)
        assert not r.passed

    def test_dry_lab_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_pilot_evidence_package_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_not_cleared_in_dict_fails(self):
        r = validate_pilot_evidence_package_dict(
            self._valid_dict(cleared_for_synthesis=False)
        )
        assert not r.passed

    def test_inconsistent_completeness_fails(self):
        r = validate_pilot_evidence_package_dict(
            self._valid_dict(is_complete=True, missing_artifacts=["cba_id"])
        )
        assert not r.passed


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_pilot_evidence_package(
            _valid_entry(
                pep_id="wrong",
                ccs_id="wrong",
                bsp_id="wrong",
                psc_id="wrong",
                pre_registration_id="wrong",
                baseline_comparison_id="wrong",
                candidate_count=0,
                cleared_for_synthesis=False,
            )
        )
        assert not r.passed
        assert len(r.errors) >= 8


class TestConstants:
    def test_pep_prefix(self):
        assert PEP_PREFIX == "PEP-"

    def test_ccs_prefix(self):
        assert CCS_PREFIX == "CCS-"

    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_psc_prefix(self):
        assert PSC_PREFIX == "PSC-"

    def test_pre_prefix(self):
        assert PRE_PREFIX == "PRE-"

    def test_bcm_prefix(self):
        assert BCM_PREFIX == "BCM-"

    def test_notes_max_length(self):
        assert PACKAGE_NOTES_MAX_LENGTH == 400

    def test_min_candidates(self):
        assert MIN_CANDIDATES == 1
