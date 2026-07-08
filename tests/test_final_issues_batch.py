"""Tests for final remaining issues batch."""
from pathlib import Path

FILES = [
    "PLAYBOOK_BENCHMARK_DRIFT.md",
    "GUIDE_BENCHMARK_REPORT_READING.md",
    "GUIDE_LEARNING_FROM_NEGATIVES.md",
    "GUIDE_EVIDENCE_DOWNGRADE.md",
    "GUIDE_CALIBRATION_ANTI_PATTERNS.md",
    "GUIDE_REVIEW_PACKET_OVERVIEW.md",
    "GUIDE_REVIEWER_ROLE.md",
    "NARRATIVE_FIRST_PRINCIPLES.md",
    "GUIDE_CLI_ARCHITECTURE.md",
    "GUIDE_SCHEMA_ARCHITECTURE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
