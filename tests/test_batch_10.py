"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "RUNBOOK_UPDATING_INDEXES.md",
    "RUNBOOK_RUNNING_DOCS_CHECKS.md",
    "RUNBOOK_FAILING_DOCS_CHECKS.md",
    "RUNBOOK_OPENING_FOLLOW_UPS.md",
    "RUNBOOK_FINISHING_DOCS_PR.md",
    "DOCS_GOVERNANCE_CHARTER.md",
    "MIGRATION_GUIDE_COMMAND_DOCS.md",
    "MIGRATION_GUIDE_RELEASE_DOCS.md",
    "MIGRATION_GUIDE_GLOSSARY_DOCS.md",
    "MIGRATION_GUIDE_BACKLOG_DOCS.md",
]


def test_all_exist():
    for f in FILES:
        path = Path("docs/evidence") / f if "RUNBOOK" not in f else Path("docs/getting-started") / f
        assert path.exists(), f"Missing: {f}"


def test_each_has_content():
    for f in FILES:
        path = Path("docs/evidence") / f if "RUNBOOK" not in f else Path("docs/getting-started") / f
        text = path.read_text()
        assert len(text) > 50, f"{f} too short"
