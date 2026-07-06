"""Tests for run-manifest verification."""

from __future__ import annotations

import hashlib
import json

from openamp_foundry.reproducibility import verify_run_manifest


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_manifest(tmp_path, payload):
    path = tmp_path / "run_manifest.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _base_manifest(input_path, input_hash, output_path):
    return {
        "run_id": "test-run",
        "pipeline_version": "0.0.0-test",
        "config_hash": "config-hash",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "inputs": [str(input_path)],
        "input_hashes": {str(input_path): input_hash},
        "outputs": [str(output_path)],
    }


def test_verify_run_manifest_passes_for_matching_input_and_output(tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("input\n", encoding="utf-8")
    output_path.write_text("output\n", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        _base_manifest(input_path, _sha256_text("input\n"), output_path),
    )

    report = verify_run_manifest(manifest_path)

    assert report["ok"] is True
    assert report["errors"] == []
    assert str(output_path) in report["observed_output_hashes"]


def test_verify_run_manifest_fails_for_input_hash_drift(tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("input\n", encoding="utf-8")
    output_path.write_text("output\n", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        _base_manifest(input_path, _sha256_text("input\n"), output_path),
    )
    input_path.write_text("changed\n", encoding="utf-8")

    report = verify_run_manifest(manifest_path)

    assert report["ok"] is False
    assert any("Input hash mismatch" in err for err in report["errors"])


def test_verify_run_manifest_fails_for_missing_output(tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "missing.txt"
    input_path.write_text("input\n", encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        _base_manifest(input_path, _sha256_text("input\n"), output_path),
    )

    report = verify_run_manifest(manifest_path)

    assert report["ok"] is False
    assert any("Output path missing" in err for err in report["errors"])


def test_verify_run_manifest_enforces_optional_output_hashes(tmp_path):
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("input\n", encoding="utf-8")
    output_path.write_text("output\n", encoding="utf-8")
    payload = _base_manifest(input_path, _sha256_text("input\n"), output_path)
    payload["output_hashes"] = {str(output_path): _sha256_text("different\n")}
    manifest_path = _write_manifest(tmp_path, payload)

    report = verify_run_manifest(manifest_path)

    assert report["ok"] is False
    assert any("Output hash mismatch" in err for err in report["errors"])
