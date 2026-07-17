"""Lab-result calibration intake for the wet-lab feedback loop.

Joins a pilot panel CSV (computational predictions) with validated lab
result JSON files (experimental outcomes) to produce a decision-grade
calibration intake report.

This module is the *first* step of the wet-lab feedback loop:

    pilot panel (predictions)
        +
    lab results (actuals)
        |
        v
    build_calibration_intake_report
        |
        v
    per-candidate prediction-vs-actual rows
        |
        v
    cohort metrics gated by minimum sample size
        |
        v
    review artifact (NOT a recalibration decision)

The output is descriptive and audit-only. It does NOT:
    - rewrite selection rules;
    - modify scoring weights;
    - claim efficacy, safety, or clinical utility;
    - recompute evidence certificates;
    - upgrade assay readouts into biological claims.

Recalibration decisions must follow a separate, human-reviewed workflow
that explicitly compares pre-registered selection rules against observed
outcomes. See docs/research/WAVE2_PLAN.md and docs/evidence/DECISION_RULES.md.
"""
from __future__ import annotations

import csv
import json
import warnings
from pathlib import Path

from openamp_foundry.data.lab_results import (
    load_lab_results_dir_with_errors,
    summarise_candidate_outcomes,
    summarise_lab_results,
    validate_lab_results_directory,
)

# Minimum sample size required before any aggregate cohort metric is reported.
# Below this threshold the cohort is marked ``insufficient_data: True`` and
# no point estimate is produced. This protects against small-sample theater
# where a single MIC readout could swing an "AUROC" by 0.30.
MIN_COHORT_SIZE = 5

# Activity-vs-MIC binary threshold for retrospective triage comparison.
# Candidates with MIC <= this value are labelled "predicted_active" if their
# pipeline activity score was above ACTIVITY_THRESHOLD, else "predicted_inactive".
# Standard "active" cutoff from CLSI / EUCAST broth microdilution guidance.
MIC_ACTIVE_CUTOFF_UG_ML = 32.0
ACTIVITY_THRESHOLD = 0.70

# Hemolysis "high risk" cutoff for retrospective triage comparison.
# Reported as % hemolysis at the highest tested concentration.
# Candidates above this are flagged "hemolysis_high".
HEMOLYSIS_HIGH_PCT = 10.0

_DISCLAIMER = (
    "Calibration intake report. Descriptive join of computational predictions "
    "and validated wet-lab results only. This is NOT proof of efficacy, safety, "
    "or clinical utility. It does NOT trigger recalibration, weight updates, "
    "or changes to the pre-registered selection rule. Recalibration requires a "
    "separate human-reviewed decision log and must not rewrite success "
    "definitions after the fact. See docs/evidence/DECISION_RULES.md and "
    "docs/research/WAVE2_PLAN.md for the pre-registered Wave 2 workflow."
)


def _load_panel_csv(panel_csv):
    """Load a pilot panel CSV into a list of row dicts.

    Accepts both legacy ``pilot_panel.csv`` and the wider ``wave1_final_panel.csv``
    shape. Missing optional columns are tolerated.
    """
    p = Path(panel_csv)
    with p.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _to_float(value):
    """Parse a CSV cell into float, returning None on failure or empty."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _candidate_predictions(row):
    """Extract the prediction columns we will compare against lab outcomes."""
    return {
        "ensemble": _to_float(row.get("ensemble")),
        "activity": _to_float(row.get("activity")),
        "safety": _to_float(row.get("safety")),
        "synthesis": _to_float(row.get("synthesis")),
        "novelty": _to_float(row.get("novelty")),
        "selectivity_proxy": _to_float(row.get("selectivity_proxy")),
        "rich_selectivity": _to_float(row.get("rich_selectivity")),
        "pilot_priority": _to_float(row.get("pilot_priority")),
    }


def _is_active_mic(result):
    """Heuristic: classify a MIC result as active / inactive.

    Returns None when the result is qualitative-only or the assay is not MIC.
    Conservative cutoff at MIC <= 32 ug/mL matches the Wave 2 plan's "active"
    definition (docs/research/WAVE2_PLAN.md, Scenario B).
    """
    if result.get("assay_type") != "MIC":
        return None
    value = result.get("result_value")
    if value is None:
        return None
    try:
        return float(value) <= MIC_ACTIVE_CUTOFF_UG_ML
    except (TypeError, ValueError):
        return None


def _is_high_hemolysis(result):
    """Heuristic: classify a hemolysis result as high risk.

    Returns None when the result is qualitative-only or the assay is not
    hemolysis_RBC. Conservative cutoff at >= 10% hemolysis at the top tested
    concentration, matching the DBAASP/RBC literature convention for
    "non-selective."
    """
    if result.get("assay_type") != "hemolysis_RBC":
        return None
    value = result.get("result_value")
    if value is None:
        return None
    try:
        return float(value) >= HEMOLYSIS_HIGH_PCT
    except (TypeError, ValueError):
        return None


def _aggregate_per_candidate(results):
    """Build per-candidate rollup of actual experimental outcomes.

    Returns dict mapping candidate_id -> {
        n_results, n_mic, n_hemolysis, active_mic, high_hemolysis, ...
    }.
    Used as the "actual" side of the prediction-vs-actual join.
    """
    out = {}
    for r in results:
        cid = r.get("candidate_id", "")
        if not cid:
            continue
        slot = out.setdefault(
            cid,
            {
                "n_results": 0,
                "n_mic": 0,
                "n_hemolysis": 0,
                "n_cytotoxicity": 0,
                "active_mic": None,
                "high_hemolysis": None,
                "any_active_qualitative": False,
                "any_toxic_qualitative": False,
                "all_controls_passed": True,
                "assay_types": set(),
            },
        )
        slot["n_results"] += 1
        slot["assay_types"].add(r.get("assay_type", "other"))

        active = _is_active_mic(r)
        if active is not None:
            slot["n_mic"] += 1
            if slot["active_mic"] is None:
                slot["active_mic"] = active
            else:
                slot["active_mic"] = slot["active_mic"] or active

        high_hemo = _is_high_hemolysis(r)
        if high_hemo is not None:
            slot["n_hemolysis"] += 1
            if slot["high_hemolysis"] is None:
                slot["high_hemolysis"] = high_hemo
            else:
                slot["high_hemolysis"] = slot["high_hemolysis"] or high_hemo

        if r.get("assay_type") == "cytotoxicity_mammalian":
            slot["n_cytotoxicity"] += 1

        qual = r.get("result_qualitative")
        if qual == "active":
            slot["any_active_qualitative"] = True
        if qual == "toxic":
            slot["any_toxic_qualitative"] = True
        if not (r.get("positive_control_passed") and r.get("negative_control_passed")):
            slot["all_controls_passed"] = False

    for v in out.values():
        v["assay_types"] = sorted(v["assay_types"])
    return out


def _cohort_metric(
    matched, assay_type, predicate_lab, prediction_score_key,
    predicate_pred_direction, threshold,
):
    """Compute a single binary-prediction-vs-binary-actual cohort metric.

    Args:
        matched: per-candidate joined rows (one per candidate with both sides).
        assay_type: assay type to filter on (e.g. "MIC").
        predicate_lab: which "actual" boolean column to compare against
            (e.g. "active_mic", "high_hemolysis").
        prediction_score_key: key into row["predictions"] holding the
            pipeline score (e.g. "activity", "rich_selectivity").
        predicate_pred_direction: "above" or "below" - whether predicted score
            above threshold means predicted positive.
        threshold: pipeline score threshold.

    Returns:
        Dict with TP, FP, FN, TN, n, insufficient_data flag, and disclaimer.
    """
    rows = [m for m in matched if m.get("has_lab", {}).get(predicate_lab) is not None]
    n = len(rows)
    if n < MIN_COHORT_SIZE:
        return {
            "assay_type": assay_type,
            "predicate": predicate_lab,
            "prediction_score_key": prediction_score_key,
            "n": n,
            "min_required": MIN_COHORT_SIZE,
            "insufficient_data": True,
            "tp": None,
            "fp": None,
            "fn": None,
            "tn": None,
            "disclaimer": (
                f"Cohort too small for retrospective triage metric "
                f"(n={n} < {MIN_COHORT_SIZE}). No point estimate reported. "
                f"Collect more results before drawing conclusions."
            ),
        }

    tp = fp = fn = tn = 0
    considered = 0
    for row in rows:
        actual_positive = bool(row["has_lab"][predicate_lab])
        pred_score = row["predictions"].get(prediction_score_key)
        if pred_score is None:
            continue
        considered += 1
        if predicate_pred_direction == "above":
            predicted_positive = pred_score >= threshold
        else:
            predicted_positive = pred_score < threshold
        if predicted_positive and actual_positive:
            tp += 1
        elif predicted_positive and not actual_positive:
            fp += 1
        elif not predicted_positive and actual_positive:
            fn += 1
        else:
            tn += 1

    return {
        "assay_type": assay_type,
        "predicate": predicate_lab,
        "n": tp + fp + fn + tn,
        "min_required": MIN_COHORT_SIZE,
        "insufficient_data": False,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "disclaimer": (
            "Small retrospective cohort. Treat as descriptive only; not a "
            "validation of the pipeline. Cluster effects and selection bias "
            "from the pre-registered shortlist are NOT removed by this metric."
        ),
    }


def _per_candidate_rows(panel_rows, per_candidate_actuals):
    """Join predictions with actuals on candidate_id.

    Returns one row per candidate in the panel. Candidates with no lab
    results get ``has_lab = None``.
    """
    rows = []
    for row in panel_rows:
        cid = row.get("candidate_id", "")
        actuals = per_candidate_actuals.get(cid)
        rows.append(
            {
                "candidate_id": cid,
                "sequence_preview": (row.get("sequence", "") or "")[:32],
                "seed": row.get("seed", ""),
                "length": row.get("length", ""),
                "ensemble": _to_float(row.get("ensemble")),
                "activity": _to_float(row.get("activity")),
                "predictions": _candidate_predictions(row),
                "has_lab": actuals,
                "coverage_note": (
                    "matched"
                    if actuals is not None
                    else "no lab results yet"
                ),
            }
        )
    return rows


def build_calibration_intake_report(panel_csv, results_dir):
    """Build a calibration-intake report from a pilot panel CSV + lab results dir.

    The report contains:

        - panel summary (n candidates, score coverage);
        - lab results summary;
        - per-candidate join rows (predictions + actuals);
        - cohort triage metrics (gated by MIN_COHORT_SIZE);
        - orphan-lab-result rows (results with no matching candidate);
        - control-failure summary;
        - disclaimer.

    Aggregate triage metrics are intentionally NOT computed when
    ``len(matched) < MIN_COHORT_SIZE``. Below that threshold the cohort is
    flagged ``insufficient_data: True`` to prevent small-sample theater.
    """
    validate_lab_results_directory(results_dir)
    panel_rows = _load_panel_csv(panel_csv)
    results, invalid_lab_result_files = load_lab_results_dir_with_errors(results_dir)
    if invalid_lab_result_files:
        warnings.warn(
            f"Skipped {len(invalid_lab_result_files)} invalid lab result files:\n"
            + "\n".join(
                f"{item['file']}: {item['error']}"
                for item in invalid_lab_result_files
            ),
            stacklevel=2,
        )

    per_candidate_actuals = _aggregate_per_candidate(results)
    per_candidate = _per_candidate_rows(panel_rows, per_candidate_actuals)

    matched = [r for r in per_candidate if r["has_lab"] is not None]
    orphan_ids = sorted(set(per_candidate_actuals) - {r["candidate_id"] for r in panel_rows})

    control_failures = [
        {
            "result_id": r["result_id"],
            "candidate_id": r.get("candidate_id"),
            "assay_type": r.get("assay_type"),
            "positive_control_passed": r.get("positive_control_passed"),
            "negative_control_passed": r.get("negative_control_passed"),
        }
        for r in results
        if not (r.get("positive_control_passed") and r.get("negative_control_passed"))
    ]

    cohort_metrics = {
        "activity_vs_active_mic": _cohort_metric(
            matched,
            assay_type="MIC",
            predicate_lab="active_mic",
            prediction_score_key="activity",
            predicate_pred_direction="above",
            threshold=ACTIVITY_THRESHOLD,
        ),
        "rich_selectivity_vs_high_hemolysis": _cohort_metric(
            matched,
            assay_type="hemolysis_RBC",
            predicate_lab="high_hemolysis",
            prediction_score_key="rich_selectivity",
            # rich_selectivity above 0.5 = predicted NEGATIVE for high_hemolysis
            # (rich_selectivity measures "more selective = less hemolytic"),
            # so predicted_positive (high hemolysis) only when score < 0.5.
            predicate_pred_direction="below",
            threshold=0.5,
        ),
    }

    return {
        "panel_csv": str(panel_csv),
        "results_dir": str(results_dir),
        "n_panel_candidates": len(panel_rows),
        "n_lab_results": len(results),
        "n_invalid_lab_result_files": len(invalid_lab_result_files),
        "invalid_lab_result_files": invalid_lab_result_files,
        "input_validation_status": (
            "blocked_on_invalid_results"
            if invalid_lab_result_files
            else "input_validated"
        ),
        "n_matched_candidates": len(matched),
        "n_orphan_lab_results": len(orphan_ids),
        "orphan_candidate_ids": orphan_ids,
        "summary": summarise_lab_results(results),
        "per_candidate_outcomes": summarise_candidate_outcomes(results),
        "per_candidate_joined": per_candidate,
        "cohort_metrics": cohort_metrics,
        "control_failures": control_failures,
        "min_cohort_size": MIN_COHORT_SIZE,
        "activity_threshold": ACTIVITY_THRESHOLD,
        "mic_active_cutoff_ug_ml": MIC_ACTIVE_CUTOFF_UG_ML,
        "hemolysis_high_pct": HEMOLYSIS_HIGH_PCT,
        "report_disclaimer": _DISCLAIMER,
    }


def write_calibration_intake_json(report, out_path):
    """Write the machine-readable calibration intake JSON."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=False)


def write_calibration_intake_markdown(report, out_path):
    """Write a human-readable markdown calibration intake summary.

    Uses .get() for optional metric fields (e.g. ``prediction_score_key``)
    so that cohort metrics from different constructors do not crash the
    markdown writer with a KeyError.
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Calibration Intake Report",
        "",
        "> " + report["report_disclaimer"],
        "",
        "## Cohort Overview",
        "",
        f"- Panel candidates: **{report['n_panel_candidates']}**",
        f"- Lab results loaded: **{report['n_lab_results']}**",
        f"- Matched candidates: **{report['n_matched_candidates']}**",
        f"- Orphan lab results (no panel match): **{report['n_orphan_lab_results']}**",
        f"- Invalid lab result files: **{report.get('n_invalid_lab_result_files', 0)}**",
        f"- Minimum cohort size for aggregate metrics: **{report['min_cohort_size']}**",
        "",
        "## Aggregate Cohort Metrics (gated by minimum sample size)",
        "",
    ]
    invalid_files = report.get("invalid_lab_result_files", [])
    if invalid_files:
        lines += [
            "## Input Validation Blockers",
            "",
            "> The intake is blocked. Invalid result files were excluded from all metrics.",
            "",
            "| File | Error |",
            "|---|---|",
        ]
        lines.extend(f"| {item['file']} | {item['error']} |" for item in invalid_files)
        lines.append("")
    for key, metric in report["cohort_metrics"].items():
        lines.append(f"### {key}")
        lines.append("")
        lines.append(f"- Assay type: `{metric['assay_type']}`")
        lines.append(f"- Predicate: `{metric['predicate']}`")
        pred_key = metric.get("prediction_score_key", "unknown")
        lines.append(f"- Prediction score key: `{pred_key}`")
        lines.append(f"- n: **{metric['n']}** (min required: {metric['min_required']})")
        if metric["insufficient_data"]:
            lines.append(f"- **Status:** insufficient_data - {metric['disclaimer']}")
        else:
            lines.append(
                f"- TP={metric['tp']}, FP={metric['fp']}, "
                f"FN={metric['fn']}, TN={metric['tn']}"
            )
            lines.append(f"- Note: {metric['disclaimer']}")
        lines.append("")

    lines += [
        "## Per-Candidate Joined Rows",
        "",
        "| Candidate | Seed | Length | Ensemble | Activity | Has lab? |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in report["per_candidate_joined"]:
        has_lab = row["has_lab"] is not None
        ensemble = row.get("ensemble")
        activity = row.get("activity")
        ens_str = f"{ensemble:.2f}" if isinstance(ensemble, (int, float)) else "-"
        act_str = f"{activity:.2f}" if isinstance(activity, (int, float)) else "-"
        lines.append(
            f"| {row['candidate_id']} | {row['seed']} | {row['length']} "
            f"| {ens_str} | {act_str} | {'yes' if has_lab else 'no'} |"
        )

    lines += [
        "",
        "## Control Failures",
        "",
    ]
    if report["control_failures"]:
        lines.append("| Result | Candidate | Assay | Pos ctrl | Neg ctrl |")
        lines.append("|---|---|---|---|---|")
        for cf in report["control_failures"]:
            lines.append(
                f"| {cf['result_id']} | {cf['candidate_id']} | {cf['assay_type']} "
                f"| {cf['positive_control_passed']} | {cf['negative_control_passed']} |"
            )
    else:
        lines.append("_None._")

    lines += [
        "",
        "## Honest Limitations",
        "",
        "- All aggregate metrics are descriptive only. They do not validate the pipeline.",
        "- Cohort metrics do NOT control for selection bias from the pre-registered shortlist.",
        "- Below the minimum cohort size, no point estimate is reported. This prevents small-sample theater.",
        "- Recalibration requires a separate human-reviewed decision log (see docs/evidence/DECISION_RULES.md).",
        "- This report does NOT change scoring weights, ensemble composition, or selection rules.",
        "",
    ]
    with p.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
