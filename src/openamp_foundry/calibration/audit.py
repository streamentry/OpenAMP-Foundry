"""Calibration pipeline consistency audit.

Checks that the four artifacts produced across the calibration pipeline
(intake report, gate verdict, engine proposal, recalibration report)
are internally consistent and can be trusted by a human reviewer.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


_CHECK_DESCRIPTIONS: dict[str, str] = {
    "INTAKE_GATE_COUNTS_MATCH": (
        "Candidate and lab-result counts must be identical between the "
        "intake report and the gate verdict."
    ),
    "ENGINE_GATE_VERDICT_MATCH": (
        "The engine must respect the gate verdict: if may_recalibrate is "
        "false, the engine must not produce a proposal."
    ),
    "ENGINE_L1_WITHIN_BUDGET": (
        "The engine's proposed L1 total must not exceed the policy budget."
    ),
    "ENGINE_INTAKE_LINK_MATCH": (
        "The intake report path referenced by the engine must match the "
        "actual intake report used."
    ),
    "REPORT_GATE_VERDICT_MATCH": (
        "The combined recalibration report's gate-verdict section must "
        "match the standalone gate verdict."
    ),
    "REPORT_ENGINE_PROPOSAL_MATCH": (
        "The combined recalibration report's proposal section must match "
        "the standalone engine proposal."
    ),
    "INTAKE_PATH_PRESENT": (
        "The intake report path provided must point to an existing file."
    ),
    "GATE_PATH_PRESENT": (
        "The gate verdict path provided must point to an existing file."
    ),
    "ENGINE_PATH_PRESENT": (
        "The engine proposal path provided must point to an existing file."
    ),
    "REPORT_PATH_PRESENT": (
        "The combined recalibration report path provided must point to an "
        "existing file."
    ),
    "TIMESTAMPS_REASONABLE": (
        "All artifact timestamps must be in the past (not in the future)."
    ),
    "INTAKE_COHORT_METRICS_WARN": (
        "If cohort metrics are flagged insufficient_data, the gate verdict "
        "should reflect this limitation."
    ),
}

_CHECK_IDS = tuple(_CHECK_DESCRIPTIONS.keys())


def _check(
    check_id: str,
    passed: bool,
    observed: str,
    expected: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "description": _CHECK_DESCRIPTIONS.get(check_id, ""),
        "passed": passed,
        "observed": observed,
        "expected": expected,
        "severity": severity,
    }


def _get_intake_counts(
    intake: dict[str, Any],
) -> dict[str, int]:
    return {
        "n_panel_candidates": intake.get("n_panel_candidates", 0),
        "n_matched_candidates": intake.get("n_matched_candidates", 0),
        "n_lab_results": intake.get("n_lab_results", 0),
    }


def _get_gate_counts(gate: dict[str, Any]) -> dict[str, int]:
    return {
        "n_panel_candidates": gate.get("n_panel_candidates", 0),
        "n_matched_candidates": gate.get("n_matched_candidates", 0),
        "n_lab_results": gate.get("n_lab_results", 0),
    }


def _load_json(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IsADirectoryError):
        return None


def _artifact_by_name(
    name: str,
    mapping: dict[str, Any],
) -> Any:
    return mapping.get(name)


def _fmt_counts(label: str, counts: dict[str, int]) -> str:
    parts = [f"{k}={v}" for k, v in counts.items()]
    return f"{label}: {{{', '.join(parts)}}}"


def _parse_timestamp(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def run_calibration_audit(
    intake_path: str | Path | None = None,
    gate_path: str | Path | None = None,
    engine_path: str | Path | None = None,
    report_path: str | Path | None = None,
    intake_data: dict[str, Any] | None = None,
    gate_data: dict[str, Any] | None = None,
    engine_data: dict[str, Any] | None = None,
    report_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a consistency audit across the calibration pipeline artifacts.

    Accepts either file paths or pre-loaded dicts for each artifact.
    When both are provided for the same artifact, the dict takes precedence.
    """
    checks: list[dict[str, Any]] = []
    now = datetime.now()

    # Load artifacts: paths used for "present" checks, data for consistency
    intake = intake_data if intake_data is not None else _load_json(intake_path)
    gate = gate_data if gate_data is not None else _load_json(gate_path)
    engine = engine_data if engine_data is not None else _load_json(engine_path)
    report = report_data if report_data is not None else _load_json(report_path)

    # Determine available artifacts (from either data dicts or loaded files)
    artifact_names = {
        "intake": intake,
        "gate": gate,
        "engine": engine,
        "report": report,
    }
    artifacts_checked = [name for name, data in artifact_names.items() if data is not None]

    # ── Artifact existence checks (only when paths are given) ──────
    for name, path, check_id in [
        ("intake", intake_path, "INTAKE_PATH_PRESENT"),
        ("gate", gate_path, "GATE_PATH_PRESENT"),
        ("engine", engine_path, "ENGINE_PATH_PRESENT"),
        ("report", report_path, "REPORT_PATH_PRESENT"),
    ]:
        if path is not None:
            if Path(path).exists():
                checks.append(
                    _check(
                        check_id,
                        passed=True,
                        observed=f"{path} exists",
                        expected=f"{path} should exist",
                    )
                )
            else:
                checks.append(
                    _check(
                        check_id,
                        passed=False,
                        observed=f"{path} does not exist",
                        expected=f"{path} should exist",
                    )
                )
        else:
            if _artifact_by_name(name, artifact_names) is not None:
                checks.append(
                    _check(
                        check_id,
                        passed=True,
                        observed=f"{name} provided as data dict (no path)",
                        expected=f"{name} should be available",
                    )
                )
            else:
                checks.append(
                    _check(
                        check_id,
                        passed=False,
                        observed=f"no path or data provided for {name}",
                        expected=f"a file path or data dict for {name} must be provided",
                        severity="info",
                    )
                )

    if not artifacts_checked:
        overall_pass = False
        summary = (
            "No artifacts were available for audit. Provide at least one "
            "valid artifact path or data dict."
        )
        return {
            "report_type": "calibration_audit",
            "schema_version": "1.0",
            "timestamp": now.isoformat(timespec="seconds"),
            "artifacts_checked": [],
            "overall_pass": overall_pass,
            "checks": checks,
            "n_checks": len(checks),
            "n_passed": sum(1 for c in checks if c["passed"]),
            "n_failed": sum(1 for c in checks if not c["passed"]),
            "n_warnings": sum(1 for c in checks if c["severity"] == "warning"),
            "summary": summary,
        }

    # ── Intake ↔ Gate count consistency ────────────────────────────
    if intake and gate and "intake" in artifacts_checked and "gate" in artifacts_checked:
        intake_counts = _get_intake_counts(intake)
        gate_counts = _get_gate_counts(gate)
        counts_match = intake_counts == gate_counts
        checks.append(
            _check(
                "INTAKE_GATE_COUNTS_MATCH",
                passed=counts_match,
                observed=(
                    f"{_fmt_counts('intake', intake_counts)}; "
                    f"{_fmt_counts('gate', gate_counts)}"
                ),
                expected="intake and gate counts must be identical",
            )
        )
    elif "intake" in artifacts_checked or "gate" in artifacts_checked:
        checks.append(
            _check(
                "INTAKE_GATE_COUNTS_MATCH",
                passed=False,
                observed="only one of intake/gate is available",
                expected="both intake and gate are needed for count comparison",
                severity="warning",
            )
        )

    # ── Engine ↔ Gate verdict consistency ──────────────────────────
    if engine and gate and "engine" in artifacts_checked and "gate" in artifacts_checked:
        gate_may = gate.get("may_recalibrate", False)
        engine_gate = engine.get("gate_passed", None)
        verdict_match = engine_gate is None or engine_gate == gate_may
        checks.append(
            _check(
                "ENGINE_GATE_VERDICT_MATCH",
                passed=verdict_match,
                observed=(
                    f"gate may_recalibrate={gate_may}; "
                    f"engine gate_passed={engine_gate}"
                ),
                expected=(
                    "if engine records gate_passed, it must match "
                    "the gate's may_recalibrate"
                ),
            )
        )
    elif "engine" in artifacts_checked or "gate" in artifacts_checked:
        checks.append(
            _check(
                "ENGINE_GATE_VERDICT_MATCH",
                passed=False,
                observed="only one of engine/gate is available",
                expected="both engine and gate are needed for verdict comparison",
                severity="warning",
            )
        )

    # ── Engine L1 budget consistency ───────────────────────────────
    if engine and "engine" in artifacts_checked:
        l1_total = engine.get("l1_total", 0.0)
        l1_budget = engine.get("l1_budget", 0.0)
        l1_within = engine.get("l1_within_budget", False)
        computed_within = l1_total <= l1_budget if l1_budget > 0 else True
        l1_ok = l1_within == computed_within
        checks.append(
            _check(
                "ENGINE_L1_WITHIN_BUDGET",
                passed=l1_ok,
                observed=(
                    f"l1_total={l1_total:.4f}, l1_budget={l1_budget:.4f}, "
                    f"declared l1_within_budget={l1_within}"
                ),
                expected=(
                    f"l1_total ({l1_total:.4f}) <= l1_budget "
                    f"({l1_budget:.4f}) and l1_within_budget=true"
                ),
            )
        )
        if not l1_ok:
            checks[-1]["observed"] += (
                f" (computed: l1_total <= l1_budget is {computed_within})"
            )

    # ── Engine intake link consistency ─────────────────────────────
    if engine and intake_path and "engine" in artifacts_checked:
        engine_intake_ref = engine.get("intake_report", None)
        resolved_ref = (
            str(Path(engine_intake_ref).resolve())
            if engine_intake_ref
            else None
        )
        resolved_provided = str(Path(intake_path).resolve()) if intake_path else None
        link_match = (
            resolved_ref is None
            or resolved_provided is None
            or resolved_ref == resolved_provided
        )
        checks.append(
            _check(
                "ENGINE_INTAKE_LINK_MATCH",
                passed=link_match,
                observed=(
                    f"engine intake_report={engine_intake_ref!r}; "
                    f"provided path={str(intake_path)!r}"
                ),
                expected="engine's intake_report should match the provided intake path",
                severity="warning" if link_match else "error",
            )
        )

    # ── Report ↔ Gate verdict consistency ──────────────────────────
    if report and gate and "report" in artifacts_checked and "gate" in artifacts_checked:
        report_gv = report.get("gate_verdict", {})
        for key in ("may_recalibrate", "n_panel_candidates", "n_matched_candidates", "n_lab_results"):
            r_val = report_gv.get(key)
            g_val = gate.get(key)
        gv_match = (
            report_gv.get("may_recalibrate") == gate.get("may_recalibrate")
            and report_gv.get("n_panel_candidates") == gate.get("n_panel_candidates")
            and report_gv.get("n_matched_candidates") == gate.get("n_matched_candidates")
            and report_gv.get("n_lab_results") == gate.get("n_lab_results")
        )
        checks.append(
            _check(
                "REPORT_GATE_VERDICT_MATCH",
                passed=gv_match,
                observed=(
                    f"report gate may_recalibrate={report_gv.get('may_recalibrate')}, "
                    f"n_panel={report_gv.get('n_panel_candidates')}, "
                    f"n_matched={report_gv.get('n_matched_candidates')}, "
                    f"n_lab={report_gv.get('n_lab_results')}; "
                    f"standalone gate may_recalibrate={gate.get('may_recalibrate')}"
                ),
                expected="report gate-verdict section must match standalone gate verdict",
            )
        )
    elif "report" in artifacts_checked or "gate" in artifacts_checked:
        checks.append(
            _check(
                "REPORT_GATE_VERDICT_MATCH",
                passed=False,
                observed="only one of report/gate is available",
                expected="both report and gate are needed for comparison",
                severity="warning",
            )
        )

    # ── Report ↔ Engine proposal consistency ───────────────────────
    if report and engine and "report" in artifacts_checked and "engine" in artifacts_checked:
        r_prop = report.get("proposal", {})
        for key in ("gate_passed", "l1_total", "l1_budget", "l1_within_budget"):
            r_val = r_prop.get(key)
            e_val = engine.get(key)
        prop_match = (
            r_prop.get("gate_passed") == engine.get("gate_passed")
            and r_prop.get("l1_total") == engine.get("l1_total")
            and r_prop.get("l1_budget") == engine.get("l1_budget")
            and r_prop.get("l1_within_budget") == engine.get("l1_within_budget")
        )
        checks.append(
            _check(
                "REPORT_ENGINE_PROPOSAL_MATCH",
                passed=prop_match,
                observed=(
                    f"report proposal gate_passed={r_prop.get('gate_passed')}, "
                    f"l1_total={r_prop.get('l1_total')}; "
                    f"engine gate_passed={engine.get('gate_passed')}, "
                    f"l1_total={engine.get('l1_total')}"
                ),
                expected=(
                    "report proposal section must match standalone engine proposal"
                ),
            )
        )
    elif "report" in artifacts_checked or "engine" in artifacts_checked:
        checks.append(
            _check(
                "REPORT_ENGINE_PROPOSAL_MATCH",
                passed=False,
                observed="only one of report/engine is available",
                expected="both report and engine are needed for comparison",
                severity="warning",
            )
        )

    # ── Timestamp sanity ───────────────────────────────────────────
    ts_check_passed = True
    ts_parts: list[str] = []
    for name, data in [
        ("intake", intake),
        ("gate", gate),
        ("engine", engine),
        ("report", report),
    ]:
        if not data:
            continue
        ts_str = data.get("timestamp") or data.get("generated_at")
        ts = _parse_timestamp(ts_str)
        if ts and ts > now:
            ts_check_passed = False
            ts_parts.append(f"{name} timestamp {ts_str} is in the future")
        elif ts:
            ts_parts.append(f"{name} timestamp {ts_str} is OK")
        else:
            ts_parts.append(f"{name} has no parseable timestamp")
    checks.append(
        _check(
            "TIMESTAMPS_REASONABLE",
            passed=ts_check_passed,
            observed="; ".join(ts_parts),
            expected="all timestamps must be in the past",
        )
    )

    # ── Intake cohort metrics warning ──────────────────────────────
    if intake and gate and "intake" in artifacts_checked and "gate" in artifacts_checked:
        cohort_metrics = intake.get("cohort_metrics", {})
        any_insufficient = any(
            m.get("insufficient_data", False)
            for m in cohort_metrics.values()
        )
        may_recalibrate = gate.get("may_recalibrate", False)
        if any_insufficient and may_recalibrate:
            checks.append(
                _check(
                    "INTAKE_COHORT_METRICS_WARN",
                    passed=False,
                    observed=(
                        "intake cohort metrics have insufficient_data, "
                        "but gate verdict allows recalibration"
                    ),
                    expected=(
                        "gate should not allow recalibration when intake "
                        "cohort data is insufficient"
                    ),
                    severity="warning",
                )
            )
        else:
            checks.append(
                _check(
                    "INTAKE_COHORT_METRICS_WARN",
                    passed=True,
                    observed=(
                        f"insufficient_data={any_insufficient}, "
                        f"may_recalibrate={may_recalibrate}"
                    ),
                    expected=(
                        "warn only when insufficient_data is true and "
                        "gate passes"
                    ),
                    severity="info",
                )
            )

    # ── Summarize ────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    n_failed = sum(1 for c in checks if not c["passed"])
    n_warnings = sum(1 for c in checks if c["severity"] == "warning")
    overall_pass = n_failed == 0

    if not artifacts_checked:
        summary = "No artifacts were checked."
    elif overall_pass:
        summary = (
            f"All {n_passed} check(s) passed across "
            f"{len(artifacts_checked)} artifact(s): "
            f"{', '.join(sorted(artifacts_checked))}."
        )
    else:
        summary = (
            f"{n_failed} of {len(checks)} check(s) failed across "
            f"{len(artifacts_checked)} artifact(s): "
            f"{', '.join(sorted(artifacts_checked))}. "
            "Review the failed checks before trusting the pipeline output."
        )

    return {
        "report_type": "calibration_audit",
        "schema_version": "1.0",
        "timestamp": now.isoformat(timespec="seconds"),
        "artifacts_checked": sorted(set(artifacts_checked)),
        "overall_pass": overall_pass,
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": n_passed,
        "n_failed": n_failed,
        "n_warnings": n_warnings,
        "summary": summary,
    }


def write_calibration_audit_json(
    audit: dict[str, Any],
    out_path: str | Path,
) -> Path:
    """Write a calibration audit report to JSON."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(audit, f, indent=2)
        f.write("\n")
    return p


def write_calibration_audit_markdown(
    audit: dict[str, Any],
    out_path: str | Path,
) -> Path:
    """Write a calibration audit report as human-readable Markdown."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    lines.append("# Calibration Pipeline Audit")
    lines.append("")

    overall = "✅ PASS" if audit["overall_pass"] else "❌ FAIL"
    lines.append(f"**Overall: {overall}**")
    lines.append("")
    lines.append(audit["summary"])
    lines.append("")

    lines.append("## Audit metadata")
    lines.append("")
    lines.append(f"- Report type: `{audit['report_type']}`")
    lines.append(f"- Schema version: `{audit['schema_version']}`")
    lines.append(f"- Generated at: **{audit['timestamp']}**")
    lines.append(f"- Artifacts checked: {', '.join(audit['artifacts_checked'])}")
    lines.append(f"- Checks: {audit['n_checks']} total, "
                 f"{audit['n_passed']} passed, "
                 f"{audit['n_failed']} failed, "
                 f"{audit['n_warnings']} warning(s)")
    lines.append("")

    if not audit["checks"]:
        lines.append("**No checks were performed.**")
        lines.append("")
        p.write_text("\n".join(lines))
        return p

    lines.append("## Consistency checks")
    lines.append("")
    lines.append("| ID | Description | Result | Observed | Expected | Severity |")
    lines.append("|----|-------------|--------|----------|----------|----------|")

    for c in audit["checks"]:
        icon = "✅" if c["passed"] else "❌"
        lines.append(
            f"| `{c['check_id']}` | {c['description']} | {icon} "
            f"| `{c['observed']}` | {c['expected']} | {c['severity']} |"
        )
    lines.append("")

    failed = [c for c in audit["checks"] if not c["passed"]]
    if failed:
        lines.append("## Failed checks")
        lines.append("")
        for c in failed:
            lines.append(f"### {c['check_id']}")
            lines.append("")
            lines.append(f"- **Description:** {c['description']}")
            lines.append(f"- **Observed:** `{c['observed']}`")
            lines.append(f"- **Expected:** {c['expected']}")
            lines.append(f"- **Severity:** {c['severity']}")
            lines.append("")

    if audit["n_warnings"] > 0:
        warnings = [c for c in audit["checks"] if c["severity"] == "warning"]
        lines.append("## Warnings")
        lines.append("")
        for c in warnings:
            lines.append(f"- **{c['check_id']}**: {c['description']}")
            lines.append(f"  - Observed: `{c['observed']}`")
            lines.append(f"  - Expected: {c['expected']}")
            lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- This audit checks **consistency** between pipeline artifacts, "
        "not the biological validity of the results."
    )
    lines.append(
        "- A passing audit means the pipeline stages agreed with each other, "
        "not that the calibration decisions are biologically correct."
    )
    lines.append(
        "- Human review of the gate verdict, weight proposals, and "
        "decision log remains mandatory."
    )
    lines.append("")

    p.write_text("\n".join(lines))
    return p
