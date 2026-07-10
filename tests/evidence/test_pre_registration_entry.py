"""Tests for pre-registration entry schema — Phase Q Q2."""

import pytest
from openamp_foundry.evidence.pre_registration_entry import (
    PreRegistrationEntry,
    validate_pre_registration_entry,
    validate_pre_registration_entry_dict,
    PRE_PREFIX,
    VALID_REGISTRATION_STATUSES,
    NOTES_MAX_LENGTH,
    MIN_CANDIDATES,
)


def _valid_entry(**kwargs) -> PreRegistrationEntry:
    defaults = dict(
        pre_id="PRE-001",
        pipeline_version="v1.0.0",
        experiment_title="MIC assay for AMP batch B001",
        hypothesis="Selected AMPs will show MIC <= 8 ug/mL against E. coli ATCC 25922",
        primary_endpoint="MIC (minimum inhibitory concentration) in ug/mL",
        candidate_ids=["AMP-001", "AMP-002", "AMP-003"],
        positive_control_id="CTL-POS-001",
        negative_control_id="CTL-NEG-001",
        registered_date="2026-07-10",
        registration_status="submitted",
        registrar="registrar@example.com",
        notes="Pre-registered before batch synthesis.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PreRegistrationEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_pre_registration_entry(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_pre_registration_entry(_valid_entry())
        assert r.pre_id == "PRE-001"
        assert r.experiment_title == "MIC assay for AMP batch B001"
        assert r.registration_status == "submitted"
        assert r.candidate_count == 3
        assert r.has_positive_control is True
        assert r.has_negative_control is True
        assert r.dry_lab_only is True

    def test_approved_status_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="approved", dry_lab_only=False)
        )
        assert r.passed

    def test_rejected_status_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="rejected")
        )
        assert r.passed

    def test_no_positive_control_warns(self):
        r = validate_pre_registration_entry(
            _valid_entry(positive_control_id=None)
        )
        assert r.passed
        assert any("positive_control" in w for w in r.warnings)

    def test_no_negative_control_warns(self):
        r = validate_pre_registration_entry(
            _valid_entry(negative_control_id=None)
        )
        assert r.passed
        assert any("negative_control" in w for w in r.warnings)

    def test_single_candidate_warns(self):
        r = validate_pre_registration_entry(
            _valid_entry(candidate_ids=["AMP-001"])
        )
        assert r.passed
        assert any("single-candidate" in w or "1 entry" in w or "only 1" in w for w in r.warnings)

    def test_approved_dry_lab_warns(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="approved", dry_lab_only=True)
        )
        assert r.passed
        assert any("approved" in w and "dry_lab_only" in w for w in r.warnings)

    def test_empty_notes_passes(self):
        r = validate_pre_registration_entry(_valid_entry(notes=""))
        assert r.passed

    def test_max_length_notes_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(notes="x" * NOTES_MAX_LENGTH)
        )
        assert r.passed

    def test_large_candidate_list_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(candidate_ids=[f"AMP-{i:03d}" for i in range(20)])
        )
        assert r.passed
        assert r.candidate_count == 20


class TestPreIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_pre_registration_entry(_valid_entry(pre_id="001"))
        assert not r.passed
        assert any("pre_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_pre_registration_entry(_valid_entry(pre_id="PEP-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_pre_registration_entry(_valid_entry(pre_id="pre-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_pre_registration_entry(_valid_entry(pre_id="PRE-"))
        assert r.passed


class TestRequiredStringValidation:
    def test_empty_pipeline_version_fails(self):
        r = validate_pre_registration_entry(_valid_entry(pipeline_version=""))
        assert not r.passed
        assert any("pipeline_version" in e for e in r.errors)

    def test_empty_experiment_title_fails(self):
        r = validate_pre_registration_entry(_valid_entry(experiment_title=""))
        assert not r.passed
        assert any("experiment_title" in e for e in r.errors)

    def test_empty_hypothesis_fails(self):
        r = validate_pre_registration_entry(_valid_entry(hypothesis=""))
        assert not r.passed
        assert any("hypothesis" in e for e in r.errors)

    def test_empty_primary_endpoint_fails(self):
        r = validate_pre_registration_entry(_valid_entry(primary_endpoint=""))
        assert not r.passed
        assert any("primary_endpoint" in e for e in r.errors)

    def test_empty_registrar_fails(self):
        r = validate_pre_registration_entry(_valid_entry(registrar=""))
        assert not r.passed
        assert any("registrar" in e for e in r.errors)


class TestCandidateIdsValidation:
    def test_empty_list_fails(self):
        r = validate_pre_registration_entry(_valid_entry(candidate_ids=[]))
        assert not r.passed
        assert any("candidate_ids" in e for e in r.errors)

    def test_single_candidate_passes_with_warning(self):
        r = validate_pre_registration_entry(
            _valid_entry(candidate_ids=["AMP-001"])
        )
        assert r.passed
        assert r.candidate_count == 1
        assert r.warnings


class TestRegisteredDateValidation:
    def test_invalid_format_fails(self):
        r = validate_pre_registration_entry(
            _valid_entry(registered_date="10/07/2026")
        )
        assert not r.passed
        assert any("registered_date" in e for e in r.errors)

    def test_partial_date_fails(self):
        r = validate_pre_registration_entry(
            _valid_entry(registered_date="2026-07")
        )
        assert not r.passed

    def test_iso_format_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registered_date="2026-07-10")
        )
        assert r.passed

    def test_different_valid_date_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registered_date="2025-01-01")
        )
        assert r.passed


class TestRegistrationStatusValidation:
    def test_invalid_status_fails(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="pending")
        )
        assert not r.passed
        assert any("registration_status" in e for e in r.errors)

    def test_submitted_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="submitted")
        )
        assert r.passed

    def test_approved_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="approved", dry_lab_only=False)
        )
        assert r.passed

    def test_rejected_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(registration_status="rejected")
        )
        assert r.passed


class TestNotesValidation:
    def test_notes_too_long_fails(self):
        r = validate_pre_registration_entry(
            _valid_entry(notes="x" * (NOTES_MAX_LENGTH + 1))
        )
        assert not r.passed
        assert any("notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        r = validate_pre_registration_entry(
            _valid_entry(notes="x" * NOTES_MAX_LENGTH)
        )
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            pre_id="PRE-001",
            pipeline_version="v1.0.0",
            experiment_title="MIC assay",
            hypothesis="AMPs inhibit E. coli",
            primary_endpoint="MIC in ug/mL",
            candidate_ids=["AMP-001", "AMP-002"],
            positive_control_id="CTL-POS-001",
            negative_control_id="CTL-NEG-001",
            registered_date="2026-07-10",
            registration_status="submitted",
            registrar="reg@example.com",
            notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_pre_registration_entry_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["hypothesis"]
        r = validate_pre_registration_entry_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields(self):
        d = self._valid_dict()
        del d["hypothesis"]
        del d["primary_endpoint"]
        r = validate_pre_registration_entry_dict(d)
        assert not r.passed

    def test_dry_lab_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_pre_registration_entry_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_optional_controls_absent_passes(self):
        d = self._valid_dict()
        del d["positive_control_id"]
        del d["negative_control_id"]
        r = validate_pre_registration_entry_dict(d)
        assert r.passed
        assert r.warnings


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_pre_registration_entry(
            _valid_entry(
                pre_id="wrong",
                pipeline_version="",
                experiment_title="",
                hypothesis="",
                primary_endpoint="",
                candidate_ids=[],
                registered_date="bad-date",
                registration_status="unknown",
                registrar="",
            )
        )
        assert not r.passed
        assert len(r.errors) >= 9


class TestConstants:
    def test_pre_prefix(self):
        assert PRE_PREFIX == "PRE-"

    def test_valid_statuses(self):
        assert "submitted" in VALID_REGISTRATION_STATUSES
        assert "approved" in VALID_REGISTRATION_STATUSES
        assert "rejected" in VALID_REGISTRATION_STATUSES

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 400

    def test_min_candidates(self):
        assert MIN_CANDIDATES == 1
