"""Tests for tutorials and walkthroughs batch."""
from pathlib import Path

FILES = [
    "TUTORIAL_INDEX_BY_LEVEL.md",
    "TUTORIAL_PREREQS_CHECKLIST.md",
    "STANDARD_TUTORIAL_EXPECTED_FILES.md",
    "GUIDE_TUTORIAL_CLEANUP.md",
    "TEMPLATE_TUTORIAL_SAFETY_NOTE.md",
    "TEMPLATE_TUTORIAL_TROUBLESHOOTING.md",
    "WALKTHROUGH_ARTIFACT_VALIDATION.md",
    "WALKTHROUGH_BENCHMARK_REVIEW.md",
    "WALKTHROUGH_REVIEW_PACKETS.md",
    "WALKTHROUGH_CALIBRATION_AUDIT.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
