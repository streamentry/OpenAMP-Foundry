"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "WALKTHROUGH_CLAIM_TO_EVIDENCE.md",
    "DECISION_TREE_FIRST_CONTRIBUTION.md",
    "DECISION_TREE_OPENING_DOCS_PR.md",
    "DECISION_TREE_BENCHMARK_CHANGE.md",
    "GUIDE_RELEASE_READINESS.md",
    "DECISION_TREE_PUBLIC_SHARING.md",
    "DECISION_TREE_EVIDENCE_DOWNGRADE.md",
    "RUNBOOK_STALE_ARTIFACTS.md",
    "RUNBOOK_BROKEN_DOCS_LINKS.md",
    "RUNBOOK_UNSAFE_CLAIMS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
