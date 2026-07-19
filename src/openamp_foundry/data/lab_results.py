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
    Skips files that fail schema validation with a warning. Raises when the
    input path is missing or is not a directory.
    """
    results, errors = load_lab_results_dir_with_errors(directory)
    if errors:
        import warnings

        warnings.warn(
            f"Skipped {len(errors)} invalid lab result files:\n"
            + "\n".join(f"{e['file']}: {e['error']}" for e in errors),
            stacklevel=2,
        )
    return results


def load_lab_results_dir_with_errors(
    directory: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Load lab results and retain structured validation failures.

    The legacy :func:`load_lab_results_dir` API intentionally remains warning-
    based for compatibility. New review and calibration workflows should use
    this helper so invalid files cannot disappear from the evidence trail.
    """
    d = validate_lab_results_directory(directory)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for p in sorted(d.glob("*.json")):
        try:
            results.append(load_lab_result(p))
        except Exception as exc:
            errors.append({
                "file": p.name,
                "error": str(exc) or exc.__class__.__name__,
            })
    return (
        sorted(results, key=lambda r: (r.get("assay_date", ""), r.get("result_id", ""))),
        errors,
    )


def validate_lab_results_directory(directory: str | Path) -> Path:
    """Validate that a lab-result input path exists and is a directory.

    An absent or mistyped result path must not be interpreted as an empty
    experimental cohort. Callers may still use an existing empty directory to
    represent a known, not-yet-populated result set.
    """
    d = Path(directory)
    if not d.exists():
        raise FileNotFoundError(f"lab results directory not found: {d}")
    if not d.is_dir():
        raise NotADirectoryError(f"lab results path is not a directory: {d}")
    return d


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


def duplicate_result_ids(results: list[dict[str, Any]]) -> list[str]:
    """Return sorted result IDs that occur more than once.

    ``result_id`` is the identity key for an experimental observation. Duplicate
    IDs can represent a copied file or two conflicting observations and must be
    surfaced before a report is treated as a clean cohort.
    """
    counts: dict[str, int] = {}
    for result in results:
        result_id = result.get("result_id", "")
        counts[result_id] = counts.get(result_id, 0) + 1
    return sorted(result_id for result_id, count in counts.items() if count > 1)

def summarise_candidate_outcomes(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build one row per candidate for decision-grade wet-lab review.

    The output stays descriptive. It does not convert assay readouts into
    claims of efficacy or safety. Raw observations remain available for audit,
    while outcome flags and numeric counts use only observations whose positive
    and negative controls both passed. This prevents a failed-control assay
    from looking like an interpretable candidate outcome.
    """
    rows: list[dict[str, Any]] = []
    for candidate_id, candidate_results in sorted(candidate_result_map(results).items()):
        assay_types = sorted({r.get("assay_type", "other") for r in candidate_results})
        organisms = sorted({r.get("organism_or_cell_line", "unknown") for r in candidate_results})
        usable_results = [
            r
            for r in candidate_results
            if r.get("positive_control_passed") and r.get("negative_control_passed")
        ]
        raw_qualitative = [
            r.get("result_qualitative") or "unclassified" for r in candidate_results
        ]
        qualitative = [
            r.get("result_qualitative") or "unclassified" for r in usable_results
        ]
        controls_failed = [
            r["result_id"]
            for r in candidate_results
            if not (r.get("positive_control_passed") and r.get("negative_control_passed"))
        ]
        raw_numeric_results = [
            r for r in candidate_results if r.get("result_value") is not None
        ]
        numeric_results = [r for r in usable_results if r.get("result_value") is not None]
        dates = sorted(r.get("assay_date", "") for r in candidate_results)

        rows.append(
            {
                "candidate_id": candidate_id,
                "n_results": len(candidate_results),
                "n_usable_results": len(usable_results),
                "assay_types": assay_types,
                "organisms_or_cells": organisms,
                "qualitative_results": qualitative,
                "raw_qualitative_results": raw_qualitative,
                "has_any_active": "active" in qualitative,
                "has_any_toxic": "toxic" in qualitative,
                "has_any_inconclusive": "inconclusive" in qualitative,
                "raw_has_any_active": "active" in raw_qualitative,
                "raw_has_any_toxic": "toxic" in raw_qualitative,
                "raw_has_any_inconclusive": "inconclusive" in raw_qualitative,
                "all_controls_passed": len(controls_failed) == 0,
                "control_fail_result_ids": controls_failed,
                "max_replicate_count": max(r.get("replicate_count", 0) for r in candidate_results),
                "first_assay_date": dates[0] if dates else None,
                "last_assay_date": dates[-1] if dates else None,
                "n_numeric_results": len(numeric_results),
                "n_raw_numeric_results": len(raw_numeric_results),
            }
        )
    return rows
