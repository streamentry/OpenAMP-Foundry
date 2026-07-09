from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


REQUIRED_INTEGRATION_CHECKS: list[str] = [
    "manifest_schema_valid",
    "evidence_level_in_range",
    "dry_lab_only_acknowledged",
    "safety_flags_reviewed",
    "baseline_comparison_present",
]


@dataclass
class IntegrationCheckResult:
    check_name: str
    passed: bool
    detail: str
    dry_lab_only: bool = True


def run_integration_checks(
    manifest_dict: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # manifest_schema_valid
    cid = manifest_dict.get("candidate_id")
    seq = manifest_dict.get("sequence")
    el = manifest_dict.get("evidence_level")
    schema_valid = bool(cid) and bool(seq) and (el is not None)
    checks.append(asdict(IntegrationCheckResult(
        check_name="manifest_schema_valid",
        passed=schema_valid,
        detail=(
            "All required fields present"
            if schema_valid
            else "Missing one or more: candidate_id, sequence, evidence_level"
        ),
    )))

    # evidence_level_in_range
    level = manifest_dict.get("evidence_level")
    level_valid = isinstance(level, int) and 1 <= level <= 6
    checks.append(asdict(IntegrationCheckResult(
        check_name="evidence_level_in_range",
        passed=level_valid,
        detail=(
            f"evidence_level={level} in 1-6"
            if level_valid
            else f"evidence_level={level} is not in range 1-6"
        ),
    )))

    # dry_lab_only_acknowledged
    dry_lab = manifest_dict.get("dry_lab_only")
    dry_lab_ok = dry_lab is True
    checks.append(asdict(IntegrationCheckResult(
        check_name="dry_lab_only_acknowledged",
        passed=dry_lab_ok,
        detail=(
            "dry_lab_only is True"
            if dry_lab_ok
            else f"dry_lab_only={dry_lab!r}, expected True"
        ),
    )))

    # safety_flags_reviewed
    safety = manifest_dict.get("safety_flags")
    safety_ok = isinstance(safety, list)
    checks.append(asdict(IntegrationCheckResult(
        check_name="safety_flags_reviewed",
        passed=safety_ok,
        detail=(
            "safety_flags key present (list)"
            if safety_ok
            else "safety_flags key missing or not a list"
        ),
    )))

    # baseline_comparison_present
    scores = manifest_dict.get("scores")
    scores_ok = isinstance(scores, dict) and len(scores) > 0
    checks.append(asdict(IntegrationCheckResult(
        check_name="baseline_comparison_present",
        passed=scores_ok,
        detail=(
            f"scores dict has {len(scores)} entries"
            if scores_ok
            else "scores dict is empty or missing"
        ),
    )))

    passed_count = sum(1 for c in checks if c["passed"])
    failed_count = sum(1 for c in checks if not c["passed"])

    return {
        "checks": checks,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "all_passed": failed_count == 0,
        "dry_lab_only": True,
    }
