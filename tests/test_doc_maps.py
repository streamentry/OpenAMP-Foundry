"""Tests for 10 doc maps batch."""
from pathlib import Path

FILES = [
    "DOC_MAP_BENCHMARK.md",
    "DOC_MAP_REVIEW.md",
    "DOC_MAP_RELEASE.md",
    "DOC_MAP_COMMAND.md",
    "DOC_MAP_ISSUE_TAXONOMY.md",
    "DOC_MAP_ROADMAP.md",
    "DOC_MAP_FILE_OWNERSHIP.md",
    "DOC_MAP_SOURCE_OF_TRUTH.md",
    "GLOSSARY_LEARNING_SEQUENCE.md",
    "READER_SELF_ASSESSMENT.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
