"""Validation logic for SimulationResult dataclass instances."""
from __future__ import annotations

import math
from typing import Any

from .interfaces import SimulationResult


def validate_simulation_result(
    result: SimulationResult,
    *,
    strict: bool = False,
) -> list[str]:
    """Validate a SimulationResult instance.

    Returns a list of error messages (empty = valid).

    Always checks:
    - module is a non-empty string
    - version is a non-empty string
    - scope is a list of non-empty strings
    - scores is a dict[str, float] with all finite values
    - uncertainty is a float in [0.0, 1.0]
    - validated_against is a list of strings
    - notes is a list of strings

    When strict=True, also checks:
    - module must not be "dummy" or contain "stub" (case-insensitive)
    - uncertainty must be < 1.0 (1.0 means "completely uncertain")
    - validated_against must be non-empty
    """
    errors: list[str] = []

    if not isinstance(result.module, str) or not result.module:
        errors.append("module must be a non-empty string")

    if not isinstance(result.version, str) or not result.version:
        errors.append("version must be a non-empty string")

    if not isinstance(result.scope, list):
        errors.append("scope must be a list")
    else:
        for i, s in enumerate(result.scope):
            if not isinstance(s, str) or not s:
                errors.append(f"scope[{i}] must be a non-empty string")

    if not isinstance(result.scores, dict):
        errors.append("scores must be a dict")
    else:
        for key, val in result.scores.items():
            if not isinstance(val, (int, float)):
                errors.append(f"scores[{key!r}] must be a number, got {type(val).__name__}")
            elif isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                errors.append(f"scores[{key!r}] must be a finite number, got {val}")

    if not isinstance(result.uncertainty, (int, float)):
        errors.append("uncertainty must be a number")
    elif isinstance(result.uncertainty, float) and math.isnan(result.uncertainty):
        errors.append("uncertainty must not be NaN")
    else:
        if result.uncertainty < 0.0:
            errors.append(f"uncertainty must be >= 0.0, got {result.uncertainty}")
        if result.uncertainty > 1.0:
            errors.append(f"uncertainty must be <= 1.0, got {result.uncertainty}")

    if not isinstance(result.validated_against, list):
        errors.append("validated_against must be a list")
    else:
        for i, va in enumerate(result.validated_against):
            if not isinstance(va, str):
                errors.append(f"validated_against[{i}] must be a string")

    if not isinstance(result.notes, list):
        errors.append("notes must be a list")
    else:
        for i, n in enumerate(result.notes):
            if not isinstance(n, str):
                errors.append(f"notes[{i}] must be a string")

    if strict:
        if isinstance(result.module, str):
            module_lower = result.module.lower()
            if result.module.lower() == "dummy":
                errors.append("strict: module must not be 'dummy'")
            if "stub" in module_lower:
                errors.append("strict: module must not contain 'stub'")
        if isinstance(result.uncertainty, (int, float)):
            if result.uncertainty >= 1.0:
                errors.append("strict: uncertainty must be < 1.0")
        if not isinstance(result.validated_against, list) or len(result.validated_against) == 0:
            errors.append("strict: validated_against must be non-empty")

    return errors


def validate_simulation_result_batch(
    results: list[SimulationResult],
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Validate a batch of SimulationResult instances.

    Returns a dict with:
    - checked: number of results checked
    - valid: number with 0 errors
    - invalid: number with >0 errors
    - errors_by_module: dict[str, list[str]] mapping module name to error list
    - any_invalid: True if any result has errors
    - dry_lab_only: always True
    """
    checked = len(results)
    errors_by_module: dict[str, list[str]] = {}
    valid_count = 0
    invalid_count = 0

    for result in results:
        errs = validate_simulation_result(result, strict=strict)
        if errs:
            invalid_count += 1
            errors_by_module[result.module] = errs
        else:
            valid_count += 1

    return {
        "checked": checked,
        "valid": valid_count,
        "invalid": invalid_count,
        "errors_by_module": errors_by_module,
        "any_invalid": invalid_count > 0,
        "dry_lab_only": True,
    }
