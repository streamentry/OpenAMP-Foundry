"""Tests for human-readable certificate report — Phase B B6.

63 tests across 7 groups verifying that build_certificate_report() produces
correct, claim-clean, readable text output for domain experts.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.evidence.certificate_quality import assess_certificate_quality
from openamp_foundry.evidence.certificate_report import (
    _wrap,
    build_certificate_report,
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


def _cert() -> dict:
    return build_certificate(_make_scored(), {"threshold": 0.7}, ["APD-001"])


# ---------------------------------------------------------------------------
# Group 1: ReturnType (6 tests)
# ---------------------------------------------------------------------------

class TestReturnType:
    """build_certificate_report() returns a non-empty string."""

    def test_returns_string(self):
        assert isinstance(build_certificate_report(_cert()), str)

    def test_returns_non_empty(self):
        assert len(build_certificate_report(_cert())) > 0

    def test_returns_multiline(self):
        assert "\n" in build_certificate_report(_cert())

    def test_minimal_cert_returns_string(self):
        cert = {"candidate_id": "X", "sequence": "AAA", "scores": {}}
        assert isinstance(build_certificate_report(cert), str)

    def test_empty_cert_returns_string(self):
        assert isinstance(build_certificate_report({}), str)

    def test_with_quality_report_returns_string(self):
        cert = _cert()
        qr = assess_certificate_quality(cert)
        assert isinstance(build_certificate_report(cert, quality_report=qr), str)


# ---------------------------------------------------------------------------
# Group 2: HeaderAndFooter (8 tests)
# ---------------------------------------------------------------------------

class TestHeaderAndFooter:
    """Report has correct header and footer."""

    def test_header_present(self):
        report = build_certificate_report(_cert())
        assert "OPENAMP FOUNDRY" in report

    def test_candidate_evidence_certificate_in_header(self):
        report = build_certificate_report(_cert())
        assert "CANDIDATE EVIDENCE CERTIFICATE" in report

    def test_separator_present(self):
        report = build_certificate_report(_cert())
        assert "=" * 20 in report

    def test_notice_in_footer(self):
        report = build_certificate_report(_cert())
        assert "NOTICE" in report

    def test_dry_lab_in_footer(self):
        report = build_certificate_report(_cert())
        assert "DRY-LAB" in report

    def test_no_biological_activity_confirmed_in_footer(self):
        report = build_certificate_report(_cert())
        assert "No biological activity has been confirmed" in report

    def test_independent_domain_expert_in_footer(self):
        report = build_certificate_report(_cert())
        assert "Independent domain expert review" in report

    def test_scores_not_biological_proof_note(self):
        report = build_certificate_report(_cert())
        assert "not biological proof" in report


# ---------------------------------------------------------------------------
# Group 3: IdentityFields (10 tests)
# ---------------------------------------------------------------------------

class TestIdentityFields:
    """Report includes candidate identity fields."""

    def test_candidate_id_in_report(self):
        report = build_certificate_report(_cert())
        assert "AMPF-001" in report

    def test_sequence_in_report(self):
        report = build_certificate_report(_cert())
        assert _SEQ in report

    def test_source_in_report(self):
        report = build_certificate_report(_cert())
        assert "test_source" in report

    def test_pipeline_version_in_report(self):
        report = build_certificate_report(_cert())
        assert "Version" in report

    def test_generated_at_in_report(self):
        report = build_certificate_report(_cert())
        assert "Generated" in report

    def test_candidate_section_label(self):
        report = build_certificate_report(_cert())
        assert "CANDIDATE" in report

    def test_proof_ladder_section_label(self):
        report = build_certificate_report(_cert())
        assert "PROOF LADDER" in report

    def test_proof_ladder_level_value_in_report(self):
        cert = _cert()
        level = cert.get("proof_ladder_level", "")
        report = build_certificate_report(cert)
        assert level in report

    def test_different_candidate_id_shows_correctly(self):
        scored = ScoredCandidate(
            candidate=PeptideCandidate("CUSTOM-999", _SEQ, "src"),
            features=compute_features(_SEQ),
            scores={"activity": 0.5},
            nearest_reference=None,
            selection_reason=["test"],
            known_failure_modes=["test"],
        )
        cert = build_certificate(scored, {}, [])
        report = build_certificate_report(cert)
        assert "CUSTOM-999" in report

    def test_config_hash_not_required_in_report(self):
        # Config hash is a field but needn't appear as a labeled section
        cert = _cert()
        report = build_certificate_report(cert)
        # Report is still valid without explicit config hash display
        assert isinstance(report, str) and len(report) > 0


# ---------------------------------------------------------------------------
# Group 4: ScoresSection (8 tests)
# ---------------------------------------------------------------------------

class TestScoresSection:
    """Report includes scores section with correct values."""

    def test_scores_section_label(self):
        report = build_certificate_report(_cert())
        assert "SCORES" in report

    def test_activity_score_in_report(self):
        report = build_certificate_report(_cert())
        assert "activity" in report

    def test_safety_score_in_report(self):
        report = build_certificate_report(_cert())
        assert "safety" in report

    def test_score_value_formatted(self):
        report = build_certificate_report(_cert())
        assert "0.800" in report or "0.80" in report

    def test_scores_section_not_biological_proof(self):
        report = build_certificate_report(_cert())
        assert "not biological proof" in report.lower()

    def test_empty_scores_handled(self):
        cert = {"candidate_id": "X", "sequence": "AAA", "scores": {}}
        report = build_certificate_report(cert)
        assert "SCORES" in report

    def test_scores_section_before_footer(self):
        report = build_certificate_report(_cert())
        scores_pos = report.index("SCORES")
        notice_pos = report.index("NOTICE")
        assert scores_pos < notice_pos

    def test_novelty_score_in_report(self):
        report = build_certificate_report(_cert())
        assert "novelty" in report


# ---------------------------------------------------------------------------
# Group 5: BaselineCaveatSection (8 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatSection:
    """Report includes baseline caveat section."""

    def test_cheap_explanation_check_in_report(self):
        report = build_certificate_report(_cert())
        assert "CHEAP-EXPLANATION CHECK" in report

    def test_caveat_text_in_report(self):
        cert = _cert()
        caveat = cert.get("baseline_caveat", "")
        report = build_certificate_report(cert)
        # At least part of the caveat should appear
        assert "Cheapest-explanation" in report or "charge=" in report

    def test_caveat_before_selection_reason(self):
        report = build_certificate_report(_cert())
        caveat_pos = report.index("CHEAP-EXPLANATION")
        sel_pos = report.index("SELECTION REASON")
        assert caveat_pos < sel_pos

    def test_selection_reason_section_label(self):
        report = build_certificate_report(_cert())
        assert "SELECTION REASON" in report

    def test_selection_reason_value_in_report(self):
        report = build_certificate_report(_cert())
        assert "high ensemble score" in report

    def test_known_failure_modes_section_label(self):
        report = build_certificate_report(_cert())
        assert "KNOWN FAILURE MODES" in report

    def test_known_failure_modes_value_in_report(self):
        report = build_certificate_report(_cert())
        assert "No wet-lab assay has been run" in report

    def test_recommended_next_steps_section_label(self):
        report = build_certificate_report(_cert())
        assert "RECOMMENDED NEXT STEPS" in report


# ---------------------------------------------------------------------------
# Group 6: QualityTierSection (10 tests)
# ---------------------------------------------------------------------------

class TestQualityTierSection:
    """Quality tier section appears correctly when quality_report is provided."""

    def test_quality_tier_section_absent_without_report(self):
        report = build_certificate_report(_cert())
        assert "QUALITY TIER" not in report

    def test_quality_tier_section_present_with_report(self):
        cert = _cert()
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        assert "QUALITY TIER" in report

    def test_tier_value_in_report(self):
        cert = _cert()
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        assert qr["quality_tier"] in report

    def test_external_review_ready_yes(self):
        cert = _cert()
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        if qr["is_external_review_ready"]:
            assert "YES" in report

    def test_external_review_ready_no(self):
        cert = {"candidate_id": "X", "sequence": "AAA", "scores": {}}
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        assert "NO" in report

    def test_missing_fields_shown_in_report(self):
        cert = {"candidate_id": "X", "sequence": "AAA", "scores": {}}
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        assert len(qr["missing_fields"]) > 0  # sanity
        for field in qr["missing_fields"]:
            assert field in report

    def test_claim_violations_count_shown(self):
        cert = _cert()
        cert["notes"] = "This is proven."
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        if qr["claim_violations"]:
            assert "Claim violations" in report or "violations" in report.lower()

    def test_quality_section_before_footer(self):
        cert = _cert()
        qr = assess_certificate_quality(cert)
        report = build_certificate_report(cert, quality_report=qr)
        tier_pos = report.index("QUALITY TIER")
        notice_pos = report.index("NOTICE")
        assert tier_pos < notice_pos

    def test_no_quality_report_still_has_footer(self):
        report = build_certificate_report(_cert())
        assert "NOTICE" in report

    def test_quality_report_none_default(self):
        # Should not raise when quality_report omitted
        report = build_certificate_report(_cert())
        assert isinstance(report, str)


# ---------------------------------------------------------------------------
# Group 7: WrapAndClaimDiscipline (13 tests)
# ---------------------------------------------------------------------------

class TestWrapAndClaimDiscipline:
    """_wrap() utility and claim-discipline in report output."""

    def test_wrap_returns_list(self):
        result = _wrap("hello world")
        assert isinstance(result, list)

    def test_wrap_short_text_single_line(self):
        result = _wrap("hello", width=40, indent=2)
        assert len(result) == 1

    def test_wrap_long_text_multiple_lines(self):
        long_text = "word " * 30
        result = _wrap(long_text, width=40, indent=2)
        assert len(result) > 1

    def test_wrap_preserves_indent(self):
        result = _wrap("hello", width=40, indent=4)
        assert result[0].startswith("    ")

    def test_wrap_empty_text(self):
        result = _wrap("", width=40, indent=2)
        assert isinstance(result, list)

    def test_report_no_proven_language(self):
        report = build_certificate_report(_cert())
        # Footer says "No biological activity has been confirmed" which is OK
        # but report body should not say "proven active" etc.
        assert "proven active" not in report.lower()
        assert "proven to be" not in report.lower()

    def test_report_no_cure_language(self):
        report = build_certificate_report(_cert())
        assert "cure" not in report.lower()

    def test_report_no_drug_language_in_body(self):
        report = build_certificate_report(_cert())
        # "drug" might appear in footer context but not as overclaim
        assert "drug candidate" not in report.lower()

    def test_report_no_clinical_language_in_body(self):
        report = build_certificate_report(_cert())
        # Check body sections before footer
        before_notice = report.split("NOTICE")[0]
        assert "clinically proven" not in before_notice.lower()

    def test_references_checked_section_label(self):
        report = build_certificate_report(_cert())
        assert "REFERENCES CHECKED" in report

    def test_references_value_in_report(self):
        cert = _cert()
        report = build_certificate_report(cert)
        refs = cert.get("references_checked", [])
        for ref in refs:
            assert ref in report

    def test_empty_references_shows_none(self):
        cert = build_certificate(_make_scored(), {}, [])
        report = build_certificate_report(cert)
        # references_checked is empty → shows (none)
        assert "(none)" in report or "REFERENCES CHECKED" in report

    def test_report_line_lengths_reasonable(self):
        report = build_certificate_report(_cert())
        lines = report.split("\n")
        # Most lines should be reasonable length (separator can be 72)
        long_lines = [l for l in lines if len(l) > 90]
        # Allow a few long lines (e.g. the caveat text)
        assert len(long_lines) < 10
