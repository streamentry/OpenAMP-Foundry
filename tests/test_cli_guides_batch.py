"""Tests for CLI guides and maintenance docs."""
from pathlib import Path

FILES = [
    "GUIDE_DEPENDENCY_REVIEW.md",
    "GUIDE_PACKAGE_METADATA.md",
    "GUIDE_STRUCTURED_LOGGING.md",
    "GUIDE_CLI_EXIT_CODES.md",
    "GUIDE_STDOUT_STDERR.md",
    "GUIDE_WARNING_TAXONOMY.md",
    "GUIDE_MINIMAL_OUTPUT.md",
    "GUIDE_REPORT_MANIFEST.md",
    "DOCS_MAINTENANCE_CALENDAR.md",
    "DOCS_IMPROVEMENT_ROADMAP.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
