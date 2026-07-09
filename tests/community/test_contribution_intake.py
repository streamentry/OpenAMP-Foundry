"""Tests for contribution intake validator."""
from __future__ import annotations
import pytest

from openamp_foundry.community.contribution_intake import (
    ContributionIntake,
    IntakeValidationResult,
    VALID_CONTRIBUTION_TYPES,
    REQUIRED_FIELDS_BY_TYPE,
    validate_contribution_intake,
    validate_intake_dict,
)


def test_valid_dataset_donation_passes():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset of 500 sequences",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences with MIC data",
            "data_license": "CC-BY-4.0",
            "record_count": 500,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is True


def test_valid_wet_lab_validation_with_human_review_passes():
    intake = ContributionIntake(
        institution_name="Research Hospital",
        contact_email="lab@hospital.org",
        contribution_type="wet_lab_validation",
        proposed_scope="MIC testing for 10 nominated candidates",
        human_review_required=True,
        dry_lab_only=True,
        extra_fields={
            "candidate_ids": "AMPF-001,AMPF-002",
            "assay_type": "MIC",
            "data_license": "CC-BY-4.0",
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is True


def test_empty_institution_name_fails():
    intake = ContributionIntake(
        institution_name="",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences",
            "data_license": "CC-BY-4.0",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "institution_name must not be empty" in result.errors


def test_invalid_email_no_at_fails():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="not-an-email",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences",
            "data_license": "CC-BY-4.0",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "contact_email must be a valid email address" in result.errors


def test_invalid_contribution_type_fails():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="invalid_type",
        proposed_scope="Something",
        human_review_required=False,
        dry_lab_only=True,
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "contribution_type" in result.errors[0]


def test_empty_proposed_scope_fails():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences",
            "data_license": "CC-BY-4.0",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "proposed_scope must not be empty" in result.errors


def test_dry_lab_only_false_fails():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset",
        human_review_required=False,
        dry_lab_only=False,
        extra_fields={
            "dataset_description": "AMP sequences",
            "data_license": "CC-BY-4.0",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "dry_lab_only must be True" in result.errors


def test_wet_lab_validation_without_human_review_fails():
    intake = ContributionIntake(
        institution_name="Research Hospital",
        contact_email="lab@hospital.org",
        contribution_type="wet_lab_validation",
        proposed_scope="MIC testing",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "candidate_ids": "AMPF-001",
            "assay_type": "MIC",
            "data_license": "CC-BY-4.0",
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert "human_review_required must be True for wet_lab_validation" in result.errors


def test_dataset_donation_missing_data_license_fails():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert any("data_license" in e for e in result.errors)


def test_algorithm_contribution_missing_has_tests_fails():
    intake = ContributionIntake(
        institution_name="University Lab",
        contact_email="lab@university.edu",
        contribution_type="algorithm_contribution",
        proposed_scope="New scoring module",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "algorithm_description": "Novel amphipathicity scorer",
            "data_license": "MIT",
        },
    )
    result = validate_contribution_intake(intake)
    assert result.passed is False
    assert any("has_tests" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    intake = ContributionIntake(
        institution_name="Example University",
        contact_email="research@example.edu",
        contribution_type="dataset_donation",
        proposed_scope="Curated AMP dataset",
        human_review_required=False,
        dry_lab_only=True,
        extra_fields={
            "dataset_description": "AMP sequences",
            "data_license": "CC-BY-4.0",
            "record_count": 100,
        },
    )
    result = validate_contribution_intake(intake)
    assert result.dry_lab_only is True


def test_validate_intake_dict_passes():
    d = {
        "institution_name": "Example University",
        "contact_email": "research@example.edu",
        "contribution_type": "dataset_donation",
        "proposed_scope": "Curated AMP dataset",
        "human_review_required": False,
        "dry_lab_only": True,
        "dataset_description": "AMP sequences with MIC data",
        "data_license": "CC-BY-4.0",
        "record_count": 500,
    }
    result = validate_intake_dict(d)
    assert result.passed is True
    assert result.institution_name == "Example University"


def test_validate_intake_dict_missing_top_level_field_fails():
    d = {
        "institution_name": "Example University",
        "contribution_type": "dataset_donation",
        "proposed_scope": "Curated AMP dataset",
        "human_review_required": False,
    }
    result = validate_intake_dict(d)
    assert result.passed is False
    assert any("contact_email" in e for e in result.errors)


def test_VALID_CONTRIBUTION_TYPES_has_six_entries():
    assert len(VALID_CONTRIBUTION_TYPES) == 6


def test_REQUIRED_FIELDS_BY_TYPE_has_six_keys():
    assert len(REQUIRED_FIELDS_BY_TYPE) == 6


def test_wet_lab_validation_gets_review_class_D():
    intake = ContributionIntake(
        institution_name="Research Hospital",
        contact_email="lab@hospital.org",
        contribution_type="wet_lab_validation",
        proposed_scope="MIC testing",
        human_review_required=True,
        dry_lab_only=True,
        extra_fields={
            "candidate_ids": "AMPF-001",
            "assay_type": "MIC",
            "data_license": "CC-BY-4.0",
        },
    )
    result = validate_contribution_intake(intake)
    assert result.required_review_class == "D"
    assert result.dry_lab_only is True
