"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "REGISTRY_TUTORIAL_FIXTURES.md",
    "STANDARD_WALKTHROUGH_SNAPSHOTS.md",
    "GUIDE_TASK_SIZE.md",
    "CHECKLIST_PR_RISK.md",
    "GUIDE_REVIEW_LATENCY.md",
    "CHECKLIST_MAINTAINER_HANDOFF.md",
    "POLICY_SECRET_SCAN.md",
    "POLICY_SAFE_FILENAMES.md",
    "GUIDE_WARNING_TAXONOMY.md",
    "POLICY_QUIET_MODE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
