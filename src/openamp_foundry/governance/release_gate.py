"""Release gate validator — confirms all required checks pass before external release.

Prevents unsafe or incomplete releases from escaping the dry-lab boundary.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

RELEASE_TYPES: set[str] = {
    "candidate", "model", "dataset", "evidence_packet", "schema"
}

# Gates that apply to ALL release types
UNIVERSAL_GATES: list[str] = [
    "ci_tests_pass",
    "agent_check_passes",
    "no_critical_issues",
    "dry_lab_only_confirmed",
    "safety_flags_reviewed",
    "data_license_verified",
    "no_hardcoded_secrets",
]

# Additional gates per release type
EXTRA_GATES_BY_TYPE: dict[str, list[str]] = {
    "candidate": ["evidence_level_checked", "human_review_complete", "proof_ladder_verified"],
    "model": ["model_card_present", "baseline_comparison_present", "human_signoff"],
    "dataset": ["data_governance_signoff", "license_declaration_present"],
    "evidence_packet": ["h_phase_checks_passed", "provenance_hash_present"],
    "schema": ["schema_compatibility_passes", "version_bumped", "changelog_updated"],
}


@dataclass
class ReleaseGateResult:
    release_type: str
    artifact_id: str
    passed: bool
    gates_passed: list[str]
    gates_failed: list[str]
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


def validate_release_gate(
    release_type: str,
    artifact_id: str,
    gate_statuses: dict[str, bool],
) -> ReleaseGateResult:
    """
    Validate that all required gates are green for a given release type.

    gate_statuses: dict mapping gate name -> bool (True=pass, False=fail)
    Any gate not present in gate_statuses is treated as failed.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not artifact_id:
        errors.append("artifact_id must not be empty")
    if release_type not in RELEASE_TYPES:
        errors.append(f"release_type={release_type!r} not in {sorted(RELEASE_TYPES)}")
        return ReleaseGateResult(
            release_type=release_type,
            artifact_id=artifact_id or "<unknown>",
            passed=False,
            gates_passed=[],
            gates_failed=[],
            errors=errors,
            warnings=warnings,
            dry_lab_only=True,
        )

    required_gates = UNIVERSAL_GATES + EXTRA_GATES_BY_TYPE.get(release_type, [])
    passed_gates = []
    failed_gates = []

    for gate in required_gates:
        status = gate_statuses.get(gate)
        if status is True:
            passed_gates.append(gate)
        else:
            failed_gates.append(gate)
            if status is None:
                errors.append(f"Gate '{gate}' status not provided (treated as failed)")
            else:
                errors.append(f"Gate '{gate}' failed")

    if "dry_lab_only_confirmed" in failed_gates:
        errors.append("CRITICAL: dry_lab_only_confirmed must be True — release blocked")

    return ReleaseGateResult(
        release_type=release_type,
        artifact_id=artifact_id,
        passed=len(failed_gates) == 0,
        gates_passed=passed_gates,
        gates_failed=failed_gates,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )
