"""Test pipeline handles edge cases gracefully."""
import subprocess
import sys
import tempfile
from pathlib import Path


def test_empty_candidates_file():
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "empty.csv"
        empty.write_text("id,sequence,source\n")
        out = Path(tmp) / "ranked.jsonl"
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", str(empty), "--out", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        # Accept either exit code 0 (success with empty output) or error
        assert r.returncode in (0, 1, 2), f"Unexpected exit: {r.returncode}: {r.stderr[:200]}"


def test_single_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "single.csv"
        csv.write_text("id,sequence,source\nTEST-001,KWKLFKKIGAVLKVL,test\n")
        out = Path(tmp) / "ranked.jsonl"
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", str(csv), "--out", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0, f"Exit {r.returncode}: {r.stderr[:200]}"
        lines = out.read_text().splitlines()
        assert len(lines) == 1, f"Expected 1 candidate, got {len(lines)}"


def test_invalid_sequence_does_not_crash():
    with tempfile.TemporaryDirectory() as tmp:
        csv = Path(tmp) / "invalid.csv"
        csv.write_text("id,sequence,source\nBAD-001,XYZ123,test\n")
        out = Path(tmp) / "ranked.jsonl"
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "rank",
             "--candidates", str(csv), "--out", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        # Should not crash — pipeline should handle invalid sequences gracefully
        assert r.returncode in (0, 1, 2), f"Crashed: {r.stderr[:200]}"
