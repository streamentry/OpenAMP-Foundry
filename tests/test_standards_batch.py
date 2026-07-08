"""Tests for 10 standards and policies."""
from pathlib import Path

FILES = [
    "STANDARD_TABLE_FORMATTING.md",
    "STANDARD_DIAGRAM_STYLE.md",
    "STANDARD_SCREENSHOT_POLICY.md",
    "CHECKLIST_ACCESSIBILITY.md",
    "CHECKLIST_CLEAR_LANGUAGE.md",
    "STANDARD_CODE_BLOCKS.md",
    "STANDARD_OUTPUT_EXCERPTS.md",
    "STANDARD_ENVIRONMENT_ASSUMPTIONS.md",
    "STANDARD_GENERATED_FILE_WARNING.md",
    "POLICY_MANUAL_EDIT_ARTIFACTS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
