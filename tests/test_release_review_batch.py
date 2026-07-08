"""Tests for release and review guides batch."""
from pathlib import Path

FILES = [
    "GUIDE_REVIEWER_CONFLICT.md",
    "GUIDE_REVIEW_ESCALATION.md",
    "GUIDE_RELEASE_READINESS_OVERVIEW.md",
    "GUIDE_PUBLIC_READINESS.md",
    "GUIDE_RELEASE_STATUS_VOCAB.md",
    "GUIDE_REDACTION_POLICY.md",
    "GUIDE_PUBLIC_SUMMARY_WRITING.md",
    "GUIDE_RELEASE_NOTES_WRITING.md",
    "GUIDE_RELEASE_BLOCKER_TAXONOMY.md",
    "GUIDE_ARCHIVE_DEPRECATION.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
