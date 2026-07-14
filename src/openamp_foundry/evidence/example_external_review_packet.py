"""
Example external review packet using toy/mock data.

E2: Partners know what to expect. Provides a factory function that builds
a fully-validated ExternalReviewPacket with synthetic candidates only.
Candidate IDs use the TOY- prefix to prevent confusion with real candidates.
This module is CI-checkable: build_example_packet() must pass all validation rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from openamp_foundry.evidence.external_review_packet import (
    BenchmarkSummary,
    CalibrationSummary,
    CandidateEntry,
    ExternalReviewPacket,
    PacketValidationResult,
    SafetyAttestations,
    build_legacy_external_review_packet,
    validate_external_review_packet,
)

TOY_PACKET_ID: str = "ERP-TOY-0001"
TOY_VERSION: str = "0.1.0"
TOY_PIPELINE_VERSION: str = "openamp-foundry==0.1.0-example"
TOY_GIT_SHA: str = "0000000000000000000000000000000000000000"
TOY_CONTACT: str = "example@openamp-foundry.example"

VALID_TOY_CANDIDATE_ID_PREFIX: str = "TOY-"


@dataclass
class ToyCandidate:
    """Structured toy candidate for E2 example packet."""

    candidate_id: str
    sequence: str
    ensemble_score: float
    family: str
    selection_rationale: str
    safety_notes: str


TOY_CANDIDATES: list[ToyCandidate] = [
    ToyCandidate(
        candidate_id="TOY-0001",
        sequence="GLLDFLSLAAKFAAADYL",
        ensemble_score=0.82,
        family="alpha-helical",
        selection_rationale="High ensemble score; representative of alpha-helical family.",
        safety_notes="Toy candidate only. Not screened. Not for synthesis.",
    ),
    ToyCandidate(
        candidate_id="TOY-0002",
        sequence="KWKLFKKIGAVLKVL",
        ensemble_score=0.76,
        family="cationic",
        selection_rationale="Cationic family representative with moderate ensemble score.",
        safety_notes="Toy candidate only. Not screened. Not for synthesis.",
    ),
    ToyCandidate(
        candidate_id="TOY-0003",
        sequence="RRWWRWWRR",
        ensemble_score=0.71,
        family="tryptophan-rich",
        selection_rationale="Tryptophan-rich motif; included for family diversity.",
        safety_notes="Toy candidate only. Not screened. Not for synthesis.",
    ),
]


def build_toy_candidate_entry(toy: ToyCandidate) -> CandidateEntry:
    """Convert a ToyCandidate into a CandidateEntry suitable for an ExternalReviewPacket."""
    if not toy.candidate_id.startswith(VALID_TOY_CANDIDATE_ID_PREFIX):
        raise ValueError(
            f"Toy candidate IDs must start with '{VALID_TOY_CANDIDATE_ID_PREFIX}', "
            f"got: {toy.candidate_id!r}"
        )
    return CandidateEntry(
        candidate_id=toy.candidate_id,
        sequence=toy.sequence,
        ensemble_score=toy.ensemble_score,
        proof_ladder_level=1,
        family=toy.family,
        selection_rationale=toy.selection_rationale,
        safety_notes=toy.safety_notes,
    )


def build_example_benchmark_summary() -> BenchmarkSummary:
    """Return a toy BenchmarkSummary for the E2 example packet."""
    return BenchmarkSummary(
        auroc=0.75,
        benchmark_name="BMC-EXAMPLE-toy-precision-at-k",
        n_positives=50,
        n_negatives=150,
    )


def build_example_calibration_summary() -> CalibrationSummary:
    """Return a toy CalibrationSummary for the E2 example packet."""
    return CalibrationSummary(
        calibration_assessment="moderately_calibrated",
        n_calibration_samples=100,
    )


def build_example_safety_attestations() -> SafetyAttestations:
    """Return SafetyAttestations appropriate for a toy example packet."""
    return SafetyAttestations(
        reviewed_by_human=False,
        safety_gate_passed=True,
        no_known_toxicity_claim=True,
        hemolysis_assay_mandatory=True,
    )


def build_example_packet(
    packet_id: str = TOY_PACKET_ID,
    version: str = TOY_VERSION,
    generated_at: str = "2026-01-01T00:00:00Z",
    pipeline_version: str = TOY_PIPELINE_VERSION,
    git_sha: str = TOY_GIT_SHA,
    contact: str = TOY_CONTACT,
) -> ExternalReviewPacket:
    """
    Build an ExternalReviewPacket populated with toy/mock candidates only.

    This packet is designed to pass all validation rules and serve as a
    reference example for external reviewers. Candidate IDs use the TOY-
    prefix; the packet is marked dry_lab_only_attestation=True.
    """
    candidates = [build_toy_candidate_entry(toy) for toy in TOY_CANDIDATES]
    return build_legacy_external_review_packet(
        packet_id=packet_id,
        version=version,
        generated_at=generated_at,
        pipeline_version=pipeline_version,
        git_sha=git_sha,
        candidate_count=len(candidates),
        candidates=candidates,
        benchmark_summary=build_example_benchmark_summary(),
        calibration_summary=build_example_calibration_summary(),
        limitations=[
            "All candidates are synthetic toy data. No biological screening performed.",
            "AUROC is illustrative only; not computed on real AMP datasets.",
            "Calibration assessment is illustrative; not computed on real assay outcomes.",
        ],
        safety_attestations=build_example_safety_attestations(),
        dry_lab_only_attestation=True,
        proof_ladder_level=1,
        contact=contact,
        notes="E2 example packet. Contains toy candidates only. Not for clinical or research use.",
    )


def validate_example_packet_passes() -> PacketValidationResult:
    """
    Build and validate the example packet.

    Returns a PacketValidationResult with is_valid=True if the example
    packet satisfies all ExternalReviewPacket validation rules.
    Raises ValueError if validation fails (which would indicate a regression
    in either the example data or the validation logic).
    """
    packet = build_example_packet()
    result = validate_external_review_packet(packet)
    if not result.is_valid:
        raise ValueError(
            f"E2 example packet failed validation: {result.violations}"
        )
    return result
