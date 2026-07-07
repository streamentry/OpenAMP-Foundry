"""Tests for metric docs batch."""
from pathlib import Path

FILES = [
    "METRIC_GUIDE_RELEASE_READINESS.md",
    "METRIC_GUIDE_NAVIGATION_HEALTH.md",
    "METRIC_GUIDE_MAINTENANCE_HEALTH.md",
    "METRIC_GUIDE_CONTRIBUTOR_DOCS.md",
    "DOCS_HEALTH_METRIC_DEFINITIONS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path(f"docs/evidence/{f}").exists(), f"Missing: {f}"


def test_each_has_content():
    for f in FILES:
        text = Path(f"docs/evidence/{f}").read_text()
        assert len(text) > 100, f"{f} too short"
