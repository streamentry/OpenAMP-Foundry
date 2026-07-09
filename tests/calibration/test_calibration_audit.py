"""Tests for the calibration pipeline audit.

Verifies:
  - Audit with no artifacts fails gracefully
  - Audit with a single artifact produces partial coverage
  - Intake ↔ gate count matching works (match and mismatch)
  - Engine ↔ gate verdict matching works (match and mismatch)
  - Engine L1 budget checks work
  - Report ↔ gate verdict consistency works
  - Report ↔ engine proposal consistency works
  - Timestamp sanity checks detect future timestamps
  - Intake cohort metrics warning triggers correctly
  - JSON writer produces valid, schema-conformant output
  - Markdown writer produces non-empty output
  - Synthetic example data passes audit when all artifacts available

Honest limitation:
  These tests use synthetic dict fixtures, not real wet-lab data.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from openamp_foundry.calibration.audit import (
    run_calibration_audit,
    write_calibration_audit_json,
    write_calibration_audit_markdown,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "calibration_audit.schema.json"
SYNTHETIC_INTAKE = REPO_ROOT / "outputs" / "calibration_intake_example.json"
SYNTHETIC_GATE = REPO_ROOT / "outputs" / "recalibration_gate_example.json"


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def base_intake() -> dict:
    return {
        "n_panel_candidates": 8,
        "n_matched_candidates": 4,
        "n_lab_results": 5,
        "n_orphan_lab_results": 0,
        "cohort_metrics": {},
        "report_disclaimer": "test data",
    }


@pytest.fixture
def base_gate() -> dict:
    return {
        "may_recalibrate": False,
        "n_panel_candidates": 8,
        "n_matched_candidates": 4,
        "n_lab_results": 5,
        "policy_version": 1,
        "summary": "FAIL: test scenario",
    }


@pytest.fixture
def base_engine() -> dict:
    return {
        "gate_passed": False,
        "l1_total": 0.0,
        "l1_budget": 0.10,
        "l1_within_budget": True,
        "deltas": [],
        "notes": ["test only"],
    }


@pytest.fixture
def base_report() -> dict:
    now = datetime.now()
    return {
        "report_type": "recalibration_report",
        "schema_version": "1.0",
        "timestamp": now.isoformat(),
        "policy_version": 1,
        "human_review_required": True,
        "gate_verdict": {
            "may_recalibrate": False,
            "n_panel_candidates": 8,
            "n_matched_candidates": 4,
            "n_lab_results": 5,
        },
        "proposal": {
            "gate_passed": False,
            "l1_total": 0.0,
            "l1_budget": 0.10,
            "l1_within_budget": True,
            "deltas": [],
            "notes": ["test only"],
        },
    }


# ── No-artifact edge cases ────────────────────────────────────────


def test_audit_no_artifacts():
    """Audit with no paths and no data fails gracefully."""
    result = run_calibration_audit()
    assert result["report_type"] == "calibration_audit"
    assert result["overall_pass"] is False
    assert result["artifacts_checked"] == []
    assert result["n_checks"] == 4  # four artifact-path checks
    assert result["summary"] == "No artifacts were available for audit. " \
        "Provide at least one valid artifact path or data dict."


def test_audit_single_artifact_via_data():
    """Audit with a single data dict produces partial coverage."""
    result = run_calibration_audit(intake_data={"n_panel_candidates": 5})
    assert result["overall_pass"] is False
    assert "intake" in result["artifacts_checked"]
    # Should include existence check + partial comparison warnings
    n_failed = result["n_failed"]
    assert n_failed >= 1


# ── Count consistency ──────────────────────────────────────────────


def test_intake_gate_counts_match():
    """When intake and gate counts match, the check passes."""
    intake = {
        "n_panel_candidates": 10,
        "n_matched_candidates": 6,
        "n_lab_results": 8,
        "n_orphan_lab_results": 0,
        "cohort_metrics": {},
    }
    gate = {
        "may_recalibrate": False,
        "n_panel_candidates": 10,
        "n_matched_candidates": 6,
        "n_lab_results": 8,
    }
    result = run_calibration_audit(
        intake_data=intake, gate_data=gate,
    )
    count_check = [c for c in result["checks"] if c["check_id"] == "INTAKE_GATE_COUNTS_MATCH"]
    assert len(count_check) == 1
    assert count_check[0]["passed"] is True


def test_intake_gate_counts_mismatch():
    """When intake and gate counts differ, the check fails."""
    intake = {
        "n_panel_candidates": 10,
        "n_matched_candidates": 6,
        "n_lab_results": 8,
        "n_orphan_lab_results": 0,
        "cohort_metrics": {},
    }
    gate = {
        "may_recalibrate": False,
        "n_panel_candidates": 10,
        "n_matched_candidates": 5,
        "n_lab_results": 7,
    }
    result = run_calibration_audit(
        intake_data=intake, gate_data=gate,
    )
    count_check = [c for c in result["checks"] if c["check_id"] == "INTAKE_GATE_COUNTS_MATCH"]
    assert len(count_check) == 1
    assert count_check[0]["passed"] is False


# ── Engine ↔ Gate verdict consistency ──────────────────────────────


def test_engine_gate_verdict_match():
    """Engine gate_passed should match gate may_recalibrate."""
    result = run_calibration_audit(
        gate_data={"may_recalibrate": False},
        engine_data={"gate_passed": False, "l1_total": 0.0, "l1_budget": 0.10, "l1_within_budget": True},
    )
    match_check = [c for c in result["checks"] if c["check_id"] == "ENGINE_GATE_VERDICT_MATCH"]
    assert len(match_check) == 1
    assert match_check[0]["passed"] is True


def test_engine_gate_verdict_mismatch():
    """Engine gate_passed disagrees with gate may_recalibrate → fail."""
    result = run_calibration_audit(
        gate_data={"may_recalibrate": True},
        engine_data={"gate_passed": False, "l1_total": 0.0, "l1_budget": 0.10, "l1_within_budget": True},
    )
    match_check = [c for c in result["checks"] if c["check_id"] == "ENGINE_GATE_VERDICT_MATCH"]
    assert len(match_check) == 1
    assert match_check[0]["passed"] is False


# ── L1 budget checks ──────────────────────────────────────────────


def test_engine_l1_within_budget():
    """L1 total within budget → check passes."""
    result = run_calibration_audit(
        engine_data={"gate_passed": True, "l1_total": 0.05, "l1_budget": 0.10, "l1_within_budget": True},
    )
    budget_check = [c for c in result["checks"] if c["check_id"] == "ENGINE_L1_WITHIN_BUDGET"]
    assert len(budget_check) == 1
    assert budget_check[0]["passed"] is True


def test_engine_l1_exceeds_budget():
    """L1 total exceeds budget → check fails."""
    result = run_calibration_audit(
        engine_data={"gate_passed": True, "l1_total": 0.15, "l1_budget": 0.10, "l1_within_budget": True},
    )
    budget_check = [c for c in result["checks"] if c["check_id"] == "ENGINE_L1_WITHIN_BUDGET"]
    assert len(budget_check) == 1
    assert budget_check[0]["passed"] is False


# ── Report consistency ─────────────────────────────────────────────


def test_report_gate_verdict_match():
    """Report gate-verdict section matches standalone gate."""
    report = {
        "report_type": "recalibration_report",
        "gate_verdict": {
            "may_recalibrate": False,
            "n_panel_candidates": 8,
            "n_matched_candidates": 4,
            "n_lab_results": 5,
        },
    }
    gate = {
        "may_recalibrate": False,
        "n_panel_candidates": 8,
        "n_matched_candidates": 4,
        "n_lab_results": 5,
    }
    result = run_calibration_audit(report_data=report, gate_data=gate)
    rv_check = [c for c in result["checks"] if c["check_id"] == "REPORT_GATE_VERDICT_MATCH"]
    assert len(rv_check) == 1
    assert rv_check[0]["passed"] is True


def test_report_engine_proposal_match():
    """Report proposal section matches standalone engine."""
    report = {
        "report_type": "recalibration_report",
        "gate_verdict": {"may_recalibrate": False, "n_panel_candidates": 0, "n_matched_candidates": 0, "n_lab_results": 0},
        "proposal": {
            "gate_passed": False,
            "l1_total": 0.0,
            "l1_budget": 0.10,
            "l1_within_budget": True,
        },
    }
    engine = {
        "gate_passed": False,
        "l1_total": 0.0,
        "l1_budget": 0.10,
        "l1_within_budget": True,
    }
    result = run_calibration_audit(report_data=report, engine_data=engine)
    rp_check = [c for c in result["checks"] if c["check_id"] == "REPORT_ENGINE_PROPOSAL_MATCH"]
    assert len(rp_check) == 1
    assert rp_check[0]["passed"] is True


# ── Timestamp sanity ──────────────────────────────────────────────


def test_timestamp_future_detected():
    """A future timestamp should fail the timestamp check."""
    future = (datetime.now() + timedelta(days=1)).isoformat()
    intake = {
        "timestamp": future,
        "n_panel_candidates": 1,
        "n_matched_candidates": 0,
        "n_lab_results": 0,
        "n_orphan_lab_results": 0,
        "cohort_metrics": {},
    }
    result = run_calibration_audit(intake_data=intake)
    ts_check = [c for c in result["checks"] if c["check_id"] == "TIMESTAMPS_REASONABLE"]
    assert len(ts_check) == 1
    assert ts_check[0]["passed"] is False
    assert "future" in ts_check[0]["observed"].lower()


# ── Cohort metrics warning ─────────────────────────────────────────


def test_cohort_metrics_warn_on_insufficient_data_with_gate_pass():
    """When intake has insufficient_data but gate passes, warn."""
    intake = {
        "n_panel_candidates": 5,
        "n_matched_candidates": 2,
        "n_lab_results": 2,
        "n_orphan_lab_results": 0,
        "cohort_metrics": {
            "mic": {
                "n": 2,
                "min_required": 5,
                "insufficient_data": True,
            },
        },
    }
    gate = {
        "may_recalibrate": True,
        "n_panel_candidates": 5,
        "n_matched_candidates": 2,
        "n_lab_results": 2,
    }
    result = run_calibration_audit(intake_data=intake, gate_data=gate)
    warn_check = [c for c in result["checks"] if c["check_id"] == "INTAKE_COHORT_METRICS_WARN"]
    assert len(warn_check) == 1
    assert warn_check[0]["passed"] is False
    assert warn_check[0]["severity"] == "warning"


# ── JSON writer ────────────────────────────────────────────────────


def test_json_writer_schema_conformant(tmp_path):
    """Written JSON should be valid and schema-conformant."""
    out = tmp_path / "audit.json"
    result = run_calibration_audit(
        intake_data={"n_panel_candidates": 5, "n_matched_candidates": 2, "n_lab_results": 3, "n_orphan_lab_results": 0, "cohort_metrics": {}},
    )
    write_calibration_audit_json(result, out)
    assert out.exists()
    with open(out) as f:
        written = json.load(f)
    assert written["report_type"] == "calibration_audit"
    assert "overall_pass" in written
    assert "checks" in written
    assert "summary" in written

    # Validate against schema
    import jsonschema
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(written)


# ── Markdown writer ────────────────────────────────────────────────


def test_markdown_writer_non_empty(tmp_path):
    """Written Markdown should be non-empty and readable."""
    out = tmp_path / "audit.md"
    result = run_calibration_audit(
        intake_data={"n_panel_candidates": 5, "n_matched_candidates": 2, "n_lab_results": 3, "n_orphan_lab_results": 0, "cohort_metrics": {}},
    )
    write_calibration_audit_markdown(result, out)
    assert out.exists()
    text = out.read_text()
    assert len(text) > 100
    assert "Calibration Pipeline Audit" in text
    assert "Consistency checks" in text


# ── Full synthetic example ─────────────────────────────────────────


def test_synthetic_example_intake_and_gate_consistent():
    """The synthetic intake and gate examples should be internally consistent."""
    with open(SYNTHETIC_INTAKE) as f:
        intake = json.load(f)
    with open(SYNTHETIC_GATE) as f:
        gate = json.load(f)
    result = run_calibration_audit(intake_data=intake, gate_data=gate)
    # Count-specific checks should pass
    count_check = [c for c in result["checks"] if c["check_id"] == "INTAKE_GATE_COUNTS_MATCH"]
    assert count_check[0]["passed"] is True
    # Cohort metrics should be flagged but gate should be false → no warning
    warn_check = [c for c in result["checks"] if c["check_id"] == "INTAKE_COHORT_METRICS_WARN"]
    assert warn_check[0]["passed"] is True


# ── Known artifact paths ───────────────────────────────────────────


def test_synthetic_artifact_paths_exist():
    """The synthetic example output files should exist on disk."""
    assert SYNTHETIC_INTAKE.exists(), f"expected intake at {SYNTHETIC_INTAKE}"
    assert SYNTHETIC_GATE.exists(), f"expected gate at {SYNTHETIC_GATE}"


# ── Engine without gate_passed field ───────────────────────────────


def test_engine_without_gate_passed():
    """Engine with no gate_passed field should not trigger a verdict mismatch."""
    engine = {"l1_total": 0.05, "l1_budget": 0.10, "l1_within_budget": True, "deltas": []}
    gate = {"may_recalibrate": True}
    result = run_calibration_audit(gate_data=gate, engine_data=engine)
    match_check = [c for c in result["checks"] if c["check_id"] == "ENGINE_GATE_VERDICT_MATCH"]
    assert match_check[0]["passed"] is True  # None == None is vacuously true


# ── File path existence checks via paths ───────────────────────────


def test_audit_with_nonexistent_paths(tmp_path):
    """Non-existent file paths should produce failed existence checks."""
    result = run_calibration_audit(
        intake_path=str(tmp_path / "nonexistent_intake.json"),
        gate_path=str(tmp_path / "nonexistent_gate.json"),
    )
    exist_checks = {c["check_id"]: c for c in result["checks"]}
    assert exist_checks["INTAKE_PATH_PRESENT"]["passed"] is False
    assert exist_checks["GATE_PATH_PRESENT"]["passed"] is False
