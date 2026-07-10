"""ARG- adapter registry schema.

Machine-readable registry of all external scoring/simulation adapters.
Tracks adapter_type, status, evidence_level, and whether the adapter
may affect candidate ranking. Only active adapters with baseline_verified
or wet_lab_validated evidence may influence ranking.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_ARG_ADAPTER_STATUSES: frozenset[str] = frozenset({
    "active",
    "deprecated",
    "experimental",
    "blocked",
    "pending_review",
})

VALID_ARG_ADAPTER_TYPES: frozenset[str] = frozenset({
    "sequence_scorer",
    "structure_predictor",
    "toxicity_filter",
    "novelty_ranker",
    "simulation_runner",
    "embedding_provider",
})

VALID_ARG_EVIDENCE_LEVELS: frozenset[str] = frozenset({
    "none",
    "baseline_claimed",
    "baseline_verified",
    "wet_lab_validated",
})

RANKING_PERMITTED_STATUSES: frozenset[str] = frozenset({"active"})

RANKING_PERMITTED_EVIDENCE_LEVELS: frozenset[str] = frozenset({
    "baseline_verified",
    "wet_lab_validated",
})


def _compute_can_affect_ranking(status: str, evidence_level: str) -> bool:
    return (
        status in RANKING_PERMITTED_STATUSES
        and evidence_level in RANKING_PERMITTED_EVIDENCE_LEVELS
    )


@dataclass
class AdapterRegistryEntry:
    adapter_id: str
    adapter_type: str
    status: str
    evidence_level: str
    version: str
    scope: str
    inputs: list[str]
    outputs: list[str]
    limitations: list[str]
    baseline_ref: str
    can_affect_ranking: bool
    registered_at: str


@dataclass
class AdapterRegistry:
    arg_id: str
    pipeline_version: str
    entries: list[AdapterRegistryEntry]
    n_entries: int
    n_active: int
    n_ranking_permitted: int
    n_blocked: int
    has_unreviewed_active: bool
    created_at: str
    dry_lab_only: bool = True


def _validate_adapter_registry_entry(entry: AdapterRegistryEntry) -> None:
    if not entry.adapter_id:
        raise ValueError("adapter_id must be non-empty")
    if entry.adapter_type not in VALID_ARG_ADAPTER_TYPES:
        raise ValueError(
            f"adapter_type {entry.adapter_type!r} not in VALID_ARG_ADAPTER_TYPES"
        )
    if entry.status not in VALID_ARG_ADAPTER_STATUSES:
        raise ValueError(
            f"status {entry.status!r} not in VALID_ARG_ADAPTER_STATUSES"
        )
    if entry.evidence_level not in VALID_ARG_EVIDENCE_LEVELS:
        raise ValueError(
            f"evidence_level {entry.evidence_level!r} "
            f"not in VALID_ARG_EVIDENCE_LEVELS"
        )
    if not entry.version:
        raise ValueError("version must be non-empty")
    if not entry.scope:
        raise ValueError("scope must be non-empty")
    if not entry.inputs:
        raise ValueError("inputs must be non-empty")
    if not entry.outputs:
        raise ValueError("outputs must be non-empty")
    if not entry.limitations:
        raise ValueError("limitations must be non-empty")
    if not entry.registered_at:
        raise ValueError("registered_at must be non-empty")
    if entry.evidence_level == "baseline_verified":
        if not entry.baseline_ref.startswith("CBR-") and not entry.baseline_ref.startswith("SEG-"):
            raise ValueError(
                f"baseline_ref for baseline_verified evidence must start "
                f"with CBR- or SEG-: {entry.baseline_ref!r}"
            )
    expected_can_affect = _compute_can_affect_ranking(
        entry.status, entry.evidence_level
    )
    if entry.can_affect_ranking != expected_can_affect:
        raise ValueError(
            f"can_affect_ranking mismatch: got {entry.can_affect_ranking}, "
            f"expected {expected_can_affect} based on "
            f"status={entry.status!r}, evidence_level={entry.evidence_level!r}"
        )


def validate_adapter_registry(arg: AdapterRegistry) -> None:
    if not arg.arg_id.startswith("ARG-"):
        raise ValueError(f"arg_id must start with 'ARG-': {arg.arg_id!r}")
    if not arg.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")

    for entry in arg.entries:
        _validate_adapter_registry_entry(entry)

    if arg.n_entries != len(arg.entries):
        raise ValueError(
            f"n_entries {arg.n_entries} != "
            f"len(entries) {len(arg.entries)}"
        )

    expected_n_active = sum(1 for e in arg.entries if e.status == "active")
    if arg.n_active != expected_n_active:
        raise ValueError(
            f"n_active {arg.n_active} != computed {expected_n_active}"
        )

    expected_n_ranking = sum(1 for e in arg.entries if e.can_affect_ranking)
    if arg.n_ranking_permitted != expected_n_ranking:
        raise ValueError(
            f"n_ranking_permitted {arg.n_ranking_permitted} != "
            f"computed {expected_n_ranking}"
        )

    expected_n_blocked = sum(1 for e in arg.entries if e.status == "blocked")
    if arg.n_blocked != expected_n_blocked:
        raise ValueError(
            f"n_blocked {arg.n_blocked} != computed {expected_n_blocked}"
        )

    expected_unreviewed = any(
        e.status == "active" and e.evidence_level == "none"
        for e in arg.entries
    )
    if arg.has_unreviewed_active != expected_unreviewed:
        raise ValueError(
            f"has_unreviewed_active {arg.has_unreviewed_active} != "
            f"computed {expected_unreviewed}"
        )

    if not arg.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not arg.created_at:
        raise ValueError("created_at must be non-empty")


def build_adapter_registry(
    *,
    arg_id: str,
    pipeline_version: str,
    entries: list[dict | AdapterRegistryEntry],
    created_at: str,
) -> AdapterRegistry:
    """Build an AdapterRegistry.

    entries: list of dicts (same keys as AdapterRegistryEntry fields)
        or AdapterRegistryEntry objects.
    """
    registry_entries: list[AdapterRegistryEntry] = []
    for item in entries:
        if isinstance(item, AdapterRegistryEntry):
            entry = item
        else:
            d = item
            entry = AdapterRegistryEntry(
                adapter_id=d["adapter_id"],
                adapter_type=d["adapter_type"],
                status=d["status"],
                evidence_level=d["evidence_level"],
                version=d["version"],
                scope=d["scope"],
                inputs=list(d["inputs"]),
                outputs=list(d["outputs"]),
                limitations=list(d["limitations"]),
                baseline_ref=d.get("baseline_ref", ""),
                can_affect_ranking=_compute_can_affect_ranking(
                    d["status"], d["evidence_level"]
                ),
                registered_at=d["registered_at"],
            )
        entry.can_affect_ranking = _compute_can_affect_ranking(
            entry.status, entry.evidence_level
        )
        registry_entries.append(entry)

    n_entries = len(registry_entries)
    n_active = sum(1 for e in registry_entries if e.status == "active")
    n_ranking_permitted = sum(1 for e in registry_entries if e.can_affect_ranking)
    n_blocked = sum(1 for e in registry_entries if e.status == "blocked")
    has_unreviewed_active = any(
        e.status == "active" and e.evidence_level == "none"
        for e in registry_entries
    )

    arg = AdapterRegistry(
        arg_id=arg_id,
        pipeline_version=pipeline_version,
        entries=registry_entries,
        n_entries=n_entries,
        n_active=n_active,
        n_ranking_permitted=n_ranking_permitted,
        n_blocked=n_blocked,
        has_unreviewed_active=has_unreviewed_active,
        created_at=created_at,
        dry_lab_only=True,
    )
    validate_adapter_registry(arg)
    return arg


def format_adapter_registry(arg: AdapterRegistry) -> str:
    lines = [
        f"Adapter Registry — {arg.arg_id}",
        f"Pipeline: {arg.pipeline_version}",
        f"Entries: {arg.n_entries} total, {arg.n_active} active, "
        f"{arg.n_ranking_permitted} ranking-permitted, "
        f"{arg.n_blocked} blocked",
    ]
    if arg.has_unreviewed_active:
        lines.append("WARNING: Unreviewed active adapters present")
    if arg.entries:
        lines.append("Registered adapters:")
        for entry in arg.entries:
            ranking_flag = "RANKING" if entry.can_affect_ranking else "no_rank"
            lines.append(
                f"  {entry.adapter_id}: type={entry.adapter_type}, "
                f"status={entry.status}, evidence={entry.evidence_level}, "
                f"{ranking_flag}"
            )
    lines.append(f"Created: {arg.created_at}")
    lines.append(f"dry_lab_only: {arg.dry_lab_only}")
    return "\n".join(lines)
