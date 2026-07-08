"""Tests for calibration and docs templates batch."""
from pathlib import Path

FILES = [
    "GUIDE_CALIBRATION_PHILOSOPHY.md",
    "GUIDE_CALIBRATION_GATE_EXPLAINER.md",
    "GUIDE_RESULT_QUALITY_FLAGS.md",
    "GUIDE_CALIBRATION_ROLLBACK.md",
    "GUIDE_CALIBRATION_AUDIT_READING.md",
    "GUIDE_NEGATIVE_RESULT_LEARNING.md",
    "GUIDE_DOCS_ISSUE_TEMPLATES.md",
    "GUIDE_DOCS_PR_DESCRIPTION.md",
    "GUIDE_DOC_EXAMPLES_STYLE.md",
    "GUIDE_DOCS_NAVIGATION_AUDIT.md",
    "GUIDE_DOCS_DUPLICATION_REVIEW.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
