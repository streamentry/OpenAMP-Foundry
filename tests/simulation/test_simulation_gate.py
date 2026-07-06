"""Tests for the simulation weighted-mode permission gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from openamp_foundry.simulation.gate import (
    MIN_AMP_VS_DECOY_DELTA,
    MIN_WITHIN_AMP_DELTA,
    evaluate_simulation_gate,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_simulation_gate_blocks_current_ablation_results(tmp_path: Path) -> None:
    amp = tmp_path / "amp.json"
    within = tmp_path / "within.json"
    _write_json(amp, {"results": {"verdict": "NO_IMPROVEMENT", "delta": -0.1153}})
    _write_json(within, {"results": {"verdict": "NO_IMPROVEMENT", "delta": -0.0995}})

    verdict = evaluate_simulation_gate(
        amp_vs_decoy_path=amp,
        within_amp_path=within,
    )

    assert verdict.may_use_weighted_mode is False
    assert verdict.integration_mode == "info"
    assert verdict.checks["amp_vs_decoy_improves"] is False
    assert verdict.checks["within_amp_improves"] is False
    assert len(verdict.reasons) == 2


def test_simulation_gate_allows_weighted_only_on_double_improvement(tmp_path: Path) -> None:
    amp = tmp_path / "amp.json"
    within = tmp_path / "within.json"
    _write_json(
        amp,
        {"results": {"verdict": "IMPROVEMENT", "delta": MIN_AMP_VS_DECOY_DELTA + 0.0100}},
    )
    _write_json(
        within,
        {"results": {"verdict": "IMPROVEMENT", "delta": MIN_WITHIN_AMP_DELTA + 0.0100}},
    )

    verdict = evaluate_simulation_gate(
        amp_vs_decoy_path=amp,
        within_amp_path=within,
    )

    assert verdict.may_use_weighted_mode is True
    assert verdict.integration_mode == "weighted"
    assert all(verdict.checks.values())


def test_simulation_gate_info_mode_never_requires_ablation(tmp_path: Path) -> None:
    verdict = evaluate_simulation_gate(
        amp_vs_decoy_path=tmp_path / "missing.json",
        within_amp_path=tmp_path / "missing2.json",
        required_mode="info",
    )

    assert verdict.may_use_weighted_mode is False
    assert verdict.integration_mode == "info"
    assert "does not affect ranking" in verdict.reasons[0]


def test_simulation_gate_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        evaluate_simulation_gate(
            amp_vs_decoy_path=tmp_path / "missing.json",
            within_amp_path=tmp_path / "missing2.json",
        )


def test_cli_simulation_gate_blocks(tmp_path: Path) -> None:
    amp = tmp_path / "amp.json"
    within = tmp_path / "within.json"
    out = tmp_path / "verdict.json"
    _write_json(amp, {"results": {"verdict": "NO_IMPROVEMENT", "delta": -0.10}})
    _write_json(within, {"results": {"verdict": "NO_IMPROVEMENT", "delta": -0.10}})

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "openamp_foundry.cli",
            "bench",
            "simulation-gate",
            "--amp-vs-decoy-json",
            str(amp),
            "--within-amp-json",
            str(within),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 3
    payload = json.loads(out.read_text())
    assert payload["may_use_weighted_mode"] is False


def test_cli_simulation_gate_allows(tmp_path: Path) -> None:
    amp = tmp_path / "amp.json"
    within = tmp_path / "within.json"
    _write_json(amp, {"results": {"verdict": "IMPROVEMENT", "delta": 0.0200}})
    _write_json(within, {"results": {"verdict": "IMPROVEMENT", "delta": 0.0500}})

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "openamp_foundry.cli",
            "bench",
            "simulation-gate",
            "--amp-vs-decoy-json",
            str(amp),
            "--within-amp-json",
            str(within),
        ],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )

    assert result.returncode == 0
