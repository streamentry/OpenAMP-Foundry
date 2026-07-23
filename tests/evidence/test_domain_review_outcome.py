"""Tests for DomainReviewOutcome schema — Phase E E9."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.domain_review_outcome import (
    DomainReviewOutcome,
    DomainReviewOutcomeResult,
    validate_domain_review_outcome,
    validate_domain_review_outcome_dict,
)


def _valid_entry(**overrides) -> DomainReviewOutcome:
    defaults = dict(
        dro_id="DRO-001",
        pipeline_version="v0.10.13",
        pep_id="PEP-001",
        rvq_id="RVQ-001",
        reviewer_token="REV-TOKEN-A",
        review_domain="antimicrobial_activity",
        review_date="2026-07-10",
        outcome_verdict="approve",
        outcome_confidence="high",
        outcome_rationale="Activity predictions are well-supported by the evidence.",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return DomainReviewOutcome(**defaults)


# ── 1. DRO ID validation ──────────────────────────────────────────────────────

class TestDroIdValidation:
    def test_valid_dro_prefix(self):
        result = validate_domain_review_outcome(_valid_entry())
        assert result.passed

    def test_wrong_prefix_fails(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id="RVQ-001"))
        assert not result.passed
        assert any("dro_id must start with 'DRO-'" in e for e in result.errors)

    def test_empty_dro_id_fails(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id=""))
        assert not result.passed

    def test_lowercase_prefix_fails(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id="dro-001"))
        assert not result.passed

    def test_dro_long_id_passes(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id="DRO-20260710-001"))
        assert result.passed

    def test_dro_id_in_result(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id="DRO-XYZ"))
        assert result.dro_id == "DRO-XYZ"

    def test_no_prefix_fails(self):
        result = validate_domain_review_outcome(_valid_entry(dro_id="001"))
        assert not result.passed


# ── 2. PEP ID validation ──────────────────────────────────────────────────────

class TestPepIdValidation:
    def test_valid_pep_prefix(self):
        result = validate_domain_review_outcome(_valid_entry())
        assert result.passed

    def test_wrong_pep_prefix_fails(self):
        result = validate_domain_review_outcome(_valid_entry(pep_id="RVQ-001"))
        assert not result.passed
        assert any("pep_id must start with 'PEP-'" in e for e in result.errors)

    def test_empty_pep_id_fails(self):
        result = validate_domain_review_outcome(_valid_entry(pep_id=""))
        assert not result.passed

    def test_pep_id_in_result(self):
        result = validate_domain_review_outcome(_valid_entry(pep_id="PEP-999"))
        assert result.pep_id == "PEP-999"

    def test_pep_long_id_passes(self):
        result = validate_domain_review_outcome(_valid_entry(pep_id="PEP-2026-001"))
        assert result.passed


# ── 3. RVQ ID validation ──────────────────────────────────────────────────────

class TestRvqIdValidation:
    def test_valid_rvq_prefix(self):
        result = validate_domain_review_outcome(_valid_entry())
        assert result.passed

    def test_wrong_rvq_prefix_fails(self):
        result = validate_domain_review_outcome(_valid_entry(rvq_id="PEP-001"))
        assert not result.passed
        assert any("rvq_id must start with 'RVQ-'" in e for e in result.errors)

    def test_empty_rvq_id_fails(self):
        result = validate_domain_review_outcome(_valid_entry(rvq_id=""))
        assert not result.passed

    def test_rvq_id_in_result(self):
        result = validate_domain_review_outcome(_valid_entry(rvq_id="RVQ-999"))
        assert result.rvq_id == "RVQ-999"

    def test_rvq_long_id_passes(self):
        result = validate_domain_review_outcome(_valid_entry(rvq_id="RVQ-2026-001"))
        assert result.passed


# ── 4. Required fields ────────────────────────────────────────────────────────

class TestRequiredFields:
    def test_all_valid_passes(self):
        result = validate_domain_review_outcome(_valid_entry())
        assert result.passed

    def test_empty_pipeline_version_fails(self):
        result = validate_domain_review_outcome(_valid_entry(pipeline_version=""))
        assert not result.passed
        assert any("pipeline_version must not be empty" in e for e in result.errors)

    def test_whitespace_pipeline_fails(self):
        result = validate_domain_review_outcome(_valid_entry(pipeline_version="   "))
        assert not result.passed

    def test_empty_reviewer_token_fails(self):
        result = validate_domain_review_outcome(_valid_entry(reviewer_token=""))
        assert not result.passed
        assert any("reviewer_token must not be empty" in e for e in result.errors)

    def test_whitespace_reviewer_token_fails(self):
        result = validate_domain_review_outcome(_valid_entry(reviewer_token="  "))
        assert not result.passed

    def test_multiple_empty_fields_all_reported(self):
        result = validate_domain_review_outcome(
            _valid_entry(pipeline_version="", reviewer_token="")
        )
        assert not result.passed
        assert len([e for e in result.errors if "must not be empty" in e]) == 2


# ── 5. Review domain validation ───────────────────────────────────────────────

class TestReviewDomainValidation:
    def test_antimicrobial_activity_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="antimicrobial_activity")
        )
        assert result.passed

    def test_toxicology_passes(self):
        result = validate_domain_review_outcome(_valid_entry(review_domain="toxicology"))
        assert result.passed

    def test_structural_biology_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="structural_biology")
        )
        assert result.passed

    def test_clinical_microbiology_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="clinical_microbiology")
        )
        assert result.passed

    def test_computational_chemistry_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="computational_chemistry")
        )
        assert result.passed

    def test_general_biomedical_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="general_biomedical")
        )
        assert result.passed

    def test_invalid_domain_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_domain="physics"))
        assert not result.passed
        assert any("review_domain must be one of" in e for e in result.errors)

    def test_empty_domain_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_domain=""))
        assert not result.passed

    def test_domain_in_result(self):
        result = validate_domain_review_outcome(
            _valid_entry(review_domain="toxicology")
        )
        assert result.review_domain == "toxicology"


# ── 6. Review date ────────────────────────────────────────────────────────────

class TestReviewDate:
    def test_valid_date(self):
        result = validate_domain_review_outcome(_valid_entry(review_date="2026-07-10"))
        assert result.passed

    def test_date_without_dashes_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_date="20260710"))
        assert not result.passed
        assert any("review_date must be ISO format" in e for e in result.errors)

    def test_slash_date_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_date="2026/07/10"))
        assert not result.passed

    def test_empty_date_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_date=""))
        assert not result.passed

    def test_another_valid_date(self):
        result = validate_domain_review_outcome(_valid_entry(review_date="2025-06-01"))
        assert result.passed

    def test_impossible_calendar_date_fails(self):
        result = validate_domain_review_outcome(_valid_entry(review_date="2026-02-30"))
        assert not result.passed
        assert any("review_date must be ISO format" in e for e in result.errors)


# ── 7. Outcome verdict validation ─────────────────────────────────────────────

class TestOutcomeVerdictValidation:
    def test_approve_passes(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_verdict="approve"))
        assert result.passed

    def test_reject_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="reject", outcome_confidence="high")
        )
        assert result.passed

    def test_conditional_approve_with_rationale_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(
                outcome_verdict="conditional_approve",
                outcome_rationale="Approve if baseline is updated.",
            )
        )
        assert result.passed

    def test_request_revision_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="request_revision")
        )
        assert result.passed

    def test_insufficient_data_with_rationale_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(
                outcome_verdict="insufficient_data",
                outcome_rationale="Need full BCM report.",
            )
        )
        assert result.passed

    def test_invalid_verdict_fails(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="maybe")
        )
        assert not result.passed
        assert any("outcome_verdict must be one of" in e for e in result.errors)

    def test_empty_verdict_fails(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_verdict=""))
        assert not result.passed

    def test_verdict_in_result(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="request_revision")
        )
        assert result.outcome_verdict == "request_revision"


# ── 8. Outcome confidence validation ──────────────────────────────────────────

class TestOutcomeConfidenceValidation:
    def test_high_passes(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_confidence="high"))
        assert result.passed

    def test_medium_passes(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_confidence="medium"))
        assert result.passed

    def test_low_passes(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_confidence="low"))
        assert result.passed

    def test_invalid_confidence_fails(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_confidence="very_high")
        )
        assert not result.passed
        assert any("outcome_confidence must be one of" in e for e in result.errors)

    def test_empty_confidence_fails(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_confidence=""))
        assert not result.passed

    def test_confidence_in_result(self):
        result = validate_domain_review_outcome(_valid_entry(outcome_confidence="medium"))
        assert result.outcome_confidence == "medium"

    def test_reject_low_confidence_warns(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="reject", outcome_confidence="low")
        )
        assert result.passed
        assert any("low-confidence rejection" in w for w in result.warnings)


# ── 9. Warnings ───────────────────────────────────────────────────────────────

class TestWarnings:
    def test_conditional_approve_no_rationale_warns(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="conditional_approve", outcome_rationale="")
        )
        assert result.passed
        assert any("conditional_approve" in w for w in result.warnings)

    def test_conditional_approve_with_rationale_no_warning(self):
        result = validate_domain_review_outcome(
            _valid_entry(
                outcome_verdict="conditional_approve",
                outcome_rationale="Need updated baseline.",
            )
        )
        assert result.passed
        assert not any("conditional_approve" in w for w in result.warnings)

    def test_insufficient_data_no_rationale_warns(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="insufficient_data", outcome_rationale="")
        )
        assert result.passed
        assert any("insufficient_data" in w for w in result.warnings)

    def test_approve_high_confidence_no_warnings(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_verdict="approve", outcome_confidence="high")
        )
        assert result.passed
        assert len(result.warnings) == 0

    def test_dry_lab_only_in_result(self):
        result = validate_domain_review_outcome(_valid_entry(dry_lab_only=True))
        assert result.dry_lab_only is True

    def test_rationale_length_at_limit_passes(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_rationale="x" * 400)
        )
        assert result.passed

    def test_rationale_over_limit_fails(self):
        result = validate_domain_review_outcome(
            _valid_entry(outcome_rationale="x" * 401)
        )
        assert not result.passed
        assert any("outcome_rationale must be at most 400" in e for e in result.errors)


# ── 10. Dict-based validator ──────────────────────────────────────────────────

class TestDictValidator:
    def test_valid_dict_passes(self):
        data = {
            "dro_id": "DRO-001",
            "pipeline_version": "v0.10.13",
            "pep_id": "PEP-001",
            "rvq_id": "RVQ-001",
            "reviewer_token": "REV-A",
            "review_domain": "antimicrobial_activity",
            "review_date": "2026-07-10",
            "outcome_verdict": "approve",
            "outcome_confidence": "high",
            "outcome_rationale": "Solid evidence base.",
            "dry_lab_only": True,
        }
        result = validate_domain_review_outcome_dict(data)
        assert result.passed

    def test_dict_wrong_prefix_fails(self):
        data = {
            "dro_id": "BAD-001",
            "pipeline_version": "v0.10.13",
            "pep_id": "PEP-001",
            "rvq_id": "RVQ-001",
            "reviewer_token": "REV-A",
            "review_domain": "toxicology",
            "review_date": "2026-07-10",
            "outcome_verdict": "approve",
            "outcome_confidence": "high",
            "outcome_rationale": "ok",
        }
        result = validate_domain_review_outcome_dict(data)
        assert not result.passed

    def test_dict_invalid_domain_fails(self):
        data = {
            "dro_id": "DRO-001",
            "pipeline_version": "v0.10.13",
            "pep_id": "PEP-001",
            "rvq_id": "RVQ-001",
            "reviewer_token": "REV-A",
            "review_domain": "astrophysics",
            "review_date": "2026-07-10",
            "outcome_verdict": "approve",
            "outcome_confidence": "high",
            "outcome_rationale": "ok",
        }
        result = validate_domain_review_outcome_dict(data)
        assert not result.passed

    def test_dict_defaults_dry_lab_true(self):
        data = {
            "dro_id": "DRO-001",
            "pipeline_version": "v0.10.13",
            "pep_id": "PEP-001",
            "rvq_id": "RVQ-001",
            "reviewer_token": "REV-A",
            "review_domain": "clinical_microbiology",
            "review_date": "2026-07-10",
            "outcome_verdict": "request_revision",
            "outcome_confidence": "medium",
            "outcome_rationale": "Needs more data.",
        }
        result = validate_domain_review_outcome_dict(data)
        assert result.dry_lab_only is True

    def test_dict_multiple_errors_reported(self):
        data = {
            "dro_id": "BAD",
            "pipeline_version": "",
            "pep_id": "WRONG",
            "rvq_id": "WRONG",
            "reviewer_token": "",
            "review_domain": "unknown",
            "review_date": "not-a-date",
            "outcome_verdict": "invalid",
            "outcome_confidence": "invalid",
            "outcome_rationale": "x" * 500,
        }
        result = validate_domain_review_outcome_dict(data)
        assert not result.passed
        assert len(result.errors) >= 5
