"""Tests for FAQ and writing guides batch."""
from pathlib import Path

FILES = [
    "POLICY_RETENTION.md",
    "GUIDE_CLAIM_WORDING_STYLE.md",
    "POLICY_CITATION_SOURCE.md",
    "GUIDE_ASSUMPTIONS_REGISTER.md",
    "GUIDE_UNCERTAINTY_LANGUAGE.md",
    "GUIDE_NO_HYPE_WRITING.md",
    "FAQ_PUBLIC.md",
    "FAQ_MAINTAINER.md",
    "FAQ_CONTRIBUTOR.md",
    "GUIDE_DATA_SOURCE_DOCS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
