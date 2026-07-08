"""Tests for simulation mode in rank CLI."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from openamp_foundry.evidence.schemas import validate_json_schema

DEMO_CANDIDATES = "examples/sequences/demo_candidates.csv"
DEMO_REFS = "examples/known_reference/demo_known_amps.csv"
CERT_SCHEMA = Path(__file__).parents[2] / "schemas" / "candidate.schema.json"


def test_simulation_mode_off_default_has_no_sim_scores():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        line = out.read_text().splitlines()[0]
        data = json.loads(line)
        scores = data["scores"]
        sim_keys = [k for k in scores if k.startswith("sim_")]
        assert len(sim_keys) == 0, f"Expected no sim_ keys, got: {sim_keys}"


def test_simulation_mode_info_adds_sim_scores():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        line = out.read_text().splitlines()[0]
        data = json.loads(line)
        scores = data["scores"]
        for key in ["sim_bacterial_binding", "sim_selectivity_ratio",
                     "sim_helix_weight", "sim_non_helical",
                     "sim_membrane_uncertainty", "sim_structure_uncertainty",
                     "sim_max_uncertainty"]:
            assert key in scores, f"Missing simulation key: {key}"
            assert isinstance(scores[key], (int, float))


def test_simulation_mode_info_scores_in_range():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        lines = out.read_text().splitlines()
        for line in lines:
            data = json.loads(line)
            scores = data["scores"]
            for key in ["sim_bacterial_binding", "sim_selectivity_ratio",
                         "sim_helix_weight", "sim_coil_weight", "sim_sheet_weight",
                         "sim_membrane_uncertainty", "sim_structure_uncertainty",
                         "sim_max_uncertainty"]:
                assert 0.0 <= scores[key] <= 1.5 or key == "sim_selectivity_ratio" and 0.0 <= scores[key] <= 2.0


def test_simulation_mode_info_report_contains_sim():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        report = Path(tmp) / "report.md"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--report", str(report),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        report_text = report.read_text()
        assert "Sim bacterial binding" in report_text
        assert "Sim helix weight" in report_text
        assert "Sim non helical" in report_text
        assert "Sim max uncertainty" in report_text


def test_simulation_mode_info_output_json_has_simulation_mode():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        report = Path(tmp) / "report.md"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--report", str(report),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["simulation_mode"] == "info"


def test_all_candidates_have_sim_scores_in_info_mode():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0
        lines = out.read_text().splitlines()
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert "sim_bacterial_binding" in data["scores"], f"Candidate {i} missing sim_bacterial_binding"


def test_fail_closed_adds_failure_mode_for_high_uncertainty():
    """Pipeline must add failure mode when simulation uncertainty exceeds 0.5."""
    import csv
    with tempfile.TemporaryDirectory() as tmp:
        high_unc_csv = Path(tmp) / "high_unc.csv"
        with open(high_unc_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "sequence", "source"])
            w.writerow(["HIGH-UNC-001", "A", "test"])
            w.writerow(["HIGH-UNC-002", "AA", "test"])
            w.writerow(["HIGH-UNC-003", "GGG", "test"])
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", str(high_unc_csv),
             "--out", str(out),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0, f"Pipeline crashed: {result.stderr[:300]}"
        lines = out.read_text().splitlines()
        high_uncertainty_found = False
        for line in lines:
            data = json.loads(line)
            failure_modes = data.get("known_failure_modes", [])
            for mode in failure_modes:
                if "uncertainty exceeds 0.5" in mode:
                    high_uncertainty_found = True
                    break
        assert high_uncertainty_found, (
            "Expected at least one candidate with failure mode for "
            "simulation uncertainty > 0.5"
        )


def test_fail_closed_pipeline_does_not_crash_on_simulation_edge_cases():
    """Pipeline must complete without crashing for edge-case sequences."""
    import csv
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        edge_csv = Path(tmp) / "edge_cases.csv"
        with open(edge_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "sequence", "source"])
            w.writerow(["EDGE-001", "A", "test"])
            w.writerow(["EDGE-002", "GG", "test"])
            w.writerow(["EDGE-003", "K" * 50, "test"])
            w.writerow(["EDGE-004", "P" * 10, "test"])
            w.writerow(["EDGE-005", "CCCCCCCCCC", "test"])
        out = Path(tmp) / "ranked.jsonl"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", str(edge_csv),
             "--out", str(out),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert result.returncode == 0, f"Pipeline crashed: {result.stderr[:300]}"
        lines = out.read_text().splitlines()
        assert len(lines) == 5, f"Expected 5 candidates, got {len(lines)}"


def test_simulation_mode_info_evidence_certificates_include_uncertainty():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ranked.jsonl"
        certs = Path(tmp) / "certs"
        result = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", DEMO_CANDIDATES,
             "--references", DEMO_REFS,
             "--out", str(out),
             "--cert-dir", str(certs),
             "--simulation-mode", "info"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )

        assert result.returncode == 0
        cert_paths = sorted(certs.glob("*.json"))
        assert cert_paths, "Expected selected-candidate certificates"
        cert = json.loads(cert_paths[0].read_text())
        validate_json_schema(cert, CERT_SCHEMA)
        scores = cert["scores"]
        assert "sim_membrane_uncertainty" in scores
        assert "sim_structure_uncertainty" in scores
        assert "sim_max_uncertainty" in scores
        assert 0.0 <= scores["sim_max_uncertainty"] <= 1.0
