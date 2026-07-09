"""Tests for coi_disclosure.py — Phase J J4."""
import pytest
from openamp_foundry.governance.coi_disclosure import (
    COIDisclosure,
    COIValidationResult,
    VALID_DISCLOSURE_TYPES,
    VALID_RELATIONSHIP_TYPES,
    validate_coi_disclosure,
    validate_coi_dict,
)


def _valid_disclosure(**overrides) -> COIDisclosure:
    defaults = dict(
        disclosure_id="COI-2026-001",
        disclosure_type="reviewer",
        subject="maintainer",
        related_artifact="REL-2026-001",
        relationship_type="none",
        description="",
        disclosure_date="2026-07-09",
        recusal_required=False,
        reviewer="lead-maintainer",
        review_status="acknowledged",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return COIDisclosure(**defaults)


def test_valid_reviewer_none_relationship_passes():
    result = validate_coi_disclosure(_valid_disclosure())
    assert result.passed
    assert result.errors == []


def test_valid_contributor_financial_relationship_passes():
    result = validate_coi_disclosure(_valid_disclosure(
        disclosure_type="contributor",
        relationship_type="financial",
        description="Holds equity in partner company",
        recusal_required=True,
    ))
    assert result.passed


def test_disclosure_id_not_starting_with_COI_fails():
    result = validate_coi_disclosure(_valid_disclosure(disclosure_id="ID-2026-001"))
    assert not result.passed
    assert any("COI-" in e for e in result.errors)


def test_empty_disclosure_id_fails():
    result = validate_coi_disclosure(_valid_disclosure(disclosure_id=""))
    assert not result.passed
    assert any("disclosure_id" in e for e in result.errors)


def test_invalid_disclosure_type_fails():
    result = validate_coi_disclosure(_valid_disclosure(disclosure_type="funder"))
    assert not result.passed
    assert any("disclosure_type" in e for e in result.errors)


def test_empty_subject_fails():
    result = validate_coi_disclosure(_valid_disclosure(subject=""))
    assert not result.passed
    assert any("subject" in e for e in result.errors)


def test_empty_related_artifact_fails():
    result = validate_coi_disclosure(_valid_disclosure(related_artifact=""))
    assert not result.passed
    assert any("related_artifact" in e for e in result.errors)


def test_invalid_relationship_type_fails():
    result = validate_coi_disclosure(_valid_disclosure(relationship_type="commercial"))
    assert not result.passed
    assert any("relationship_type" in e for e in result.errors)


def test_non_none_relationship_empty_description_fails():
    result = validate_coi_disclosure(_valid_disclosure(
        relationship_type="financial",
        description="",
    ))
    assert not result.passed
    assert any("description" in e for e in result.errors)


def test_none_relationship_empty_description_passes():
    result = validate_coi_disclosure(_valid_disclosure(
        relationship_type="none",
        description="",
    ))
    assert result.passed


def test_invalid_disclosure_date_fails():
    result = validate_coi_disclosure(_valid_disclosure(disclosure_date="09-07-2026"))
    assert not result.passed
    assert any("disclosure_date" in e for e in result.errors)


def test_empty_reviewer_fails():
    result = validate_coi_disclosure(_valid_disclosure(reviewer=""))
    assert not result.passed
    assert any("reviewer" in e for e in result.errors)


def test_invalid_review_status_fails():
    result = validate_coi_disclosure(_valid_disclosure(review_status="approved"))
    assert not result.passed
    assert any("review_status" in e for e in result.errors)


def test_dry_lab_only_false_fails():
    result = validate_coi_disclosure(_valid_disclosure(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


def test_financial_without_recusal_produces_warning():
    result = validate_coi_disclosure(_valid_disclosure(
        relationship_type="financial",
        description="Holds equity",
        recusal_required=False,
    ))
    assert result.passed
    assert any("financial" in w for w in result.warnings)


def test_validate_coi_dict_passes_with_valid_dict():
    d = dict(
        disclosure_id="COI-2026-001",
        disclosure_type="reviewer",
        subject="maintainer",
        related_artifact="REL-2026-001",
        relationship_type="none",
        description="",
        disclosure_date="2026-07-09",
        recusal_required=False,
        reviewer="lead-maintainer",
        review_status="acknowledged",
    )
    result = validate_coi_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_validate_coi_dict_fails_with_missing_fields():
    result = validate_coi_dict({"disclosure_id": "COI-2026-001"})
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    result = validate_coi_disclosure(_valid_disclosure())
    assert result.dry_lab_only is True
    result2 = validate_coi_disclosure(_valid_disclosure(dry_lab_only=False))
    assert result2.dry_lab_only is True


def test_valid_disclosure_types_has_4_entries():
    assert len(VALID_DISCLOSURE_TYPES) == 4
    assert "reviewer" in VALID_DISCLOSURE_TYPES
    assert "contributor" in VALID_DISCLOSURE_TYPES
    assert "maintainer" in VALID_DISCLOSURE_TYPES
    assert "external_advisor" in VALID_DISCLOSURE_TYPES


def test_valid_relationship_types_has_5_entries():
    assert len(VALID_RELATIONSHIP_TYPES) == 5
    assert "financial" in VALID_RELATIONSHIP_TYPES
    assert "institutional" in VALID_RELATIONSHIP_TYPES
    assert "competitive" in VALID_RELATIONSHIP_TYPES
    assert "personal" in VALID_RELATIONSHIP_TYPES
    assert "none" in VALID_RELATIONSHIP_TYPES
