"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "RUNBOOK_BENCHMARK_REGRESSION_TRIAGE.md",
    "RUNBOOK_SCHEMA_CHANGE_REVIEW.md",
    "RUNBOOK_DEPENDENCY_CHANGE_REVIEW.md",
    "RUNBOOK_EXTERNAL_REVIEW_DELAYS.md",
    "CHECKLIST_DOC_QUALITY.md",
    "POLICY_DOCS_FRESHNESS.md",
    "GUIDE_RESOLVING_DOC_CONFLICTS.md",
    "STANDARD_DOC_METADATA.md",
    "CHECKLIST_DOC_REVIEW_BY_TYPE.md",
    "CATALOG_DOC_ANTI_PATTERNS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
