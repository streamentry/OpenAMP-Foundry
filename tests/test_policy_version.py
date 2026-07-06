"""Tests for calibration/policy_version.py."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from openamp_foundry.calibration.policy import (
    LockedChange,
    PolicyRule,
    ProhibitedAction,
    RateLimit,
    RecalibrationPolicy,
    ReviewerArtefact,
)
from openamp_foundry.calibration.policy_version import (
    VersionValidation,
    _find_latest_decision_log,
    _parse_decision_log_date,
    auto_increment_version,
    validate_policy_version,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_policy(
    *,
    policy_version: int = 2,
    locked_at: str = "2026-07-05",
    human_reviewer: str = "test-reviewer",
    locked_rule_ids: tuple[str, ...] = ("MIN_COHORT_SIZE", "CONTROLS_ACCEPTED"),
    source_path: str = "/dev/null/policy.yaml",
) -> RecalibrationPolicy:
    """Construct a minimal RecalibrationPolicy for testing."""

    locked_changes = tuple(
        LockedChange(
            rule_id=rid,
            locked_at=locked_at,
            reason=f"Locked rule {rid}",
        )
        for rid in locked_rule_ids
    )
    minimum_conditions = tuple(
        PolicyRule(
            id=rid,
            description=f"Rule {rid}",
            threshold=5,
            applies_to="cohort",
            rationale=f"Rationale for {rid}",
        )
        for rid in locked_rule_ids
    )
    return RecalibrationPolicy(
        policy_version=policy_version,
        locked_at=locked_at,
        human_reviewer=human_reviewer,
        minimum_conditions=minimum_conditions,
        prohibited_actions=(),
        rate_limits=(),
        required_reviewer_artefacts=(),
        locked_changes=locked_changes,
        notes=(),
        source_path=Path(source_path),
    )


def _write_decision_log(directory: str | Path, date_str: str) -> Path:
    """Write a minimal decision-log file and return its path."""
    p = Path(directory) / f"DECISION_LOG_{date_str}.md"
    p.write_text(f"# Decision Log {date_str}\n\nApproved.\n")
    return p


# ---------------------------------------------------------------------------
# _parse_decision_log_date
# ---------------------------------------------------------------------------

class TestParseDecisionLogDate:
    def test_valid(self) -> None:
        p = Path("DECISION_LOG_2026-07-05.md")
        d = _parse_decision_log_date(p)
        assert d == date(2026, 7, 5)

    def test_invalid_format(self) -> None:
        p = Path("random_file.md")
        assert _parse_decision_log_date(p) is None

    def test_invalid_date(self) -> None:
        p = Path("DECISION_LOG_2026-13-01.md")
        assert _parse_decision_log_date(p) is None

    def test_wrong_prefix(self) -> None:
        p = Path("OTHER_2026-07-05.md")
        assert _parse_decision_log_date(p) is None


# ---------------------------------------------------------------------------
# _find_latest_decision_log
# ---------------------------------------------------------------------------

class TestFindLatestDecisionLog:
    def test_finds_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, "2026-07-01")
            p2 = _write_decision_log(tmp, "2026-07-10")
            found = _find_latest_decision_log(tmp)
            assert found == p2

    def test_no_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            found = _find_latest_decision_log(tmp)
            assert found is None

    def test_non_existent_dir(self) -> None:
        found = _find_latest_decision_log("/tmp/nonexistent_log_dir_xyz")
        assert found is None

    def test_ignores_non_matching_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "README.md").write_text("hello")
            Path(tmp, "data.csv").write_text("a,b")
            assert _find_latest_decision_log(tmp) is None


# ---------------------------------------------------------------------------
# validate_policy_version
# ---------------------------------------------------------------------------

class TestValidatePolicyVersion:
    def test_passes_when_all_valid(self) -> None:
        prev = _make_policy(policy_version=1)
        curr = _make_policy(policy_version=2)
        result = validate_policy_version(curr, prev)
        assert result.passed
        assert result.version_valid
        assert result.locked_changes_preserved
        assert result.decision_log_valid  # no dir = no check = valid
        assert result.reasons == ()

    def test_fails_when_version_not_increased(self) -> None:
        prev = _make_policy(policy_version=2)
        curr = _make_policy(policy_version=2)
        result = validate_policy_version(curr, prev)
        assert not result.passed
        assert not result.version_valid

    def test_fails_when_version_decreased(self) -> None:
        prev = _make_policy(policy_version=3)
        curr = _make_policy(policy_version=2)
        result = validate_policy_version(curr, prev)
        assert not result.passed
        assert not result.version_valid

    def test_fails_when_locked_changes_removed(self) -> None:
        prev = _make_policy(
            policy_version=1,
            locked_rule_ids=("A", "B", "C"),
        )
        curr = _make_policy(
            policy_version=2,
            locked_rule_ids=("A", "B"),
        )
        result = validate_policy_version(curr, prev)
        assert not result.passed
        assert result.version_valid
        assert not result.locked_changes_preserved
        assert any("C" in r for r in result.reasons)

    def test_passes_when_locked_changes_added(self) -> None:
        prev = _make_policy(
            policy_version=1,
            locked_rule_ids=("A",),
        )
        curr = _make_policy(
            policy_version=2,
            locked_rule_ids=("A", "B"),
        )
        result = validate_policy_version(curr, prev)
        assert result.passed
        assert result.locked_changes_preserved

    def test_decision_log_fresh(self) -> None:
        today = date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, today)
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(curr, prev, decision_log_dir=tmp)
            assert result.passed
            assert result.decision_log_valid

    def test_decision_log_within_30_days(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, "2026-07-05")
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(
                curr, prev, decision_log_dir=tmp, today="2026-07-20"
            )
            assert result.passed
            assert result.decision_log_valid

    def test_decision_log_exactly_30_days(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, "2026-06-20")
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(
                curr, prev, decision_log_dir=tmp, today="2026-07-20"
            )
            assert result.passed
            assert result.decision_log_valid

    def test_decision_log_expired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, "2026-06-19")
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(
                curr, prev, decision_log_dir=tmp, today="2026-07-20"
            )
            assert not result.passed
            assert not result.decision_log_valid

    def test_decision_log_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(curr, prev, decision_log_dir=tmp)
            assert not result.passed
            assert not result.decision_log_valid

    def test_decision_log_future_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_decision_log(tmp, "2026-08-01")
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(
                curr, prev, decision_log_dir=tmp, today="2026-07-20"
            )
            assert not result.passed
            assert not result.decision_log_valid

    def test_no_decision_log_dir_skips_check(self) -> None:
        prev = _make_policy(policy_version=1)
        curr = _make_policy(policy_version=2)
        result = validate_policy_version(curr, prev, decision_log_dir=None)
        assert result.passed
        # decision_log_valid is True when no dir is given (check not required)
        assert result.decision_log_valid

    def test_multiple_failures_all_reported(self) -> None:
        prev = _make_policy(
            policy_version=3,
            locked_rule_ids=("A", "B"),
        )
        curr = _make_policy(
            policy_version=1,
            locked_rule_ids=("A",),
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_policy_version(curr, prev, decision_log_dir=tmp)
            assert not result.passed
            assert not result.version_valid
            assert not result.locked_changes_preserved
            assert not result.decision_log_valid
            assert len(result.reasons) >= 2

    def test_repr(self) -> None:
        v = VersionValidation(
            passed=False,
            version_valid=False,
            locked_changes_preserved=True,
            decision_log_valid=False,
            reasons=("Version not increased", "Log missing"),
        )
        assert not v
        s = repr(v)
        assert "VersionValidation" in s
        assert "passed=False" in s

    def test_bool(self) -> None:
        assert not VersionValidation(
            passed=False,
            version_valid=True,
            locked_changes_preserved=True,
            decision_log_valid=True,
        )
        assert VersionValidation(
            passed=True,
            version_valid=True,
            locked_changes_preserved=True,
            decision_log_valid=True,
        )

    def test_decision_log_ignores_non_log_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "README.md").write_text("hello")
            Path(tmp, "data.json").write_text("{}")
            prev = _make_policy(policy_version=1)
            curr = _make_policy(policy_version=2)
            result = validate_policy_version(curr, prev, decision_log_dir=tmp)
            assert not result.passed
            assert not result.decision_log_valid
            assert any("No decision-log" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# auto_increment_version
# ---------------------------------------------------------------------------

SAMPLE_YAML = """\
policy_version: 1
locked_at: "2026-07-04"
human_reviewer: "original-reviewer"
minimum_conditions:
  - id: MIN_COHORT_SIZE
    description: "Minimum cohort size"
    threshold: 5
    applies_to: "cohort"
    rationale: "Statistical significance floor"
prohibited_actions:
  - id: NO_TOXICITY_RELAXATION
    description: "Cannot relax toxicity thresholds"
    rationale: "Safety floor"
  - id: NO_HEMOLYSIS_RELAXATION
    description: "Cannot relax hemolysis thresholds"
    rationale: "Safety floor"
  - id: NO_NOVELTY_RELAXATION
    description: "Cannot relax novelty thresholds"
    rationale: "Novelty floor"
  - id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
    description: "No pathogen optimization"
    rationale: "Safety"
  - id: NO_POST_HOC_SUCCESS_REDEFINITION
    description: "No post-hoc success redefinition"
    rationale: "Honesty"
rate_limits:
  - id: L1_WEIGHT_BUDGET
    description: "L1 weight change budget"
    threshold: 0.1
    applies_to: "weight_update"
    rationale: "Conservative recalibration"
  - id: RECALIBRATION_COOLDOWN
    description: "Cooldown between recalibrations"
    threshold: 7
    applies_to: "days"
    rationale: "Prevent rapid cycling"
required_reviewer_artefacts:
  - id: DECISION_LOG_ENTRY
    description: "Human decision log entry"
    expected_path: "DECISION_LOG_*.md"
    kind: "markdown"
locked_changes:
  - rule_id: MIN_COHORT_SIZE
    locked_at: "2026-07-04"
    reason: "Safety-critical"
  - rule_id: NO_TOXICITY_RELAXATION
    locked_at: "2026-07-04"
    reason: "Safety floor"
  - rule_id: NO_HEMOLYSIS_RELAXATION
    locked_at: "2026-07-04"
    reason: "Safety floor"
  - rule_id: NO_NOVELTY_RELAXATION
    locked_at: "2026-07-04"
    reason: "Novelty floor"
  - rule_id: NO_DANGEROUS_PATHGEN_OPTIMIZATION
    locked_at: "2026-07-04"
    reason: "Safety"
  - rule_id: NO_POST_HOC_SUCCESS_REDEFINITION
    locked_at: "2026-07-04"
    reason: "Honesty"
  - rule_id: L1_WEIGHT_BUDGET
    locked_at: "2026-07-04"
    reason: "Rate limit"
  - rule_id: RECALIBRATION_COOLDOWN
    locked_at: "2026-07-04"
    reason: "Rate limit"
  - rule_id: DECISION_LOG_ENTRY
    locked_at: "2026-07-04"
    reason: "Review requirement"
notes: []
"""


class TestAutoIncrementVersion:
    def test_bumps_version_by_one(self) -> None:
        prev = _make_policy(policy_version=1)
        result = auto_increment_version(prev, "2026-07-10", "new-reviewer")
        assert result["policy_version"] == 2
        assert result["locked_at"] == "2026-07-10"
        assert result["human_reviewer"] == "new-reviewer"

    def test_from_yaml_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "recalibration_policy.yaml")
            p.write_text(SAMPLE_YAML)
            prev = _make_policy(
                policy_version=1,
                source_path=str(p),
            )
            result = auto_increment_version(
                prev,
                "2026-08-01",
                "bumper",
                policy_dir=tmp,
            )
            assert result["policy_version"] == 2
            assert result["locked_at"] == "2026-08-01"
            assert result["human_reviewer"] == "bumper"
            # locked_changes preserved from source
            locks = result["locked_changes"]
            assert len(locks) >= 1
            assert locks[0]["rule_id"] == "MIN_COHORT_SIZE"

    def test_preserves_all_fields(self) -> None:
        prev = _make_policy(
            policy_version=1,
            locked_rule_ids=("A", "B", "C"),
        )
        result = auto_increment_version(prev, "2026-07-10", "reviewer")
        assert result["policy_version"] == 2
        assert result["locked_at"] == "2026-07-10"
        assert result["human_reviewer"] == "reviewer"
        # All original locked rules preserved
        rule_ids = {lc["rule_id"] for lc in result["locked_changes"]}
        assert rule_ids == {"A", "B", "C"}

    def test_from_missing_yaml_falls_back_to_dataclass(self) -> None:
        prev = _make_policy(
            policy_version=1,
            source_path="/tmp/nonexistent_policy_file_xyz.yaml",
        )
        result = auto_increment_version(prev, "2026-07-10", "fallback-reviewer")
        assert result["policy_version"] == 2
        assert result["locked_at"] == "2026-07-10"
        assert result["human_reviewer"] == "fallback-reviewer"
        assert "minimum_conditions" in result


# ---------------------------------------------------------------------------
# Integration: policy loader round-trip
# ---------------------------------------------------------------------------

def test_round_trip_through_policy_loader() -> None:
    """Auto-increment produces a dict that can be re-loaded as valid policy."""
    from openamp_foundry.calibration.policy import load_recalibration_policy

    # Write a valid policy
    with tempfile.TemporaryDirectory() as tmp:
        yaml_path = str(Path(tmp, "recalibration_policy.yaml"))
        Path(yaml_path).write_text(SAMPLE_YAML)
        prev = load_recalibration_policy(yaml_path)

        # Bump
        result = auto_increment_version(prev, "2026-08-01", "integration-tester")

        # Write bumped version
        bumped_path = str(Path(tmp, "bumped_policy.yaml"))
        with open(bumped_path, "w") as f:
            yaml.dump(result, f, default_flow_style=False)

        # Re-load must succeed
        bumped = load_recalibration_policy(bumped_path)
        assert bumped.policy_version == prev.policy_version + 1
        assert bumped.human_reviewer == "integration-tester"
        assert bumped.locked_at == "2026-08-01"
