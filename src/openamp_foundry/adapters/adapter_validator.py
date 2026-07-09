"""Adapter declaration validator — enforces the Adapter Author Guide contract.

All adapters must pass this check before being used in gated or ranked pipelines.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_ADAPTER_MODES: set[str] = {"off", "info", "gated", "deprecated"}
VALID_OUTPUT_STATUSES: set[str] = {"ok", "warning", "error", "unavailable"}
VALID_RANKING_EFFECTS: set[str] = {"none", "proposed", "active"}
VALID_RELEASE_STATUSES: set[str] = {"open", "staged", "restricted", "internal", "do-not-release"}

REQUIRED_OUTPUT_CONTRACT_FIELDS: list[str] = [
    "adapter_id", "adapter_version", "mode", "output_status",
    "score_fields", "uncertainty", "warnings", "failure_reason",
    "release_status", "ranking_effect",
]


@dataclass
class AdapterDeclaration:
    adapter_id: str
    adapter_version: str
    mode: str
    output_status: str
    score_fields: dict
    uncertainty: float | None
    warnings: list[str]
    failure_reason: str | None
    release_status: str
    ranking_effect: str
    has_baseline_comparison: bool
    makes_network_calls: bool
    network_call_documented: bool
    dry_lab_only: bool = True


@dataclass
class AdapterValidationResult:
    adapter_id: str
    passed: bool
    errors: list[str]
    warnings_list: list[str]
    dry_lab_only: bool = True


def validate_adapter_declaration(decl: AdapterDeclaration) -> AdapterValidationResult:
    errors: list[str] = []
    warnings_list: list[str] = []

    if not decl.adapter_id:
        errors.append("adapter_id must not be empty")
    if not decl.adapter_version:
        errors.append("adapter_version must not be empty")
    if decl.mode not in VALID_ADAPTER_MODES:
        errors.append(f"mode={decl.mode!r} not in {sorted(VALID_ADAPTER_MODES)}")
    if decl.output_status not in VALID_OUTPUT_STATUSES:
        errors.append(f"output_status={decl.output_status!r} not in {sorted(VALID_OUTPUT_STATUSES)}")
    if decl.ranking_effect not in VALID_RANKING_EFFECTS:
        errors.append(f"ranking_effect={decl.ranking_effect!r} not in {sorted(VALID_RANKING_EFFECTS)}")
    if decl.release_status not in VALID_RELEASE_STATUSES:
        errors.append(f"release_status={decl.release_status!r} not in {sorted(VALID_RELEASE_STATUSES)}")
    if not decl.dry_lab_only:
        errors.append("dry_lab_only must be True")
    if decl.ranking_effect in {"proposed", "active"} and not decl.has_baseline_comparison:
        errors.append("ranking_effect requires has_baseline_comparison=True")
    if decl.makes_network_calls and not decl.network_call_documented:
        errors.append("network calls must be documented (network_call_documented=True)")
    if decl.mode == "gated" and decl.ranking_effect == "none":
        warnings_list.append("mode=gated with ranking_effect=none is unusual; verify intent")
    if decl.mode == "deprecated" and decl.ranking_effect in {"proposed", "active"}:
        errors.append("deprecated adapter must not have active/proposed ranking_effect")
    if decl.uncertainty is not None and not (0.0 <= decl.uncertainty <= 1.0):
        errors.append(f"uncertainty={decl.uncertainty} must be in 0.0-1.0 or None")

    return AdapterValidationResult(
        adapter_id=decl.adapter_id or "<unknown>",
        passed=len(errors) == 0,
        errors=errors,
        warnings_list=warnings_list,
        dry_lab_only=True,
    )


def validate_adapter_dict(d: dict[str, Any]) -> AdapterValidationResult:
    """Validate a raw dict (e.g. from JSON). Converts to AdapterDeclaration first."""
    missing = [f for f in REQUIRED_OUTPUT_CONTRACT_FIELDS if f not in d]
    if missing:
        return AdapterValidationResult(
            adapter_id=d.get("adapter_id", "<unknown>"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            warnings_list=[],
            dry_lab_only=True,
        )
    try:
        decl = AdapterDeclaration(
            adapter_id=d.get("adapter_id", ""),
            adapter_version=d.get("adapter_version", ""),
            mode=d.get("mode", ""),
            output_status=d.get("output_status", ""),
            score_fields=d.get("score_fields", {}),
            uncertainty=d.get("uncertainty"),
            warnings=d.get("warnings", []),
            failure_reason=d.get("failure_reason"),
            release_status=d.get("release_status", ""),
            ranking_effect=d.get("ranking_effect", ""),
            has_baseline_comparison=d.get("has_baseline_comparison", False),
            makes_network_calls=d.get("makes_network_calls", False),
            network_call_documented=d.get("network_call_documented", False),
            dry_lab_only=d.get("dry_lab_only", True),
        )
    except Exception as e:
        return AdapterValidationResult(
            adapter_id=d.get("adapter_id", "<unknown>"),
            passed=False,
            errors=[f"Could not parse AdapterDeclaration: {e}"],
            warnings_list=[],
            dry_lab_only=True,
        )
    return validate_adapter_declaration(decl)
