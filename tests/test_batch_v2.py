"""Tests for latest batch."""
from pathlib import Path

FILES = [
    "CATALOG_AGENT_ISSUES.md",
    "GUIDE_ALLOWED_CLAIMS.md",
    "GUIDE_ISSUE_TRIAGE.md",
    "GUIDE_REVIEW_DASHBOARD.md",
    "INDEX_ADR.md",
    "GUIDE_DECISION_VALIDATOR.md",
    "GUIDE_PLATFORM_VERIFICATION.md",
    "MATRIX_CONTRIBUTOR_ENV.md",
    "GUIDE_REPRODUCIBILITY_CHECK.md",
    "ARCHITECTURE_OVERVIEW_CONTRIBUTORS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
