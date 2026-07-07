"""Tests for playbooks."""
from pathlib import Path

PLAYBOOKS = [
    "PLAYBOOK_OVERCLAIM_REVIEW.md",
    "PLAYBOOK_PROOF_CONFUSION.md",
    "PLAYBOOK_BENCHMARK_REGRESSION.md",
    "PLAYBOOK_STALE_ARTIFACT.md",
    "PLAYBOOK_CHANGED_OUTPUT.md",
]


def test_all_exist():
    for p in PLAYBOOKS:
        assert Path(f"docs/evidence/{p}").exists(), f"Missing: {p}"


def test_each_has_steps():
    for p in PLAYBOOKS:
        text = Path(f"docs/evidence/{p}").read_text()
        assert "Steps" in text or "steps" in text
