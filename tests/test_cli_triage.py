"""CLI integration test for the triage benchmark command."""

import json
from pathlib import Path

import pytest

from openamp_foundry.cli.main import main


def test_bench_triage_cli(tmp_path, capsys):
    """bench triage CLI must return per-scorer pairwise AUROCs."""
    hemo_csv = Path("examples/validation/hemolysis_reference.csv")
    decoy_csv = Path("examples/validation/random_background.csv")
    if not hemo_csv.exists() or not decoy_csv.exists():
        pytest.skip("Triage benchmark data not found — run from project root")
    out = str(tmp_path / "triage_report.json")
    rc = main([
        "bench", "triage",
        "--hemolysis-csv", str(hemo_csv),
        "--decoy-csv", str(decoy_csv),
        "--n-bootstrap", "100",
        "--out", out,
    ])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "ok"
    assert data["benchmark"] == "multi_class_triage"
    assert data["n_selective"] > 0
    assert data["n_hemolytic"] > 0
    assert data["n_decoy"] > 0
    assert "ensemble" in data["per_scorer"]
    assert "expert_composite" in data["per_scorer"]
    assert "triage_score" in data["per_scorer"]
    assert "selective_vs_hemolytic" in data["per_scorer"]["ensemble"]
