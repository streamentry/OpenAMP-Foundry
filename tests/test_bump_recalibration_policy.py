"""Tests for scripts/bump_recalibration_policy.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from openamp_foundry.calibration.policy import load_recalibration_policy

MINIMAL_POLICY = """\
policy_version: 1
locked_at: "2026-07-04"
human_reviewer: "test-reviewer"
minimum_conditions:
  - id: MIN_COHORT_SIZE
    description: "Minimum cohort size"
    threshold: 5
    applies_to: "cohort"
    rationale: "Statistical significance floor"
  - id: MIN_POSITIVES_IN_COHORT
    description: "Minimum positives"
    threshold: 2
    applies_to: "cohort"
    rationale: "Need at least 2 positives"
prohibited_actions:
  - id: NO_TOXICITY_RELAXATION
    description: "Cannot relax toxicity thresholds"
    rationale: "Safety floor"
  - id: NO_HEMOLYSIS_RELAXATION
    description: "Cannot relax hemolysis thresholds"
    rationale: "Safety floor"
  - id: NO_NOVELTY_RELAXATION
    description: "Cannot relax novelty thresholds"
    rationale: "Safety floor"
  - id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
    description: "No pathogen enhancement"
    rationale: "Dual-use safeguard"
  - id: NO_POST_HOC_SUCCESS_REDEFINITION
    description: "No success criteria changes after results"
    rationale: "Anti-cherry-picking"
rate_limits:
  - id: WEIGHT_CHANGE_L1_BUDGET
    description: "Maximum L1 distance per recalibration event"
    threshold: 0.10
    applies_to: "candidate_weights_post_minus_pre_l1"
    rationale: "Prevents large jumps"
  - id: COOLDOWN_DAYS
    description: "Minimum days between recalibration events"
    threshold: 14
    applies_to: "previous_recalibration_at"
    rationale: "Time separation prevents overfitting"
required_reviewer_artefacts:
  - id: INTAKE_REPORT_JSON
    description: "Machine-readable intake report"
    expected_path: "outputs/calibration_intake.json"
    kind: "machine"
  - id: DECISION_LOG_ENTRY
    description: "Dated, human-authored decision log entry"
    expected_path: "docs/DECISION_LOG_<YYYY-MM-DD>.md"
    kind: "human"
locked_changes:
  - rule_id: MIN_COHORT_SIZE
    locked_at: "2026-07-04"
    reason: "Anti-cherry-picking floor"
  - rule_id: MIN_POSITIVES_IN_COHORT
    locked_at: "2026-07-04"
    reason: "Anti-cherry-picking floor"
  - rule_id: NO_TOXICITY_RELAXATION
    locked_at: "2026-07-04"
    reason: "Permanent safety floor"
  - rule_id: NO_HEMOLYSIS_RELAXATION
    locked_at: "2026-07-04"
    reason: "Permanent safety floor"
  - rule_id: NO_NOVELTY_RELAXATION
    locked_at: "2026-07-04"
    reason: "Permanent novelty safeguard"
  - rule_id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
    locked_at: "2026-07-04"
    reason: "Permanent dual-use safeguard"
  - rule_id: NO_POST_HOC_SUCCESS_REDEFINITION
    locked_at: "2026-07-04"
    reason: "Permanent anti-cherry-picking"
notes:
  - "Test policy for bump script"
"""


def _run_script(
    tmp_path: Path,
    *,
    human_reviewer: str = "test-bumper",
    decision_log_dir: str | Path | None = None,
    today: str | None = "2026-07-06",
    dry_run: bool = False,
) -> dict:
    """Run bump_recalibration_policy.py and return parsed JSON output."""
    script = Path(__file__).parent.parent / "scripts" / "bump_recalibration_policy.py"
    policy_path = tmp_path / "recalibration_policy.yaml"
    log_dir = tmp_path / "decision_logs"

    if decision_log_dir is None:
        decision_log_dir = str(log_dir)

    cmd = [
        sys.executable,
        str(script),
        "--policy", str(policy_path),
        "--human-reviewer", human_reviewer,
        "--decision-log-dir", str(decision_log_dir),
        "--today", today,
    ]
    if dry_run:
        cmd.append("--dry-run")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "status": "PARSE_ERROR",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }


class TestBumpRecalibrationPolicy:
    def test_bump_version_success(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-07-05.md").write_text("# Decision log entry")

        result = _run_script(
            tmp_path,
            human_reviewer="dr-reviewer",
            today="2026-07-06",
        )

        assert result["status"] == "bumped"
        assert result["old_version"] == 1
        assert result["new_version"] == 2
        assert result["human_reviewer"] == "dr-reviewer"
        assert result["locked_at"] == "2026-07-06"
        assert result["decision_log"] == "DECISION_LOG_2026-07-05.md"

        # Verify file was written
        loaded = load_recalibration_policy(str(policy_path))
        assert loaded.policy_version == 2
        assert loaded.human_reviewer == "dr-reviewer"
        assert loaded.locked_at == "2026-07-06"

        # Verify locked_changes preserved
        rule_ids = {lc.rule_id for lc in loaded.locked_changes}
        assert "MIN_COHORT_SIZE" in rule_ids
        assert "NO_TOXICITY_RELAXATION" in rule_ids

    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)
        original_content = policy_path.read_text()

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-07-05.md").write_text("# Decision log entry")

        result = _run_script(
            tmp_path,
            today="2026-07-06",
            dry_run=True,
        )

        assert result["status"] == "dry_run"
        assert result["old_version"] == 1
        assert result["new_version"] == 2

        # File must not have changed
        assert policy_path.read_text() == original_content

    def test_fails_without_decision_log(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()

        result = _run_script(
            tmp_path,
            today="2026-07-06",
        )

        assert result["status"] == "failed"
        assert "No decision-log file" in "; ".join(result["reasons"])

    def test_fails_with_stale_decision_log(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-05-01.md").write_text("# Old entry")

        result = _run_script(
            tmp_path,
            today="2026-07-06",
        )

        assert result["status"] == "failed"
        assert "exceeds 30-day limit" in "; ".join(result["reasons"])

    def test_fails_with_future_decision_log(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-08-01.md").write_text("# Future entry")

        result = _run_script(
            tmp_path,
            today="2026-07-06",
        )

        assert result["status"] == "failed"
        assert "in the future" in "; ".join(result["reasons"])

    def test_fails_on_missing_policy_file(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-07-05.md").write_text("# Entry")

        result = _run_script(
            tmp_path,
            human_reviewer="reviewer",
            today="2026-07-06",
        )

        assert result["status"] == "failed"
        assert "Policy file not found" in "; ".join(result["reasons"])

    def test_exit_code_3_on_failure(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()

        script = Path(__file__).parent.parent / "scripts" / "bump_recalibration_policy.py"
        cmd = [
            sys.executable,
            str(script),
            "--policy", str(policy_path),
            "--human-reviewer", "reviewer",
            "--decision-log-dir", str(log_dir),
            "--today", "2026-07-06",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        assert result.returncode == 3

    def test_exit_code_0_on_success(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-07-05.md").write_text("# Entry")

        script = Path(__file__).parent.parent / "scripts" / "bump_recalibration_policy.py"
        cmd = [
            sys.executable,
            str(script),
            "--policy", str(policy_path),
            "--human-reviewer", "reviewer",
            "--decision-log-dir", str(log_dir),
            "--today", "2026-07-06",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        assert result.returncode == 0

    def test_bumpable_twice(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "recalibration_policy.yaml"
        policy_path.write_text(MINIMAL_POLICY)

        log_dir = tmp_path / "decision_logs"
        log_dir.mkdir()
        (log_dir / "DECISION_LOG_2026-07-05.md").write_text("# First decision")

        # First bump: v1 -> v2
        r1 = _run_script(tmp_path, human_reviewer="r1", today="2026-07-06")
        assert r1["status"] == "bumped"
        assert r1["new_version"] == 2

        loaded_1 = load_recalibration_policy(str(policy_path))
        assert loaded_1.policy_version == 2

        # Add second decision log (within 30 days of second bump's today)
        (log_dir / "DECISION_LOG_2026-08-01.md").write_text("# Second decision")

        # Second bump: v2 -> v3
        r2 = _run_script(tmp_path, human_reviewer="r2", today="2026-08-02")
        assert r2["status"] == "bumped"
        assert r2["old_version"] == 2
        assert r2["new_version"] == 3

        loaded_2 = load_recalibration_policy(str(policy_path))
        assert loaded_2.policy_version == 3
        assert loaded_2.human_reviewer == "r2"
        assert loaded_2.locked_at == "2026-08-02"
