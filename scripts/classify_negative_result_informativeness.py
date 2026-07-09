"""Classify a negative-result entry as informative, neutral, or non-informative.

Evaluates entries against the 7-dimension informativeness framework defined in
docs/evidence/NEGATIVE_RESULT_INFORMATIVENESS_GUIDE.md.

Each entry is scored 0.0-7.0 (14 half-points). Classification:
  - INFORMATIVE: 6.0–7.0  — calibration asset
  - NEUTRAL:     3.5–5.5  — basic data present, analysis missing
  - NON_INFORMATIVE: 0.0–3.0 — cannot support learning

Fail-closed on missing entries: any missing required field scores 0 for that dimension.

Usage:
    python scripts/classify_negative_result_informativeness.py \\
        --entry '{"candidate_id": "TEST-001", "sequence": "ACDEFGHIKLMNPQRSTVWY", ...}' \\
        [--out-json output.json]

    python scripts/classify_negative_result_informativeness.py \\
        --input examples/negative_result_entry_example.json \\
        [--out-json output.json]

Exit codes:
    0  Success
    2  Input error (missing file, invalid JSON)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


INFORMATIVE_SCORE_MIN = 6.0
NEUTRAL_SCORE_MIN = 3.5


def load_entry(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Load entry from JSON string, file path, or dict."""
    if isinstance(source, dict):
        return source
    p = Path(source)
    if p.exists():
        try:
            with p.open("r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in {p}: {e}"
            raise ValueError(msg) from e
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON string: {e}"
        raise ValueError(msg) from e


def _identity_score(entry: dict[str, Any]) -> float:
    """Score for Identity dimension (0.0-1.0)."""
    score = 0.0
    cid = entry.get("candidate_id", "")
    seq = entry.get("sequence", "")
    if isinstance(cid, str) and len(cid.strip()) > 0:
        score += 0.5
    if isinstance(seq, str) and len(seq.strip()) > 0:
        score += 0.5
    return score


def _context_score(entry: dict[str, Any]) -> float:
    """Score for Context dimension (0.0-1.0)."""
    score = 0.0
    pv = entry.get("pipeline_version")
    sb = entry.get("source_batch")
    dt = entry.get("date")
    if isinstance(pv, str) and len(pv.strip()) > 0:
        score += 0.5
    if isinstance(sb, str) and len(sb.strip()) > 0:
        score += 0.5
    return score


def _specificity_score(entry: dict[str, Any]) -> float:
    """Score for Specificity dimension (0.0-1.0).

    Checks reason_detail for numeric values/thresholds and driving features.
    """
    score = 0.0
    detail = entry.get("reason_detail", "")
    if not isinstance(detail, str) or len(detail.strip()) == 0:
        return score
    if len(detail) >= 20:
        score += 0.25
    if any(c.isdigit() for c in detail):
        score += 0.25
    descriptive_indicators = [
        "because", "driving", "due to", "from", "score", "threshold",
        "below", "above", "exceeds", "gate",
    ]
    if any(ind in detail.lower() for ind in descriptive_indicators):
        score += 0.25
    feature_markers = ["GRAVY", "charge", "hydrophob", "hemolysis", "helic",
                       "prolin", "cys", "length", "weight", "score",
                       "similarity", "pattern", "motif"]
    if any(m in detail for m in feature_markers):
        score += 0.25
    return min(score, 1.0)


def _actionability_score(entry: dict[str, Any]) -> float:
    """Score for Actionability dimension (0.0-1.0).

    Looks for indicators that enable specific actions or reveal systematic issues.
    """
    score = 0.0
    notes = entry.get("reviewer_notes", "")
    detail = entry.get("reason_detail", "")
    if not isinstance(notes, str):
        notes = ""

    actionable_indicators = [
        "should", "consider", "recommend", "suggest", "track", "flag",
        "tighten", "loosen", "adjust", "recalibrat", "improve", "fix",
        "systematic", "pattern", "recurring", "consistent", "all candidate",
        "batch-level", "class",
    ]
    if any(ind in notes.lower() for ind in actionable_indicators):
        score += 0.5
    if any(ind in detail.lower() for ind in ["systematic", "pattern", "batch-level",
                                              "all candidate"]):
        score += 0.25
    if len(notes) >= 50:
        score += 0.25
    return min(score, 1.0)


def _verifiability_score(entry: dict[str, Any]) -> float:
    """Score for Verifiability dimension (0.0-1.0)."""
    score = 0.0
    for key in ["score_activity", "score_safety", "score_novelty", "score_ensemble"]:
        val = entry.get(key)
        if isinstance(val, (int, float)) and 0 <= val <= 1:
            score += 0.25
    score = min(score, 0.5)
    result = entry.get("assay_result")
    unit = entry.get("assay_unit")
    if isinstance(result, str) and len(result.strip()) > 0:
        score += 0.25
    if isinstance(unit, str) and len(unit.strip()) > 0:
        score += 0.25
    return min(score, 1.0)


def _structured_metadata_score(entry: dict[str, Any]) -> float:
    """Score for Structured Metadata dimension (0.0-1.0).

    Checks category-appropriate conditional fields and superseded_by.
    """
    score = 0.0
    eid = entry.get("entry_id")
    if eid is not None:
        score += 0.25
    cat = entry.get("reason_category", "")
    if isinstance(cat, str) and cat in (
        "pre_selection_reject", "selected_untested", "lab_inactive",
        "lab_toxic", "control_failure", "synthesis_failure",
    ):
        score += 0.25
    if cat in ("lab_inactive", "lab_toxic", "synthesis_failure"):
        at = entry.get("assay_type")
        ar = entry.get("assay_result")
        au = entry.get("assay_unit")
        if isinstance(at, str) and len(at.strip()) > 0:
            score += 0.25
        if isinstance(ar, str) and len(ar.strip()) > 0:
            score += 0.25
        if isinstance(au, str) and len(au.strip()) > 0:
            score += 0.25
    sb = entry.get("superseded_by")
    if sb is not None:
        score += 0.5
    return min(score, 1.0)


def _interpretation_score(entry: dict[str, Any]) -> float:
    """Score for Interpretation dimension (0.0-1.0).

    Evaluates reviewer_notes for analytical content beyond restating the detail.
    """
    score = 0.0
    notes = entry.get("reviewer_notes", "")
    if not isinstance(notes, str) or len(notes.strip()) < 30:
        return score
    score += 0.25
    detail = entry.get("reason_detail", "")
    if not isinstance(detail, str):
        detail = ""
    if notes != detail:
        score += 0.25
    analytical_markers = [
        "because", "suggest", "indicate", "hypothesis", "consistent with",
        "expected", "unexpected", "notable", "concern", "risk", "tradeoff",
        "recommend", "consider", "should", "may", "could", "warrant",
    ]
    if any(m in notes.lower() for m in analytical_markers):
        score += 0.25
    if len(notes) >= 100:
        score += 0.25
    return min(score, 1.0)


def classify_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Classify a single negative-result entry.

    Returns dict with per-dimension scores, total, classification, and
    metadata.
    """
    dimensions = {
        "identity": _identity_score(entry),
        "context": _context_score(entry),
        "specificity": _specificity_score(entry),
        "actionability": _actionability_score(entry),
        "verifiability": _verifiability_score(entry),
        "structured_metadata": _structured_metadata_score(entry),
        "interpretation": _interpretation_score(entry),
    }
    total = round(sum(dimensions.values()), 2)

    if total >= INFORMATIVE_SCORE_MIN:
        classification = "INFORMATIVE"
    elif total >= NEUTRAL_SCORE_MIN:
        classification = "NEUTRAL"
    else:
        classification = "NON_INFORMATIVE"

    return {
        "entry_id": entry.get("entry_id"),
        "candidate_id": entry.get("candidate_id"),
        "reason_category": entry.get("reason_category"),
        "classification": classification,
        "total_score": total,
        "dimensions": dimensions,
        "caveat": (
            "Computational classification only. Does not validate scientific "
            "accuracy. An INFORMATIVE entry may still contain incorrect "
            "conclusions."
        ),
    }


def build_markdown(result: dict[str, Any]) -> str:
    """Build human-readable Markdown summary from classification result."""
    dim_labels = {
        "identity": "Identity",
        "context": "Context",
        "specificity": "Specificity",
        "actionability": "Actionability",
        "verifiability": "Verifiability",
        "structured_metadata": "Structured metadata",
        "interpretation": "Interpretation",
    }
    cid = result.get("candidate_id", "unknown")
    eid = result.get("entry_id", "?")
    lines = [
        f"# Negative-Result Informativeness Classification: {cid}",
        "",
        f"**Entry ID:** {eid}",
        f"**Category:** {result.get('reason_category', 'N/A')}",
        f"**Classification: {result['classification']}**",
        f"**Total score:** {result['total_score']}/7.0",
        "",
        "| Dimension | Score |",
        "|-----------|-------|",
    ]
    for key, label in dim_labels.items():
        lines.append(f"| {label} | {result['dimensions'].get(key, 0.0)} |")
    lines.append("")
    lines.append("### Classification thresholds")
    lines.append(f"- INFORMATIVE: >= {INFORMATIVE_SCORE_MIN}")
    lines.append(f"- NEUTRAL: >= {NEUTRAL_SCORE_MIN}")
    lines.append(f"- NON_INFORMATIVE: < {NEUTRAL_SCORE_MIN}")
    lines.append("")
    lines.append(f"> {result['caveat']}")
    return "\n".join(lines) + "\n"


def build_output(
    entry: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Build the full output dict with entry, result, and metadata."""
    return {
        "classifier_version": "v1.0.0",
        "framework": "NEGATIVE_RESULT_INFORMATIVENESS_GUIDE.md",
        "input_entry": entry,
        "result": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify a negative-result entry as informative/neutral/non-informative."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--entry", type=str, help="JSON string of a negative-result entry")
    source.add_argument("--input", type=str, help="Path to JSON file with a negative-result entry")
    parser.add_argument("--out-json", type=str, help="Path to write JSON output")
    parser.add_argument("--out-md", type=str, help="Path to write Markdown output")
    args = parser.parse_args()

    try:
        if args.input:
            entry = load_entry(args.input)
        else:
            entry = load_entry(args.entry)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    result = classify_entry(entry)
    output = build_output(entry, result)

    print(f"Classification: {result['classification']}")
    print(f"Total score: {result['total_score']}/7.0")
    for dim_key, dim_score in result["dimensions"].items():
        print(f"  {dim_key}: {dim_score}")

    if args.out_json:
        p = Path(args.out_json)
        with p.open("w") as f:
            json.dump(output, f, indent=2)
        print(f"JSON output written to {p}")

    if args.out_md:
        p = Path(args.out_md)
        md = build_markdown(result)
        with p.open("w") as f:
            f.write(md)
        print(f"Markdown output written to {p}")


if __name__ == "__main__":
    main()
