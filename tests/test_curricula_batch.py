"""Tests for curricula and governance docs batch."""
from pathlib import Path

FILES = [
    "CURRICULUM_REVIEWER.md",
    "CURRICULUM_BENCHMARK_REVIEWER.md",
    "CURRICULUM_RELEASE_OPERATOR.md",
    "CURRICULUM_AGENT.md",
    "LEARNING_PATH_OVERVIEW.md",
    "CURRICULUM_MAINTAINER.md",
    "DOC_MAP_TRUST_LAYER.md",
    "DOCS_IMPROVEMENT_SCORECARD.md",
    "DOCS_ARCHIVE_INDEX_GUIDE.md",
    "DOCS_DEPRECATION_NOTICE_TEMPLATE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
