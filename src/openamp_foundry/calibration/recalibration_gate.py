"""Recalibration gate: evaluate a calibration-intake report against a policy.

This module answers the binary question:

    "May recalibration proceed from this intake report?"

It does NOT trigger any weight update, scoring change, or selection
rule modification. It only emits a ``GateVerdict`` that downstream
code (or a human reviewer) must inspect before any recalibration is
allowed to take effect.

Design notes:

* Every ``minimum_condition`` rule in the policy is checked against
  the intake report. If ANY rule fails, the verdict is
  ``may_recalibrate=False``.
* The prohibited-action audit is informational only -- it does not
  block the gate, because no concrete weight changes have been
  proposed yet. The audit is surfaced so reviewers see which safety
  floors they would be required to respect if they propose any change.
* Rate-limit status is also informational only. The gate does not
  itself know when the previous recalibration ran; that input must be
  supplied by the caller via ``previous_recalibration_at`` and
  ``candidate_weight_l1_distance``. If those are ``None``, the
  corresponding status is "unknown" and the verdict still passes the
  minimum-conditions check, but the verdict carries a clear note.
* Reviewer-artefact status reports which required artefacts are
  present on disk. Missing artefacts are surfaced as warnings but do
  not by themselves block the gate; the human review is the final
  step. This is documented in the policy notes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openamp_foundry.calibration.policy import (
    PolicyRule,
    RecalibrationPolicy,
    ReviewerArtefact,
)


@dataclass(frozen=True)
class RuleResult:
    """Outcome of evaluating a single minimum_condition rule."""

    rule_id: str
    passed: bool
    observed: Any
    threshold: Any
    reason: str


@dataclass(frozen=True)
class ProhibitedActionAudit:
    """Whether a prohibited action is in force."""

    action_id: str
    description: str
    in_force: bool


@dataclass(frozen=True)
class RateLimitStatus:
    """Status of a single rate-limit rule."""

    rule_id: str
    observed: Any
    threshold: Any
    status: str  # "ok" | "exceeded" | "unknown"
    note: str


@dataclass(frozen=True)
class ReviewerArtefactStatus:
    """Status of a single required reviewer artefact."""

    artefact_id: str
    expected_path: str
    present: bool
    resolved_path: str | None
    note: str


@dataclass(frozen=True)
class GateVerdict:
    """The output of evaluating the recalibration gate."""

    may_recalibrate: bool
    policy_version: int
    policy_locked_at: str
    intake_report_path: str
    n_panel_candidates: int
    n_matched_candidates: int
    n_lab_results: int
    rule_results: tuple[RuleResult, ...]
    prohibited_action_audit: tuple[ProhibitedActionAudit, ...]
    rate_limit_status: tuple[RateLimitStatus, ...]
    reviewer_artefact_status: tuple[ReviewerArtefactStatus, ...]
    reasons: tuple[str, ...]
    summary: str
    n_invalid_lab_result_files: int = 0
    n_input_integrity_issues: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation."""

        return {
            "may_recalibrate": self.may_recalibrate,
            "policy_version": self.policy_version,
            "policy_locked_at": self.policy_locked_at,
            "intake_report_path": self.intake_report_path,
            "n_panel_candidates": self.n_panel_candidates,
            "n_matched_candidates": self.n_matched_candidates,
            "n_lab_results": self.n_lab_results,
            "n_invalid_lab_result_files": self.n_invalid_lab_result_files,
            "n_input_integrity_issues": self.n_input_integrity_issues,
            "rule_results": [asdict(r) for r in self.rule_results],
            "prohibited_action_audit": [asdict(a) for a in self.prohibited_action_audit],
            "rate_limit_status": [asdict(s) for s in self.rate_limit_status],
            "reviewer_artefact_status": [
                asdict(s) for s in self.reviewer_artefact_status
            ],
            "reasons": list(self.reasons),
            "summary": self.summary,
        }


def _cohort_n_positives_and_negatives(report: dict[str, Any]) -> tuple[int, int]:
    """Count confirmed positives and negatives in the joined cohort.

    A candidate contributes to ``n_positive_lab`` if it has
    ``has_lab.active_mic == True``. Otherwise (when ``has_lab`` is a
    dict and ``active_mic`` is False) it contributes to
    ``n_negative_lab``. Candidates with ``has_lab is None`` are
    excluded from both counts.
    """

    rows = report.get("per_candidate_joined", [])
    pos = 0
    neg = 0
    for row in rows:
        has_lab = row.get("has_lab")
        if not isinstance(has_lab, dict):
            continue
        if has_lab.get("active_mic") is True:
            pos += 1
        elif has_lab.get("active_mic") is False:
            neg += 1
    return pos, neg


def _evaluate_rule(
    rule: PolicyRule,
    report: dict[str, Any],
    cohort_pos: int,
    cohort_neg: int,
) -> RuleResult:
    """Apply one minimum_condition rule against the intake report."""

    if rule.id == "MIN_COHORT_SIZE":
        observed = report.get("n_matched_candidates", 0)
        passed = observed >= rule.threshold
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=observed,
            threshold=rule.threshold,
            reason=(
                f"matched cohort size {observed} >= threshold {rule.threshold}"
                if passed
                else (
                    f"matched cohort size {observed} below threshold "
                    f"{rule.threshold}; recalibration forbidden"
                )
            ),
        )

    if rule.id == "MIN_POSITIVES_IN_COHORT":
        observed = cohort_pos
        passed = observed >= rule.threshold
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=observed,
            threshold=rule.threshold,
            reason=(
                f"confirmed positives {observed} >= threshold {rule.threshold}"
                if passed
                else (
                    f"only {observed} confirmed active candidate(s); need at "
                    f"least {rule.threshold} to learn anything useful about activity"
                )
            ),
        )

    if rule.id == "MIN_NEGATIVES_IN_COHORT":
        observed = cohort_neg
        passed = observed >= rule.threshold
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=observed,
            threshold=rule.threshold,
            reason=(
                f"confirmed negatives {observed} >= threshold {rule.threshold}"
                if passed
                else (
                    f"only {observed} confirmed inactive candidate(s); need at "
                    f"least {rule.threshold} to measure false-positive rate"
                )
            ),
        )

    if rule.id == "POSITIVE_CONTROLS_ALL_PASS":
        control_failures = report.get("control_failures", []) or []
        offending = [
            cf for cf in control_failures if not cf.get("positive_control_passed", True)
        ]
        passed = len(offending) == 0
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=(
                "all passed" if passed
                else f"{len(offending)} failed positive control(s)"
            ),
            threshold=rule.threshold,
            reason=(
                "all positive controls passed"
                if passed
                else (
                    f"{len(offending)} positive control(s) failed; recalibration "
                    "forbidden until all positive controls pass"
                )
            ),
        )

    if rule.id == "NEGATIVE_CONTROLS_ALL_PASS":
        control_failures = report.get("control_failures", []) or []
        offending = [
            cf for cf in control_failures if not cf.get("negative_control_passed", True)
        ]
        passed = len(offending) == 0
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=(
                "all passed" if passed
                else f"{len(offending)} failed negative control(s)"
            ),
            threshold=rule.threshold,
            reason=(
                "all negative controls passed"
                if passed
                else (
                    f"{len(offending)} negative control(s) failed; recalibration "
                    "forbidden until all negative controls pass"
                )
            ),
        )

    if rule.id == "NO_ORPHAN_LAB_RESULTS":
        observed = report.get("n_orphan_lab_results", 0)
        passed = observed <= rule.threshold
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=observed,
            threshold=rule.threshold,
            reason=(
                f"no orphan lab results ({observed} <= {rule.threshold})"
                if passed
                else (
                    f"{observed} orphan lab result(s) detected; these are results "
                    "whose candidate_id is not in the pilot panel"
                )
            ),
        )

    if rule.id == "COHORT_METRICS_AVAILABLE":
        cohort_metrics = report.get("cohort_metrics", {}) or {}
        activity = cohort_metrics.get("activity_vs_active_mic", {}) or {}
        insufficient = bool(activity.get("insufficient_data", True))
        passed = insufficient is rule.threshold  # i.e. insufficient_data == False
        return RuleResult(
            rule_id=rule.id,
            passed=passed,
            observed=("insufficient" if insufficient else "available"),
            threshold=rule.threshold,
            reason=(
                "cohort metrics are available (not flagged insufficient_data)"
                if passed
                else (
                    "cohort metrics are flagged insufficient_data; cannot "
                    "use them for recalibration"
                )
            ),
        )

    # Unknown rule id -- treat as failed so reviewers notice the problem.
    return RuleResult(
        rule_id=rule.id,
        passed=False,
        observed=None,
        threshold=rule.threshold,
        reason=f"unknown minimum_condition rule id: {rule.id!r}",
    )


def _evaluate_prohibited_actions(
    policy: RecalibrationPolicy,
) -> tuple[ProhibitedActionAudit, ...]:
    """Return one audit row per prohibited_action, all in_force=True."""

    return tuple(
        ProhibitedActionAudit(
            action_id=action.id,
            description=action.description.strip(),
            in_force=True,
        )
        for action in policy.prohibited_actions
    )


def _parse_iso_date(value: str) -> date | None:
    """Parse an ISO date string, accepting ``YYYY-MM-DD`` only."""

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _evaluate_rate_limits(
    policy: RecalibrationPolicy,
    *,
    intake_report_date: str | None,
    previous_recalibration_at: str | None,
    candidate_weight_l1_distance: float | None,
) -> tuple[RateLimitStatus, ...]:
    """Evaluate rate-limit rules. Unknown inputs become status='unknown'."""

    out: list[RateLimitStatus] = []
    for limit in policy.rate_limits:
        if limit.id == "COOLDOWN_DAYS":
            if not intake_report_date or not previous_recalibration_at:
                out.append(
                    RateLimitStatus(
                        rule_id=limit.id,
                        observed=None,
                        threshold=limit.threshold,
                        status="unknown",
                        note=(
                            "cooldown not evaluable: intake_report_date or "
                            "previous_recalibration_at missing"
                        ),
                    )
                )
                continue
            d_intake = _parse_iso_date(intake_report_date)
            d_prev = _parse_iso_date(previous_recalibration_at)
            if d_intake is None or d_prev is None:
                out.append(
                    RateLimitStatus(
                        rule_id=limit.id,
                        observed=None,
                        threshold=limit.threshold,
                        status="unknown",
                        note="could not parse one of the dates as YYYY-MM-DD",
                    )
                )
                continue
            days = (d_intake - d_prev).days
            passed = days >= limit.threshold
            out.append(
                RateLimitStatus(
                    rule_id=limit.id,
                    observed=days,
                    threshold=limit.threshold,
                    status="ok" if passed else "exceeded",
                    note=(
                        f"days since previous recalibration: {days} "
                        f"(threshold {limit.threshold})"
                    ),
                )
            )
            continue

        if limit.id == "WEIGHT_CHANGE_L1_BUDGET":
            if candidate_weight_l1_distance is None:
                out.append(
                    RateLimitStatus(
                        rule_id=limit.id,
                        observed=None,
                        threshold=limit.threshold,
                        status="unknown",
                        note=(
                            "weight-change L1 budget not evaluable: "
                            "candidate_weight_l1_distance missing"
                        ),
                    )
                )
                continue
            passed = candidate_weight_l1_distance <= limit.threshold
            out.append(
                RateLimitStatus(
                    rule_id=limit.id,
                    observed=candidate_weight_l1_distance,
                    threshold=limit.threshold,
                    status="ok" if passed else "exceeded",
                    note=(
                        f"proposed L1 weight distance: {candidate_weight_l1_distance:.4f} "
                        f"(budget {limit.threshold})"
                    ),
                )
            )
            continue

        # Unknown rate-limit id -- mark as unknown.
        out.append(
            RateLimitStatus(
                rule_id=limit.id,
                observed=None,
                threshold=limit.threshold,
                status="unknown",
                note=f"unknown rate_limit rule id: {limit.id!r}",
            )
        )

    return tuple(out)


def _resolve_artefact_path(template: str, *, project_root: Path | None) -> str:
    """Resolve a path template, substituting YYYY-MM-DD if possible.

    The current date is substituted only when the literal substring
    ``<YYYY-MM-DD>`` appears. If no project root is supplied we use the
    current working directory.
    """

    today = date.today().isoformat()
    rendered = template.replace("<YYYY-MM-DD>", today)
    root = project_root if project_root is not None else Path.cwd()
    candidate = root / rendered
    return str(candidate)


def _evaluate_reviewer_artefacts(
    artefacts: tuple[ReviewerArtefact, ...],
    *,
    project_root: Path | None,
) -> tuple[ReviewerArtefactStatus, ...]:
    """Check which required reviewer artefacts already exist on disk."""

    out: list[ReviewerArtefactStatus] = []
    for art in artefacts:
        path = _resolve_artefact_path(art.expected_path, project_root=project_root)
        p = Path(path)
        present = p.exists()
        note = (
            f"present at {path}" if present else f"missing (expected {path})"
        )
        out.append(
            ReviewerArtefactStatus(
                artefact_id=art.id,
                expected_path=path,
                present=present,
                resolved_path=path if present else None,
                note=note,
            )
        )
    return tuple(out)


def evaluate_recalibration_gate(
    intake_report: dict[str, Any],
    policy: RecalibrationPolicy,
    *,
    intake_report_date: str | None = None,
    previous_recalibration_at: str | None = None,
    candidate_weight_l1_distance: float | None = None,
    project_root: Path | None = None,
) -> GateVerdict:
    """Evaluate the recalibration gate against an intake report and policy.

    Args:
        intake_report: Output of
            ``openamp_foundry.calibration.intake.build_calibration_intake_report``.
        policy: Loaded ``RecalibrationPolicy`` from the policy YAML file.
        intake_report_date: ISO ``YYYY-MM-DD`` string for the date of the
            intake report (used to evaluate the COOLDOWN_DAYS rate limit).
        previous_recalibration_at: ISO ``YYYY-MM-DD`` string for the
            previous successful recalibration event (or ``None`` if no
            prior recalibration has occurred for this scoring config).
        candidate_weight_l1_distance: Optional float for the L1 distance
            between current and proposed scoring weights. ``None`` means
            no concrete weight proposal has been submitted yet.
        project_root: Optional path to use for resolving relative
            reviewer-artefact paths. Defaults to the current working
            directory.

    Returns:
        A ``GateVerdict`` whose ``may_recalibrate`` field is ``True`` only
        when EVERY minimum_condition rule passes.
    """

    cohort_pos, cohort_neg = _cohort_n_positives_and_negatives(intake_report)

    rule_results = tuple(
        _evaluate_rule(rule, intake_report, cohort_pos, cohort_neg)
        for rule in policy.minimum_conditions
    )

    prohibited_audit = _evaluate_prohibited_actions(policy)

    rate_status = _evaluate_rate_limits(
        policy,
        intake_report_date=intake_report_date,
        previous_recalibration_at=previous_recalibration_at,
        candidate_weight_l1_distance=candidate_weight_l1_distance,
    )

    artefact_status = _evaluate_reviewer_artefacts(
        policy.required_reviewer_artefacts, project_root=project_root
    )

    failed_rules = [r for r in rule_results if not r.passed]
    invalid_file_entries = intake_report.get("invalid_lab_result_files", []) or []
    try:
        declared_invalid_files = int(
            intake_report.get("n_invalid_lab_result_files", 0) or 0
        )
    except (TypeError, ValueError):
        declared_invalid_files = 1
    n_invalid_lab_result_files = max(
        declared_invalid_files,
        len(invalid_file_entries) if isinstance(invalid_file_entries, list) else 1,
    )
    input_integrity_entries = intake_report.get("input_integrity_issues", []) or []
    n_input_integrity_issues = (
        len(input_integrity_entries) if isinstance(input_integrity_entries, list) else 1
    )
    may_recalibrate = (
        len(failed_rules) == 0
        and n_invalid_lab_result_files == 0
        and n_input_integrity_issues == 0
    )

    reasons: list[str] = []
    for r in failed_rules:
        reasons.append(f"{r.rule_id}: {r.reason}")
    if n_invalid_lab_result_files:
        reasons.append(
            "INPUT_VALIDATION: "
            f"{n_invalid_lab_result_files} invalid lab result file(s) were "
            "excluded; recalibration is forbidden until the input set is clean"
        )
    if n_input_integrity_issues:
        reasons.append(
            "INPUT_INTEGRITY: "
            f"{n_input_integrity_issues} duplicate-identity issue(s) were "
            "detected; recalibration is forbidden until the input set is clean"
        )
    for s in rate_status:
        if s.status == "exceeded":
            reasons.append(f"{s.rule_id}: {s.note}")
    for s in artefact_status:
        if not s.present:
            reasons.append(
                f"reviewer artefact missing: {s.artefact_id} ({s.expected_path})"
            )

    summary = (
        "PASS: all minimum conditions satisfied; recalibration may proceed subject "
        "to human reviewer approval and rate-limit warnings above."
        if may_recalibrate
        else (
            "FAIL: "
            f"{len(failed_rules)} minimum condition(s) failed and/or input "
            "validation is blocked; recalibration is forbidden until each "
            "issue is resolved."
        )
    )

    return GateVerdict(
        may_recalibrate=may_recalibrate,
        policy_version=policy.policy_version,
        policy_locked_at=policy.locked_at,
        intake_report_path=str(intake_report.get("panel_csv", "")),
        n_panel_candidates=intake_report.get("n_panel_candidates", 0),
        n_matched_candidates=intake_report.get("n_matched_candidates", 0),
        n_lab_results=intake_report.get("n_lab_results", 0),
        rule_results=rule_results,
        prohibited_action_audit=prohibited_audit,
        rate_limit_status=rate_status,
        reviewer_artefact_status=artefact_status,
        reasons=tuple(reasons),
        summary=summary,
        n_invalid_lab_result_files=n_invalid_lab_result_files,
        n_input_integrity_issues=n_input_integrity_issues,
    )


def write_gate_verdict_json(
    verdict: GateVerdict,
    out_path: str | Path,
) -> Path:
    """Write a GateVerdict to JSON."""

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(verdict.to_dict(), f, indent=2, sort_keys=False)
        f.write("\n")
    return p


def write_gate_verdict_markdown(
    verdict: GateVerdict,
    out_path: str | Path,
    *,
    intake_report_path: str,
    policy_path: str,
) -> Path:
    """Write a GateVerdict as a human-readable Markdown report."""

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Recalibration Gate Verdict")
    lines.append("")
    lines.append("This artefact is the machine-readable output of the OpenAMP")
    lines.append("recalibration gate. It is descriptive only -- it does NOT trigger")
    lines.append("any weight update or scoring change. A human reviewer must read")
    lines.append("the verdict and any matching decision log entry before any")
    lines.append("recalibration is allowed to take effect.")
    lines.append("")
    lines.append(f"- Policy version: **{verdict.policy_version}**")
    lines.append(f"- Policy locked at: **{verdict.policy_locked_at}**")
    lines.append(f"- Intake report: `{intake_report_path}`")
    lines.append(f"- Policy file: `{policy_path}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**may_recalibrate = {str(verdict.may_recalibrate).lower()}**"
    )
    lines.append("")
    lines.append(verdict.summary)
    lines.append("")
    lines.append("## Cohort summary")
    lines.append("")
    lines.append(f"- Panel candidates: {verdict.n_panel_candidates}")
    lines.append(f"- Lab results: {verdict.n_lab_results}")
    lines.append(
        f"- Invalid lab result files: {verdict.n_invalid_lab_result_files}"
    )
    lines.append(f"- Input integrity issues: {verdict.n_input_integrity_issues}")
    lines.append(f"- Matched candidates: {verdict.n_matched_candidates}")
    lines.append("")
    lines.append("## Minimum conditions")
    lines.append("")
    lines.append("| Rule | Passed | Observed | Threshold | Reason |")
    lines.append("|------|--------|----------|-----------|--------|")
    for r in verdict.rule_results:
        lines.append(
            f"| {r.rule_id} | "
            f"{'PASS' if r.passed else 'FAIL'} | "
            f"`{r.observed}` | `{r.threshold}` | {r.reason} |"
        )
    lines.append("")
    if verdict.reasons:
        lines.append("## Reasons (blockers)")
        lines.append("")
        for reason in verdict.reasons:
            lines.append(f"- {reason}")
        lines.append("")
    lines.append("## Prohibited actions (permanent floor)")
    lines.append("")
    lines.append("Any proposed recalibration MUST respect every entry below.")
    lines.append("")
    for a in verdict.prohibited_action_audit:
        lines.append(f"### {a.action_id}")
        lines.append("")
        lines.append(a.description)
        lines.append("")
        lines.append("In force: **yes** (this rule cannot be relaxed by future policy edits).")
        lines.append("")
    lines.append("## Rate-limit status")
    lines.append("")
    if not verdict.rate_limit_status:
        lines.append("_No rate-limit rules defined._")
        lines.append("")
    else:
        lines.append("| Rule | Status | Observed | Threshold | Note |")
        lines.append("|------|--------|----------|-----------|------|")
        for s in verdict.rate_limit_status:
            lines.append(
                f"| {s.rule_id} | {s.status} | `{s.observed}` | "
                f"`{s.threshold}` | {s.note} |"
            )
        lines.append("")
    lines.append("## Reviewer artefact status")
    lines.append("")
    if not verdict.reviewer_artefact_status:
        lines.append("_No required reviewer artefacts._")
        lines.append("")
    else:
        lines.append("| Artefact | Present | Path | Note |")
        lines.append("|----------|---------|------|------|")
        for s in verdict.reviewer_artefact_status:
            lines.append(
                f"| {s.artefact_id} | "
                f"{'yes' if s.present else 'no'} | "
                f"`{s.expected_path}` | {s.note} |"
            )
        lines.append("")
    lines.append("## How to act on this verdict")
    lines.append("")
    lines.append("- If `may_recalibrate=true`, a human reviewer MAY propose a")
    lines.append("  weight change. The proposal MUST respect every prohibited")
    lines.append("  action listed above and MUST stay within the weight-change")
    lines.append("  L1 budget. A decision log entry is required.")
    lines.append("- If `may_recalibrate=false`, no weight update is allowed")
    lines.append("  from this intake report. Reasons above must be resolved")
    lines.append("  (e.g. wait for more data, fix control failures, document")
    lines.append("  orphan results) and a new intake report generated.")
    lines.append("")
    p.write_text("\n".join(lines))
    return p
