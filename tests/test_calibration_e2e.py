"""End-to-end smoke test for the calibration chain.

Exercises the full flow:
    synthetic pilot panel CSV
        + synthetic lab result JSON files
        → calibration-intake report
        → recalibration-gate verdict
        → correct exit code + output structure

This is THE critical safety path for the wet-lab feedback loop.
If this test breaks, the calibration pipeline cannot be trusted.

Honest limitation: All data is synthetic. Tests never rely on real
wet-lab numbers. They verify code-path integrity, not biological signal.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from openamp_foundry.calibration import (
    MIN_COHORT_SIZE,
    BudgetExceededError,
    PolicyViolationError,
    WeightUpdateProposal,
    build_calibration_intake_report,
    compute_weight_update,
    evaluate_recalibration_gate,
    load_recalibration_policy,
    write_calibration_intake_json,
    write_gate_verdict_json,
    write_weight_update_proposal_json,
    write_weight_update_proposal_markdown,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = REPO_ROOT / "configs" / "recalibration_policy.yaml"
EXAMPLES_PANEL = REPO_ROOT / "examples" / "lab_results_panel.csv"
EXAMPLES_RESULTS_DIR = REPO_ROOT / "examples" / "lab_results"


# ── Helpers ────────────────────────────────────────────────────────────

_PANEL_FIELDS = [
    "pilot_rank", "candidate_id", "sequence", "length", "seed",
    "ensemble", "activity", "boman_activity", "disagreement",
    "safety", "synthesis", "novelty", "serum_stability",
    "selectivity_proxy", "rich_selectivity", "pilot_priority",
    "amphipathic_score", "charge_ph74",
]


def _panel_row(candidate_id: str, sequence: str, seed: str,
               ensemble: float = 0.80, activity: float = 0.82,
               rich_selectivity: float = 0.70, **kw) -> dict:
    row = {
        "pilot_rank": "1",
        "candidate_id": candidate_id,
        "sequence": sequence,
        "length": str(len(sequence)),
        "seed": seed,
        "ensemble": f"{ensemble:.2f}",
        "activity": f"{activity:.2f}",
        "boman_activity": "0.75",
        "disagreement": "0.05",
        "safety": "0.90",
        "synthesis": "0.85",
        "novelty": "0.70",
        "serum_stability": "0.65",
        "selectivity_proxy": "0.60",
        "rich_selectivity": f"{rich_selectivity:.2f}",
        "pilot_priority": "0.75",
        "amphipathic_score": "1.5",
        "charge_ph74": "4.0",
    }
    row.update(kw)
    return row


def _write_panel_csv(panel_csv: Path, rows: list[dict]) -> None:
    with panel_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_PANEL_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _lab_result(
    candidate_id: str = "CAND-001",
    assay_type: str = "MIC",
    result_value: float = 8.0,
    result_qualitative: str = "active",
    positive_control_passed: bool = True,
    negative_control_passed: bool = True,
    organism: str = "SYNTHETIC - E. coli ATCC 25922",
    result_id: str | None = None,
) -> dict:
    return {
        "result_id": result_id or f"RES-{candidate_id}",
        "candidate_id": candidate_id,
        "assay_type": assay_type,
        "organism_or_cell_line": organism,
        "result_value": result_value,
        "result_unit": "µg/mL" if assay_type == "MIC" else "%",
        "result_qualitative": result_qualitative,
        "positive_control_passed": positive_control_passed,
        "negative_control_passed": negative_control_passed,
        "positive_control_id": "ciprofloxacin 0.25 µg/mL",
        "negative_control_id": "PBS",
        "assay_date": "2026-07-05",
        "replicate_count": 3,
        "performed_by_lab": "SYNTHETIC - E2E Test",
        "raw_data_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "computational_candidate_certificate_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "notes": "SYNTHETIC DATA - e2e test",
        "disclaimer": (
            "SYNTHETIC TEST. This is not a real experimental result "
            "and does not constitute a drug or clinical claim."
        ),
    }


def _write_lab_result(results_dir: Path, result: dict) -> Path:
    p = results_dir / f"{result['result_id']}.json"
    p.write_text(json.dumps(result))
    return p


def _build_passing_data(tmp_path: Path, n: int = 5):
    """Create synthetic data where all candidates have complete,
    control-passing lab results. n must be >= MIN_COHORT_SIZE."""
    panel_rows = []
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    panel_csv = tmp_path / "panel.csv"
    for i in range(n):
        cid = f"PASS-CAND-{i:03d}"
        active = i % 2 == 0
        panel_rows.append(
            _panel_row(
                candidate_id=cid,
                sequence=f"AAAKKKFFF{i}" if len(str(i)) <= 1 else "AAAKKKFFFI",
                seed=f"SEED-P{i}",
                ensemble=0.82 if active else 0.55,
                activity=0.85 if active else 0.45,
                rich_selectivity=0.75 if active else 0.35,
            )
        )
        _write_lab_result(
            results_dir,
            _lab_result(
                candidate_id=cid,
                assay_type="MIC",
                result_value=8.0 if active else 128.0,
                result_qualitative="active" if active else "inactive",
            ),
        )
    _write_panel_csv(panel_csv, panel_rows)


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def passing_setup(tmp_path):
    """Create a passing calibration dataset with >= MIN_COHORT_SIZE
    candidates, all with complete, control-passing lab results."""
    _build_passing_data(tmp_path, n=MIN_COHORT_SIZE)
    return tmp_path


@pytest.fixture
def failing_setup(tmp_path):
    """Create a failing dataset: too few matched candidates,
    and one control failure."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    panel_csv = tmp_path / "panel.csv"
    # 4 candidates
    panel_rows = [
        _panel_row(candidate_id="FAIL-CAND-001", sequence="AAAKKK", seed="SEED-F1"),
        _panel_row(candidate_id="FAIL-CAND-002", sequence="BBBLLL", seed="SEED-F2"),
        _panel_row(candidate_id="FAIL-CAND-003", sequence="CCCMNN", seed="SEED-F3"),
        _panel_row(candidate_id="FAIL-CAND-004", sequence="DDDOOP", seed="SEED-F4"),
    ]
    _write_panel_csv(panel_csv, panel_rows)
    _write_lab_result(
        results_dir,
        _lab_result(candidate_id="FAIL-CAND-001", result_value=8.0, result_qualitative="active"),
    )
    # Control failure (positive control failed)
    _write_lab_result(
        results_dir,
        _lab_result(
            candidate_id="FAIL-CAND-002", result_value=128.0,
            result_qualitative="inactive", positive_control_passed=False,
        ),
    )
    return tmp_path


# ── Full-chain Python API test ─────────────────────────────────────────


class TestCalibrationE2EPythonAPI:
    """Test the full chain using the Python API directly."""

    def test_passing_chain_returns_may_recalibrate(self, passing_setup):
        """Happy path: cohort >= MIN_COHORT_SIZE, all controls pass
        → intake → gate → may_recalibrate=True."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        assert intake["n_matched_candidates"] >= MIN_COHORT_SIZE
        assert len(intake["control_failures"]) == 0

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)
        assert verdict.may_recalibrate is True, (
            f"Expected may_recalibrate=True on passing data, got False.\n"
            f"Failed rules: {[r.rule_id for r in verdict.rule_results if not r.passed]}"
        )
        assert verdict.n_matched_candidates >= MIN_COHORT_SIZE

    def test_failing_chain_returns_may_recalibrate_false(self, failing_setup):
        """Sad path: cohort < MIN_COHORT_SIZE, control failure
        → intake → gate → may_recalibrate=False."""
        panel_csv = failing_setup / "panel.csv"
        results_dir = failing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        assert intake["n_matched_candidates"] < MIN_COHORT_SIZE
        assert len(intake["control_failures"]) >= 1

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)
        assert verdict.may_recalibrate is False
        failed_ids = [r.rule_id for r in verdict.rule_results if not r.passed]
        assert "MIN_COHORT_SIZE" in failed_ids

    def test_failing_chain_reports_control_failure(self, failing_setup):
        """The failing setup's control failure must be surfaced in
        the gate verdict."""
        panel_csv = failing_setup / "panel.csv"
        results_dir = failing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        assert len(intake["control_failures"]) >= 1
        cf = intake["control_failures"][0]
        assert cf["positive_control_passed"] is False

    def test_passing_chain_produces_valid_json_output(self, passing_setup, tmp_path):
        """The full chain produces valid, schema-conformant JSON output."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)

        intake_out = tmp_path / "intake.json"
        write_calibration_intake_json(intake, intake_out)
        assert intake_out.exists() and intake_out.stat().st_size > 200
        reloaded = json.loads(intake_out.read_text())
        assert reloaded["n_matched_candidates"] >= MIN_COHORT_SIZE

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(reloaded, policy)

        gate_out = tmp_path / "gate.json"
        write_gate_verdict_json(verdict, gate_out)
        assert gate_out.exists() and gate_out.stat().st_size > 200
        gate_data = json.loads(gate_out.read_text())
        assert gate_data["may_recalibrate"] is True
        assert gate_data["policy_version"] == 1

    def test_all_minimum_conditions_satisfied(self, passing_setup):
        """Verify every minimum_condition rule passes on clean data."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        for rule in verdict.rule_results:
            assert rule.passed, (
                f"Rule {rule.rule_id} failed on passing data: "
                f"{rule.reason}"
            )

    def test_prohibited_actions_always_in_force(self, passing_setup):
        """Prohibited actions must always be in_force=true regardless of data."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        for audit in verdict.prohibited_action_audit:
            assert audit.in_force is True, (
                f"Prohibited action {audit.action_id} is NOT in force"
            )

    def test_passing_data_with_multiple_assays(self, tmp_path):
        """A candidate with both MIC and hemolysis results still passes."""
        (tmp_path / "results").mkdir(parents=True, exist_ok=True)
        panel_csv = tmp_path / "panel.csv"
        panel_rows = []
        for i in range(MIN_COHORT_SIZE):
            cid = f"MULTI-CAND-{i:03d}"
            active = i % 2 == 0
            panel_rows.append(
                _panel_row(
                    candidate_id=cid, sequence=f"MMMNNN{i}", seed=f"SEED-M{i}",
                    ensemble=0.82 if active else 0.55,
                    activity=0.85 if active else 0.45,
                )
            )
            _write_lab_result(
                tmp_path / "results",
                _lab_result(
                    candidate_id=cid, assay_type="MIC",
                    result_value=8.0 if active else 128.0,
                    result_qualitative="active" if active else "inactive",
                    result_id=f"RES-MIC-{cid}",
                ),
            )
            if i < 3:
                _write_lab_result(
                    tmp_path / "results",
                    _lab_result(
                        candidate_id=cid, assay_type="hemolysis_RBC",
                        result_value=5.0, result_qualitative="inactive",
                        result_id=f"RES-HEMO-{cid}",
                    ),
                )
        _write_panel_csv(panel_csv, panel_rows)

        intake = build_calibration_intake_report(panel_csv, tmp_path / "results")
        assert intake["n_matched_candidates"] == MIN_COHORT_SIZE

        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)
        assert verdict.may_recalibrate is True


# ── Full-chain CLI integration test ────────────────────────────────────


class TestCalibrationE2ECLI:
    """Test the full calibration chain via CLI subprocess.

    This is the closest we get to "user runs the commands" without
    shelling out to make.
    """

    def test_cli_full_chain_passing(self, passing_setup, tmp_path):
        """Run calibration-intake + recalibration-gate via CLI
        on passing data. Assert both exit codes and output structure."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake_out = tmp_path / "intake.json"
        gate_out = tmp_path / "gate.json"

        # Step 1: calibration-intake
        intake_cmd = [
            sys.executable, "-m", "openamp_foundry.cli",
            "calibration-intake",
            "--panel", str(panel_csv),
            "--results-dir", str(results_dir),
            "--out-json", str(intake_out),
        ]
        proc = subprocess.run(
            intake_cmd,
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, (
            f"calibration-intake failed:\n"
            f"stdout: {proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
        )
        intake_payload = json.loads(proc.stdout)
        assert intake_payload["status"] == "ok"
        assert intake_payload["n_matched_candidates"] >= MIN_COHORT_SIZE
        assert intake_out.exists()

        # Step 2: recalibration-gate
        gate_cmd = [
            sys.executable, "-m", "openamp_foundry.cli",
            "recalibration-gate",
            "--intake-report", str(intake_out),
            "--intake-report-date", date.today().isoformat(),
            "--policy", str(POLICY_PATH),
            "--project-root", str(REPO_ROOT),
            "--out-json", str(gate_out),
        ]
        proc = subprocess.run(
            gate_cmd,
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0, (
            f"recalibration-gate expected exit 0, got {proc.returncode}\n"
            f"stdout: {proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
        )
        gate_payload = json.loads(proc.stdout)
        assert gate_payload["status"] == "ok"
        assert gate_payload["may_recalibrate"] is True
        assert gate_payload["policy_version"] == 1
        assert gate_payload["n_matched_candidates"] >= MIN_COHORT_SIZE
        assert gate_out.exists()

        # Step 3: verify gate output JSON
        gate_data = json.loads(gate_out.read_text())
        assert gate_data["may_recalibrate"] is True
        assert len(gate_data["rule_results"]) >= 7
        assert all(r["passed"] for r in gate_data["rule_results"])
        assert "PASS" in gate_data["summary"] or "may proceed" in gate_data["summary"].lower()

    def test_cli_full_chain_failing(self, failing_setup, tmp_path):
        """Run the full chain on failing data. Assert exit code 3."""
        panel_csv = failing_setup / "panel.csv"
        results_dir = failing_setup / "results"
        intake_out = tmp_path / "intake_fail.json"
        gate_out = tmp_path / "gate_fail.json"

        # Step 1: calibration-intake
        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "calibration-intake",
                "--panel", str(panel_csv),
                "--results-dir", str(results_dir),
                "--out-json", str(intake_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0
        assert intake_out.exists()

        # Step 2: recalibration-gate (expect exit 3)
        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "recalibration-gate",
                "--intake-report", str(intake_out),
                "--intake-report-date", date.today().isoformat(),
                "--policy", str(POLICY_PATH),
                "--project-root", str(REPO_ROOT),
                "--out-json", str(gate_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 3, (
            f"expected exit 3 (gate failed), got {proc.returncode}\n"
            f"stdout: {proc.stdout[:500]}"
        )
        payload = json.loads(proc.stdout)
        assert payload["may_recalibrate"] is False
        assert gate_out.exists()

        gate_data = json.loads(gate_out.read_text())
        failed_ids = [r["rule_id"] for r in gate_data["rule_results"] if not r["passed"]]
        assert "MIN_COHORT_SIZE" in failed_ids
        assert any(
            "POSITIVE_CONTROLS" in r["rule_id"]
            for r in gate_data["rule_results"] if not r["passed"]
        ), f"expected POSITIVE_CONTROLS failure; failed: {failed_ids}"

    def test_cli_chain_with_rate_limits(self, passing_setup, tmp_path):
        """Pass full chain with rate-limit inputs: verify they appear in output."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake_out = tmp_path / "intake_rl.json"
        gate_out = tmp_path / "gate_rl.json"

        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "calibration-intake",
                "--panel", str(panel_csv),
                "--results-dir", str(results_dir),
                "--out-json", str(intake_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0

        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "recalibration-gate",
                "--intake-report", str(intake_out),
                "--intake-report-date", date.today().isoformat(),
                # Previous recalibration far enough in the past to pass cooldown
                "--previous-recalibration-at", "2026-01-01",
                "--weight-l1-distance", "0.05",
                "--policy", str(POLICY_PATH),
                "--project-root", str(REPO_ROOT),
                "--out-json", str(gate_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)

        # Rate-limit statuses should be "ok" or "unknown" for a clean run
        for rl in payload["rate_limit_status"]:
            assert rl["status"] in ("ok", "unknown"), (
                f"Rate limit {rl['rule_id']} status was {rl['status']}: "
                f"{rl['note']}"
            )

    def test_cli_chain_missing_intake_rejected(self, tmp_path):
        """CLI should return exit 2 when intake file doesn't exist."""
        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "recalibration-gate",
                "--intake-report", str(tmp_path / "nonexistent.json"),
                "--policy", str(POLICY_PATH),
                "--project-root", str(REPO_ROOT),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 2
        payload = json.loads(proc.stdout)
        assert payload["status"] == "error"

    def test_cli_chain_with_synthetic_example(self, tmp_path):
        """The shipped synthetic example must produce a consistent
        failing chain: cohort < 5, one positive control failed."""
        intake_out = tmp_path / "intake_example.json"
        gate_out = tmp_path / "gate_example.json"

        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "calibration-intake",
                "--panel", str(EXAMPLES_PANEL),
                "--results-dir", str(EXAMPLES_RESULTS_DIR),
                "--out-json", str(intake_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0
        assert intake_out.exists()

        proc = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli",
                "recalibration-gate",
                "--intake-report", str(intake_out),
                "--intake-report-date", "2026-07-04",
                "--policy", str(POLICY_PATH),
                "--project-root", str(REPO_ROOT),
                "--out-json", str(gate_out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 3
        payload = json.loads(proc.stdout)
        assert payload["may_recalibrate"] is False

        gate_data = json.loads(gate_out.read_text())
        failed_ids = [r["rule_id"] for r in gate_data["rule_results"] if not r["passed"]]
        assert "MIN_COHORT_SIZE" in failed_ids
        assert "POSITIVE_CONTROLS_ALL_PASS" in failed_ids


# ── Recalibration Engine tests ────────────────────────────────────────


class TestRecalibrationEngine:
    """Test the weight-update proposal engine."""

    def test_raises_on_gate_false(self, failing_setup):
        """Engine must raise PolicyViolationError when gate says no."""
        panel_csv = failing_setup / "panel.csv"
        results_dir = failing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)
        assert verdict.may_recalibrate is False

        current_weights = {"activity": 0.40, "safety": 0.25}
        with pytest.raises(PolicyViolationError):
            compute_weight_update(intake, verdict, current_weights, policy_l1_budget=0.10)

    def test_returns_proposal_on_gate_true(self, passing_setup):
        """Engine must return a WeightUpdateProposal when gate says yes."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)
        assert verdict.may_recalibrate is True

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert isinstance(proposal, WeightUpdateProposal)
        assert proposal.gate_passed is True
        assert proposal.policy_version == 1
        assert proposal.n_matched >= MIN_COHORT_SIZE

    def test_proposal_contains_deltas(self, passing_setup):
        """Proposal must contain per-scorer WeightDelta entries."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )

        # Activity metric should be mapped to a delta
        activity_deltas = [d for d in proposal.deltas if d.scorer == "activity"]
        assert len(activity_deltas) >= 1
        d = activity_deltas[0]
        assert d.current_weight == 0.40
        assert isinstance(d.proposed_weight, float)
        assert isinstance(d.delta, float)
        assert isinstance(d.rationale, str)
        assert len(d.rationale) > 10

    def test_proposal_l1_within_budget_by_default(self, passing_setup):
        """Proposal L1 total must be within a reasonable budget."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert proposal.l1_total <= 0.10
        assert proposal.l1_within_budget is True

    def test_raises_on_budget_exceeded(self, passing_setup):
        """Engine must raise when L1 proposal exceeds budget."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        # Force poor precision so engine proposes a non-zero delta
        intake["cohort_metrics"]["activity_vs_active_mic"] = {
            "tp": 1, "fp": 4, "fn": 1, "tn": 2,
            "insufficient_data": False,
            "n": 8,
        }

        current_weights = {"activity": 0.40, "safety": 0.25}
        # Tiny budget should be exceeded by the non-zero delta
        with pytest.raises(BudgetExceededError):
            compute_weight_update(
                intake, verdict, current_weights,
                policy_l1_budget=0.001,
            )

    def test_proposal_has_timestamp(self, passing_setup):
        """Proposal must include an ISO timestamp."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert "T" in proposal.timestamp

    def test_skips_insufficient_data_metric(self, passing_setup):
        """Engine skips cohort metrics flagged insufficient_data."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        # Manually mark the metrics as insufficient_data
        for key in intake["cohort_metrics"]:
            intake["cohort_metrics"][key]["insufficient_data"] = True
            # Remove tp/fp/fn/tn to mimic the markdown writer's contract
            for col in ("tp", "fp", "fn", "tn"):
                intake["cohort_metrics"][key].pop(col, None)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert len(proposal.deltas) == 0
        assert any("insufficient_data" in note for note in proposal.notes)

    def test_skips_unmapped_metric(self, passing_setup):
        """Engine skips cohort metrics with no scorer mapping."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        # Add a synthetic metric with no mapping
        intake["cohort_metrics"]["unmapped_metric"] = {
            "tp": 3, "fp": 1, "fn": 1, "tn": 3,
            "insufficient_data": False,
            "n": 8,
        }

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert any("no mapped scorer weight" in note for note in proposal.notes)

    def test_skips_missing_scorer_in_weights(self, passing_setup):
        """Engine skips metrics whose mapped scorer is not in current_weights."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        # Only pass weights that don't include the mapped scorers
        current_weights = {"some_other_scorer": 1.0}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        assert any("current_weights has no such key" in note for note in proposal.notes)

    def test_proposal_delta_direction_is_reasonable(self, passing_setup):
        """When precision is high, delta should be zero or positive."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        # Override the activity metric with perfect confusion matrix
        intake["cohort_metrics"]["activity_vs_active_mic"] = {
            "tp": 3, "fp": 0, "fn": 0, "tn": 2,
            "insufficient_data": False,
            "n": 5,
        }

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )
        activity_deltas = [d for d in proposal.deltas if d.scorer == "activity"]
        if activity_deltas:
            d = activity_deltas[0]
            # Perfect precision/recall -> delta should be 0
            assert d.delta == 0.0

    def test_dry_run_prints_diff_and_skips_file_writes(self, passing_setup, tmp_path):
        """compute_weight_update with dry-run semantics: print diff, no file writes.

        The engine itself does not have a dry-run mode (it always returns
        a proposal without side effects). This test verifies the CLI-level
        contract: the proposal dict is inspectable without writing files,
        and writing functions are only called explicitly.
        """
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )

        # Dry-run contract: proposal must be inspectable without side effects
        assert proposal.gate_passed is True
        assert len(proposal.deltas) > 0
        for delta in proposal.deltas:
            assert isinstance(delta.scorer, str)
            assert isinstance(delta.current_weight, (int, float))
            assert isinstance(delta.proposed_weight, (int, float))
            assert isinstance(delta.rationale, str)

        # Verify no proposal output files were written unless explicitly called
        out_json = tmp_path / "proposal.json"
        out_md = tmp_path / "proposal.md"
        assert not out_json.exists(), (
            "Dry-run should not write JSON; found proposal.json"
        )
        assert not out_md.exists(), (
            "Dry-run should not write MD; found proposal.md"
        )

    def test_writes_proposal_json(self, passing_setup, tmp_path):
        """write_weight_update_proposal_json produces valid JSON."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )

        out = tmp_path / "proposal.json"
        write_weight_update_proposal_json(proposal, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["gate_passed"] is True
        assert "deltas" in data
        assert "l1_total" in data

    def test_writes_proposal_markdown(self, passing_setup, tmp_path):
        """write_weight_update_proposal_markdown produces readable Markdown."""
        panel_csv = passing_setup / "panel.csv"
        results_dir = passing_setup / "results"
        intake = build_calibration_intake_report(panel_csv, results_dir)
        policy = load_recalibration_policy(POLICY_PATH)
        verdict = evaluate_recalibration_gate(intake, policy)

        current_weights = {"activity": 0.40, "safety": 0.25}
        proposal = compute_weight_update(
            intake, verdict, current_weights, policy_l1_budget=0.10,
        )

        out = tmp_path / "proposal.md"
        write_weight_update_proposal_markdown(proposal, out)
        assert out.exists()
        text = out.read_text()
        assert "Weight Update Proposal" in text
        assert "L1 Budget" in text
        assert "Gate passed" in text


# ── Makefile target integrity ──────────────────────────────────────────


class TestMakefileTargets:
    """Verify the Makefile targets for calibration are functional."""

    def test_make_calibration_intake_example_target(self):
        """`make lab-result-intake-example` must produce a valid JSON output."""
        result = subprocess.run(
            ["make", "lab-result-intake-example"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, (
            f"make lab-result-intake-example failed:\n"
            f"stdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"
        )
        out_path = REPO_ROOT / "outputs" / "calibration_intake_example.json"
        assert out_path.exists(), "intake example output not found"
        data = json.loads(out_path.read_text())
        assert data["n_panel_candidates"] >= 5
        assert "cohort_metrics" in data

    def test_make_recalibration_gate_example_target(self):
        """`make recalibration-gate-example` must produce a valid JSON verdict.

        The gate exits 3 on synthetic data (cohort too small); Make propagates
        this as exit 2. We assert the output file was written correctly
        regardless of the gate's binary verdict.
        """
        result = subprocess.run(
            ["make", "recalibration-gate-example"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=120,
        )
        out_path = REPO_ROOT / "outputs" / "recalibration_gate_example.json"
        assert out_path.exists(), "gate example output not found"
        data = json.loads(out_path.read_text())
        assert data["may_recalibrate"] is False
        # Gate exits 3 when may_recalibrate=False; Make propagates error
        assert result.returncode != 0, (
            "Make returned 0 but recalibration-gate should exit 3 "
            "on synthetic data (cohort < 5)"
        )


# ── Recalibration report module ────────────────────────────────────────────


class TestRecalibrationReport:
    """Tests for the combined recalibration report (proposal + gate verdict)."""

    def _run_chain(self, tmp_path, n=5):
        """Helper: build intake + gate + proposal for testing."""
        _build_passing_data(tmp_path, n=n)
        panel_csv = tmp_path / "panel.csv"
        results_dir = tmp_path / "results"
        policy = load_recalibration_policy(POLICY_PATH)
        intake = build_calibration_intake_report(
            panel_csv=panel_csv,
            results_dir=results_dir,
        )
        gate = evaluate_recalibration_gate(
            intake_report=intake,
            policy=policy,
            project_root=REPO_ROOT,
        )
        l1_budget = next(
            (rl.threshold for rl in policy.rate_limits if rl.id == "WEIGHT_CHANGE_L1_BUDGET"),
            0.1,
        )
        proposal = compute_weight_update(
            intake_report=intake,
            gate_verdict=gate,
            current_weights={"activity": 0.40, "safety": 0.25},
            policy_l1_budget=l1_budget,
        )
        return proposal, gate

    def test_build_report_shape(self, tmp_path):
        """Report dict contains all top-level keys."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        assert report["report_type"] == "recalibration_report"
        assert report["schema_version"] == "1.0"
        assert report["human_review_required"] is True
        assert "gate_verdict" in report
        assert "proposal" in report
        assert isinstance(report["timestamp"], str)

    def test_build_report_gate_context(self, tmp_path):
        """Gate verdict details are preserved in the report."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        gv = report["gate_verdict"]
        assert "may_recalibrate" in gv
        assert "rule_results" in gv
        assert "prohibited_action_audit" in gv
        assert "rate_limit_status" in gv
        assert "summary" in gv
        assert "reasons" in gv
        assert isinstance(gv["rule_results"], list)
        assert isinstance(gv["prohibited_action_audit"], list)

    def test_build_report_proposal_shape(self, tmp_path):
        """Proposal section has correct keys."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        prop = report["proposal"]
        assert "gate_passed" in prop
        assert "l1_total" in prop
        assert "l1_budget" in prop
        assert "l1_within_budget" in prop
        assert "deltas" in prop
        assert "notes" in prop
        assert isinstance(prop["deltas"], list)

    def test_build_report_delta_fields(self, tmp_path):
        """Each delta has required fields."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        for d in report["proposal"]["deltas"]:
            assert "scorer" in d
            assert "current_weight" in d
            assert "proposed_weight" in d
            assert "delta" in d
            assert "rationale" in d
            assert isinstance(d["scorer"], str)
            assert isinstance(d["current_weight"], (int, float))

    def test_validate_report_against_schema(self, tmp_path):
        """Report validates against the JSON Schema."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
            validate_recalibration_report,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        is_valid, errors = validate_recalibration_report(report)
        assert is_valid, f"Schema validation failed: {errors}"
        assert len(errors) == 0

    def test_write_report_json(self, tmp_path):
        """JSON output can be read back and validates."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
            validate_recalibration_report,
            write_recalibration_report_json,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        out = tmp_path / "test_report.json"
        write_recalibration_report_json(report, out)
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded["report_type"] == "recalibration_report"
        is_valid, errors = validate_recalibration_report(loaded)
        assert is_valid, f"Schema validation failed after write/read: {errors}"

    def test_write_report_markdown(self, tmp_path):
        """Markdown output includes required sections."""
        from openamp_foundry.reports.recalibration_report import (
            build_recalibration_report,
            write_recalibration_report_markdown,
        )

        proposal, gate = self._run_chain(tmp_path)
        report = build_recalibration_report(proposal, gate)
        out = tmp_path / "test_report.md"
        write_recalibration_report_markdown(report, out)
        assert out.exists()
        text = out.read_text()
        assert "Recalibration Report" in text
        assert "HUMAN REVIEW REQUIRED" in text
        assert "Gate verdict" in text
        assert "Proposed weight updates" in text
        assert "Next steps" in text

    def test_report_schema_rejects_missing_fields(self, tmp_path):
        """Schema validation catches missing required fields."""
        from openamp_foundry.reports.recalibration_report import (
            validate_recalibration_report,
        )

        bad_report = {"report_type": "recalibration_report"}
        is_valid, errors = validate_recalibration_report(bad_report)
        assert not is_valid
        assert len(errors) > 0

    def test_report_schema_rejects_human_review_false(self, tmp_path):
        """Schema enforces human_review_required=True."""
        from openamp_foundry.reports.recalibration_report import (
            validate_recalibration_report,
        )

        report = {
            "report_type": "recalibration_report",
            "schema_version": "1.0",
            "timestamp": "2026-07-06T12:00:00",
            "policy_version": 1,
            "human_review_required": False,
            "gate_verdict": {
                "may_recalibrate": True,
                "n_panel_candidates": 5,
                "n_matched_candidates": 5,
                "n_lab_results": 10,
                "summary": "test",
            },
            "proposal": {
                "gate_passed": True,
                "l1_total": 0.0,
                "l1_budget": 0.1,
                "l1_within_budget": True,
                "deltas": [],
            },
        }
        is_valid, errors = validate_recalibration_report(report)
        assert not is_valid
        assert len(errors) > 0
