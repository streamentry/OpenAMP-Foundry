"""Tests for contributor runbooks."""
from pathlib import Path

RUNBOOKS = [
    "RUNBOOK_PICKING_UP_ISSUE.md",
    "RUNBOOK_BLOCKED_WORK.md",
    "RUNBOOK_PAUSING_WORK.md",
    "RUNBOOK_ASKING_FOR_REVIEW.md",
    "RUNBOOK_HANDLING_REVIEW.md",
]


def test_all_exist():
    for r in RUNBOOKS:
        assert Path(f"docs/getting-started/{r}").exists(), f"Missing: {r}"


def test_each_has_content():
    for r in RUNBOOKS:
        text = Path(f"docs/getting-started/{r}").read_text()
        assert len(text) > 50, f"{r} is too short"
