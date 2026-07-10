"""External review packet schema — Phase E E1.

Machine-checkable ERP- schema for complete external review packets.
Enables lab partners and reviewers to verify what a review packet contains
before running experiments.

Key safety invariants:
- dry_lab_only_attestation must always be True
- proof_ladder_level capped at 2 (computationally nominated) for dry-lab packets
- safety_attestations.no_known_toxicity_claim must be True
- limitations list must be non-empty
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


VALID_CALIBRATION_ASSESSMENTS: frozenset[str] = frozenset({
    "well_calibrated",
    "moderately_calibrated",
    "poorly_calibrated",
    "uninformative",
})

DRY_LAB_MAX_PROOF_LADDER_LEVEL: int = 2
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_GIT_SHA_RE = re.compile(r"^[a-f0-9]{7,40}$")
_AA_SEQ_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")


@dataclass
class CandidateEntry:
    candidate_id: str
    sequence: str
    ensemble_score: float
    proof_ladder_level: int
    family: str = ""
    selection_rationale: str = ""
    safety_notes: str = ""


@dataclass
class BenchmarkSummary:
    auroc: float
    benchmark_name: str
    n_positives: int
    n_negatives: int


@dataclass
class CalibrationSummary:
    calibration_assessment: str
    n_calibration_samples: int = 0


@dataclass
class SafetyAttestations:
    reviewed_by_human: bool
    safety_gate_passed: bool
    no_known_toxicity_claim: bool
    hemolysis_assay_mandatory: bool = True


@dataclass
class ExternalReviewPacket:
    packet_id: str
    version: str
    generated_at: str
    pipeline_version: str
    git_sha: str
    candidate_count: int
    candidates: list[CandidateEntry] = field(default_factory=list)
    benchmark_summary: BenchmarkSummary | None = None
    calibration_summary: CalibrationSummary | None = None
    limitations: list[str] = field(default_factory=list)
    safety_attestations: SafetyAttestations | None = None
    dry_lab_only_attestation: bool = True
    proof_ladder_level: int = 1
    contact: str = ""
    notes: str = ""


@dataclass
class PacketValidationResult:
    is_valid: bool
    violations: list[str]
    warnings: list[str]
    packet_id: str
    validation_summary: str


def validate_external_review_packet(
    packet: ExternalReviewPacket,
) -> PacketValidationResult:
    """Validate an ExternalReviewPacket against ERP- schema rules.

    Returns a PacketValidationResult with all violations and warnings.
    A packet is valid only when violations is empty.
    """
    violations: list[str] = []
    warnings: list[str] = []

    # Rule 1: packet_id prefix
    if not packet.packet_id.startswith("ERP-"):
        violations.append(
            f"packet_id must start with 'ERP-', got '{packet.packet_id}'"
        )

    # Rule 2: version semver format
    if not _SEMVER_RE.match(packet.version):
        violations.append(
            f"version must be semver (X.Y.Z), got '{packet.version}'"
        )

    # Rule 3: git_sha hex format
    if not _GIT_SHA_RE.match(packet.git_sha):
        violations.append(
            f"git_sha must be 7-40 lowercase hex chars, got '{packet.git_sha}'"
        )

    # Rule 4: candidate_count consistency
    if packet.candidate_count != len(packet.candidates):
        violations.append(
            f"candidate_count ({packet.candidate_count}) does not match "
            f"len(candidates) ({len(packet.candidates)})"
        )

    # Rule 5: candidates not empty
    if not packet.candidates:
        violations.append("candidates must not be empty (minItems: 1)")

    # Rule 6: dry_lab_only_attestation must be True
    if not packet.dry_lab_only_attestation:
        violations.append(
            "dry_lab_only_attestation must be True — "
            "this packet contains dry-lab computational outputs only"
        )

    # Rule 7: packet-level proof_ladder_level cap
    if packet.proof_ladder_level > DRY_LAB_MAX_PROOF_LADDER_LEVEL:
        violations.append(
            f"proof_ladder_level ({packet.proof_ladder_level}) exceeds dry-lab cap "
            f"of {DRY_LAB_MAX_PROOF_LADDER_LEVEL}. "
            "Dry-lab outputs cannot claim beyond 'computationally nominated' (Level 2)."
        )

    # Rule 8: proof_ladder_level must be >= 1
    if packet.proof_ladder_level < 1:
        violations.append(
            f"proof_ladder_level must be >= 1, got {packet.proof_ladder_level}"
        )

    # Rule 9: safety_attestations
    if packet.safety_attestations is None:
        violations.append("safety_attestations is required")
    else:
        if not packet.safety_attestations.no_known_toxicity_claim:
            violations.append(
                "safety_attestations.no_known_toxicity_claim must be True — "
                "dry-lab scores do not prove biological safety"
            )

    # Rule 10: limitations non-empty
    if not packet.limitations:
        violations.append(
            "limitations must contain at least one entry. "
            "Minimum: 'Computational outputs are hypotheses and review aids. "
            "They are not biological proof.'"
        )

    # Rule 11: benchmark_summary auroc range
    if packet.benchmark_summary is not None:
        if not (0.0 <= packet.benchmark_summary.auroc <= 1.0):
            violations.append(
                f"benchmark_summary.auroc must be in [0, 1], "
                f"got {packet.benchmark_summary.auroc}"
            )

    # Rule 12: calibration_assessment vocabulary
    if packet.calibration_summary is not None:
        if (
            packet.calibration_summary.calibration_assessment
            not in VALID_CALIBRATION_ASSESSMENTS
        ):
            violations.append(
                f"calibration_summary.calibration_assessment must be one of "
                f"{sorted(VALID_CALIBRATION_ASSESSMENTS)}, "
                f"got '{packet.calibration_summary.calibration_assessment}'"
            )

    # Rule 13+14: per-candidate validation
    for i, cand in enumerate(packet.candidates):
        if not (0.0 <= cand.ensemble_score <= 1.0):
            violations.append(
                f"candidates[{i}].ensemble_score must be in [0, 1], "
                f"got {cand.ensemble_score}"
            )
        if cand.proof_ladder_level > DRY_LAB_MAX_PROOF_LADDER_LEVEL:
            violations.append(
                f"candidates[{i}].proof_ladder_level ({cand.proof_ladder_level}) "
                f"exceeds dry-lab cap of {DRY_LAB_MAX_PROOF_LADDER_LEVEL}"
            )

    is_valid = len(violations) == 0

    if is_valid:
        summary = (
            f"ERP- packet '{packet.packet_id}' is valid: "
            f"{len(packet.candidates)} candidate(s), "
            f"proof_ladder_level={packet.proof_ladder_level}, "
            "dry_lab_only=True."
        )
    else:
        summary = (
            f"ERP- packet '{packet.packet_id}' has {len(violations)} violation(s). "
            "Fix all violations before sending to external reviewers."
        )

    return PacketValidationResult(
        is_valid=is_valid,
        violations=violations,
        warnings=warnings,
        packet_id=packet.packet_id,
        validation_summary=summary,
    )


def format_external_review_packet(packet: ExternalReviewPacket) -> str:
    """Format an ExternalReviewPacket as a human-readable string."""
    result = validate_external_review_packet(packet)
    lines = [
        "=== EXTERNAL REVIEW PACKET ===",
        f"Packet ID: {packet.packet_id}",
        f"Version: {packet.version}",
        f"Pipeline: {packet.pipeline_version} ({packet.git_sha})",
        f"Generated: {packet.generated_at}",
        f"Candidates: {packet.candidate_count}",
        f"Proof ladder level: {packet.proof_ladder_level}",
        f"Dry-lab only: {'YES' if packet.dry_lab_only_attestation else 'NO'}",
        "",
        "-- SAFETY ATTESTATIONS --",
    ]
    if packet.safety_attestations:
        lines.extend([
            f"  Reviewed by human: {packet.safety_attestations.reviewed_by_human}",
            f"  Safety gate passed: {packet.safety_attestations.safety_gate_passed}",
            f"  No toxicity claim: {packet.safety_attestations.no_known_toxicity_claim}",
            f"  Hemolysis assay mandatory: {packet.safety_attestations.hemolysis_assay_mandatory}",
        ])
    lines.extend(["", "-- LIMITATIONS --"])
    for lim in packet.limitations:
        lines.append(f"  • {lim}")
    lines.extend(["", "-- VALIDATION --"])
    if result.is_valid:
        lines.append("  STATUS: VALID")
    else:
        lines.append(f"  STATUS: INVALID ({len(result.violations)} violation(s))")
        for v in result.violations:
            lines.append(f"  ✗ {v}")
    lines.extend(["", result.validation_summary])
    if not result.is_valid:
        lines.extend([
            "",
            "NOTICE: Do not send this packet to external reviewers until all violations are resolved.",
        ])
    return "\n".join(lines)
