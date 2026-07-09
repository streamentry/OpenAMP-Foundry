"""Calibration overfit warning — flags when a cohort is too small
relative to model parameters to support reliable learning.

This is a dry-lab computational check only. It does not measure
biological activity, safety, or real-world performance.
"""

from __future__ import annotations

import json
from pathlib import Path


def check_cohort_overfit_risk(
    cohort_size: int,
    model_params: int,
    n_features: int,
    min_recommended: int = 30,
) -> dict:
    """Assess overfit risk for a single cohort.

    Parameters
    ----------
    cohort_size : int
        Number of samples in the calibration cohort.
    model_params : int
        Number of trainable parameters in the model.
    n_features : int
        Number of input features.
    min_recommended : int
        Minimum cohort size considered sufficient (default 30).

    Returns
    -------
    dict with keys: cohort_size, model_params, n_features, ratio,
    warning_level, message, recommendation, dry_lab_only.
    """
    ratio = cohort_size / max(model_params, 1)

    if cohort_size < 10:
        warning_level = "critical"
        message = (
            f"Cohort size {cohort_size} is critically small — "
            f"any apparent signal is likely noise."
        )
        recommendation = (
            "Do not use this cohort for calibration. "
            "Gather at least 10 samples before attempting any weight update."
        )
    elif cohort_size < min_recommended and ratio < 3.0:
        warning_level = "warning"
        message = (
            f"Cohort size {cohort_size} is below the recommended minimum "
            f"{min_recommended} and the ratio of samples to parameters "
            f"({ratio:.2f}) is below 3.0. Risk of overfitting is high."
        )
        recommendation = (
            "Consider pooling cohorts or deferring calibration "
            "until more data are available."
        )
    elif cohort_size < min_recommended or ratio < 5.0:
        warning_level = "caution"
        message = (
            f"Cohort size {cohort_size} or sample-to-parameter ratio "
            f"({ratio:.2f}) suggests elevated overfit risk."
        )
        recommendation = (
            "Proceed with caution. Monitor for score degradation "
            "on held-out data after calibration."
        )
    else:
        warning_level = "none"
        message = (
            f"Cohort size {cohort_size} and ratio {ratio:.2f} "
            f"are adequate for calibration."
        )
        recommendation = "No special action required."

    return {
        "cohort_size": cohort_size,
        "model_params": model_params,
        "n_features": n_features,
        "ratio": round(ratio, 4),
        "warning_level": warning_level,
        "message": message,
        "recommendation": recommendation,
        "dry_lab_only": True,
    }


def run_overfit_check(
    cohort_sizes: list[int],
    model_params: int,
    n_features: int,
    min_recommended: int = 30,
) -> dict:
    """Run overfit risk check across multiple cohorts.

    Parameters
    ----------
    cohort_sizes : list of int
        One cohort size per dataset fold, class, or replicate.
    model_params : int
        Number of trainable parameters in the model.
    n_features : int
        Number of input features.
    min_recommended : int
        Minimum cohort size considered sufficient (default 30).

    Returns
    -------
    dict with keys: per_cohort, worst_level, any_critical,
    any_warning, recommendation, dry_lab_only.
    """
    if not cohort_sizes:
        return {
            "per_cohort": [],
            "worst_level": "none",
            "any_critical": False,
            "any_warning": False,
            "recommendation": "No cohorts provided. Nothing to check.",
            "dry_lab_only": True,
        }

    results = [
        check_cohort_overfit_risk(cs, model_params, n_features, min_recommended)
        for cs in cohort_sizes
    ]

    severity = {"none": 0, "caution": 1, "warning": 2, "critical": 3}
    worst = max(results, key=lambda r: severity[r["warning_level"]])
    worst_level = worst["warning_level"]
    any_critical = any(r["warning_level"] == "critical" for r in results)
    any_warning = any(r["warning_level"] in ("warning", "critical") for r in results)

    if worst_level == "critical":
        rec = (
            "Critical overfit risk detected in one or more cohorts. "
            "Do not proceed with calibration until cohort sizes are increased."
        )
    elif worst_level == "warning":
        rec = (
            "Warning-level overfit risk detected. "
            "Strongly consider pooling cohorts or deferring calibration."
        )
    elif worst_level == "caution":
        rec = (
            "Caution-level overfit risk detected. "
            "Proceed with monitoring, but be aware of elevated false-learning risk."
        )
    else:
        rec = "No overfit risk detected across all cohorts."

    return {
        "per_cohort": results,
        "worst_level": worst_level,
        "any_critical": any_critical,
        "any_warning": any_warning,
        "recommendation": rec,
        "dry_lab_only": True,
    }


def write_overfit_check_json(report: dict, path: str | Path) -> None:
    """Write the overfit check report to a JSON file."""
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def write_overfit_check_markdown(report: dict, path: str | Path) -> None:
    """Write the overfit check report to a Markdown file."""
    lines = [
        "# Calibration Overfit Risk Report",
        "",
        "> **Dry-lab only.** This report is a computational check and does not",
        "> measure biological activity, safety, or real-world performance.",
        "",
        "## Summary",
        "",
        f"| Key | Value |",
        f"|-----|-------|",
        f"| Worst level | {report['worst_level']} |",
        f"| Any critical | {report['any_critical']} |",
        f"| Any warning | {report['any_warning']} |",
    ]
    if report.get("recommendation"):
        lines.append(f"| Recommendation | {report['recommendation']} |")
    lines.append(f"| Dry-lab only | {report['dry_lab_only']} |")
    lines.extend([
        "",
        "## Per-Cohort Details",
        "",
        "| Cohort | Size | Params | Features | Ratio | Level | Message |",
        "|--------|------|--------|----------|-------|-------|---------|",
    ])
    for i, c in enumerate(report["per_cohort"]):
        lines.append(
            f"| {i} | {c['cohort_size']} | {c['model_params']} | "
            f"{c['n_features']} | {c['ratio']} | {c['warning_level']} | "
            f"{c['message']} |"
        )

    lines.extend([
        "",
        "## Caveats",
        "",
        "- This check evaluates **statistical overfit risk** only.",
        "- A passing check does not confirm biological validity.",
        "- Small cohorts can produce spurious correlations that appear "
        "significant in dry-lab benchmarks.",
        "- All calibration decisions require qualified human review.",
    ])
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
