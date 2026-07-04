"""Tests for the recalibration policy + gate workflow.

Verifies:
  - Policy YAML loads, validates, and exposes its rules
  - Removing a canonical prohibited_action causes the policy to be rejected
  - Unlocked rules cause the policy to be rejected
  - Duplicate rule ids are rejected
  - Type errors in the YAML are surfaced with helpful messages
  - The gate produces a binary verdict from the policy + intake report
  - Every minimum_condition rule is checked against a real intake report
  - Prohibited-action audit is always present and in_force=true
  - Rate-limit status surfaces UNKNOWN when inputs are missing
  - Rate-limit cooldown is enforced when dates are provided
  - Reviewer-artefact status reports which files exist
  - JSON + Markdown writers produce non-empty, schema-valid output
  - The synthetic example yields may_recalibrate=False (cohort too small,
    one positive control failed)
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from textwrap import dedent

import pytest

from openamp_foundry.calibration.policy import (
    PolicyLoadError,
    canonical_prohibited_action_ids,
    load_recalibration_policy,
)
from openamp_foundry.calibration.recalibration_gate import (
    GateVerdict,
    RateLimitStatus,
    ReviewerArtefactStatus,
    RuleResult,
    evaluate_recalibration_gate,
    write_gate_verdict_json,
    write_gate_verdict_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = REPO_ROOT / "configs" / "recalibration_policy.yaml"
SYNTHETIC_INTAKE = REPO_ROOT / "outputs" / "calibration_intake_example.json"


# ────────────────────────────────────────────────────────────────────
# Policy loader tests
# ────────────────────────────────────────────────────────────────────


def test_policy_loads_successfully():
    p = load_recalibration_policy(POLICY_PATH)
    assert p.policy_version == 1
    assert p.locked_at == "2026-07-04"
    assert len(p.minimum_conditions) >= 7
    assert len(p.prohibited_actions) == 5
    assert len(p.locked_changes) == 12


def test_policy_rule_by_id():
    p = load_recalibration_policy(POLICY_PATH)
    rule = p.rule_by_id("MIN_COHORT_SIZE")
    assert rule is not None
    assert rule.threshold == 5
    assert rule.is_locked("MIN_COHORT_SIZE") if hasattr(rule, "is_locked") else True


def test_policy_is_locked_true_for_listed_rule():
    p = load_recalibration_policy(POLICY_PATH)
    assert p.is_locked("MIN_COHORT_SIZE") is True


def test_policy_is_locked_false_for_unlisted_rule():
    p = load_recalibration_policy(POLICY_PATH)
    assert p.is_locked("DOES_NOT_EXIST") is False


def test_canonical_prohibited_actions_match_policy():
    p = load_recalibration_policy(POLICY_PATH)
    canonical = set(canonical_prohibited_action_ids())
    policy_ids = {a.id for a in p.prohibited_actions}
    assert canonical.issubset(policy_ids)


def test_policy_missing_file_raises(tmp_path):
    with pytest.raises(PolicyLoadError, match="does not exist"):
        load_recalibration_policy(tmp_path / "nope.yaml")


def test_policy_missing_policy_version(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("locked_at: '2026-01-01'\n")
    with pytest.raises(PolicyLoadError, match="policy_version"):
        load_recalibration_policy(p)


def test_policy_negative_version(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("policy_version: -1\nlocked_at: '2026-01-01'\n")
    with pytest.raises(PolicyLoadError, match="policy_version"):
        load_recalibration_policy(p)


def test_policy_missing_locked_at(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("policy_version: 1\n")
    with pytest.raises(PolicyLoadError, match="locked_at"):
        load_recalibration_policy(p)


def test_policy_missing_human_reviewer(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("policy_version: 1\nlocked_at: '2026-01-01'\n")
    with pytest.raises(PolicyLoadError, match="human_reviewer"):
        load_recalibration_policy(p)


def test_policy_duplicate_rule_id_in_minimum_conditions(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions:
          - id: MIN_COHORT_SIZE
            description: x
            threshold: 5
            applies_to: r
            rationale: x
          - id: MIN_COHORT_SIZE
            description: x
            threshold: 6
            applies_to: r
            rationale: x
        prohibited_actions:
          - id: NO_TOXICITY_RELAXATION
            description: x
            rationale: x
        locked_changes:
          - rule_id: MIN_COHORT_SIZE
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_TOXICITY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="duplicate id"):
        load_recalibration_policy(p)


def test_policy_rule_not_locked(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions:
          - id: NEW_RULE
            description: x
            threshold: 5
            applies_to: r
            rationale: x
        prohibited_actions:
          - id: NO_TOXICITY_RELAXATION
            description: x
            rationale: x
        locked_changes:
          - rule_id: NO_TOXICITY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="NEW_RULE"):
        load_recalibration_policy(p)


def test_policy_canonical_prohibited_action_missing(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions: []
        prohibited_actions:
          - id: NO_HEMOLYSIS_RELAXATION
            description: x
            rationale: x
          - id: NO_NOVELTY_RELAXATION
            description: x
            rationale: x
        locked_changes:
          - rule_id: NO_HEMOLYSIS_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_NOVELTY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="NO_TOXICITY_RELAXATION"):
        load_recalibration_policy(p)


def test_policy_prohibited_action_not_locked(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions: []
        prohibited_actions:
          - id: NO_TOXICITY_RELAXATION
            description: x
            rationale: x
          - id: NO_HEMOLYSIS_RELAXATION
            description: x
            rationale: x
          - id: NO_NOVELTY_RELAXATION
            description: x
            rationale: x
          - id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
            description: x
            rationale: x
          - id: NO_POST_HOC_SUCCESS_REDEFINITION
            description: x
            rationale: x
        # NO_TOXICITY_RELAXATION is intentionally omitted from locked_changes
        locked_changes:
          - rule_id: NO_HEMOLYSIS_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_NOVELTY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_POST_HOC_SUCCESS_REDEFINITION
            locked_at: '2026-01-01'
            reason: x
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="NO_TOXICITY_RELAXATION"):
        load_recalibration_policy(p)


def test_policy_threshold_must_be_present(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions:
          - id: NEW_RULE
            description: x
            applies_to: r
            rationale: x
        prohibited_actions: []
        locked_changes: []
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="threshold"):
        load_recalibration_policy(p)


def test_policy_notes_must_be_list_of_strings(tmp_path):
    text = dedent(
        """
        policy_version: 1
        locked_at: '2026-01-01'
        human_reviewer: tester
        minimum_conditions: []
        prohibited_actions:
          - id: NO_TOXICITY_RELAXATION
            description: x
            rationale: x
          - id: NO_HEMOLYSIS_RELAXATION
            description: x
            rationale: x
          - id: NO_NOVELTY_RELAXATION
            description: x
            rationale: x
          - id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
            description: x
            rationale: x
          - id: NO_POST_HOC_SUCCESS_REDEFINITION
            description: x
            rationale: x
        locked_changes:
          - rule_id: NO_TOXICITY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_HEMOLYSIS_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_NOVELTY_RELAXATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
            locked_at: '2026-01-01'
            reason: x
          - rule_id: NO_POST_HOC_SUCCESS_REDEFINITION
            locked_at: '2026-01-01'
            reason: x
        notes: 5
        """
    )
    p = tmp_path / "bad.yaml"
    p.write_text(text)
    with pytest.raises(PolicyLoadError, match="notes"):
        load_recalibration_policy(p)


# ────────────────────────────────────────────────────────────────────
# Gate evaluation: minimum conditions
# ────────────────────────────────────────────────────────────────────


def _empty_intake_report():
    """Return an intake-report dict that should fail every rule."""

    return {
        "panel_csv": "x.csv",
        "results_dir": "y",
        "n_panel_candidates": 0,
        "n_lab_results": 0,
        "n_matched_candidates": 0,
        "n_orphan_lab_results": 0,
        "orphan_candidate_ids": [],
        "summary": {},
        "per_candidate_outcomes": {},
        "per_candidate_joined": [],
        "cohort_metrics": {
            "activity_vs_active_mic": {
                "n": 0,
                "insufficient_data": True,
            }
        },
        "control_failures": [],
        "min_cohort_size": 5,
        "activity_threshold": 0.5,
        "mic_active_cutoff_ug_ml": 32.0,
        "hemolysis_high_pct": 10.0,
        "report_disclaimer": "x",
    }


def _passing_intake_report(n_active: int = 3, n_inactive: int = 3):
    """Return an intake-report dict where all rules should pass."""

    rows = []
    actives = n_active
    inactives = n_inactive
    for i in range(actives):
        rows.append(
            {
                "candidate_id": f"ACTIVE-{i:03d}",
                "has_lab": {
                    "active_mic": True,
                    "high_hemolysis": False,
                    "all_controls_passed": True,
                },
            }
        )
    for i in range(inactives):
        rows.append(
            {
                "candidate_id": f"INACTIVE-{i:03d}",
                "has_lab": {
                    "active_mic": False,
                    "high_hemolysis": False,
                    "all_controls_passed": True,
                },
            }
        )
    return {
        "panel_csv": "x.csv",
        "results_dir": "y",
        "n_panel_candidates": actives + inactives,
        "n_lab_results": actives + inactives,
        "n_matched_candidates": actives + inactives,
        "n_orphan_lab_results": 0,
        "orphan_candidate_ids": [],
        "summary": {},
        "per_candidate_outcomes": {},
        "per_candidate_joined": rows,
        "cohort_metrics": {
            "activity_vs_active_mic": {
                "n": actives + inactives,
                "insufficient_data": False,
            }
        },
        "control_failures": [],
        "min_cohort_size": 5,
        "activity_threshold": 0.5,
        "mic_active_cutoff_ug_ml": 32.0,
        "hemolysis_high_pct": 10.0,
        "report_disclaimer": "x",
    }


def test_gate_rejects_empty_report():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_empty_intake_report(), p)
    assert v.may_recalibrate is False
    # Many rule failures expected
    failed = [r for r in v.rule_results if not r.passed]
    assert len(failed) >= 4


def test_gate_accepts_passing_report():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(3, 3), p)
    assert v.may_recalibrate is True
    # All rules pass
    for r in v.rule_results:
        assert r.passed, f"rule {r.rule_id} unexpectedly failed: {r.reason}"


def test_gate_detects_failed_positive_control():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(3, 3)
    report["control_failures"] = [
        {"result_id": "X", "candidate_id": "Y", "positive_control_passed": False,
         "negative_control_passed": True}
    ]
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "POSITIVE_CONTROLS_ALL_PASS" in failed_ids


def test_gate_detects_failed_negative_control():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(3, 3)
    report["control_failures"] = [
        {"result_id": "X", "candidate_id": "Y", "positive_control_passed": True,
         "negative_control_passed": False}
    ]
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "NEGATIVE_CONTROLS_ALL_PASS" in failed_ids


def test_gate_detects_orphan_results():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(3, 3)
    report["n_orphan_lab_results"] = 2
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "NO_ORPHAN_LAB_RESULTS" in failed_ids


def test_gate_detects_insufficient_metrics():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(3, 3)
    report["cohort_metrics"]["activity_vs_active_mic"]["insufficient_data"] = True
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "COHORT_METRICS_AVAILABLE" in failed_ids


def test_gate_min_positives_below_threshold():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(n_active=1, n_inactive=3)
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "MIN_POSITIVES_IN_COHORT" in failed_ids


def test_gate_min_negatives_below_threshold():
    p = load_recalibration_policy(POLICY_PATH)
    report = _passing_intake_report(n_active=3, n_inactive=1)
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "MIN_NEGATIVES_IN_COHORT" in failed_ids


# ────────────────────────────────────────────────────────────────────
# Gate evaluation: prohibited actions and rate limits
# ────────────────────────────────────────────────────────────────────


def test_prohibited_action_audit_always_in_force():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_empty_intake_report(), p)
    assert len(v.prohibited_action_audit) == len(p.prohibited_actions)
    for a in v.prohibited_action_audit:
        assert a.in_force is True
        assert a.description  # non-empty


def test_rate_limit_unknown_when_no_dates():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(), p)
    cooldown = next(
        s for s in v.rate_limit_status if s.rule_id == "COOLDOWN_DAYS"
    )
    assert cooldown.status == "unknown"
    assert "missing" in cooldown.note


def test_rate_limit_unknown_when_no_weight_l1():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(), p)
    l1 = next(
        s for s in v.rate_limit_status if s.rule_id == "WEIGHT_CHANGE_L1_BUDGET"
    )
    assert l1.status == "unknown"


def test_rate_limit_cooldown_ok():
    p = load_recalibration_policy(POLICY_PATH)
    today = date.today().isoformat()
    # Choose a previous date well beyond the 14-day threshold
    prev = "2020-01-01"
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p,
        intake_report_date=today,
        previous_recalibration_at=prev,
    )
    cooldown = next(
        s for s in v.rate_limit_status if s.rule_id == "COOLDOWN_DAYS"
    )
    assert cooldown.status == "ok"


def test_rate_limit_cooldown_exceeded():
    p = load_recalibration_policy(POLICY_PATH)
    today = date.today().isoformat()
    # Choose a previous date inside the 14-day cooldown (today itself = 0 days)
    prev = date.today().isoformat()
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p,
        intake_report_date=today,
        previous_recalibration_at=prev,
    )
    cooldown = next(
        s for s in v.rate_limit_status if s.rule_id == "COOLDOWN_DAYS"
    )
    assert cooldown.status == "exceeded"
    assert cooldown.observed == 0


def test_rate_limit_weight_l1_exceeded():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p,
        candidate_weight_l1_distance=0.50,
    )
    l1 = next(
        s for s in v.rate_limit_status if s.rule_id == "WEIGHT_CHANGE_L1_BUDGET"
    )
    assert l1.status == "exceeded"


def test_rate_limit_weight_l1_within_budget():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p,
        candidate_weight_l1_distance=0.05,
    )
    l1 = next(
        s for s in v.rate_limit_status if s.rule_id == "WEIGHT_CHANGE_L1_BUDGET"
    )
    assert l1.status == "ok"


# ────────────────────────────────────────────────────────────────────
# Gate evaluation: reviewer artefacts
# ────────────────────────────────────────────────────────────────────


def test_reviewer_artefact_status_when_missing(tmp_path):
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p, project_root=tmp_path
    )
    for s in v.reviewer_artefact_status:
        # The synthetic artefacts aren't in tmp_path, so all should be missing
        assert s.present is False


def test_reviewer_artefact_status_when_present(tmp_path):
    # Create the expected intake files
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "calibration_intake.json").write_text("{}")
    (tmp_path / "outputs" / "calibration_intake.md").write_text("# x")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    today_log = docs_dir / f"DECISION_LOG_{date.today().isoformat()}.md"
    today_log.write_text("# decision log")

    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(
        _passing_intake_report(), p, project_root=tmp_path
    )
    present = {s.artefact_id: s.present for s in v.reviewer_artefact_status}
    assert present["INTAKE_REPORT_JSON"] is True
    assert present["INTAKE_REPORT_MARKDOWN"] is True
    assert present["DECISION_LOG_ENTRY"] is True


# ────────────────────────────────────────────────────────────────────
# Gate evaluation: writers
# ────────────────────────────────────────────────────────────────────


def test_gate_verdict_to_dict_is_serialisable():
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(), p)
    d = v.to_dict()
    json.dumps(d)  # must not raise


def test_gate_verdict_writers_produce_files(tmp_path):
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(), p)
    json_path = tmp_path / "v.json"
    md_path = tmp_path / "v.md"
    write_gate_verdict_json(v, json_path)
    write_gate_verdict_markdown(
        v,
        md_path,
        intake_report_path="outputs/calibration_intake.json",
        policy_path="configs/recalibration_policy.yaml",
    )
    assert json_path.exists() and json_path.stat().st_size > 100
    assert md_path.exists() and md_path.stat().st_size > 100
    # Markdown mentions every prohibited action
    md_text = md_path.read_text()
    for a in p.prohibited_actions:
        assert a.id in md_text


# ────────────────────────────────────────────────────────────────────
# End-to-end with the synthetic example
# ────────────────────────────────────────────────────────────────────


def test_synthetic_example_fails_gate():
    """The synthetic example has cohort=4 (<5) and one failed positive control."""
    p = load_recalibration_policy(POLICY_PATH)
    if not SYNTHETIC_INTAKE.exists():
        pytest.skip("synthetic intake not generated yet")
    with SYNTHETIC_INTAKE.open() as f:
        report = json.load(f)
    v = evaluate_recalibration_gate(report, p)
    assert v.may_recalibrate is False
    failed_ids = [r.rule_id for r in v.rule_results if not r.passed]
    assert "MIN_COHORT_SIZE" in failed_ids
    assert "POSITIVE_CONTROLS_ALL_PASS" in failed_ids


def test_gate_verdict_dataclass_fields():
    """Type-check the GateVerdict dataclass surface."""
    p = load_recalibration_policy(POLICY_PATH)
    v = evaluate_recalibration_gate(_passing_intake_report(), p)
    assert isinstance(v, GateVerdict)
    assert isinstance(v.rule_results, tuple)
    assert all(isinstance(r, RuleResult) for r in v.rule_results)
    assert isinstance(v.rate_limit_status, tuple)
    assert all(isinstance(s, RateLimitStatus) for s in v.rate_limit_status)
    assert isinstance(v.reviewer_artefact_status, tuple)
    assert all(
        isinstance(s, ReviewerArtefactStatus)
        for s in v.reviewer_artefact_status
    )


# ────────────────────────────────────────────────────────────────────
# CLI surface
# ────────────────────────────────────────────────────────────────────


def test_cli_recalibration_gate_smoke():
    """The CLI must exist, accept our flags, and emit JSON to stdout."""
    import subprocess

    if not SYNTHETIC_INTAKE.exists():
        pytest.skip("synthetic intake not generated yet")

    cmd = [
        sys.executable,
        "-m",
        "openamp_foundry.cli",
        "recalibration-gate",
        "--intake-report",
        str(SYNTHETIC_INTAKE),
        "--intake-report-date",
        "2026-07-04",
        "--project-root",
        str(REPO_ROOT),
    ]
    proc = subprocess.run(
        cmd, cwd=str(REPO_ROOT), env={"PYTHONPATH": "src", "PATH": sys.exec_prefix + "/bin:" + __import__("os").environ.get("PATH", "")},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 3, (
        f"expected exit code 3 (gate failed), got {proc.returncode}\n"
        f"stdout:\n{proc.stdout[:500]}\nstderr:\n{proc.stderr[:500]}"
    )
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ok"
    assert payload["may_recalibrate"] is False
    assert payload["policy_version"] == 1


def test_cli_recalibration_gate_missing_intake(tmp_path):
    import subprocess

    cmd = [
        sys.executable,
        "-m",
        "openamp_foundry.cli",
        "recalibration-gate",
        "--intake-report",
        str(tmp_path / "nope.json"),
        "--project-root",
        str(REPO_ROOT),
    ]
    proc = subprocess.run(
        cmd, cwd=str(REPO_ROOT), env={"PYTHONPATH": "src", "PATH": sys.exec_prefix + "/bin:" + __import__("os").environ.get("PATH", "")},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "error"
