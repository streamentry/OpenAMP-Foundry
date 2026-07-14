"""ERP- external review packet schema.

Assembles BRC + ECI + FET + PTR + SRS into a single record listing everything
a scientist needs to review the batch's computational evidence. Dry-lab-only
constraint explicit. Closes the "what do I send to a reviewer?" question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

REQUIRED_PACKET_COMPONENTS: tuple[str, ...] = (
    "BRC", "ECI", "FET", "PTR", "SRS",
)

VALID_PACKET_STATUSES: frozenset[str] = frozenset({
    "ready", "incomplete", "draft",
})

# Compatibility vocabulary for the superseded Phase E packet API.  The V4
# ERP below remains canonical; these names let old toy fixtures and CLI
# consumers fail safely while they migrate to component-based packets.
VALID_CALIBRATION_ASSESSMENTS: frozenset[str] = frozenset({
    "well_calibrated",
    "moderately_calibrated",
    "poorly_calibrated",
    "uninformative",
})
DRY_LAB_MAX_PROOF_LADDER_LEVEL = 2
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_GIT_SHA_RE = re.compile(r"^[a-f0-9]{7,40}$")


@dataclass
class CandidateEntry:
    """Legacy Phase E candidate entry used only by toy compatibility data."""

    candidate_id: str
    sequence: str
    ensemble_score: float
    proof_ladder_level: int
    family: str = ""
    selection_rationale: str = ""
    safety_notes: str = ""


@dataclass
class BenchmarkSummary:
    """Legacy Phase E benchmark summary used only by toy compatibility data."""

    auroc: float
    benchmark_name: str
    n_positives: int
    n_negatives: int


@dataclass
class CalibrationSummary:
    """Legacy Phase E calibration summary used only by toy compatibility data."""

    calibration_assessment: str
    n_calibration_samples: int = 0
    calibration_error: float = 0.0
    n_bins: int = 0
    assessment: str = ""


@dataclass
class SafetyAttestations:
    """Legacy Phase E safety attestations retained for migration only."""

    reviewed_by_human: bool = False
    safety_gate_passed: bool = False
    no_known_toxicity_claim: bool = False
    hemolysis_assay_mandatory: bool = True
    dual_use_screened: bool = False
    hemolysis_risk_flagged: bool = False


@dataclass
class PacketComponent:
    component_type: str
    artifact_id: str
    present: bool


@dataclass
class ExternalReviewPacket:
    erp_id: str
    batch_id: str
    pipeline_version: str
    components: list[PacketComponent]
    n_components_required: int
    n_components_present: int
    missing_component_types: list[str]
    packet_status: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


@dataclass
class PacketValidationResult:
    """Result returned when validating a legacy Phase E compatibility packet."""

    is_valid: bool
    violations: list[str]
    warnings: list[str]
    packet_id: str
    validation_summary: str


def _compute_status(n_present: int, n_required: int) -> str:
    if n_present == n_required:
        return "ready"
    if n_present == 0:
        return "draft"
    return "incomplete"


def validate_external_review_packet(erp: ExternalReviewPacket) -> None:
    if hasattr(erp, "packet_id"):
        return _validate_legacy_packet(erp)
    if not erp.erp_id.startswith("ERP-"):
        raise ValueError(f"erp_id must start with 'ERP-': {erp.erp_id!r}")
    if not erp.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not erp.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    component_types = [c.component_type for c in erp.components]
    for req in REQUIRED_PACKET_COMPONENTS:
        if component_types.count(req) != 1:
            raise ValueError(f"Exactly one component required for {req!r}")
    if erp.packet_status not in VALID_PACKET_STATUSES:
        raise ValueError(
            f"packet_status {erp.packet_status!r} not in VALID_PACKET_STATUSES"
        )
    if not erp.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not erp.limitations:
        raise ValueError("limitations must be non-empty")
    if not erp.created_at:
        raise ValueError("created_at must be non-empty")
    n_req = len(REQUIRED_PACKET_COMPONENTS)
    if erp.n_components_required != n_req:
        raise ValueError(
            f"n_components_required must be {n_req}, got {erp.n_components_required}"
        )
    n_present = sum(1 for c in erp.components if c.present)
    if erp.n_components_present != n_present:
        raise ValueError("n_components_present mismatch")
    expected_missing = sorted(
        c.component_type for c in erp.components if not c.present
    )
    if erp.missing_component_types != expected_missing:
        raise ValueError("missing_component_types mismatch")


def _validate_legacy_packet(packet: ExternalReviewPacket) -> PacketValidationResult:
    """Validate the superseded Phase E shape without changing the V4 schema."""

    violations: list[str] = []
    if not packet.packet_id.startswith("ERP-"):
        violations.append(f"packet_id must start with 'ERP-', got '{packet.packet_id}'")
    if not _SEMVER_RE.match(packet.version):
        violations.append(f"version must be semver (X.Y.Z), got '{packet.version}'")
    if not _GIT_SHA_RE.match(packet.git_sha):
        violations.append(
            f"git_sha must be 7-40 lowercase hex chars, got '{packet.git_sha}'"
        )
    if packet.candidate_count != len(packet.candidates):
        violations.append("candidate_count does not match len(candidates)")
    if not packet.candidates:
        violations.append("candidates must not be empty (minItems: 1)")
    if not packet.dry_lab_only_attestation:
        violations.append("dry_lab_only_attestation must be True")
    if not (1 <= packet.proof_ladder_level <= DRY_LAB_MAX_PROOF_LADDER_LEVEL):
        violations.append(
            f"proof_ladder_level must be in [1, {DRY_LAB_MAX_PROOF_LADDER_LEVEL}]"
        )
    if packet.safety_attestations is None:
        violations.append("safety_attestations is required")
    elif not packet.safety_attestations.no_known_toxicity_claim:
        violations.append("safety_attestations.no_known_toxicity_claim must be True")
    if not packet.limitations:
        violations.append("limitations must be non-empty")
    if packet.benchmark_summary is not None and not (
        0.0 <= packet.benchmark_summary.auroc <= 1.0
    ):
        violations.append("benchmark_summary.auroc must be in [0, 1]")
    if packet.calibration_summary is not None and (
        packet.calibration_summary.calibration_assessment
        not in VALID_CALIBRATION_ASSESSMENTS
    ):
        violations.append("calibration_summary.calibration_assessment is invalid")
    for index, candidate in enumerate(packet.candidates):
        if not 0.0 <= candidate.ensemble_score <= 1.0:
            violations.append(f"candidates[{index}].ensemble_score must be in [0, 1]")
        if candidate.proof_ladder_level > DRY_LAB_MAX_PROOF_LADDER_LEVEL:
            violations.append(
                f"candidates[{index}].proof_ladder_level exceeds dry-lab cap"
            )
    valid = not violations
    summary = (
        f"ERP- packet '{packet.packet_id}' is valid"
        if valid
        else f"ERP- packet '{packet.packet_id}' has {len(violations)} violation(s)"
    )
    return PacketValidationResult(
        is_valid=valid,
        violations=violations,
        warnings=[],
        packet_id=packet.packet_id,
        validation_summary=summary,
    )


def build_legacy_external_review_packet(
    *,
    packet_id: str,
    version: str,
    generated_at: str,
    pipeline_version: str,
    git_sha: str,
    candidate_count: int,
    candidates: list[CandidateEntry],
    benchmark_summary: BenchmarkSummary | None,
    calibration_summary: CalibrationSummary | None,
    limitations: list[str],
    safety_attestations: SafetyAttestations | None,
    dry_lab_only_attestation: bool,
    proof_ladder_level: int,
    contact: str,
    notes: str,
) -> ExternalReviewPacket:
    """Build a migration-only packet for the retired Phase E API.

    The object carries a valid V4 component shell plus legacy attributes. New
    integrations must call build_external_review_packet() directly.
    """

    packet = ExternalReviewPacket(
        erp_id=packet_id,
        batch_id=f"LEGACY-{packet_id}",
        pipeline_version=pipeline_version,
        components=[
            PacketComponent(
                component_type=component_type,
                artifact_id=f"LEGACY-{component_type}-{packet_id}",
                present=True,
            )
            for component_type in REQUIRED_PACKET_COMPONENTS
        ],
        n_components_required=len(REQUIRED_PACKET_COMPONENTS),
        n_components_present=len(REQUIRED_PACKET_COMPONENTS),
        missing_component_types=[],
        packet_status="ready",
        dry_lab_only=dry_lab_only_attestation,
        limitations=limitations,
        created_at=generated_at,
    )
    for name, value in {
        "packet_id": packet_id,
        "version": version,
        "generated_at": generated_at,
        "git_sha": git_sha,
        "candidate_count": candidate_count,
        "candidates": candidates,
        "candidate_entries": candidates,
        "benchmark_summary": benchmark_summary,
        "benchmark_summaries": (
            [benchmark_summary] if benchmark_summary is not None else []
        ),
        "calibration_summary": calibration_summary,
        "safety_attestations": safety_attestations,
        "dry_lab_only_attestation": dry_lab_only_attestation,
        "proof_ladder_level": proof_ladder_level,
        "contact": contact,
        "notes": notes,
        "calibration_assessment": (
            calibration_summary.calibration_assessment
            if calibration_summary is not None
            else "uninformative"
        ),
    }.items():
        setattr(packet, name, value)
    return packet


def build_external_review_packet(
    *,
    erp_id: str,
    batch_id: str,
    pipeline_version: str,
    brc_artifact_id: str = "",
    eci_artifact_id: str = "",
    fet_artifact_id: str = "",
    ptr_artifact_id: str = "",
    srs_artifact_id: str = "",
    limitations: list[str],
    created_at: str,
) -> ExternalReviewPacket:
    artifact_map = {
        "BRC": brc_artifact_id,
        "ECI": eci_artifact_id,
        "FET": fet_artifact_id,
        "PTR": ptr_artifact_id,
        "SRS": srs_artifact_id,
    }
    components = [
        PacketComponent(
            component_type=ct,
            artifact_id=artifact_map[ct],
            present=bool(artifact_map[ct]),
        )
        for ct in REQUIRED_PACKET_COMPONENTS
    ]
    n_req = len(REQUIRED_PACKET_COMPONENTS)
    n_present = sum(1 for c in components if c.present)
    missing = sorted(c.component_type for c in components if not c.present)
    status = _compute_status(n_present, n_req)

    erp = ExternalReviewPacket(
        erp_id=erp_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        components=components,
        n_components_required=n_req,
        n_components_present=n_present,
        missing_component_types=missing,
        packet_status=status,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_external_review_packet(erp)
    return erp


def format_external_review_packet(erp: ExternalReviewPacket) -> str:
    if hasattr(erp, "packet_id"):
        result = _validate_legacy_packet(erp)
        return "\n".join(
            [
                "=== EXTERNAL REVIEW PACKET ===",
                f"Packet ID: {erp.packet_id}",
                f"Version: {erp.version}",
                f"Candidates: {erp.candidate_count}",
                f"Dry-lab only: {erp.dry_lab_only_attestation}",
                f"Status: {'VALID' if result.is_valid else 'INVALID'}",
                result.validation_summary,
            ]
        )
    lines = [
        f"External Review Packet — {erp.erp_id}",
        f"Batch: {erp.batch_id}  |  Pipeline: {erp.pipeline_version}",
        f"Status: {erp.packet_status}  |  Components: {erp.n_components_present}/{erp.n_components_required}",
    ]
    if erp.missing_component_types:
        lines.append(f"Missing: {', '.join(erp.missing_component_types)}")
    lines.append("Components:")
    for comp in erp.components:
        status_label = "PRESENT" if comp.present else "MISSING"
        artifact_str = comp.artifact_id if comp.artifact_id else "(none)"
        lines.append(f"  [{status_label}] {comp.component_type}: {artifact_str}")
    lines.append(f"Created: {erp.created_at}")
    lines.append(f"Limitations: {'; '.join(erp.limitations)}")
    lines.append(f"dry_lab_only: {erp.dry_lab_only}")
    return "\n".join(lines)
