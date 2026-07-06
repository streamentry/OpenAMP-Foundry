"""Run-manifest verification utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MISSING_HASH_SENTINELS = {"", "N/A", None}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_path(path: str, root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def _sorted_json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _missing_field_errors(manifest: dict[str, Any]) -> list[str]:
    required = [
        "run_id",
        "pipeline_version",
        "config_hash",
        "generated_at",
        "inputs",
        "input_hashes",
        "outputs",
    ]
    return [f"Missing required manifest field: {field}" for field in required if field not in manifest]


def _check_input_hashes(manifest: dict[str, Any], root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    input_hashes = manifest.get("input_hashes", {})
    if not isinstance(input_hashes, dict):
        return ["input_hashes must be an object"], warnings

    for path_str, expected_hash in sorted(input_hashes.items()):
        if expected_hash in MISSING_HASH_SENTINELS:
            warnings.append(f"Input has no recorded hash: {path_str}")
            continue
        input_p = _resolve_path(path_str, root)
        if not input_p.exists():
            errors.append(f"Input file missing: {path_str}")
            continue
        if not input_p.is_file():
            errors.append(f"Input path is not a file: {path_str}")
            continue
        actual_hash = _sha256_file(input_p)
        if actual_hash != expected_hash:
            errors.append(
                "Input hash mismatch for "
                f"{path_str}: expected {expected_hash}, actual {actual_hash}"
            )
    return errors, warnings


def _check_outputs(manifest: dict[str, Any], root: Path) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    observed: dict[str, str] = {}
    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list):
        return ["outputs must be a list"], observed

    for path_str in outputs:
        output_p = _resolve_path(str(path_str), root)
        if not output_p.exists():
            errors.append(f"Output path missing: {path_str}")
        elif output_p.is_file():
            observed[str(path_str)] = _sha256_file(output_p)
    return errors, observed


def _check_output_hashes(manifest: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    output_hashes = manifest.get("output_hashes", {})
    if output_hashes and not isinstance(output_hashes, dict):
        return ["output_hashes must be an object when present"]

    for path_str, expected_hash in sorted(output_hashes.items()):
        output_p = _resolve_path(path_str, root)
        if not output_p.exists():
            errors.append(f"Output hash target missing: {path_str}")
            continue
        if not output_p.is_file():
            errors.append(f"Output hash target is not a file: {path_str}")
            continue
        actual_hash = _sha256_file(output_p)
        if actual_hash != expected_hash:
            errors.append(
                "Output hash mismatch for "
                f"{path_str}: expected {expected_hash}, actual {actual_hash}"
            )
    return errors


def _error_report(manifest_path: Path, errors: list[str]) -> dict[str, Any]:
    return {
        "ok": False,
        "manifest_path": str(manifest_path),
        "errors": errors,
        "warnings": [],
        "observed_output_hashes": {},
    }


def verify_run_manifest(
    manifest_path: str | Path,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Verify a run manifest against the current filesystem."""
    manifest_p = Path(manifest_path)
    root_p = Path(root) if root is not None else Path.cwd()

    if not manifest_p.exists():
        return _error_report(manifest_p, [f"Manifest not found: {manifest_p}"])

    try:
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _error_report(manifest_p, [f"Manifest is not valid JSON: {exc}"])

    errors = _missing_field_errors(manifest)
    input_errors, warnings = _check_input_hashes(manifest, root_p)
    output_errors, observed = _check_outputs(manifest, root_p)
    output_hash_errors = _check_output_hashes(manifest, root_p)
    errors.extend(input_errors)
    errors.extend(output_errors)
    errors.extend(output_hash_errors)

    payload = _sorted_json_dumps(manifest).encode("utf-8")
    payload_hash = hashlib.sha256(payload).hexdigest()
    return {
        "ok": not errors,
        "manifest_path": str(manifest_p),
        "manifest_payload_sha256": payload_hash,
        "errors": errors,
        "warnings": warnings,
        "observed_output_hashes": observed,
    }
