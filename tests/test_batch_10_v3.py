"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "ISSUE_PRIORITY_RUBRIC.md",
    "ISSUE_LABEL_GUIDE.md",
    "MILESTONE_PLANNING_GUIDE.md",
    "ISSUE_BATCHING_GUIDE.md",
    "ISSUE_CLOSING_POLICY.md",
    "DUPLICATE_ISSUE_GUIDE.md",
    "ISSUE_DEPENDENCY_GUIDE.md",
    "ISSUE_DECOMPOSITION_GUIDE.md",
    "PR_REVIEW_RUBRIC.md",
    "CHANGE_NOTE_GUIDE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"


def test_each_has_content():
    for f in FILES:
        text = Path("docs/evidence", f).read_text()
        assert len(text) > 50, f"{f} too short"
