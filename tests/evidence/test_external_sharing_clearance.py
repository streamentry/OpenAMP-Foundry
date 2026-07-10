"""Tests for ExternalSharingClearance schema — Phase Q Q3."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.external_sharing_clearance import (
    ExternalSharingClearance,
    ExternalSharingClearanceResult,
    validate_external_sharing_clearance,
    validate_external_sharing_clearance_dict,
)


def _valid_entry(**overrides) -> ExternalSharingClearance:
    defaults = dict(
        esc_id="ESC-001",
        pipeline_version="v0.10.8",
        pep_id="PEP-001",
        pre_id="PRE-001",
        external_lab_token="LAB-TOKEN-A",
        sharing_date="2026-07-10",
        caveat_confirmed=True,
        dry_lab_only_acknowledged=True,
        sharing_purpose="pilot_experiment",
        sharing_notes="Sharing for MIC validation of top 5 candidates.",
        reviewer="Dr. Smith",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return ExternalSharingClearance(**defaults)


# ── 1. ESC ID validation ─────────────────────────────────────────────────────

class TestEscIdValidation:
    def test_valid_esc_prefix(self):
        result = validate_external_sharing_clearance(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id="REF-001"))
        assert not result.passed
        assert any("esc_id must start with 'ESC-'" in e for e in result.errors)

    def test_empty_esc_id_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id=""))
        assert not result.passed
        assert any("esc_id must start with 'ESC-'" in e for e in result.errors)

    def test_lowercase_prefix_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id="esc-001"))
        assert not result.passed

    def test_esc_prefix_with_long_id(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id="ESC-20260710-001"))
        assert result.passed

    def test_esc_prefix_captured_in_result(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id="ESC-XYZ"))
        assert result.esc_id == "ESC-XYZ"

    def test_no_prefix_just_number_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(esc_id="001"))
        assert not result.passed


# ── 2. PEP ID validation ─────────────────────────────────────────────────────

class TestPepIdValidation:
    def test_valid_pep_prefix(self):
        result = validate_external_sharing_clearance(_valid_entry())
        assert result.passed

    def test_wrong_pep_prefix_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pep_id="BCM-001"))
        assert not result.passed
        assert any("pep_id must start with 'PEP-'" in e for e in result.errors)

    def test_empty_pep_id_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pep_id=""))
        assert not result.passed

    def test_pep_id_captured_in_result(self):
        result = validate_external_sharing_clearance(_valid_entry(pep_id="PEP-999"))
        assert result.pep_id == "PEP-999"

    def test_lowercase_pep_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pep_id="pep-001"))
        assert not result.passed

    def test_pep_long_id_passes(self):
        result = validate_external_sharing_clearance(_valid_entry(pep_id="PEP-2026-07-10-001"))
        assert result.passed


# ── 3. PRE ID validation ─────────────────────────────────────────────────────

class TestPreIdValidation:
    def test_valid_pre_prefix(self):
        result = validate_external_sharing_clearance(_valid_entry())
        assert result.passed

    def test_wrong_pre_prefix_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pre_id="BSP-001"))
        assert not result.passed
        assert any("pre_id must start with 'PRE-'" in e for e in result.errors)

    def test_empty_pre_id_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pre_id=""))
        assert not result.passed

    def test_pre_id_captured_in_result(self):
        result = validate_external_sharing_clearance(_valid_entry(pre_id="PRE-999"))
        assert result.pre_id == "PRE-999"

    def test_lowercase_pre_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pre_id="pre-001"))
        assert not result.passed

    def test_pre_long_id_passes(self):
        result = validate_external_sharing_clearance(_valid_entry(pre_id="PRE-2026-07-10-001"))
        assert result.passed


# ── 4. Required fields validation ────────────────────────────────────────────

class TestRequiredFields:
    def test_all_fields_present_passes(self):
        result = validate_external_sharing_clearance(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_version_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(pipeline_version="   "))
        assert not result.passed

    def test_empty_external_lab_token_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(external_lab_token=""))
        assert not result.passed
        assert any("external_lab_token must not be empty" in e for e in result.errors)

    def test_whitespace_lab_token_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(external_lab_token="   "))
        assert not result.passed

    def test_empty_reviewer_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(reviewer=""))
        assert not result.passed
        assert any("reviewer must not be empty" in e for e in result.errors)

    def test_whitespace_reviewer_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(reviewer="  "))
        assert not result.passed

    def test_multiple_empty_required_fields_all_reported(self):
        result = validate_external_sharing_clearance(
            _valid_entry(pipeline_version="", reviewer="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 2

    def test_valid_minimal_sharing_notes(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes=""))
        # empty notes is a warning, not an error
        assert result.passed
        assert any("sharing_notes is empty" in w for w in result.warnings)


# ── 5. Sharing date format ────────────────────────────────────────────────────

class TestSharingDateFormat:
    def test_valid_iso_date(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="2026-07-10"))
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="20260710"))
        assert not result.passed
        assert any("sharing_date must be ISO format" in e for e in result.errors)

    def test_date_slash_separator_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="2026/07/10"))
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date=""))
        assert not result.passed

    def test_partial_date_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="2026-07"))
        assert not result.passed

    def test_text_date_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="July 10 2026"))
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_date="2025-01-01"))
        assert result.passed


# ── 6. Caveat confirmed ───────────────────────────────────────────────────────

class TestCaveatConfirmed:
    def test_caveat_true_passes(self):
        result = validate_external_sharing_clearance(_valid_entry(caveat_confirmed=True))
        assert result.passed

    def test_caveat_false_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(caveat_confirmed=False))
        assert not result.passed
        assert any("caveat_confirmed must be True" in e for e in result.errors)

    def test_caveat_false_is_blocking(self):
        # even with all other fields valid, caveat_false blocks the record
        entry = _valid_entry(caveat_confirmed=False)
        result = validate_external_sharing_clearance(entry)
        assert not result.passed

    def test_caveat_confirmed_in_result(self):
        # result does not expose caveat_confirmed directly but passed reflects it
        result = validate_external_sharing_clearance(_valid_entry(caveat_confirmed=True))
        assert result.passed

    def test_both_caveats_false_both_reported(self):
        result = validate_external_sharing_clearance(
            _valid_entry(caveat_confirmed=False, dry_lab_only_acknowledged=False)
        )
        assert not result.passed
        assert any("caveat_confirmed" in e for e in result.errors)
        assert any("dry_lab_only_acknowledged" in e for e in result.errors)


# ── 7. Dry-lab-only acknowledged ─────────────────────────────────────────────

class TestDryLabOnlyAcknowledged:
    def test_acknowledged_true_passes(self):
        result = validate_external_sharing_clearance(
            _valid_entry(dry_lab_only_acknowledged=True)
        )
        assert result.passed

    def test_acknowledged_false_fails(self):
        result = validate_external_sharing_clearance(
            _valid_entry(dry_lab_only_acknowledged=False)
        )
        assert not result.passed
        assert any("dry_lab_only_acknowledged must be True" in e for e in result.errors)

    def test_not_acknowledged_is_blocking(self):
        result = validate_external_sharing_clearance(
            _valid_entry(dry_lab_only_acknowledged=False)
        )
        assert not result.passed

    def test_result_dry_lab_only_flag(self):
        result = validate_external_sharing_clearance(_valid_entry(dry_lab_only=True))
        assert result.dry_lab_only is True

    def test_result_dry_lab_false_flag(self):
        result = validate_external_sharing_clearance(_valid_entry(dry_lab_only=False))
        assert result.dry_lab_only is False


# ── 8. Sharing purpose validation ────────────────────────────────────────────

class TestSharingPurpose:
    def test_pilot_experiment_passes(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="pilot_experiment")
        )
        assert result.passed

    def test_peer_review_passes(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="peer_review", sharing_notes="For peer review.")
        )
        assert result.passed

    def test_collaboration_passes(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="collaboration", sharing_notes="Joint project.")
        )
        assert result.passed

    def test_invalid_purpose_fails(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="publication")
        )
        assert not result.passed
        assert any("sharing_purpose must be one of" in e for e in result.errors)

    def test_empty_purpose_fails(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_purpose=""))
        assert not result.passed

    def test_purpose_captured_in_result(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="peer_review", sharing_notes="Review notes.")
        )
        assert result.sharing_purpose == "peer_review"

    def test_pilot_experiment_generates_warning(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_purpose="pilot_experiment")
        )
        assert any("pilot_experiment" in w for w in result.warnings)


# ── 9. Sharing notes ─────────────────────────────────────────────────────────

class TestSharingNotes:
    def test_valid_notes_passes(self):
        result = validate_external_sharing_clearance(
            _valid_entry(sharing_notes="Sharing for MIC validation.")
        )
        assert result.passed

    def test_empty_notes_triggers_warning_not_error(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes=""))
        assert result.passed
        assert any("sharing_notes is empty" in w for w in result.warnings)

    def test_notes_at_limit_passes(self):
        notes = "x" * 400
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes=notes))
        assert result.passed

    def test_notes_over_limit_fails(self):
        notes = "x" * 401
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes=notes))
        assert not result.passed
        assert any("sharing_notes must be at most 400" in e for e in result.errors)

    def test_notes_just_over_limit_fails(self):
        notes = "y" * 401
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes=notes))
        assert not result.passed

    def test_whitespace_only_notes_triggers_warning(self):
        result = validate_external_sharing_clearance(_valid_entry(sharing_notes="   "))
        # whitespace-only is empty for warning purposes
        assert result.passed
        assert any("sharing_notes is empty" in w for w in result.warnings)


# ── 10. Dict-based validator ─────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "esc_id": "ESC-001",
            "pipeline_version": "v0.10.8",
            "pep_id": "PEP-001",
            "pre_id": "PRE-001",
            "external_lab_token": "LAB-A",
            "sharing_date": "2026-07-10",
            "caveat_confirmed": True,
            "dry_lab_only_acknowledged": True,
            "sharing_purpose": "pilot_experiment",
            "sharing_notes": "Sharing candidates.",
            "reviewer": "Dr. Smith",
            "dry_lab_only": True,
        }
        result = validate_external_sharing_clearance_dict(data)
        assert result.passed

    def test_dict_missing_esc_id_fails(self):
        data = {
            "esc_id": "WRONG-001",
            "pipeline_version": "v0.10.8",
            "pep_id": "PEP-001",
            "pre_id": "PRE-001",
            "external_lab_token": "LAB-A",
            "sharing_date": "2026-07-10",
            "caveat_confirmed": True,
            "dry_lab_only_acknowledged": True,
            "sharing_purpose": "pilot_experiment",
            "sharing_notes": "ok",
            "reviewer": "Dr. Smith",
        }
        result = validate_external_sharing_clearance_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_only_true(self):
        data = {
            "esc_id": "ESC-001",
            "pipeline_version": "v0.10.8",
            "pep_id": "PEP-001",
            "pre_id": "PRE-001",
            "external_lab_token": "LAB-A",
            "sharing_date": "2026-07-10",
            "caveat_confirmed": True,
            "dry_lab_only_acknowledged": True,
            "sharing_purpose": "pilot_experiment",
            "sharing_notes": "ok",
            "reviewer": "Dr. Jones",
        }
        result = validate_external_sharing_clearance_dict(data)
        assert result.dry_lab_only is True

    def test_dict_caveat_false_fails(self):
        data = {
            "esc_id": "ESC-001",
            "pipeline_version": "v0.10.8",
            "pep_id": "PEP-001",
            "pre_id": "PRE-001",
            "external_lab_token": "LAB-A",
            "sharing_date": "2026-07-10",
            "caveat_confirmed": False,
            "dry_lab_only_acknowledged": True,
            "sharing_purpose": "pilot_experiment",
            "sharing_notes": "ok",
            "reviewer": "Dr. Jones",
        }
        result = validate_external_sharing_clearance_dict(data)
        assert not result.passed

    def test_dict_multiple_errors_reported(self):
        data = {
            "esc_id": "BAD-001",
            "pipeline_version": "",
            "pep_id": "BAD-001",
            "pre_id": "BAD-001",
            "external_lab_token": "LAB-A",
            "sharing_date": "not-a-date",
            "caveat_confirmed": False,
            "dry_lab_only_acknowledged": False,
            "sharing_purpose": "invalid",
            "sharing_notes": "",
            "reviewer": "",
        }
        result = validate_external_sharing_clearance_dict(data)
        assert not result.passed
        assert len(result.errors) >= 5
