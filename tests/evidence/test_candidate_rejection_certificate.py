"""Tests for CandidateRejectionCertificate — Phase B B7.

63 tests across 7 groups.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.candidate_rejection_certificate import (
    CRC_PREFIX,
    VALID_PROOF_LADDER_LEVELS,
    VALID_REJECTION_GATES,
    VALID_REJECTION_REASONS,
    CandidateRejectionCertificate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid() -> CandidateRejectionCertificate:
    return CandidateRejectionCertificate(
        crc_id="CRC-0001",
        pipeline_version="0.10.30",
        candidate_id="AMPF-001",
        sequence="KWKLFKKIGAVLKVL",
        rejection_date="2024-06-01",
        rejection_gate="activity_threshold",
        rejection_reason="activity_score_below_threshold",
        evidence_summary="Activity score 0.31 below threshold 0.60; candidate rejected by activity gate.",
        proof_ladder_level_at_rejection="baseline_triaged",
        dry_lab_only=True,
        scores={"activity": 0.31, "safety": 0.85},
        notes="Reviewed by pipeline_owner.",
    )


def _valid_dict() -> dict:
    r = _valid()
    return {
        "crc_id": r.crc_id,
        "pipeline_version": r.pipeline_version,
        "candidate_id": r.candidate_id,
        "sequence": r.sequence,
        "rejection_date": r.rejection_date,
        "rejection_gate": r.rejection_gate,
        "rejection_reason": r.rejection_reason,
        "evidence_summary": r.evidence_summary,
        "proof_ladder_level_at_rejection": r.proof_ladder_level_at_rejection,
        "dry_lab_only": r.dry_lab_only,
        "scores": r.scores,
        "notes": r.notes,
    }


# ---------------------------------------------------------------------------
# Group 1: ValidRecord (8 tests)
# ---------------------------------------------------------------------------

class TestValidRecord:
    def test_valid_record_passes(self):
        assert _valid().validate() == []

    def test_valid_dict_passes(self):
        assert validate_dict(_valid_dict()) == []

    def test_crc_prefix_constant(self):
        assert CRC_PREFIX == "CRC-"

    def test_valid_rejection_gates_non_empty(self):
        assert len(VALID_REJECTION_GATES) >= 8

    def test_valid_rejection_reasons_non_empty(self):
        assert len(VALID_REJECTION_REASONS) >= 8

    def test_valid_proof_ladder_levels_count(self):
        assert len(VALID_PROOF_LADDER_LEVELS) == 10

    def test_record_with_warnings_only_passes(self):
        r = _valid()
        r.notes = ""
        result = r.validate()
        # warnings only, no errors
        assert all("WARNING" in msg for msg in result)

    def test_record_with_notes_and_evidence_no_warnings(self):
        r = _valid()
        r.notes = "Reviewed."
        result = r.validate()
        assert result == []


# ---------------------------------------------------------------------------
# Group 2: IDAndVersionRules (10 tests)
# ---------------------------------------------------------------------------

class TestIDAndVersionRules:
    def test_missing_crc_prefix_fails(self):
        r = _valid()
        r.crc_id = "WRONG-001"
        assert any("CRC-" in e for e in r.validate())

    def test_empty_crc_id_fails(self):
        r = _valid()
        r.crc_id = ""
        errors = r.validate()
        assert any("crc_id" in e for e in errors)

    def test_empty_pipeline_version_fails(self):
        r = _valid()
        r.pipeline_version = ""
        assert any("pipeline_version" in e for e in r.validate())

    def test_whitespace_pipeline_version_fails(self):
        r = _valid()
        r.pipeline_version = "   "
        assert any("pipeline_version" in e for e in r.validate())

    def test_empty_candidate_id_fails(self):
        r = _valid()
        r.candidate_id = ""
        assert any("candidate_id" in e for e in r.validate())

    def test_crc_prefix_with_suffix_passes(self):
        r = _valid()
        r.crc_id = "CRC-9999"
        assert r.validate() == []

    def test_lowercase_crc_fails(self):
        r = _valid()
        r.crc_id = "crc-001"
        errors = r.validate()
        assert any("CRC-" in e for e in errors)

    def test_pipeline_version_with_dots_passes(self):
        r = _valid()
        r.pipeline_version = "1.2.3"
        assert r.validate() == []

    def test_long_candidate_id_passes(self):
        r = _valid()
        r.candidate_id = "VERY-LONG-CANDIDATE-ID-0000001"
        assert r.validate() == []

    def test_validate_dict_wrong_prefix(self):
        d = _valid_dict()
        d["crc_id"] = "WRONG-001"
        errors = validate_dict(d)
        assert any("CRC-" in e for e in errors)


# ---------------------------------------------------------------------------
# Group 3: SequenceAndDateRules (8 tests)
# ---------------------------------------------------------------------------

class TestSequenceAndDateRules:
    def test_empty_sequence_fails(self):
        r = _valid()
        r.sequence = ""
        assert any("sequence" in e for e in r.validate())

    def test_invalid_sequence_chars_fails(self):
        r = _valid()
        r.sequence = "KWKLFKK123"
        assert any("amino acid" in e for e in r.validate())

    def test_valid_sequence_passes(self):
        r = _valid()
        r.sequence = "ACDEFGHIKLMNPQRSTVWY"
        assert r.validate() == []

    def test_non_iso_date_fails(self):
        r = _valid()
        r.rejection_date = "June 1 2024"
        assert any("ISO 8601" in e for e in r.validate())

    def test_valid_date_passes(self):
        r = _valid()
        r.rejection_date = "2024-12-31"
        assert r.validate() == []

    def test_datetime_format_passes(self):
        r = _valid()
        r.rejection_date = "2024-06-01T12:00:00Z"
        assert r.validate() == []

    def test_empty_date_fails(self):
        r = _valid()
        r.rejection_date = ""
        assert any("rejection_date" in e for e in r.validate())

    def test_lowercase_sequence_validated_by_content(self):
        r = _valid()
        r.sequence = "kwklfkkigavlkvl"
        # lowercase but valid AA chars when uppercased
        assert r.validate() == []


# ---------------------------------------------------------------------------
# Group 4: GateAndReasonRules (10 tests)
# ---------------------------------------------------------------------------

class TestGateAndReasonRules:
    def test_invalid_gate_fails(self):
        r = _valid()
        r.rejection_gate = "unknown_gate"
        assert any("rejection_gate" in e for e in r.validate())

    def test_all_valid_gates_pass(self):
        for gate in VALID_REJECTION_GATES:
            r = _valid()
            r.rejection_gate = gate
            # Pick a compatible reason
            errors = [e for e in r.validate() if "rejection_gate" in e]
            assert errors == [], f"Gate {gate!r} should be valid"

    def test_invalid_reason_fails(self):
        r = _valid()
        r.rejection_reason = "not_a_valid_reason"
        assert any("rejection_reason" in e for e in r.validate())

    def test_all_valid_reasons_pass(self):
        for reason in VALID_REJECTION_REASONS:
            r = _valid()
            r.rejection_reason = reason
            errors = [e for e in r.validate() if "rejection_reason" in e]
            assert errors == [], f"Reason {reason!r} should be valid"

    def test_empty_gate_fails(self):
        r = _valid()
        r.rejection_gate = ""
        assert any("rejection_gate" in e for e in r.validate())

    def test_empty_reason_fails(self):
        r = _valid()
        r.rejection_reason = ""
        assert any("rejection_reason" in e for e in r.validate())

    def test_wave0_5_safety_gate_passes(self):
        r = _valid()
        r.rejection_gate = "wave0_5_safety_gate"
        errors = [e for e in r.validate() if "rejection_gate" in e]
        assert errors == []

    def test_hemolysis_gate_passes(self):
        r = _valid()
        r.rejection_gate = "hemolysis_gate"
        errors = [e for e in r.validate() if "rejection_gate" in e]
        assert errors == []

    def test_manual_review_gate_passes(self):
        r = _valid()
        r.rejection_gate = "manual_review"
        errors = [e for e in r.validate() if "rejection_gate" in e]
        assert errors == []

    def test_empty_evidence_summary_fails(self):
        r = _valid()
        r.evidence_summary = ""
        assert any("evidence_summary" in e for e in r.validate())


# ---------------------------------------------------------------------------
# Group 5: ProofLadderAndDryLabRules (10 tests)
# ---------------------------------------------------------------------------

class TestProofLadderAndDryLabRules:
    def test_invalid_ladder_level_fails(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "not_a_level"
        assert any("proof_ladder_level" in e for e in r.validate())

    def test_all_dry_lab_safe_levels_pass(self):
        safe_levels = VALID_PROOF_LADDER_LEVELS[:5]  # up to multi_signal
        for level in safe_levels:
            r = _valid()
            r.proof_ladder_level_at_rejection = level
            errors = [e for e in r.validate() if "proof_ladder_level" in e]
            assert errors == [], f"Level {level!r} should be valid for dry_lab_only"

    def test_dry_lab_only_false_fails(self):
        r = _valid()
        r.dry_lab_only = False
        assert any("dry_lab_only" in e for e in r.validate())

    def test_dry_lab_cap_enforced(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "expert_reviewed_assay_proposal"  # level 5
        assert any("cap" in e or "dry_lab" in e for e in r.validate())

    def test_dry_lab_cap_at_multi_signal(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "multi_signal_candidate_evidence"
        errors = [e for e in r.validate() if "proof_ladder_level" in e]
        assert errors == []

    def test_valid_input_level_passes(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "valid_input"
        errors = [e for e in r.validate() if "proof_ladder_level" in e]
        assert errors == []

    def test_leakage_aware_benchmark_passes(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "leakage_aware_benchmark"
        errors = [e for e in r.validate() if "proof_ladder_level" in e]
        assert errors == []

    def test_independent_replication_blocked(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "independent_replication"
        assert any("dry_lab" in e or "cap" in e for e in r.validate())

    def test_reusable_discovery_loop_blocked(self):
        r = _valid()
        r.proof_ladder_level_at_rejection = "reusable_discovery_loop"
        assert any("dry_lab" in e or "cap" in e for e in r.validate())

    def test_scores_not_dict_fails(self):
        r = _valid()
        r.scores = "not_a_dict"  # type: ignore
        assert any("scores" in e for e in r.validate())


# ---------------------------------------------------------------------------
# Group 6: NotesAndWarnings (8 tests)
# ---------------------------------------------------------------------------

class TestNotesAndWarnings:
    def test_notes_exceeds_400_fails(self):
        r = _valid()
        r.notes = "x" * 401
        assert any("notes" in e for e in r.validate())

    def test_notes_exactly_400_passes(self):
        r = _valid()
        r.notes = "x" * 400
        errors = [e for e in r.validate() if "notes" in e and "WARNING" not in e]
        assert errors == []

    def test_empty_notes_produces_warning(self):
        r = _valid()
        r.notes = ""
        result = r.validate()
        assert any("WARNING" in msg and "notes" in msg for msg in result)

    def test_short_evidence_summary_produces_warning(self):
        r = _valid()
        r.evidence_summary = "Too short."
        result = r.validate()
        assert any("WARNING" in msg and "evidence_summary" in msg for msg in result)

    def test_warnings_not_errors(self):
        r = _valid()
        r.notes = ""
        result = r.validate()
        assert all("WARNING" in msg for msg in result)

    def test_valid_with_notes_no_warning(self):
        r = _valid()
        r.notes = "Reviewed by domain expert."
        result = r.validate()
        assert not any("notes" in msg for msg in result)

    def test_empty_scores_dict_passes(self):
        r = _valid()
        r.scores = {}
        assert r.validate() == []

    def test_multiple_scores_pass(self):
        r = _valid()
        r.scores = {"activity": 0.31, "safety": 0.85, "novelty": 0.55, "ensemble": 0.40}
        assert r.validate() == []


# ---------------------------------------------------------------------------
# Group 7: ValidateDictEdgeCases (9 tests)
# ---------------------------------------------------------------------------

class TestValidateDictEdgeCases:
    def test_empty_dict_fails(self):
        errors = validate_dict({})
        assert len(errors) > 0

    def test_missing_crc_id_fails(self):
        d = _valid_dict()
        del d["crc_id"]
        errors = validate_dict(d)
        assert any("crc_id" in e for e in errors)

    def test_missing_dry_lab_only_defaults_false(self):
        d = _valid_dict()
        del d["dry_lab_only"]
        errors = validate_dict(d)
        assert any("dry_lab_only" in e for e in errors)

    def test_missing_scores_defaults_empty_dict(self):
        d = _valid_dict()
        del d["scores"]
        # scores defaults to {} in validate_dict
        errors = [e for e in validate_dict(d) if "scores" in e and "WARNING" not in e]
        assert errors == []

    def test_missing_notes_defaults_empty_string(self):
        d = _valid_dict()
        del d["notes"]
        result = validate_dict(d)
        # empty notes → warning only
        assert all("WARNING" in msg for msg in result) or result == []

    def test_construction_error_returns_error(self):
        result = validate_dict({"crc_id": None, "pipeline_version": None})
        assert len(result) > 0

    def test_validate_dict_valid_returns_empty(self):
        assert validate_dict(_valid_dict()) == []

    def test_validate_dict_bad_gate(self):
        d = _valid_dict()
        d["rejection_gate"] = "made_up_gate"
        errors = validate_dict(d)
        assert any("rejection_gate" in e for e in errors)

    def test_validate_dict_bad_reason(self):
        d = _valid_dict()
        d["rejection_reason"] = "made_up_reason"
        errors = validate_dict(d)
        assert any("rejection_reason" in e for e in errors)
