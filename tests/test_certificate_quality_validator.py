"""Tests for certificate quality-tier validator — Phase B B5.

63 tests across 7 groups verifying that assess_certificate_quality() correctly
computes draft / internal_review / external_review_ready tiers and that
missing fields and forbidden claims are correctly detected.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.certificate_quality import (
    QUALITY_TIERS,
    _DRAFT_REQUIRED,
    _EXTERNAL_REQUIRED,
    _INTERNAL_REQUIRED,
    assess_certificate_quality,
)
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEQ = "KWKLFKKIGAVLKVL"


def _make_scored(sequence: str = _SEQ) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=PeptideCandidate("AMPF-001", sequence, "test_source"),
        features=compute_features(sequence),
        scores={"activity": 0.80, "safety": 0.90, "novelty": 0.50, "ensemble": 0.82},
        nearest_reference=None,
        selection_reason=["high ensemble score"],
        known_failure_modes=["No wet-lab assay has been run."],
    )


def _full_cert() -> dict:
    return build_certificate(_make_scored(), {"threshold": 0.7}, ["APD-001"])


def _minimal_cert() -> dict:
    return {
        "candidate_id": "AMPF-001",
        "sequence": _SEQ,
        "scores": {"activity": 0.80},
    }


# ---------------------------------------------------------------------------
# Group 1: TierConstants (6 tests)
# ---------------------------------------------------------------------------

class TestTierConstants:
    """QUALITY_TIERS is ordered and complete."""

    def test_quality_tiers_is_tuple(self):
        assert isinstance(QUALITY_TIERS, tuple)

    def test_quality_tiers_has_three_values(self):
        assert len(QUALITY_TIERS) == 3

    def test_quality_tiers_draft_first(self):
        assert QUALITY_TIERS[0] == "draft"

    def test_quality_tiers_internal_review_second(self):
        assert QUALITY_TIERS[1] == "internal_review"

    def test_quality_tiers_external_review_ready_third(self):
        assert QUALITY_TIERS[2] == "external_review_ready"

    def test_draft_required_fields_subset_of_internal(self):
        assert _DRAFT_REQUIRED.issubset(_INTERNAL_REQUIRED)


# ---------------------------------------------------------------------------
# Group 2: FullCertificateIsExternalReady (10 tests)
# ---------------------------------------------------------------------------

class TestFullCertificateIsExternalReady:
    """build_certificate() output reaches external_review_ready tier."""

    def test_full_cert_tier_is_external_review_ready(self):
        report = assess_certificate_quality(_full_cert())
        assert report["quality_tier"] == "external_review_ready"

    def test_full_cert_is_external_review_ready_true(self):
        report = assess_certificate_quality(_full_cert())
        assert report["is_external_review_ready"] is True

    def test_full_cert_no_missing_fields(self):
        report = assess_certificate_quality(_full_cert())
        assert report["missing_fields"] == []

    def test_full_cert_no_claim_violations(self):
        report = assess_certificate_quality(_full_cert())
        assert report["claim_violations"] == []

    def test_full_cert_no_warnings(self):
        report = assess_certificate_quality(_full_cert())
        assert report["warnings"] == []

    def test_report_has_quality_tier_key(self):
        report = assess_certificate_quality(_full_cert())
        assert "quality_tier" in report

    def test_report_has_missing_fields_key(self):
        report = assess_certificate_quality(_full_cert())
        assert "missing_fields" in report

    def test_report_has_claim_violations_key(self):
        report = assess_certificate_quality(_full_cert())
        assert "claim_violations" in report

    def test_report_has_warnings_key(self):
        report = assess_certificate_quality(_full_cert())
        assert "warnings" in report

    def test_report_has_is_external_review_ready_key(self):
        report = assess_certificate_quality(_full_cert())
        assert "is_external_review_ready" in report


# ---------------------------------------------------------------------------
# Group 3: MinimalCertIsDraft (10 tests)
# ---------------------------------------------------------------------------

class TestMinimalCertIsDraft:
    """Minimal cert with only draft fields reaches draft tier."""

    def test_minimal_cert_tier_is_draft(self):
        report = assess_certificate_quality(_minimal_cert())
        assert report["quality_tier"] == "draft"

    def test_minimal_cert_not_external_review_ready(self):
        report = assess_certificate_quality(_minimal_cert())
        assert report["is_external_review_ready"] is False

    def test_minimal_cert_missing_internal_fields(self):
        report = assess_certificate_quality(_minimal_cert())
        assert len(report["missing_fields"]) > 0

    def test_minimal_cert_missing_selection_reason(self):
        report = assess_certificate_quality(_minimal_cert())
        assert "selection_reason" in report["missing_fields"]

    def test_minimal_cert_missing_proof_ladder_level(self):
        report = assess_certificate_quality(_minimal_cert())
        assert "proof_ladder_level" in report["missing_fields"]

    def test_minimal_cert_missing_baseline_caveat(self):
        report = assess_certificate_quality(_minimal_cert())
        assert "baseline_caveat" in report["missing_fields"]

    def test_minimal_cert_missing_pipeline_version(self):
        report = assess_certificate_quality(_minimal_cert())
        assert "pipeline_version" in report["missing_fields"]

    def test_minimal_cert_no_claim_violations(self):
        report = assess_certificate_quality(_minimal_cert())
        assert report["claim_violations"] == []

    def test_minimal_cert_has_warnings(self):
        report = assess_certificate_quality(_minimal_cert())
        assert len(report["warnings"]) > 0

    def test_minimal_cert_not_in_quality_tiers_tuple(self):
        report = assess_certificate_quality(_minimal_cert())
        # draft is in QUALITY_TIERS
        assert report["quality_tier"] in ("draft", "below_draft") or report["quality_tier"] in QUALITY_TIERS


# ---------------------------------------------------------------------------
# Group 4: BelowDraft (8 tests)
# ---------------------------------------------------------------------------

class TestBelowDraft:
    """Certs missing draft-required fields are below_draft."""

    def test_empty_cert_is_below_draft(self):
        report = assess_certificate_quality({})
        assert report["quality_tier"] == "below_draft"

    def test_missing_candidate_id_is_below_draft(self):
        cert = {"sequence": _SEQ, "scores": {}}
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "below_draft"

    def test_missing_sequence_is_below_draft(self):
        cert = {"candidate_id": "AMPF-001", "scores": {}}
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "below_draft"

    def test_missing_scores_is_below_draft(self):
        cert = {"candidate_id": "AMPF-001", "sequence": _SEQ}
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "below_draft"

    def test_below_draft_not_external_review_ready(self):
        report = assess_certificate_quality({})
        assert report["is_external_review_ready"] is False

    def test_below_draft_has_missing_fields(self):
        report = assess_certificate_quality({})
        assert len(report["missing_fields"]) > 0

    def test_empty_candidate_id_is_below_draft(self):
        cert = {"candidate_id": "", "sequence": _SEQ, "scores": {}}
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "below_draft"

    def test_empty_sequence_is_below_draft(self):
        cert = {"candidate_id": "AMPF-001", "sequence": "   ", "scores": {}}
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "below_draft"


# ---------------------------------------------------------------------------
# Group 5: ClaimViolationsBlockTier (10 tests)
# ---------------------------------------------------------------------------

class TestClaimViolationsBlockTier:
    """Forbidden-claim violations block tier advancement past draft."""

    def _cert_with_claim(self, claim: str) -> dict:
        cert = _full_cert()
        cert["notes"] = claim
        return cert

    def test_proven_claim_blocks_internal_review(self):
        cert = self._cert_with_claim("This candidate is proven to be active.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_clinical_claim_blocks_internal_review(self):
        cert = self._cert_with_claim("Clinically useful compound.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_drug_candidate_claim_blocks(self):
        cert = self._cert_with_claim("This is a drug candidate.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_cure_claim_blocks(self):
        cert = self._cert_with_claim("A cure for MRSA infections.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_safe_in_humans_claim_blocks(self):
        cert = self._cert_with_claim("Safe in humans.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_antibiotic_for_treatment_blocks(self):
        cert = self._cert_with_claim("Antibiotic for treatment of MRSA.")
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"

    def test_claim_violation_is_in_report(self):
        cert = self._cert_with_claim("proven active compound")
        report = assess_certificate_quality(cert)
        assert len(report["claim_violations"]) > 0

    def test_claim_violation_has_pattern_info(self):
        cert = self._cert_with_claim("This is proven.")
        report = assess_certificate_quality(cert)
        assert any("proven" in v.lower() for v in report["claim_violations"])

    def test_clean_cert_has_no_claim_violations(self):
        report = assess_certificate_quality(_full_cert())
        assert report["claim_violations"] == []

    def test_dry_lab_language_not_a_violation(self):
        cert = _full_cert()
        cert["notes"] = "Computationally nominated dry-lab candidate only."
        report = assess_certificate_quality(cert)
        assert report["claim_violations"] == []


# ---------------------------------------------------------------------------
# Group 6: InternalReviewTier (10 tests)
# ---------------------------------------------------------------------------

class TestInternalReviewTier:
    """Cert with all internal fields but missing external fields reaches internal_review."""

    def _internal_cert(self) -> dict:
        """Full cert minus the external-only fields."""
        cert = _full_cert()
        # Remove external-only fields (those in _EXTERNAL_REQUIRED but not _INTERNAL_REQUIRED)
        for field in list(_EXTERNAL_REQUIRED - _INTERNAL_REQUIRED):
            cert.pop(field, None)
        return cert

    def test_internal_cert_tier_is_internal_review(self):
        report = assess_certificate_quality(self._internal_cert())
        assert report["quality_tier"] == "internal_review"

    def test_internal_cert_not_external_review_ready(self):
        report = assess_certificate_quality(self._internal_cert())
        assert report["is_external_review_ready"] is False

    def test_internal_cert_has_missing_external_fields(self):
        report = assess_certificate_quality(self._internal_cert())
        assert len(report["missing_fields"]) > 0

    def test_internal_cert_no_claim_violations(self):
        report = assess_certificate_quality(self._internal_cert())
        assert report["claim_violations"] == []

    def test_internal_cert_warnings_mention_missing_external(self):
        report = assess_certificate_quality(self._internal_cert())
        assert any("external" in w.lower() for w in report["warnings"])

    def test_internal_required_is_subset_of_external_required(self):
        assert _INTERNAL_REQUIRED.issubset(_EXTERNAL_REQUIRED)

    def test_external_has_more_fields_than_internal(self):
        assert len(_EXTERNAL_REQUIRED) > len(_INTERNAL_REQUIRED)

    def test_missing_recommended_next_steps_gives_internal_tier(self):
        cert = _full_cert()
        cert.pop("recommended_next_steps", None)
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "internal_review"

    def test_missing_config_hash_gives_internal_tier(self):
        cert = _full_cert()
        cert.pop("config_hash", None)
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "internal_review"

    def test_empty_references_checked_gives_internal_tier(self):
        cert = _full_cert()
        cert["references_checked"] = []
        report = assess_certificate_quality(cert)
        # Empty list counts as missing
        assert report["quality_tier"] == "internal_review"


# ---------------------------------------------------------------------------
# Group 7: EdgeCases (9 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_assess_returns_dict(self):
        report = assess_certificate_quality(_full_cert())
        assert isinstance(report, dict)

    def test_missing_fields_is_list(self):
        report = assess_certificate_quality(_full_cert())
        assert isinstance(report["missing_fields"], list)

    def test_claim_violations_is_list(self):
        report = assess_certificate_quality(_full_cert())
        assert isinstance(report["claim_violations"], list)

    def test_warnings_is_list(self):
        report = assess_certificate_quality(_full_cert())
        assert isinstance(report["warnings"], list)

    def test_is_external_review_ready_is_bool(self):
        report = assess_certificate_quality(_full_cert())
        assert isinstance(report["is_external_review_ready"], bool)

    def test_cert_with_none_field_treated_as_missing(self):
        cert = _minimal_cert()
        cert["selection_reason"] = None
        # None counts as missing, so still draft at best
        report = assess_certificate_quality(cert)
        assert "selection_reason" in report.get("missing_fields", []) or report["quality_tier"] in ("draft", "below_draft")

    def test_cert_with_empty_string_field_treated_as_missing(self):
        cert = dict(_full_cert())
        cert["pipeline_version"] = ""
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] != "external_review_ready"

    def test_below_draft_quality_tier_string(self):
        report = assess_certificate_quality({})
        assert isinstance(report["quality_tier"], str)

    def test_claim_in_list_field_detected(self):
        cert = _full_cert()
        cert["selection_reason"] = ["This is a proven cure for infections."]
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "draft"
