"""Verify all CLI subcommands accept --help and produce usage text."""
import subprocess
import sys

from openamp_foundry.cli.main import build_parser

COMMANDS = [
    "rank", "validate", "validate-cert-quality",
    "generate-batch", "pilot-panel", "validate-scoring",
    "external-predict", "pilot-confident", "external-consensus",
    "reviewer-questionnaire", "gate-check", "ip-report",
    "presynth-qc", "gold-standard", "diversity-check",
    "synthesis-order", "batch-pack", "lab-result-report",
    "calibration-intake", "recalibration-gate", "recalibration-engine",
    "novelty-check-broad", "validate-policy-version", "select-batch",
    "phase-ac-disconfirming-gate-check",
    "phase-aa-reproducibility-gate-check",
    "phase-z-accountability-gate-check",
    "scientific-review-readiness-check",
]


def test_all_commands_listed():
    parser = build_parser()
    choices = parser._subparsers._group_actions[0].choices
    for name in COMMANDS:
        assert name in choices, f"Missing subcommand: {name}"


def test_all_commands_accept_help():
    for cmd in COMMANDS:
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", cmd, "--help"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0, f"{cmd} --help exited {r.returncode}: {r.stderr[:100]}"
        assert "usage:" in r.stdout, f"{cmd} --help missing usage: {r.stdout[:100]}"
