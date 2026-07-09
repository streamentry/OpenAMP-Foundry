"""Generate a negative-result dashboard from a collection of negative-result entries.

Reads a JSON file containing negative-result entries (see
examples/negative_result_dashboard_example.json) and produces a structured
dashboard with summary statistics, score distributions, per-category analysis,
and pipeline insights. Outputs JSON and/or Markdown.

Usage:
    python scripts/negative_result_dashboard.py \\
        --input examples/negative_result_dashboard_example.json \\
        --out-json outputs/negative_result_dashboard.json \\
        --out-md outputs/negative_result_dashboard.md

Exit codes:
    0  Success
    2  Input error (missing file, invalid JSON, wrong structure)
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_ENTRY_FIELDS = {"entry_id", "candidate_id", "reason_category"}
SCORE_FIELDS = ["score_activity", "score_safety", "score_novelty", "score_ensemble"]
SHORT_SCORE_NAMES = {"score_activity": "activity", "score_safety": "safety", "score_novelty": "novelty", "score_ensemble": "ensemble"}


def _stats(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "count": 0}
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return {
        "mean": round(mean, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "std": round(math.sqrt(variance), 4),
        "count": n,
    }


def _count_by(entries: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entries:
        val = e.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items()))


def build_dashboard(entries: list[dict], source_file: str = "") -> dict:
    total = len(entries)

    by_category = _count_by(entries, "reason_category")
    by_pipeline_version = _count_by(entries, "pipeline_version")

    score_values: dict[str, list[float]] = {name: [] for name in SCORE_FIELDS}
    for e in entries:
        for field in SCORE_FIELDS:
            val = e.get(field)
            if isinstance(val, (int, float)):
                score_values[field].append(float(val))

    scores_distribution = {}
    for field, vals in score_values.items():
        short = SHORT_SCORE_NAMES.get(field, field)
        scores_distribution[short] = _stats(vals)

    category_scores: dict[str, dict[str, list[float]]] = {}
    for e in entries:
        cat = e.get("reason_category", "unknown")
        if cat not in category_scores:
            category_scores[cat] = {name: [] for name in SCORE_FIELDS}
        for field in SCORE_FIELDS:
            val = e.get(field)
            if isinstance(val, (int, float)):
                category_scores[cat][field].append(float(val))

    category_score_summary = {}
    for cat, fields in category_scores.items():
        category_score_summary[cat] = {}
        for field, vals in fields.items():
            short = SHORT_SCORE_NAMES.get(field, field)
            category_score_summary[cat][short] = _stats(vals)

    if by_category:
        most_common_cat = max(by_category, key=by_category.get)
        most_common_count = by_category[most_common_cat]
    else:
        most_common_cat = "none"
        most_common_count = 0

    cat_mean_activity = {}
    cat_mean_safety = {}
    for cat, entry_stats in category_score_summary.items():
        if "activity" in entry_stats:
            cat_mean_activity[cat] = entry_stats["activity"]["mean"]
        if "safety" in entry_stats:
            cat_mean_safety[cat] = entry_stats["safety"]["mean"]

    highest_activity_cat = max(cat_mean_activity, key=cat_mean_activity.get) if cat_mean_activity else "none"
    lowest_safety_cat = min(cat_mean_safety, key=cat_mean_safety.get) if cat_mean_safety else "none"

    recalibration_count = sum(
        1 for e in entries if e.get("recalibration_used") == "yes"
    )

    return {
        "dashboard_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pipeline_version": "v0.5.79",
            "source_file": source_file,
            "total_entries": total,
            "pipeline_version_count": len(by_pipeline_version),
        },
        "summary": {
            "total_entries": total,
            "by_category": by_category,
            "by_pipeline_version": by_pipeline_version,
        },
        "scores_distribution": scores_distribution,
        "category_score_summary": category_score_summary,
        "insights": {
            "total_failures_analyzed": total,
            "most_common_failure_category": most_common_cat,
            "most_common_failure_count": most_common_count,
            "category_with_highest_avg_activity": highest_activity_cat,
            "category_with_lowest_avg_safety": lowest_safety_cat,
            "recalibration_opportunities": recalibration_count,
            "note": (
                "Dashboard insights are computational summaries of pipeline "
                "failure records. They are not biological proof. A high-scoring "
                "failure category does not mean the pipeline is failing correctly "
                "or incorrectly — it means that category generates more entries. "
                "Score distributions reflect pipeline-predicted scores, not "
                "measured activity or safety."
            ),
        },
        "_caveat": (
            "This dashboard is informational only. It summarises the structure "
            "and distribution of negative-result entries in the archive. "
            "A category with many entries may reflect pipeline prioritisation "
            "choices, not biological failure rate. Score distributions are "
            "computational predictions and must not be treated as measured "
            "values. This dashboard does not determine whether rejected "
            "candidates would have been biologically active or safe. "
            "All conclusions about candidate quality require qualified "
            "human review and wet-lab validation."
        ),
    }


def generate_markdown(dashboard: dict) -> str:
    lines: list[str] = []
    lines.append("# Negative-Result Dashboard\n")
    meta = dashboard.get("dashboard_metadata", {})
    lines.append(f"**Generated:** {meta.get('generated_at', '?')}  ")
    lines.append(f"**Pipeline version:** {meta.get('pipeline_version', '?')}  ")
    lines.append(f"**Total entries analyzed:** {meta.get('total_entries', 0)}\n")

    summary = dashboard.get("summary", {})
    total = summary.get("total_entries", 0)
    lines.append("## Summary\n")
    lines.append(f"**Total negative-result entries:** {total}\n")

    by_category = summary.get("by_category", {})
    if by_category:
        lines.append("### By Failure Category\n")
        lines.append("| Category | Count | Percentage |")
        lines.append("|----------|-------|------------|")
        for cat, count in by_category.items():
            pct = f"{100 * count / total:.1f}%" if total > 0 else "0%"
            lines.append(f"| {cat} | {count} | {pct} |")
        lines.append("")

    by_pv = summary.get("by_pipeline_version", {})
    if by_pv:
        lines.append("### By Pipeline Version\n")
        lines.append("| Pipeline Version | Count |")
        lines.append("|------------------|-------|")
        for pv, count in by_pv.items():
            lines.append(f"| {pv} | {count} |")
        lines.append("")

    sd = dashboard.get("scores_distribution", {})
    if sd:
        lines.append("## Score Distribution (all entries)\n")
        lines.append("| Score | Mean | Min | Max | Std | Count |")
        lines.append("|-------|------|-----|-----|-----|-------|")
        for score_name in ["activity", "safety", "novelty", "ensemble"]:
            s = sd.get(score_name, {})
            lines.append(
                f"| {score_name} | {s.get('mean', '?'):} | "
                f"{s.get('min', '?'):} | {s.get('max', '?'):} | "
                f"{s.get('std', '?'):} | {s.get('count', 0)} |"
            )
        lines.append("")

    css = dashboard.get("category_score_summary", {})
    if css:
        lines.append("## Per-Category Score Analysis\n")
        for cat, scores in css.items():
            lines.append(f"### {cat}\n")
            lines.append("| Score | Mean | Min | Max | Std | Count |")
            lines.append("|-------|------|-----|-----|-----|-------|")
            for score_name in ["activity", "safety", "novelty", "ensemble"]:
                s = scores.get(score_name, {})
                if s.get("count", 0) > 0:
                    lines.append(
                        f"| {score_name} | {s.get('mean', '?'):} | "
                        f"{s.get('min', '?'):} | {s.get('max', '?'):} | "
                        f"{s.get('std', '?'):} | {s.get('count', 0)} |"
                    )
            lines.append("")

    insights = dashboard.get("insights", {})
    if insights:
        lines.append("## Insights\n")
        lines.append(
            f"- **Most common failure category:** "
            f"{insights.get('most_common_failure_category', '?')} "
            f"({insights.get('most_common_failure_count', 0)} entries)"
        )
        lines.append(
            f"- **Category with highest avg activity score:** "
            f"{insights.get('category_with_highest_avg_activity', '?')}"
        )
        lines.append(
            f"- **Category with lowest avg safety score:** "
            f"{insights.get('category_with_lowest_avg_safety', '?')}"
        )
        lines.append(
            f"- **Recalibration opportunities:** "
            f"{insights.get('recalibration_opportunities', 0)} "
            f"entries contributed to recalibration"
        )
        lines.append(
            f"- **Note:** {insights.get('note', '')}"
        )

    lines.append(f"\n## Caveat\n\n{dashboard.get('_caveat', '')}\n")
    return "\n".join(lines)


def load_entries(input_path: str | Path) -> list[dict]:
    path = Path(input_path)
    if not path.exists():
        print(f"Error: Input not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(2)

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("entries", data.get("candidates", []))
        if not entries and all(k in REQUIRED_ENTRY_FIELDS for k in data if k != "schema"):
            entries = [data]
    else:
        print("Error: Input must be a JSON array or object with an 'entries' key", file=sys.stderr)
        sys.exit(2)

    if not isinstance(entries, list) or not entries:
        print("Error: No entries found in input", file=sys.stderr)
        sys.exit(2)

    for i, entry in enumerate(entries):
        missing = REQUIRED_ENTRY_FIELDS - set(entry.keys())
        if missing:
            print(
                f"Error: Entry {i} (candidate: {entry.get('candidate_id', '?')}) "
                f"missing required fields: {missing}",
                file=sys.stderr,
            )
            sys.exit(2)

    return entries


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a negative-result dashboard from a collection of entries."
    )
    parser.add_argument("--input", required=True, help="Path to negative-result entries JSON file")
    parser.add_argument("--out-json", default=None, help="Output JSON dashboard path")
    parser.add_argument("--out-md", default=None, help="Output Markdown dashboard path")

    args = parser.parse_args()

    entries = load_entries(args.input)

    dashboard = build_dashboard(entries, source_file=str(args.input))

    print(json.dumps(dashboard, indent=2))

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(dashboard, indent=2) + "\n")
        print(f"\nJSON dashboard written to: {args.out_json}")

    if args.out_md:
        md = generate_markdown(dashboard)
        Path(args.out_md).write_text(md + "\n")
        print(f"Markdown dashboard written to: {args.out_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
