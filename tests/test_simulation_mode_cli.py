"""Tests for simulation mode in rank CLI."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from openamp_foundry.evidence.schemas import validate_json_schema

DEMO_CANDIDATES = "examples/sequences/demo_candidates.csv"
DEMO_REFS = "examples/known_reference/demo_known_amps.csv"
CERT_SCHEMA = Path(__file__).parents[1] / "schemas" / "candidate.schema.json"


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
