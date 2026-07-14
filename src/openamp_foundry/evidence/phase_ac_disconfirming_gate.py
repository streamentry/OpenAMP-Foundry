"""ACDG- Phase AC disconfirming-evidence gate.

Aggregates validated ``DTR-`` records and makes unresolved follow-up visible.
The gate does not claim that a claim is true.  It only records whether an
explicit disconfirming pass exists and whether claim-affecting findings have
an acknowledged follow-up action.
"""

from __future__ import annotations

from dataclasses import dataclass

from openamp_foundry.evidence.disconfirming_test_record import (
    DisconfirmingTestRecord,
    validate_disconfirming_test_record,
)

VALID_ACDG_VERDICTS: frozenset[str] = frozenset(
    {
        "disconfirming_evidence_verified",
        "disconfirming_evidence_partial",
        "disconfirming_evidence_not_established",
    }
)


def _expected_action(test_outcome: str) -> str:
    return {
        "refuted": "downgrade_claim",
        "inconclusive": "investigate",
        "not_refuted": "none",
        "skipped": "none",
    }.get(test_outcome, "")


@dataclass
class PhaseAcDisconfirmingGate:
    acdg_id: str
    pipeline_version: str
    dtr_ids: list[str]
    resolved_dtr_ids: list[str]
    unresolved_dtr_ids: list[str]
    n_records_present: int
    n_claims_affected: int
    n_actions_required: int
    n_actions_resolved: int
    verdict: str
    limitations: list[str]
    dry_lab_only: bool = True
    created_at: str = ""


def _compute_verdict(n_records_present: int, unresolved_count: int) -> str:
    if n_records_present == 0:
        return "disconfirming_evidence_not_established"
    if unresolved_count:
        return "disconfirming_evidence_partial"
    return "disconfirming_evidence_verified"


def build_phase_ac_disconfirming_gate(
    *,
    acdg_id: str,
    pipeline_version: str,
    records: list[DisconfirmingTestRecord],
    resolved_dtr_ids: list[str],
    limitations: list[str],
    created_at: str,
) -> PhaseAcDisconfirmingGate:
    if len({record.dtr_id for record in records}) != len(records):
        raise ValueError("records must not contain duplicate dtr_id values")

    dtr_ids = [record.dtr_id for record in records]
    for record in records:
        validate_disconfirming_test_record(record)
        if record.pipeline_version != pipeline_version:
            raise ValueError(
                f"record {record.dtr_id!r} pipeline_version does not match gate"
            )
        expected_action = _expected_action(record.test_outcome)
        if record.required_action != expected_action:
            raise ValueError(
                f"record {record.dtr_id!r} required_action is inconsistent with "
                f"test_outcome {record.test_outcome!r}"
            )
        expected_affected = record.test_outcome == "refuted"
        if record.is_claim_affected != expected_affected:
            raise ValueError(
                f"record {record.dtr_id!r} is_claim_affected is inconsistent "
                f"with test_outcome {record.test_outcome!r}"
            )

    if len(set(resolved_dtr_ids)) != len(resolved_dtr_ids):
        raise ValueError("resolved_dtr_ids must not contain duplicates")
    unknown_resolved = set(resolved_dtr_ids) - set(dtr_ids)
    if unknown_resolved:
        raise ValueError(
            f"resolved_dtr_ids contain unknown records: {sorted(unknown_resolved)}"
        )

    action_required_ids = {
        record.dtr_id
        for record in records
        if record.required_action != "none"
    }
    invalid_resolved = set(resolved_dtr_ids) - action_required_ids
    if invalid_resolved:
        raise ValueError(
            "resolved_dtr_ids must refer to records requiring action: "
            f"{sorted(invalid_resolved)}"
        )
    unresolved_dtr_ids = sorted(action_required_ids - set(resolved_dtr_ids))
    gate = PhaseAcDisconfirmingGate(
        acdg_id=acdg_id,
        pipeline_version=pipeline_version,
        dtr_ids=dtr_ids,
        resolved_dtr_ids=list(resolved_dtr_ids),
        unresolved_dtr_ids=unresolved_dtr_ids,
        n_records_present=len(records),
        n_claims_affected=sum(record.is_claim_affected for record in records),
        n_actions_required=len(action_required_ids),
        n_actions_resolved=len(set(resolved_dtr_ids)),
        verdict=_compute_verdict(len(records), len(unresolved_dtr_ids)),
        limitations=limitations,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_phase_ac_disconfirming_gate(gate)
    return gate


def validate_phase_ac_disconfirming_gate(
    gate: PhaseAcDisconfirmingGate,
) -> None:
    if not gate.acdg_id.startswith("ACDG-"):
        raise ValueError(f"acdg_id must start with 'ACDG-': {gate.acdg_id!r}")
    if not gate.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(set(gate.dtr_ids)) != len(gate.dtr_ids):
        raise ValueError("dtr_ids must not contain duplicates")
    if any(not dtr_id.startswith("DTR-") for dtr_id in gate.dtr_ids):
        raise ValueError("every dtr_id must start with 'DTR-'")
    if len(set(gate.resolved_dtr_ids)) != len(gate.resolved_dtr_ids):
        raise ValueError("resolved_dtr_ids must not contain duplicates")
    if not set(gate.resolved_dtr_ids).issubset(gate.dtr_ids):
        raise ValueError("resolved_dtr_ids must be a subset of dtr_ids")
    if not set(gate.unresolved_dtr_ids).issubset(gate.dtr_ids):
        raise ValueError("unresolved_dtr_ids must be a subset of dtr_ids")
    if gate.n_records_present != len(gate.dtr_ids):
        raise ValueError("n_records_present mismatch")
    if gate.n_claims_affected < 0 or gate.n_claims_affected > gate.n_records_present:
        raise ValueError("n_claims_affected must be within record count")
    if gate.n_actions_required < 0 or gate.n_actions_resolved < 0:
        raise ValueError("action counts must be non-negative")
    if gate.n_actions_resolved > gate.n_actions_required:
        raise ValueError("n_actions_resolved cannot exceed n_actions_required")
    if gate.n_actions_required - gate.n_actions_resolved != len(gate.unresolved_dtr_ids):
        raise ValueError("unresolved_dtr_ids does not match action counts")
    if gate.verdict not in VALID_ACDG_VERDICTS:
        raise ValueError(f"verdict {gate.verdict!r} not in VALID_ACDG_VERDICTS")
    expected_verdict = _compute_verdict(
        gate.n_records_present, len(gate.unresolved_dtr_ids)
    )
    if gate.verdict != expected_verdict:
        raise ValueError(
            f"verdict {gate.verdict!r} inconsistent with gate contents"
        )
    if not gate.limitations:
        raise ValueError("limitations must be non-empty")
    if gate.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not gate.created_at:
        raise ValueError("created_at must be non-empty")


def format_phase_ac_disconfirming_gate(
    gate: PhaseAcDisconfirmingGate,
) -> str:
    lines = [
        f"Phase AC Disconfirming Evidence Gate — {gate.acdg_id}",
        f"Pipeline: {gate.pipeline_version}",
        f"DTR records: {gate.n_records_present}",
        f"Claims affected: {gate.n_claims_affected}",
        f"Actions resolved: {gate.n_actions_resolved}/{gate.n_actions_required}",
        f"Unresolved records: {', '.join(gate.unresolved_dtr_ids) if gate.unresolved_dtr_ids else 'none'}",
        f"Verdict: {gate.verdict}",
        f"dry_lab_only: {gate.dry_lab_only}",
    ]
    if gate.limitations:
        lines.append("Limitations:")
        lines.extend(f"  - {limitation}" for limitation in gate.limitations)
    if gate.created_at:
        lines.append(f"Created: {gate.created_at}")
    return "\n".join(lines)
