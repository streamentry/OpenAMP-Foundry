"""Tests for E2 example external review packet (toy/mock data only)."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.example_external_review_packet import (
    TOY_CANDIDATES,
    TOY_CONTACT,
    TOY_GIT_SHA,
    TOY_PACKET_ID,
    TOY_PIPELINE_VERSION,
    TOY_VERSION,
    VALID_TOY_CANDIDATE_ID_PREFIX,
    ToyCandidate,
    build_example_benchmark_summary,
    build_example_calibration_summary,
    build_example_packet,
    build_example_safety_attestations,
    build_toy_candidate_entry,
    validate_example_packet_passes,
)
from openamp_foundry.evidence.external_review_packet import (
    validate_external_review_packet,
)


class TestToyConstants:
    def test_toy_packet_id_prefix(self):
        assert TOY_PACKET_ID.startswith("ERP-")

    def test_toy_packet_id_contains_toy(self):
        assert "TOY" in TOY_PACKET_ID

    def test_toy_version_is_string(self):
        assert isinstance(TOY_VERSION, str)
        assert len(TOY_VERSION) > 0

    def test_toy_pipeline_version_is_string(self):
        assert isinstance(TOY_PIPELINE_VERSION, str)
        assert "example" in TOY_PIPELINE_VERSION.lower()

    def test_toy_git_sha_length(self):
        assert len(TOY_GIT_SHA) == 40

    def test_toy_git_sha_is_zeros(self):
        assert TOY_GIT_SHA == "0" * 40

    def test_toy_contact_is_string(self):
        assert isinstance(TOY_CONTACT, str)
        assert "@" in TOY_CONTACT

    def test_valid_toy_prefix(self):
        assert VALID_TOY_CANDIDATE_ID_PREFIX == "TOY-"


class TestToyCandidates:
    def test_three_toy_candidates(self):
        assert len(TOY_CANDIDATES) == 3

    def test_all_ids_have_toy_prefix(self):
        for toy in TOY_CANDIDATES:
            assert toy.candidate_id.startswith("TOY-"), toy.candidate_id

    def test_all_sequences_nonempty(self):
        for toy in TOY_CANDIDATES:
            assert len(toy.sequence) > 0

    def test_all_scores_in_range(self):
        for toy in TOY_CANDIDATES:
            assert 0.0 <= toy.ensemble_score <= 1.0

    def test_all_families_nonempty(self):
        for toy in TOY_CANDIDATES:
            assert len(toy.family) > 0

    def test_all_rationales_nonempty(self):
        for toy in TOY_CANDIDATES:
            assert len(toy.selection_rationale) > 0

    def test_all_safety_notes_mention_toy(self):
        for toy in TOY_CANDIDATES:
            assert "toy" in toy.safety_notes.lower() or "not for" in toy.safety_notes.lower()

    def test_toy_candidate_is_dataclass(self):
        toy = TOY_CANDIDATES[0]
        assert isinstance(toy, ToyCandidate)

    def test_distinct_candidate_ids(self):
        ids = [t.candidate_id for t in TOY_CANDIDATES]
        assert len(ids) == len(set(ids))

    def test_distinct_sequences(self):
        seqs = [t.sequence for t in TOY_CANDIDATES]
        assert len(seqs) == len(set(seqs))


class TestBuildToyCandidate:
    def test_build_returns_candidate_entry(self):
        from openamp_foundry.evidence.external_review_packet import CandidateEntry
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert isinstance(entry, CandidateEntry)

    def test_candidate_id_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.candidate_id == TOY_CANDIDATES[0].candidate_id

    def test_sequence_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.sequence == TOY_CANDIDATES[0].sequence

    def test_score_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.ensemble_score == TOY_CANDIDATES[0].ensemble_score

    def test_proof_ladder_level_is_1(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.proof_ladder_level == 1

    def test_family_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.family == TOY_CANDIDATES[0].family

    def test_rationale_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.selection_rationale == TOY_CANDIDATES[0].selection_rationale

    def test_safety_notes_preserved(self):
        entry = build_toy_candidate_entry(TOY_CANDIDATES[0])
        assert entry.safety_notes == TOY_CANDIDATES[0].safety_notes

    def test_invalid_prefix_raises(self):
        bad = ToyCandidate(
            candidate_id="REAL-0001",
            sequence="ACDEF",
            ensemble_score=0.5,
            family="x",
            selection_rationale="x",
            safety_notes="x",
        )
        with pytest.raises(ValueError, match="TOY-"):
            build_toy_candidate_entry(bad)

    def test_empty_prefix_raises(self):
        bad = ToyCandidate(
            candidate_id="0001",
            sequence="ACDEF",
            ensemble_score=0.5,
            family="x",
            selection_rationale="x",
            safety_notes="x",
        )
        with pytest.raises(ValueError):
            build_toy_candidate_entry(bad)


class TestBuildExampleHelpers:
    def test_benchmark_summary_auroc_in_range(self):
        bm = build_example_benchmark_summary()
        assert 0.0 <= bm.auroc <= 1.0

    def test_benchmark_summary_name_nonempty(self):
        bm = build_example_benchmark_summary()
        assert len(bm.benchmark_name) > 0

    def test_benchmark_summary_positives_positive(self):
        bm = build_example_benchmark_summary()
        assert bm.n_positives > 0

    def test_benchmark_summary_negatives_positive(self):
        bm = build_example_benchmark_summary()
        assert bm.n_negatives > 0

    def test_calibration_summary_valid_assessment(self):
        from openamp_foundry.evidence.external_review_packet import VALID_CALIBRATION_ASSESSMENTS
        cs = build_example_calibration_summary()
        assert cs.calibration_assessment in VALID_CALIBRATION_ASSESSMENTS

    def test_calibration_summary_samples_positive(self):
        cs = build_example_calibration_summary()
        assert cs.n_calibration_samples > 0

    def test_safety_attestations_no_toxicity_claim(self):
        sa = build_example_safety_attestations()
        assert sa.no_known_toxicity_claim is True

    def test_safety_attestations_hemolysis_mandatory(self):
        sa = build_example_safety_attestations()
        assert sa.hemolysis_assay_mandatory is True

    def test_safety_attestations_gate_passed(self):
        sa = build_example_safety_attestations()
        assert sa.safety_gate_passed is True


class TestBuildExamplePacket:
    def setup_method(self):
        self.packet = build_example_packet()

    def test_packet_id_is_default(self):
        assert self.packet.packet_id == TOY_PACKET_ID

    def test_packet_id_has_erp_prefix(self):
        assert self.packet.packet_id.startswith("ERP-")

    def test_dry_lab_attestation_true(self):
        assert self.packet.dry_lab_only_attestation is True

    def test_candidate_count_matches_list(self):
        assert self.packet.candidate_count == len(self.packet.candidates)

    def test_candidate_count_is_three(self):
        assert self.packet.candidate_count == 3

    def test_all_candidate_ids_toy_prefix(self):
        for c in self.packet.candidates:
            assert c.candidate_id.startswith("TOY-")

    def test_proof_ladder_level_at_most_2(self):
        from openamp_foundry.evidence.external_review_packet import DRY_LAB_MAX_PROOF_LADDER_LEVEL
        assert self.packet.proof_ladder_level <= DRY_LAB_MAX_PROOF_LADDER_LEVEL

    def test_limitations_nonempty(self):
        assert len(self.packet.limitations) > 0

    def test_limitations_mention_toy(self):
        combined = " ".join(self.packet.limitations).lower()
        assert "toy" in combined or "synthetic" in combined

    def test_contact_is_toy_contact(self):
        assert self.packet.contact == TOY_CONTACT

    def test_notes_mention_example(self):
        assert "example" in self.packet.notes.lower()

    def test_notes_mention_not_for_use(self):
        assert "not for" in self.packet.notes.lower()

    def test_version_is_default(self):
        assert self.packet.version == TOY_VERSION

    def test_pipeline_version_is_default(self):
        assert self.packet.pipeline_version == TOY_PIPELINE_VERSION

    def test_git_sha_is_default(self):
        assert self.packet.git_sha == TOY_GIT_SHA

    def test_custom_packet_id(self):
        packet = build_example_packet(packet_id="ERP-TOY-9999")
        assert packet.packet_id == "ERP-TOY-9999"

    def test_custom_generated_at(self):
        packet = build_example_packet(generated_at="2030-01-01T00:00:00Z")
        assert packet.generated_at == "2030-01-01T00:00:00Z"

    def test_custom_contact(self):
        packet = build_example_packet(contact="reviewer@lab.example")
        assert packet.contact == "reviewer@lab.example"


class TestValidateExamplePacket:
    def test_example_packet_is_valid(self):
        result = validate_example_packet_passes()
        assert result.is_valid is True

    def test_example_packet_no_violations(self):
        result = validate_example_packet_passes()
        assert result.violations == []

    def test_example_packet_has_packet_id(self):
        result = validate_example_packet_passes()
        assert result.packet_id == TOY_PACKET_ID

    def test_validate_directly(self):
        packet = build_example_packet()
        result = validate_external_review_packet(packet)
        assert result.is_valid is True

    def test_validate_summary_nonempty(self):
        result = validate_example_packet_passes()
        assert len(result.validation_summary) > 0

    def test_invalid_proof_ladder_fails(self):
        from openamp_foundry.evidence.external_review_packet import DRY_LAB_MAX_PROOF_LADDER_LEVEL
        packet = build_example_packet()
        packet.proof_ladder_level = DRY_LAB_MAX_PROOF_LADDER_LEVEL + 1
        result = validate_external_review_packet(packet)
        assert not result.is_valid

    def test_empty_limitations_fails(self):
        packet = build_example_packet()
        packet.limitations = []
        result = validate_external_review_packet(packet)
        assert not result.is_valid

    def test_false_dry_lab_attestation_fails(self):
        packet = build_example_packet()
        packet.dry_lab_only_attestation = False
        result = validate_external_review_packet(packet)
        assert not result.is_valid

    def test_mismatched_candidate_count_fails(self):
        packet = build_example_packet()
        packet.candidate_count = 999
        result = validate_external_review_packet(packet)
        assert not result.is_valid

    def test_empty_candidates_fails(self):
        packet = build_example_packet()
        packet.candidates = []
        packet.candidate_count = 0
        result = validate_external_review_packet(packet)
        assert not result.is_valid
