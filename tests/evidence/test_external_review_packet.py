"""Tests for external_review_packet module (E1)."""
from __future__ import annotations

import pytest

from openamp_foundry.evidence.external_review_packet import (
    BenchmarkSummary,
    CalibrationSummary,
    CandidateEntry,
    DRY_LAB_MAX_PROOF_LADDER_LEVEL,
    ExternalReviewPacket,
    PacketValidationResult,
    SafetyAttestations,
    VALID_CALIBRATION_ASSESSMENTS,
    format_external_review_packet,
    validate_external_review_packet,
)


# --- Helpers ---

def _make_candidate(**kwargs) -> CandidateEntry:
    defaults = dict(
        candidate_id="AMPF-001",
        sequence="KWKLFKKIGAVLKVL",
        ensemble_score=0.85,
        proof_ladder_level=2,
    )
    defaults.update(kwargs)
    return CandidateEntry(**defaults)


def _make_packet(**kwargs) -> ExternalReviewPacket:
    candidate = _make_candidate()
    defaults = dict(
        packet_id="ERP-2026-001",
        version="1.0.0",
        generated_at="2026-07-10T00:00:00Z",
        pipeline_version="0.9.0",
        git_sha="abc1234",
        candidate_count=1,
        candidates=[candidate],
        benchmark_summary=BenchmarkSummary(
            auroc=0.82, benchmark_name="500-AMP", n_positives=50, n_negatives=200
        ),
        calibration_summary=CalibrationSummary(
            calibration_assessment="well_calibrated", n_calibration_samples=100
        ),
        limitations=["Computational outputs are hypotheses. Not biological proof."],
        safety_attestations=SafetyAttestations(
            reviewed_by_human=True,
            safety_gate_passed=True,
            no_known_toxicity_claim=True,
        ),
        dry_lab_only_attestation=True,
        proof_ladder_level=2,
        contact="lab@example.org",
    )
    defaults.update(kwargs)
    return ExternalReviewPacket(**defaults)


# --- CandidateEntry ---

class TestCandidateEntry:
    def test_is_dataclass(self):
        c = _make_candidate()
        assert isinstance(c, CandidateEntry)

    def test_fields_accessible(self):
        c = _make_candidate()
        assert c.candidate_id == "AMPF-001"
        assert c.ensemble_score == pytest.approx(0.85)

    def test_optional_fields_default(self):
        c = _make_candidate()
        assert c.family == ""
        assert c.selection_rationale == ""

    def test_custom_fields(self):
        c = _make_candidate(family="defensin", selection_rationale="high score")
        assert c.family == "defensin"


# --- BenchmarkSummary ---

class TestBenchmarkSummary:
    def test_is_dataclass(self):
        b = BenchmarkSummary(auroc=0.8, benchmark_name="test", n_positives=10, n_negatives=40)
        assert isinstance(b, BenchmarkSummary)

    def test_fields_stored(self):
        b = BenchmarkSummary(0.75, "500-AMP", 50, 200)
        assert b.auroc == pytest.approx(0.75)
        assert b.benchmark_name == "500-AMP"

    def test_counts_stored(self):
        b = BenchmarkSummary(0.8, "test", 30, 120)
        assert b.n_positives == 30
        assert b.n_negatives == 120


# --- CalibrationSummary ---

class TestCalibrationSummary:
    def test_is_dataclass(self):
        c = CalibrationSummary(calibration_assessment="well_calibrated")
        assert isinstance(c, CalibrationSummary)

    def test_assessment_stored(self):
        c = CalibrationSummary("poorly_calibrated", n_calibration_samples=50)
        assert c.calibration_assessment == "poorly_calibrated"

    def test_default_samples(self):
        c = CalibrationSummary("uninformative")
        assert c.n_calibration_samples == 0


# --- SafetyAttestations ---

class TestSafetyAttestations:
    def test_is_dataclass(self):
        s = SafetyAttestations(True, True, True)
        assert isinstance(s, SafetyAttestations)

    def test_fields_stored(self):
        s = SafetyAttestations(reviewed_by_human=True, safety_gate_passed=False, no_known_toxicity_claim=True)
        assert s.reviewed_by_human is True
        assert s.safety_gate_passed is False

    def test_hemolysis_default_true(self):
        s = SafetyAttestations(True, True, True)
        assert s.hemolysis_assay_mandatory is True


# --- ExternalReviewPacket ---

class TestExternalReviewPacket:
    def test_is_dataclass(self):
        p = _make_packet()
        assert isinstance(p, ExternalReviewPacket)

    def test_fields_accessible(self):
        p = _make_packet()
        assert p.packet_id == "ERP-2026-001"
        assert p.dry_lab_only_attestation is True

    def test_default_notes_empty(self):
        p = _make_packet()
        assert p.notes == ""

    def test_candidates_stored(self):
        p = _make_packet()
        assert len(p.candidates) == 1


# --- PacketValidationResult ---

class TestPacketValidationResult:
    def test_is_dataclass(self):
        r = PacketValidationResult(True, [], [], "ERP-001", "ok")
        assert isinstance(r, PacketValidationResult)

    def test_fields_accessible(self):
        r = PacketValidationResult(False, ["v1"], ["w1"], "ERP-001", "bad")
        assert r.is_valid is False
        assert len(r.violations) == 1
        assert len(r.warnings) == 1

    def test_packet_id_stored(self):
        r = PacketValidationResult(True, [], [], "ERP-XYZ", "ok")
        assert r.packet_id == "ERP-XYZ"

    def test_summary_stored(self):
        r = PacketValidationResult(True, [], [], "ERP-001", "all good")
        assert r.validation_summary == "all good"


# --- validate_external_review_packet ---

class TestValidateExternalReviewPacket:
    def test_valid_packet_passes(self):
        result = validate_external_review_packet(_make_packet())
        assert result.is_valid is True
        assert result.violations == []

    def test_returns_validation_result(self):
        result = validate_external_review_packet(_make_packet())
        assert isinstance(result, PacketValidationResult)

    def test_invalid_packet_id_prefix(self):
        p = _make_packet(packet_id="PKT-001")
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("ERP-" in v for v in result.violations)

    def test_invalid_version_format(self):
        p = _make_packet(version="1.0")
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("version" in v for v in result.violations)

    def test_invalid_git_sha_too_short(self):
        p = _make_packet(git_sha="abc")
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_invalid_git_sha_uppercase(self):
        p = _make_packet(git_sha="ABC1234")
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_candidate_count_mismatch(self):
        p = _make_packet(candidate_count=5)
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("candidate_count" in v for v in result.violations)

    def test_empty_candidates(self):
        p = _make_packet(candidates=[], candidate_count=0)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_dry_lab_false_blocked(self):
        p = _make_packet(dry_lab_only_attestation=False)
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_proof_ladder_above_cap_blocked(self):
        p = _make_packet(proof_ladder_level=3)
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("proof_ladder_level" in v or "dry-lab cap" in v for v in result.violations)

    def test_proof_ladder_zero_blocked(self):
        p = _make_packet(proof_ladder_level=0)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_no_toxicity_claim_false_blocked(self):
        safety = SafetyAttestations(
            reviewed_by_human=True,
            safety_gate_passed=True,
            no_known_toxicity_claim=False,
        )
        p = _make_packet(safety_attestations=safety)
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("toxicity" in v for v in result.violations)

    def test_none_safety_attestations_blocked(self):
        p = _make_packet(safety_attestations=None)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_empty_limitations_blocked(self):
        p = _make_packet(limitations=[])
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("limitations" in v for v in result.violations)

    def test_auroc_above_one_blocked(self):
        bs = BenchmarkSummary(auroc=1.1, benchmark_name="test", n_positives=10, n_negatives=40)
        p = _make_packet(benchmark_summary=bs)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_auroc_below_zero_blocked(self):
        bs = BenchmarkSummary(auroc=-0.1, benchmark_name="test", n_positives=10, n_negatives=40)
        p = _make_packet(benchmark_summary=bs)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_invalid_calibration_assessment_blocked(self):
        cs = CalibrationSummary(calibration_assessment="excellent")
        p = _make_packet(calibration_summary=cs)
        result = validate_external_review_packet(p)
        assert not result.is_valid
        assert any("calibration_assessment" in v for v in result.violations)

    def test_valid_calibration_assessments_accepted(self):
        for assessment in VALID_CALIBRATION_ASSESSMENTS:
            cs = CalibrationSummary(calibration_assessment=assessment)
            p = _make_packet(calibration_summary=cs)
            result = validate_external_review_packet(p)
            cal_violations = [v for v in result.violations if "calibration_assessment" in v]
            assert cal_violations == [], f"{assessment} should be valid"

    def test_candidate_ensemble_score_above_one_blocked(self):
        c = _make_candidate(ensemble_score=1.5)
        p = _make_packet(candidates=[c], candidate_count=1)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_candidate_ensemble_score_below_zero_blocked(self):
        c = _make_candidate(ensemble_score=-0.1)
        p = _make_packet(candidates=[c], candidate_count=1)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_candidate_proof_ladder_above_cap_blocked(self):
        c = _make_candidate(proof_ladder_level=3)
        p = _make_packet(candidates=[c], candidate_count=1)
        result = validate_external_review_packet(p)
        assert not result.is_valid

    def test_candidate_proof_ladder_at_cap_ok(self):
        c = _make_candidate(proof_ladder_level=DRY_LAB_MAX_PROOF_LADDER_LEVEL)
        p = _make_packet(candidates=[c], candidate_count=1)
        result = validate_external_review_packet(p)
        candidate_violations = [v for v in result.violations if "candidates[0]" in v]
        assert candidate_violations == []

    def test_valid_summary_contains_packet_id(self):
        result = validate_external_review_packet(_make_packet())
        assert "ERP-2026-001" in result.validation_summary

    def test_violation_summary_contains_count(self):
        p = _make_packet(packet_id="NOT-VALID", dry_lab_only_attestation=False)
        result = validate_external_review_packet(p)
        assert str(len(result.violations)) in result.validation_summary or "violation" in result.validation_summary

    def test_dry_lab_max_level_is_2(self):
        assert DRY_LAB_MAX_PROOF_LADDER_LEVEL == 2

    def test_valid_calibration_vocabulary_size(self):
        assert len(VALID_CALIBRATION_ASSESSMENTS) == 4

    def test_multiple_violations_all_reported(self):
        p = _make_packet(
            packet_id="BAD",
            dry_lab_only_attestation=False,
            limitations=[],
        )
        result = validate_external_review_packet(p)
        assert len(result.violations) >= 3

    def test_git_sha_40_chars_valid(self):
        sha = "a" * 40
        p = _make_packet(git_sha=sha)
        result = validate_external_review_packet(p)
        sha_violations = [v for v in result.violations if "git_sha" in v]
        assert sha_violations == []

    def test_git_sha_7_chars_valid(self):
        p = _make_packet(git_sha="abcdef0")
        result = validate_external_review_packet(p)
        sha_violations = [v for v in result.violations if "git_sha" in v]
        assert sha_violations == []


# --- format_external_review_packet ---

class TestFormatExternalReviewPacket:
    def test_returns_string(self):
        assert isinstance(format_external_review_packet(_make_packet()), str)

    def test_contains_header(self):
        assert "EXTERNAL REVIEW PACKET" in format_external_review_packet(_make_packet())

    def test_contains_packet_id(self):
        assert "ERP-2026-001" in format_external_review_packet(_make_packet())

    def test_valid_packet_shows_valid(self):
        assert "VALID" in format_external_review_packet(_make_packet())

    def test_invalid_packet_shows_invalid(self):
        p = _make_packet(dry_lab_only_attestation=False)
        assert "INVALID" in format_external_review_packet(p)

    def test_contains_limitations(self):
        text = format_external_review_packet(_make_packet())
        assert "LIMITATIONS" in text

    def test_contains_safety_section(self):
        text = format_external_review_packet(_make_packet())
        assert "SAFETY" in text

    def test_dry_lab_yes_shown(self):
        text = format_external_review_packet(_make_packet())
        assert "YES" in text

    def test_notice_in_invalid_output(self):
        p = _make_packet(dry_lab_only_attestation=False)
        text = format_external_review_packet(p)
        assert "NOTICE" in text

    def test_candidate_count_shown(self):
        text = format_external_review_packet(_make_packet())
        assert "Candidates" in text

    def test_pipeline_version_shown(self):
        text = format_external_review_packet(_make_packet())
        assert "0.9.0" in text

    def test_summary_in_output(self):
        p = _make_packet()
        result = validate_external_review_packet(p)
        text = format_external_review_packet(p)
        assert result.validation_summary in text
