"""Tests for metric guides."""
from pathlib import Path

GUIDES = [
    "METRIC_GUIDE_ONBOARDING_SUCCESS.md",
    "METRIC_GUIDE_SAFETY_CLARITY.md",
    "METRIC_GUIDE_ARTIFACT_EXPLAINABILITY.md",
    "METRIC_GUIDE_BENCHMARK_EXPLAINABILITY.md",
    "METRIC_GUIDE_REVIEW_READINESS.md",
]


def test_all_exist():
    for g in GUIDES:
        assert Path(f"docs/evidence/{g}").exists(), f"Missing: {g}"


def test_each_has_question():
    for g in GUIDES:
        text = Path(f"docs/evidence/{g}").read_text()
        assert "Question" in text or "question" in text
