"""Tests for scripts/generate_review_packet.py."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

GENERATE_SCRIPT = _SCRIPTS_DIR / "generate_review_packet.py"
PACKET_SCHEMA = _SCHEMAS_DIR / "external_review_packet.schema.json"


def test_script_exists():
    assert GENERATE_SCRIPT.exists()


class TestGenerateReviewPacketCLI:
    def test_generates_skeleton(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--pipeline-version", "v0.5.73",
                "--git-sha", "abc1234567890abcdef1234567890abcdef1234",
                "--candidate-count", "36",
                "--proof-ladder-level", "2",
                "--out", str(out),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert out.exists()
        packet = json.loads(out.read_text(encoding="utf-8"))
        assert packet["pipeline_version"] == "v0.5.73"
        assert packet["git_sha"] == "abc1234567890abcdef1234567890abcdef1234"
        assert packet["candidate_count"] == 36
        assert packet["proof_ladder_level"] == 2
        assert packet["dry_lab_only_attestation"] is True
        assert len(packet["candidates"]) == 36

    def test_skeleton_validates_against_schema(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--pipeline-version", "v0.5.73",
                "--git-sha", "abc1234",
                "--candidate-count", "10",
                "--proof-ladder-level", "1",
                "--out", str(out),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        packet = json.loads(out.read_text(encoding="utf-8"))
        validate_json_schema(packet, PACKET_SCHEMA)

    def test_validate_flag_passes(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--pipeline-version", "v0.5.73",
                "--git-sha", "deadbeef",
                "--candidate-count", "24",
                "--proof-ladder-level", "2",
                "--out", str(out),
                "--validate",
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert "Validation passed" in r.stdout

    def test_skeleton_has_required_fields(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--pipeline-version", "v0.5.73",
                "--git-sha", "feedface",
                "--candidate-count", "5",
                "--proof-ladder-level", "1",
                "--out", str(out),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        packet = json.loads(out.read_text(encoding="utf-8"))
        for field in ["packet_id", "version", "generated_at", "pipeline_version",
                       "git_sha", "candidate_count", "candidates", "benchmark_summary",
                       "calibration_summary", "limitations", "safety_attestations",
                       "dry_lab_only_attestation", "proof_ladder_level", "contact"]:
            assert field in packet, f"Missing field: {field}"

    def test_proof_ladder_level_out_of_range_fails(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--pipeline-version", "v0.5.73",
                "--git-sha", "abc1234",
                "--candidate-count", "10",
                "--proof-ladder-level", "9",
                "--out", str(out),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode != 0
        assert "invalid choice" in r.stderr or "invalid choice" in r.stdout

    def test_missing_required_args_fails(self, tmp_path):
        out = tmp_path / "packet.json"
        r = subprocess.run(
            [sys.executable, str(GENERATE_SCRIPT), "--out", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode != 0
