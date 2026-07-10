"""ESC- external-simulator review checklist schema.

Before any external simulation service is connected to the pipeline,
it must pass a structured review.  This checklist makes the review
machine-auditable: every item is explicitly confirmed or flagged.

The items cover: data privacy (what does the service receive?),
output trustworthiness (what does it return?), security (authentication
and TLS), license (can results be used commercially/academically?),
and operational reliability (SLA, fallback, failure modes).

A simulator with unchecked critical items must not be used in candidate
ranking until those items are resolved.
"""

from __future__ import annotations

from dataclasses import dataclass

CHECKLIST_ITEMS: tuple[str, ...] = (
    "data_sent_to_service_documented",
    "sequence_data_not_transmitted",
    "output_schema_documented",
    "output_schema_validated_against_schema",
    "authentication_required",
    "tls_enforced",
    "license_permits_research_use",
    "failure_mode_documented",
    "timeout_policy_declared",
    "network_call_declared_in_nsn_policy",
    "baseline_comparison_exists",
    "deprecation_policy_declared",
)

REQUIRED_ITEMS: tuple[str, ...] = (
    "data_sent_to_service_documented",
    "sequence_data_not_transmitted",
    "output_schema_documented",
    "tls_enforced",
    "license_permits_research_use",
    "failure_mode_documented",
    "network_call_declared_in_nsn_policy",
)

VALID_ESC_VERDICTS: frozenset[str] = frozenset({
    "approved",
    "conditional_approval",
    "not_approved",
})


@dataclass
class ExternalSimulatorChecklist:
    esc_id: str
    simulator_name: str
    pipeline_version: str
    items_checked: list[str]
    items_unchecked: list[str]
    required_items_complete: bool
    n_items_checked: int
    esc_verdict: str
    reviewer_notes: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_external_simulator_checklist(esc: ExternalSimulatorChecklist) -> None:
    if not esc.esc_id.startswith("ESC-"):
        raise ValueError(f"esc_id must start with 'ESC-': {esc.esc_id!r}")
    if not esc.simulator_name:
        raise ValueError("simulator_name must be non-empty")
    if not esc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for item in esc.items_checked:
        if item not in CHECKLIST_ITEMS:
            raise ValueError(f"checked item {item!r} not in CHECKLIST_ITEMS")
    for item in esc.items_unchecked:
        if item not in CHECKLIST_ITEMS:
            raise ValueError(f"unchecked item {item!r} not in CHECKLIST_ITEMS")
    all_items = set(esc.items_checked) | set(esc.items_unchecked)
    if all_items != set(CHECKLIST_ITEMS):
        raise ValueError(
            "items_checked + items_unchecked must cover all CHECKLIST_ITEMS exactly"
        )
    if esc.n_items_checked != len(esc.items_checked):
        raise ValueError("n_items_checked must equal len(items_checked)")
    expected_required_complete = all(
        r in esc.items_checked for r in REQUIRED_ITEMS
    )
    if esc.required_items_complete != expected_required_complete:
        raise ValueError(
            "required_items_complete inconsistent with items_checked and REQUIRED_ITEMS"
        )
    if esc.esc_verdict not in VALID_ESC_VERDICTS:
        raise ValueError(
            f"esc_verdict {esc.esc_verdict!r} not in VALID_ESC_VERDICTS"
        )
    if esc.esc_verdict == "approved" and not esc.required_items_complete:
        raise ValueError(
            "esc_verdict='approved' requires required_items_complete=True"
        )
    if not esc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not esc.limitations:
        raise ValueError("limitations must be non-empty")
    if not esc.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(required_complete: bool, n_checked: int) -> str:
    if required_complete and n_checked == len(CHECKLIST_ITEMS):
        return "approved"
    if required_complete:
        return "conditional_approval"
    return "not_approved"


def build_external_simulator_checklist(
    *,
    esc_id: str,
    simulator_name: str,
    pipeline_version: str,
    items_checked: list[str],
    reviewer_notes: str = "",
    limitations: list[str],
    created_at: str,
) -> ExternalSimulatorChecklist:
    """Build an ExternalSimulatorChecklist.

    items_unchecked, required_items_complete, n_items_checked, and esc_verdict
    are all auto-computed from items_checked and CHECKLIST_ITEMS / REQUIRED_ITEMS.
    """
    checked_set = set(items_checked)
    unchecked = [item for item in CHECKLIST_ITEMS if item not in checked_set]
    required_complete = all(r in checked_set for r in REQUIRED_ITEMS)
    n_checked = len(items_checked)
    verdict = _compute_verdict(required_complete, n_checked)
    esc = ExternalSimulatorChecklist(
        esc_id=esc_id,
        simulator_name=simulator_name,
        pipeline_version=pipeline_version,
        items_checked=list(items_checked),
        items_unchecked=unchecked,
        required_items_complete=required_complete,
        n_items_checked=n_checked,
        esc_verdict=verdict,
        reviewer_notes=reviewer_notes,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_external_simulator_checklist(esc)
    return esc


def format_external_simulator_checklist(esc: ExternalSimulatorChecklist) -> str:
    lines = [
        f"External-Simulator Checklist — {esc.esc_id}",
        f"Simulator: {esc.simulator_name}  |  Pipeline: {esc.pipeline_version}",
        f"Verdict: {esc.esc_verdict}",
        f"Items checked: {esc.n_items_checked}/{len(CHECKLIST_ITEMS)}",
        f"Required items complete: {esc.required_items_complete}",
    ]
    if esc.items_unchecked:
        lines.append(f"Unchecked items: {', '.join(esc.items_unchecked)}")
    if esc.reviewer_notes:
        lines.append(f"Notes: {esc.reviewer_notes}")
    lines.append(f"Limitations: {'; '.join(esc.limitations)}")
    lines.append(f"Created: {esc.created_at}")
    lines.append(f"dry_lab_only: {esc.dry_lab_only}")
    return "\n".join(lines)
