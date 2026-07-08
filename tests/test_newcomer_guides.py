"""Tests for newcomer guides batch."""
from pathlib import Path

FILES = [
    "MAP_READER_BY_PERSONA.md",
    "GUIDE_TRUST_MODEL.md",
    "GUIDE_EVIDENCE_BOUNDARY.md",
    "SAFETY_CHARTER.md",
    "PAGE_NON_GOALS.md",
    "GUIDE_MISUSE_SCENARIOS.md",
    "GUIDE_SAFE_CONTRIBUTION_BOUNDARY.md",
    "GUIDE_FIRST_PR.md",
    "GUIDE_LOCAL_SETUP.md",
    "TOUR_COMMANDS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
