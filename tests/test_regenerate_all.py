from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.regenerate_all import check_determinism, run_make, run_targets, sha256


class TestSha256:
    def test_returns_consistent_hash(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello")
        h1 = sha256(f)
        h2 = sha256(f)
        assert h1 == h2

    def test_changes_when_content_changes(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello")
        h1 = sha256(f)
        f.write_text("world")
        h2 = sha256(f)
        assert h1 != h2


class TestRunTargets:
    def test_returns_0_for_help_target(self):
        rc = run_targets(["help"])
        assert rc == 0

    def test_returns_1_for_bad_target(self):
        rc = run_targets(["nonexistent-target-xyz"])
        assert rc == 1


class TestRunMake:
    def test_returns_0_for_help(self):
        assert run_make("help") == 0

    def test_returns_nonzero_for_bad_target(self):
        assert run_make("nonexistent-xyz") != 0


class TestCheckDeterminism:
    def test_passes_when_no_diff(self, tmp_path, monkeypatch):
        tracked = [str(tmp_path / "stable.json")]
        Path(tracked[0]).write_text("{}")

        subprocess_run_calls = []

        def fake_run(cmd, **kw):
            subprocess_run_calls.append(cmd)
            class Fake:
                returncode = 0
                stdout = ""
                stderr = ""
            return Fake()

        monkeypatch.setattr(subprocess, "run", fake_run)
        rc = check_determinism(tracked=tracked)
        assert rc == 0

    def test_fails_when_diff_detected(self, tmp_path, monkeypatch):
        tracked = [str(tmp_path / "changed.json")]
        Path(tracked[0]).write_text("{}")

        subprocess_run_calls = []

        def fake_run(cmd, **kw):
            subprocess_run_calls.append(cmd)
            class Fake:
                returncode = 1
                stdout = " outputs/metrics_snapshot.json | 2 +-\n"
                stderr = ""
            return Fake()

        monkeypatch.setattr(subprocess, "run", fake_run)
        rc = check_determinism(tracked=tracked)
        assert rc == 1


class TestRegenerateAllScript:
    def test_help_flag_succeeds(self):
        result = subprocess.run(
            [sys.executable, "scripts/regenerate_all.py", "--help"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 0
        assert "Regenerate all derived outputs" in result.stdout

    def test_skip_targets_passes_when_no_diff(self, tmp_path, monkeypatch):
        snap = tmp_path / "metrics_snapshot.json"
        snap.write_text(json.dumps({"standard": {"auroc": 0.7832}}), encoding="utf-8")

        monkeypatch.setattr(
            "scripts.regenerate_all.TRACKED",
            [str(snap)],
        )

        def fake_run(cmd, **kw):
            class Fake:
                returncode = 0
                stdout = ""
                stderr = ""
            return Fake()

        monkeypatch.setattr(subprocess, "run", fake_run)

        from scripts.regenerate_all import main
        rc = main(["--skip-targets"])
        assert rc == 0

    def test_skip_targets_fails_on_diff(self, tmp_path, monkeypatch):
        snap = tmp_path / "metrics_snapshot.json"
        snap.write_text(json.dumps({"standard": {"auroc": 0.7832}}), encoding="utf-8")

        monkeypatch.setattr(
            "scripts.regenerate_all.TRACKED",
            [str(snap)],
        )

        call_count = 0

        def fake_run(cmd, **kw):
            nonlocal call_count
            call_count += 1
            class Fake:
                returncode = 0 if call_count > 1 else 1
                stdout = " outputs/metrics_snapshot.json | 2 +-\n"
                stderr = ""
            return Fake()

        monkeypatch.setattr(subprocess, "run", fake_run)

        from scripts.regenerate_all import main
        rc = main(["--skip-targets"])
        assert rc == 1
