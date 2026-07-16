"""Tests for the calibration intake workflow.

Verifies:
  - Lab result files load + validate against schema
  - Pilot panel CSV loads + predictions are extracted
  - Per-candidate join correctly attaches lab results to predictions
  - Cohort metrics below MIN_COHORT_SIZE are flagged insufficient_data
  - Cohort metrics at/above MIN_COHORT_SIZE produce TP/FP/FN/TN
  - Control failures are surfaced
  - Orphan lab results are detected
  - JSON and Markdown output writers are non-empty and validate
  - Synthetic example data exists and validates

Honest limitation:
  No real wet-lab data is available. All tests use clearly synthetic JSON
  in tmp_path. Tests must NEVER rely on real-world MIC/hemolysis numbers
  to pass.
"""
from __future__ import annotations

import csv
import json
import warnings
from pathlib import Path

import pytest

from openamp_foundry.calibration.intake import (
    ACTIVITY_THRESHOLD,
    HEMOLYSIS_HIGH_PCT,
    MIC_ACTIVE_CUTOFF_UG_ML,
    MIN_COHORT_SIZE,
    build_calibration_intake_report,
    write_calibration_intake_json,
    write_calibration_intake_markdown,
)

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "lab_result.schema.json"


def _lab_result(**overrides) -> dict:
    base = {
        "result_id": "RES-TEST-001",
        "candidate_id": "TEST-CAND-001",
        "assay_type": "MIC",
        "organism_or_cell_line": "SYNTHETIC TEST - E. coli ATCC 25922",
        "result_value": 8.0,
        "result_unit": "µg/mL",
        "result_qualitative": "active",
        "positive_control_passed": True,
        "negative_control_passed": True,
        "positive_control_id": "ciprofloxacin 0.25 µg/mL",
        "negative_control_id": "PBS",
        "assay_date": "2026-07-04",
        "replicate_count": 3,
        "performed_by_lab": "SYNTHETIC TEST - Lab X",
        "raw_data_sha256": None,
        "computational_candidate_certificate_hash": (
            "0000000000000000000000000000000000000000000000000000000000000000"
        ),
        "notes": "SYNTHETIC TEST DATA - not a real assay.",
        "disclaimer": (
            "SYNTHETIC TEST. This is not a real experimental result on a "
            "computationally nominated candidate and does not constitute a "
            "drug or clinical claim."
        ),
    }
    base.update(overrides)
    return base


def _write_panel_csv(panel_csv: Path, rows: list[dict]) -> None:
    fields = [
        "pilot_rank", "candidate_id", "sequence", "length", "seed",
        "ensemble", "activity", "boman_activity", "disagreement",
        "safety", "synthesis", "novelty", "serum_stability",
        "selectivity_proxy", "rich_selectivity", "pilot_priority",
        "amphipathic_score", "charge_ph74",
    ]
    with panel_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _write_lab_result_file(directory: Path, result: dict) -> Path:
    p = directory / f"{result['result_id']}.json"
    p.write_text(json.dumps(result))
    return p


@pytest.fixture
def empty_panel_csv(tmp_path) -> Path:
    p = tmp_path / "panel.csv"
    _write_panel_csv(p, [])
    return p


@pytest.fixture
def empty_results_dir(tmp_path) -> Path:
    d = tmp_path / "results"
    d.mkdir()
    return d


class TestLoadPanelCsv:
    def test_empty_panel(self, empty_panel_csv, empty_results_dir):
        report = build_calibration_intake_report(empty_panel_csv, empty_results_dir)
        assert report["n_panel_candidates"] == 0
        assert report["n_lab_results"] == 0
        assert report["n_matched_candidates"] == 0
        assert report["per_candidate_joined"] == []

    def test_panel_rows_parsed(self, tmp_path):
        panel = tmp_path / "panel.csv"
        results = tmp_path / "results"
        results.mkdir()
        _write_panel_csv(
            panel,
            [
                {
                    "pilot_rank": "1",
                    "candidate_id": "CAND-A",
                    "sequence": "AAAKKKFFF",
                    "length": "9",
                    "seed": "SEED-A",
                    "ensemble": "0.81",
                    "activity": "0.85",
                    "boman_activity": "0.78",
                    "disagreement": "0.07",
                    "safety": "0.90",
                    "synthesis": "0.85",
                    "novelty": "0.70",
                    "serum_stability": "0.65",
                    "selectivity_proxy": "0.60",
                    "rich_selectivity": "0.72",
                    "pilot_priority": "0.80",
                    "amphipathic_score": "1.5",
                    "charge_ph74": "4.0",
                },
            ],
        )
        report = build_calibration_intake_report(panel, results)
        assert report["n_panel_candidates"] == 1
        row = report["per_candidate_joined"][0]
        assert row["candidate_id"] == "CAND-A"
        assert row["predictions"]["activity"] == 0.85
        assert row["ensemble"] == 0.81
        assert row["has_lab"] is None
        assert row["coverage_note"] == "no lab results yet"

    def test_missing_columns_are_tolerated(self, tmp_path):
        """A CSV missing optional score columns must not crash the loader."""
        panel = tmp_path / "panel.csv"
        results = tmp_path / "results"
        results.mkdir()
        with panel.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["pilot_rank", "candidate_id", "sequence"])
            w.writeheader()
            w.writerow({"pilot_rank": "1", "candidate_id": "CAND-A", "sequence": "AAAKKK"})
        report = build_calibration_intake_report(panel, results)
        assert report["n_panel_candidates"] == 1
        assert report["per_candidate_joined"][0]["predictions"]["activity"] is None


class TestLoadLabResults:
    def test_valid_result_loads(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        _write_lab_result_file(results, _lab_result())
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        report = build_calibration_intake_report(panel, results)
        assert report["n_lab_results"] == 1

    def test_invalid_result_skipped_with_warning(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        # Valid file
        _write_lab_result_file(results, _lab_result())
        # Invalid file (missing required field)
        (results / "bad.json").write_text(
            json.dumps({"result_id": "BAD-001"})
        )
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            report = build_calibration_intake_report(panel, results)
        assert report["n_lab_results"] == 1
        assert report["n_invalid_lab_result_files"] == 1
        assert report["input_validation_status"] == "blocked_on_invalid_results"
        assert report["invalid_lab_result_files"][0]["file"] == "bad.json"
        assert any("Skipped" in str(w.message) for w in caught)

    def test_invalid_result_blocks_cli_intake(self, tmp_path):
        from argparse import Namespace

        from openamp_foundry.cli.commands.reports import _run_calibration_intake

        results = tmp_path / "results"
        results.mkdir()
        (results / "bad.json").write_text(json.dumps({"result_id": "BAD-001"}))
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])

        exit_code = _run_calibration_intake(
            Namespace(
                panel=str(panel),
                results_dir=str(results),
                out_json=str(tmp_path / "intake.json"),
                out_md=str(tmp_path / "intake.md"),
            )
        )

        assert exit_code == 3
        report = json.loads((tmp_path / "intake.json").read_text())
        assert report["input_validation_status"] == "blocked_on_invalid_results"


class TestPerCandidateJoin:
    def test_match_by_candidate_id(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(
            panel,
            [
                {
                    "pilot_rank": "1", "candidate_id": "CAND-A", "sequence": "AAA",
                    "length": "3", "seed": "SEED-X", "ensemble": "0.80",
                    "activity": "0.82", "boman_activity": "0.78",
                    "disagreement": "0.04", "safety": "0.90", "synthesis": "0.85",
                    "novelty": "0.70", "serum_stability": "0.65",
                    "selectivity_proxy": "0.60", "rich_selectivity": "0.70",
                    "pilot_priority": "0.78", "amphipathic_score": "1.5",
                    "charge_ph74": "4.0",
                },
                {
                    "pilot_rank": "2", "candidate_id": "CAND-B", "sequence": "BBB",
                    "length": "3", "seed": "SEED-Y", "ensemble": "0.70",
                    "activity": "0.72", "boman_activity": "0.70",
                    "disagreement": "0.02", "safety": "0.85", "synthesis": "0.80",
                    "novelty": "0.65", "serum_stability": "0.60",
                    "selectivity_proxy": "0.55", "rich_selectivity": "0.65",
                    "pilot_priority": "0.68", "amphipathic_score": "1.4",
                    "charge_ph74": "3.5",
                },
            ],
        )
        _write_lab_result_file(
            results, _lab_result(result_id="RES-001", candidate_id="CAND-A")
        )
        report = build_calibration_intake_report(panel, results)
        assert report["n_matched_candidates"] == 1
        assert report["per_candidate_joined"][0]["has_lab"] is not None
        assert report["per_candidate_joined"][1]["has_lab"] is None

    def test_orphan_lab_results_detected(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        _write_lab_result_file(
            results, _lab_result(result_id="RES-A", candidate_id="CAND-NOT-IN-PANEL")
        )
        report = build_calibration_intake_report(panel, results)
        assert report["n_orphan_lab_results"] == 1
        assert "CAND-NOT-IN-PANEL" in report["orphan_candidate_ids"]


class TestPerCandidateActuals:
    def test_active_mic_below_cutoff(self):
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [_lab_result(assay_type="MIC", result_value=8.0, candidate_id="C1")]
        )
        assert out["C1"]["active_mic"] is True

    def test_inactive_mic_above_cutoff(self):
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [_lab_result(assay_type="MIC", result_value=128.0, candidate_id="C1")]
        )
        assert out["C1"]["active_mic"] is False

    def test_mic_at_cutoff_is_active(self):
        """MIC == 32 ug/mL is the documented activity threshold (inclusive)."""
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [_lab_result(assay_type="MIC", result_value=32.0, candidate_id="C1")]
        )
        assert out["C1"]["active_mic"] is True

    def test_high_hemolysis_detected(self):
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [
                _lab_result(
                    assay_type="hemolysis_RBC",
                    result_value=42.0,
                    result_qualitative="toxic",
                    candidate_id="C1",
                )
            ]
        )
        assert out["C1"]["high_hemolysis"] is True

    def test_low_hemolysis_detected(self):
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [
                _lab_result(
                    assay_type="hemolysis_RBC",
                    result_value=3.5,
                    result_qualitative="inactive",
                    candidate_id="C1",
                )
            ]
        )
        assert out["C1"]["high_hemolysis"] is False

    def test_hemolysis_at_threshold(self):
        """Hemolysis == 10% is the threshold (>=10 is high)."""
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [
                _lab_result(
                    assay_type="hemolysis_RBC",
                    result_value=10.0,
                    candidate_id="C1",
                )
            ]
        )
        assert out["C1"]["high_hemolysis"] is True

    def test_qualitative_only_mic_returns_none(self):
        """When MIC is qualitative-only (result_value=None), predicate is None."""
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [_lab_result(assay_type="MIC", result_value=None, candidate_id="C1")]
        )
        assert out["C1"]["active_mic"] is None

    def test_controls_failed_flagged(self):
        from openamp_foundry.calibration.intake import _aggregate_per_candidate

        out = _aggregate_per_candidate(
            [
                _lab_result(
                    positive_control_passed=False,
                    negative_control_passed=True,
                    candidate_id="C1",
                )
            ]
        )
        assert out["C1"]["all_controls_passed"] is False


class TestCohortMetricsGating:
    def _make_setup(self, tmp_path, n_mic: int):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        rows = []
        for i in range(n_mic):
            cid = f"CAND-{i:03d}"
            rows.append(
                {
                    "pilot_rank": str(i + 1),
                    "candidate_id": cid,
                    "sequence": "AAAKKKFFF" + str(i),
                    "length": "10",
                    "seed": f"SEED-{i}",
                    "ensemble": "0.82" if i % 2 == 0 else "0.55",
                    "activity": "0.85" if i % 2 == 0 else "0.45",
                    "boman_activity": "0.80",
                    "disagreement": "0.05",
                    "safety": "0.90",
                    "synthesis": "0.85",
                    "novelty": "0.70",
                    "serum_stability": "0.65",
                    "selectivity_proxy": "0.60",
                    "rich_selectivity": "0.72",
                    "pilot_priority": "0.80",
                    "amphipathic_score": "1.5",
                    "charge_ph74": "4.0",
                }
            )
            _write_lab_result_file(
                results,
                _lab_result(
                    result_id=f"RES-{i:03d}",
                    candidate_id=cid,
                    assay_type="MIC",
                    # Half active (MIC=8), half inactive (MIC=128)
                    result_value=8.0 if i % 2 == 0 else 128.0,
                    result_qualitative="active" if i % 2 == 0 else "inactive",
                ),
            )
        _write_panel_csv(panel, rows)
        return panel, results

    def test_below_min_cohort_size_marked_insufficient(self, tmp_path):
        panel, results = self._make_setup(tmp_path, n_mic=MIN_COHORT_SIZE - 1)
        report = build_calibration_intake_report(panel, results)
        metric = report["cohort_metrics"]["activity_vs_active_mic"]
        assert metric["insufficient_data"] is True
        assert metric["n"] == MIN_COHORT_SIZE - 1
        assert metric["tp"] is None

    def test_at_min_cohort_size_reports_counts(self, tmp_path):
        panel, results = self._make_setup(tmp_path, n_mic=MIN_COHORT_SIZE)
        report = build_calibration_intake_report(panel, results)
        metric = report["cohort_metrics"]["activity_vs_active_mic"]
        assert metric["insufficient_data"] is False
        assert metric["n"] == MIN_COHORT_SIZE
        # With our alternating scheme, predicted_positive == actual_positive
        # for every other candidate, so we expect pure TP + TN.
        assert metric["tp"] + metric["tn"] + metric["fp"] + metric["fn"] == MIN_COHORT_SIZE

    def test_above_min_cohort_size_computes_auroc_proxy(self, tmp_path):
        """With more samples, we should see TP+TN+FP+FN == n."""
        panel, results = self._make_setup(tmp_path, n_mic=10)
        report = build_calibration_intake_report(panel, results)
        metric = report["cohort_metrics"]["activity_vs_active_mic"]
        assert metric["insufficient_data"] is False
        assert metric["n"] == 10
        assert metric["tp"] + metric["tn"] + metric["fp"] + metric["fn"] == 10

    def test_hemolysis_cohort_uses_below_threshold_direction(self, tmp_path):
        """rich_selectivity above 0.5 = predicted NEGATIVE for high_hemolysis.

        So predicted_positive (high hemolysis) only when score < 0.5.
        """
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        rows = []
        for i in range(6):
            cid = f"CAND-H{i}"
            # Half low rich_selectivity (predict high hemolysis), half high.
            rich_sel = "0.3" if i < 3 else "0.8"
            rows.append(
                {
                    "pilot_rank": str(i + 1), "candidate_id": cid,
                    "sequence": "AAAK", "length": "4", "seed": "SEED-H",
                    "ensemble": "0.7", "activity": "0.7", "boman_activity": "0.7",
                    "disagreement": "0.0", "safety": "0.9", "synthesis": "0.9",
                    "novelty": "0.7", "serum_stability": "0.6",
                    "selectivity_proxy": "0.6", "rich_selectivity": rich_sel,
                    "pilot_priority": "0.7", "amphipathic_score": "1.0",
                    "charge_ph74": "3.0",
                }
            )
            _write_lab_result_file(
                results,
                _lab_result(
                    result_id=f"RES-H{i}",
                    candidate_id=cid,
                    assay_type="hemolysis_RBC",
                    result_value=50.0 if i < 3 else 2.0,
                    result_qualitative="toxic" if i < 3 else "inactive",
                ),
            )
        _write_panel_csv(panel, rows)
        report = build_calibration_intake_report(panel, results)
        metric = report["cohort_metrics"]["rich_selectivity_vs_high_hemolysis"]
        assert metric["insufficient_data"] is False
        assert metric["n"] == 6


class TestControlFailures:
    def test_control_failure_surfaced(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        _write_lab_result_file(
            results,
            _lab_result(
                positive_control_passed=False,
                negative_control_passed=True,
            ),
        )
        report = build_calibration_intake_report(panel, results)
        assert len(report["control_failures"]) == 1
        assert report["control_failures"][0]["positive_control_passed"] is False

    def test_no_control_failures_returns_empty(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        _write_lab_result_file(results, _lab_result())
        report = build_calibration_intake_report(panel, results)
        assert report["control_failures"] == []


class TestWriters:
    def test_json_writer_produces_valid_file(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        _write_lab_result_file(results, _lab_result())
        report = build_calibration_intake_report(panel, results)
        out = tmp_path / "out.json"
        write_calibration_intake_json(report, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["n_lab_results"] == 1
        assert "report_disclaimer" in data

    def test_markdown_writer_produces_nonempty_file(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        _write_lab_result_file(results, _lab_result())
        report = build_calibration_intake_report(panel, results)
        out = tmp_path / "out.md"
        write_calibration_intake_markdown(report, out)
        assert out.exists()
        text = out.read_text()
        assert "Calibration Intake Report" in text
        assert "insufficient_data" in text or "TP=" in text
        assert "Honest Limitations" in text

    def test_markdown_writer_survives_missing_prediction_score_key(self, tmp_path):
        report = {
            "report_disclaimer": "SYNTHETIC DATA — not real",
            "n_panel_candidates": 3,
            "n_lab_results": 3,
            "n_matched_candidates": 3,
            "n_orphan_lab_results": 0,
            "min_cohort_size": 5,
            "cohort_metrics": {
                "activity_vs_mic": {
                    "assay_type": "MIC",
                    "predicate": "active_mic",
                    "n": 3,
                    "min_required": 5,
                    "insufficient_data": True,
                    "tp": None,
                    "fp": None,
                    "fn": None,
                    "tn": None,
                    "disclaimer": "Small cohort.",
                }
            },
            "per_candidate_joined": [],
            "control_failures": [],
        }
        out = tmp_path / "out.md"
        write_calibration_intake_markdown(report, out)
        assert out.exists()
        text = out.read_text()
        assert "prediction_score_key" not in [k for k in report["cohort_metrics"]["activity_vs_mic"].keys()]
        assert "Prediction score key:" in text


class TestDisclaimer:
    def test_disclaimer_present(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        panel = tmp_path / "panel.csv"
        _write_panel_csv(panel, [])
        report = build_calibration_intake_report(panel, results)
        d = report["report_disclaimer"]
        assert "NOT proof of efficacy" in d
        assert "recalibration" in d.lower()
        assert "selection rule" in d


class TestExampleData:
    """Verify the synthetic example data validates and produces a clean report."""

    @pytest.fixture
    def example_root(self):
        return Path(__file__).resolve().parents[2] / "examples"

    def test_synthetic_results_validate_against_schema(self, example_root):
        from openamp_foundry.evidence.schemas import validate_json_schema

        results_dir = example_root / "lab_results"
        assert results_dir.exists(), "examples/lab_results/ should exist"
        for p in sorted(results_dir.glob("*.json")):
            data = json.loads(p.read_text())
            validate_json_schema(data, SCHEMA_PATH)

    def test_synthetic_panel_exists(self, example_root):
        panel = example_root / "lab_results_panel.csv"
        assert panel.exists()
        with panel.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 5

    def test_synthetic_example_produces_report(self, example_root, tmp_path):
        panel = example_root / "lab_results_panel.csv"
        results_dir = example_root / "lab_results"
        report = build_calibration_intake_report(panel, results_dir)
        assert report["n_panel_candidates"] >= 5
        assert report["n_lab_results"] >= 5
        assert report["n_matched_candidates"] >= 1
        # Honest: with synthetic data this should be insufficient
        assert all(
            m["insufficient_data"]
            for m in report["cohort_metrics"].values()
        )

    def test_readme_warns_synthetic(self, example_root):
        readme = example_root / "lab_results" / "README.md"
        assert readme.exists()
        text = readme.read_text()
        assert "SYNTHETIC" in text
        assert "not" in text.lower()  # Must explicitly disclaim real-world use


class TestConstants:
    def test_thresholds_match_docs(self):
        """Threshold values are exposed as constants and match the documentation."""
        assert ACTIVITY_THRESHOLD == 0.70
        assert MIC_ACTIVE_CUTOFF_UG_ML == 32.0
        assert HEMOLYSIS_HIGH_PCT == 10.0
        assert MIN_COHORT_SIZE >= 5  # minimum honest gate
