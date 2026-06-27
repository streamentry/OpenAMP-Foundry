"""Lab results ingestion for the active-learning loop.

Loads and validates lab assay results against schemas/lab_result.schema.json.
Results feed the active-learning cycle: hits → stronger signal for next generation,
misses → updated negative dataset.

IMPORTANT: This module records experimental data only. It does not prove efficacy,
safety, or suitability for any use. All biological claims require qualified expert
review and independent replication.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openamp_foundry.evidence.schemas import validate_json_schema

LAB_RESULT_SCHEMA = Path(__file__).parent.parent.parent.parent / "schemas" / "lab_result.schema.json"


def load_lab_result(path: str | Path) -> dict[str, Any]:
    """Load and validate a single lab result JSON file.

    Raises ValueError if the file does not validate against lab_result.schema.json.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        result = json.load(f)
    validate_json_schema(result, LAB_RESULT_SCHEMA)
    return result


def load_lab_results_dir(directory: str | Path) -> list[dict[str, Any]]:
    """Load all lab result JSON files from a directory.

    Returns a list of validated result dicts, sorted by assay_date then result_id.
    Skips files that fail schema validation with a warning.
    """
    d = Path(directory)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for p in sorted(d.glob("*.json")):
        try:
            results.append(load_lab_result(p))
        except Exception as exc:
            errors.append(f"{p.name}: {exc}")
    if errors:
        import warnings
        warnings.warn(
            f"Skipped {len(errors)} invalid lab result files:\n" + "\n".join(errors),
            stacklevel=2,
        )
    return sorted(results, key=lambda r: (r.get("assay_date", ""), r.get("result_id", "")))


def summarise_lab_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce a summary of lab results for a candidate batch.

    Returns counts by assay_type, qualitative result, and control status.
    All findings are raw experimental observations, not validated biological claims.
    """
    n = len(results)
    if n == 0:
        return {
            "n_results": 0,
            "disclaimer": "No lab results loaded.",
        }

    by_type: dict[str, int] = {}
    by_qualitative: dict[str, int] = {}
    n_controls_ok = 0

    for r in results:
        assay = r.get("assay_type", "other")
        by_type[assay] = by_type.get(assay, 0) + 1

        qual = r.get("result_qualitative") or "unclassified"
        by_qualitative[qual] = by_qualitative.get(qual, 0) + 1

        if r.get("positive_control_passed") and r.get("negative_control_passed"):
            n_controls_ok += 1

    return {
        "n_results": n,
        "n_valid_controls": n_controls_ok,
        "by_assay_type": by_type,
        "by_qualitative_result": by_qualitative,
        "disclaimer": (
            "Lab result summary. Raw experimental observations only. "
            "Not a validated drug efficacy, safety, or clinical claim. "
            "All results require qualified expert interpretation and independent replication."
        ),
    }


def candidate_result_map(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Map candidate_id → list of lab results.

    Allows quickly looking up all assay results for a given candidate.
    """
    mapping: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        cid = r["candidate_id"]
        mapping.setdefault(cid, []).append(r)
    return mapping
