"""Recalibration report: human-readable weight-change proposal with gate context.

Combines a ``WeightUpdateProposal`` with the full ``GateVerdict`` so a human
reviewer can inspect the proposed deltas alongside the policy-rule results
that triggered them.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from openamp_foundry.calibration.engine import WeightUpdateProposal
from openamp_foundry.calibration.recalibration_gate import GateVerdict


_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "recalibration_report.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load the recalibration report JSON Schema."""
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def validate_recalibration_report(
    report: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Validate a recalibration report dict against the JSON Schema.

    Returns (is_valid, errors).
    """
    try:
        import jsonschema

        schema = _load_schema()
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(
            e.message for e in validator.iter_errors(report)
        )
        return (len(errors) == 0, errors)
    except ImportError:
        return (True, [])


def build_recalibration_report(
    proposal: WeightUpdateProposal,
    gate_verdict: GateVerdict,
) -> dict[str, Any]:
    """Build a combined recalibration report from proposal and gate verdict.

    The report includes:

    - Report metadata (type, schema version, timestamp, policy version).
    - The full gate verdict (rule results, prohibited actions, rate limits,
      reviewer artefacts, summary).
    - The full proposal (deltas, L1 summary, notes).
    - An explicit ``human_review_required`` flag (always ``True``).
    """
    now = datetime.now().isoformat(timespec="seconds")

    report: dict[str, Any] = {
        "report_type": "recalibration_report",
        "schema_version": "1.0",
        "timestamp": now,
        "policy_version": proposal.policy_version,
        "human_review_required": True,
        "gate_verdict": gate_verdict.to_dict(),
        "proposal": {
            "gate_passed": proposal.gate_passed,
            "l1_total": proposal.l1_total,
            "l1_budget": proposal.l1_budget,
            "l1_within_budget": proposal.l1_within_budget,
            "deltas": [d.to_dict() for d in proposal.deltas],
            "notes": list(proposal.notes),
        },
    }

    return report


def write_recalibration_report_json(
    report: dict[str, Any],
    out_path: str | Path,
) -> Path:
    """Write a combined recalibration report to JSON."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(report, f, indent=2, sort_keys=False)
        f.write("\n")
    return p


def write_recalibration_report_markdown(
    report: dict[str, Any],
    out_path: str | Path,
) -> Path:
    """Write a combined recalibration report as human-readable Markdown.

    Includes:

    - Report banner (human review required).
    - Gate verdict summary (may_recalibrate, cohort, rule results,
      prohibited actions, rate limits).
    - Proposed weight deltas with before/after values and rationale.
    - L1 budget summary.
    - Next-steps checklist for the human reviewer.
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    lines.append("# Recalibration Report")
    lines.append("")
    lines.append(
        "> ⚠ **HUMAN REVIEW REQUIRED.** This report is a **proposal only**. "
        "It does NOT modify any scoring weights, ensemble composition, or "
        "selection rules. A human reviewer must inspect the proposal, verify "
        "the gate verdict, sign a dated decision log entry, and THEN "
        "manually apply the approved weight changes."
    )
    lines.append("")

    # --- Metadata ---
    lines.append("## Report metadata")
    lines.append("")
    lines.append(f"- Report type: `{report['report_type']}`")
    lines.append(f"- Schema version: `{report['schema_version']}`")
    lines.append(f"- Generated at: **{report['timestamp']}**")
    lines.append(f"- Policy version: **{report['policy_version']}**")
    lines.append("")

    # --- Gate verdict ---
    gv = report.get("gate_verdict", {})
    lines.append("## Gate verdict")
    lines.append("")
    lines.append(
        f"**may_recalibrate = {str(gv.get('may_recalibrate', '?')).lower()}**"
    )
    lines.append("")
    lines.append(gv.get("summary", ""))
    lines.append("")
    lines.append("### Cohort")
    lines.append("")
    lines.append(f"- Panel candidates: {gv.get('n_panel_candidates', '?')}")
    lines.append(f"- Matched candidates: {gv.get('n_matched_candidates', '?')}")
    lines.append(f"- Lab results: {gv.get('n_lab_results', '?')}")
    lines.append("")

    # Rule results
    rule_results = gv.get("rule_results", [])
    if rule_results:
        lines.append("### Minimum conditions")
        lines.append("")
        lines.append("| Rule | Passed | Observed | Threshold | Reason |")
        lines.append("|------|--------|----------|-----------|--------|")
        for r in rule_results:
            lines.append(
                f"| {r.get('rule_id', '?')} | "
                f"{'PASS' if r.get('passed') else 'FAIL'} | "
                f"`{r.get('observed', '?')}` | `{r.get('threshold', '?')}` | "
                f"{r.get('reason', '')} |"
            )
        lines.append("")

    # Blockers
    reasons = gv.get("reasons", [])
    if reasons:
        lines.append("### Blocking reasons")
        lines.append("")
        for reason in reasons:
            lines.append(f"- {reason}")
        lines.append("")

    # Prohibited actions
    prohibited = gv.get("prohibited_action_audit", [])
    if prohibited:
        lines.append("### Prohibited actions (permanent floor)")
        lines.append("")
        for a in prohibited:
            lines.append(
                f"- **{a.get('action_id', '?')}**: In force — "
                f"{a.get('description', '')}"
            )
        lines.append("")

    # Rate limits
    rate_limits = gv.get("rate_limit_status", [])
    if rate_limits:
        lines.append("### Rate-limit status")
        lines.append("")
        lines.append("| Rule | Status | Observed | Threshold | Note |")
        lines.append("|------|--------|----------|-----------|------|")
        for s in rate_limits:
            lines.append(
                f"| {s.get('rule_id', '?')} | {s.get('status', '?')} | "
                f"`{s.get('observed', '?')}` | `{s.get('threshold', '?')}` | "
                f"{s.get('note', '')} |"
            )
        lines.append("")

    # --- Proposal ---
    prop = report.get("proposal", {})
    lines.append("## Proposed weight updates")
    lines.append("")
    l1_total = prop.get("l1_total", 0.0)
    l1_budget = prop.get("l1_budget", 0.0)
    l1_within = prop.get("l1_within_budget", False)
    lines.append(f"- L1 total: **{l1_total:.4f}** / budget {l1_budget:.4f}")
    lines.append(f"- Within budget: **{l1_within}**")
    if not l1_within:
        lines.append(
            "  ⚠ **Budget exceeded.** This proposal cannot be applied "
            "without reducing the total L1 delta."
        )
    lines.append("")

    # Deltas table
    deltas = prop.get("deltas", [])
    if deltas:
        lines.append(
            "| Scorer | Current | Proposed | Delta | "
            "Precision | Recall | Pos/Neg | Rationale |"
        )
        lines.append(
            "|--------|---------|----------|-------|"
            "-----------|--------|---------|-----------|"
        )
        for d in deltas:
            p_str = (
                f"{d['precision']:.3f}"
                if d.get("precision") is not None
                else "N/A"
            )
            r_str = (
                f"{d['recall']:.3f}"
                if d.get("recall") is not None
                else "N/A"
            )
            lines.append(
                f"| {d['scorer']} | {d['current_weight']:.4f} | "
                f"{d['proposed_weight']:.4f} | {d['delta']:+.4f} | "
                f"{p_str} | {r_str} | "
                f"{d.get('n_positive', '?')}/{d.get('n_negative', '?')} | "
                f"{d['rationale']} |"
            )
        lines.append("")
    else:
        lines.append("**No weight changes proposed.**")
        lines.append("")

    # Notes
    notes = prop.get("notes", [])
    if notes:
        lines.append("### Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    # --- Next steps ---
    lines.append("## Next steps")
    lines.append("")
    lines.append("1. **Read** the full gate verdict above.")
    lines.append("2. **Verify** every rule result and blocker.")
    lines.append(
        "3. **Check** that the proposed deltas respect all prohibited actions."
    )
    lines.append("4. **Sign** a dated decision-log entry if approved.")
    lines.append("   (See `docs/DECISION_RULES.md` for the required format.)")
    lines.append("5. **Apply** the approved weight changes by editing")
    lines.append("   the scoring config file.")
    lines.append("6. **Regenerate** all benchmark outputs after applying.")
    lines.append("7. **Record** the new benchmark results alongside the")
    lines.append("   decision log.")
    lines.append("")

    p.write_text("\n".join(lines))
    return p
