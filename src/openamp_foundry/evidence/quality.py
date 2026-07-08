from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from openamp_foundry.evidence.schemas import validate_json_schema

VALID_PROOF_LADDER_LEVELS = frozenset({
    "valid_input",
    "reproducible_dry_lab_features",
    "baseline_triaged",
    "leakage_aware_benchmark",
    "multi_signal_candidate_evidence",
    "expert_reviewed_assay_proposal",
    "initial_qualified_assay_result",
    "safety_adjusted_follow_up_signal",
    "independent_replication",
    "reusable_discovery_loop",
    "translational_or_clinical_relevance",
})

REQUIRED_SCORE_KEYS = frozenset({"activity", "safety", "synthesis", "novelty", "ensemble"})


def _check_schema(cert: dict[str, Any], schema_path: str | Path) -> list[str]:
    try:
        validate_json_schema(cert, schema_path)
        return []
    except Exception as exc:
        return [f"Schema validation failed: {exc}"]


def _check_proof_ladder_level(cert: dict[str, Any]) -> list[str]:
    level = cert.get("proof_ladder_level")
    if not level:
        return ["Missing proof_ladder_level"]
    if level not in VALID_PROOF_LADDER_LEVELS:
        return [f"Invalid proof_ladder_level: {level}"]
    return []


def _check_known_failure_modes(cert: dict[str, Any]) -> list[str]:
    modes = cert.get("known_failure_modes", [])
    if not isinstance(modes, list):
        return ["known_failure_modes must be a list"]
    if not modes:
        return ["known_failure_modes is empty — no failure modes documented"]
    return []


def _check_recommended_next_steps(cert: dict[str, Any]) -> list[str]:
    steps = cert.get("recommended_next_steps", [])
    if not isinstance(steps, list):
        return ["recommended_next_steps must be a list"]
    if not steps:
        return ["recommended_next_steps is empty"]
    has_disclaimer = any(
        "no antimicrobial activity" in s.lower()
        or "do not claim" in s.lower()
        or "not validated" in s.lower()
        for s in steps
    )
    if not has_disclaimer:
        return ["recommended_next_steps missing disclaimer about antimicrobial activity"]
    return []


def _check_generated_at(cert: dict[str, Any]) -> list[str]:
    ts = cert.get("generated_at", "")
    if not ts:
        return ["Missing generated_at"]
    try:
        datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return [f"Invalid generated_at timestamp: {ts}"]
    return []


def _check_scores(cert: dict[str, Any]) -> list[str]:
    scores = cert.get("scores", {})
    if not isinstance(scores, dict):
        return ["scores must be a dict"]
    missing = REQUIRED_SCORE_KEYS - set(scores.keys())
    if missing:
        return [f"Missing required score keys: {sorted(missing)}"]
    return []


def _check_selection_reason(cert: dict[str, Any]) -> list[str]:
    reasons = cert.get("selection_reason", [])
    if not isinstance(reasons, list):
        return ["selection_reason must be a list"]
    if not reasons:
        return ["selection_reason is empty — no selection rationale documented"]
    return []


def _check_features(cert: dict[str, Any]) -> list[str]:
    features = cert.get("features", {})
    if not isinstance(features, dict):
        return ["features must be a dict"]
    if not features:
        return ["features is empty"]
    return []


_ALL_CHECKS = [
    _check_schema,
    _check_proof_ladder_level,
    _check_known_failure_modes,
    _check_recommended_next_steps,
    _check_generated_at,
    _check_scores,
    _check_selection_reason,
    _check_features,
]

_CRITICAL_CHECKS = frozenset({_check_schema, _check_proof_ladder_level, _check_scores, _check_generated_at})


def assess_certificate_quality(
    cert: dict[str, Any],
    schema_path: str | Path = "schemas/candidate.schema.json",
) -> dict[str, Any]:
    errors: list[str] = []
    for check in _ALL_CHECKS:
        if check is _check_schema:
            errors.extend(check(cert, schema_path))
        else:
            errors.extend(check(cert))

    critical_check_names = {check.__name__ for check in _CRITICAL_CHECKS}
    critical_prefixes = ("Schema validation", "Missing proof_ladder", "Invalid proof_ladder", "Missing required score", "Missing generated_at", "Invalid generated_at")
    critical_errors = [
        e for e in errors
        if e.startswith(critical_prefixes)
    ]

    if errors and not critical_errors:
        tier = "warn"
    elif critical_errors:
        tier = "fail"
    else:
        tier = "pass"

    return {
        "tier": tier,
        "critical_errors": critical_errors,
        "warnings": [e for e in errors if e not in critical_errors],
        "error_count": len(errors),
    }
