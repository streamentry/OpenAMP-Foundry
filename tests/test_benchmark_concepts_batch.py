"""Tests for benchmark concept guides batch."""
from pathlib import Path

FILES = [
    "CONCEPT_STALE_ARTIFACT.md",
    "GUIDE_FOLDER_OWNERSHIP.md",
    "GUIDE_BENCHMARK_PHILOSOPHY.md",
    "GUIDE_BENCHMARK_CARD_WRITING.md",
    "GUIDE_CHEAP_BASELINE.md",
    "CONCEPT_LEAKAGE.md",
    "GUIDE_BENCHMARK_SLICE.md",
    "GUIDE_CONFIDENCE_INTERVALS.md",
    "GUIDE_METRIC_POLARITY.md",
    "GUIDE_BENCHMARK_REGRESSION_INTERP.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
