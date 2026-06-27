"""CLI integration tests."""
from __future__ import annotations

import json

import pytest

from openamp_foundry.cli import main


def test_rank_command_success(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    ret = main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
    ])
    assert ret == 0


def test_rank_command_with_report_and_certs(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    report = str(tmp_path / "report.md")
    certs = str(tmp_path / "certs")
    ret = main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--report", report,
        "--cert-dir", certs,
    ])
    assert ret == 0


def test_validate_command_success(tmp_path):
    # First generate a certificate
    out = str(tmp_path / "ranked.jsonl")
    certs = str(tmp_path / "certs")
    main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--cert-dir", certs,
    ])
    import os
    cert_files = list((tmp_path / "certs").glob("*.json"))
    assert cert_files, "No certificates were generated"
    ret = main([
        "validate",
        "--certificate", str(cert_files[0]),
        "--schema", "schemas/candidate.schema.json",
    ])
    assert ret == 0


def test_bench_leakage_detects_duplicates(tmp_path, capsys):
    # Demo candidates 1, 2, 5 are exact copies of references
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["near_duplicate_count"] == 3
    assert result["warning"] is not None


def test_bench_leakage_no_duplicates(tmp_path, capsys):
    # Use negative examples as candidates — they won't match the reference AMPs
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/negative/demo_negative_peptides.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--threshold", "0.90",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["near_duplicate_count"] == 0
    assert result["warning"] is None


def test_bench_leakage_output_file(tmp_path, capsys):
    out = str(tmp_path / "leakage_report.json")
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
    ])
    assert ret == 0
    data = json.loads((tmp_path / "leakage_report.json").read_text())
    assert "near_duplicates" in data


def test_report_contains_disclaimer(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    report = str(tmp_path / "report.md")
    main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--report", report,
    ])
    text = (tmp_path / "report.md").read_text()
    assert "NOT validated biological predictors" in text
    assert "no antimicrobial activity has been demonstrated" in text.lower() or "No antimicrobial activity" in text
