"""Tests for review and data docs batch."""
from pathlib import Path

FILES = [
    "CHECKLIST_REVIEW_REQUEST.md",
    "GUIDE_REVIEWER_QUESTIONNAIRE.md",
    "GUIDE_EXTERNAL_REVIEWER_ONBOARDING.md",
    "GUIDE_REVIEW_DECISION_VOCAB.md",
    "GUIDE_DISSENT_UNCERTAINTY.md",
    "GUIDE_DATASET_SPLIT_DOCS.md",
    "GUIDE_FIXTURE_DESIGN.md",
    "STANDARD_ARTIFACT_NAMING.md",
    "GUIDE_EXAMPLE_DATA_LICENSING.md",
    "GUIDE_TOY_DATA_MARKERS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
