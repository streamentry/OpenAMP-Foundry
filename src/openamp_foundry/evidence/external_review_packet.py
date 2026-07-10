"""ERP- external review packet schema.

Assembles BRC + ECI + FET + PTR + SRS into a single record listing everything
a scientist needs to review the batch's computational evidence. Dry-lab-only
constraint explicit. Closes the "what do I send to a reviewer?" question.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_PACKET_COMPONENTS: tuple[str, ...] = (
    "BRC", "ECI", "FET", "PTR", "SRS",
)

VALID_PACKET_STATUSES: frozenset[str] = frozenset({
    "ready", "incomplete", "draft",
})


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


def _compute_status(n_present: int, n_required: int) -> str:
    if n_present == n_required:
        return "ready"
    if n_present == 0:
        return "draft"
    return "incomplete"


def validate_external_review_packet(erp: ExternalReviewPacket) -> None:
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
