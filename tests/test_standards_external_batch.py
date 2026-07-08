"""Tests for standards and external guides batch."""
from pathlib import Path

FILES = [
    "STANDARD_CSV_INPUT.md",
    "STANDARD_JSONL_ARTIFACT.md",
    "STANDARD_ADAPTER_DOCS.md",
    "GUIDE_OFFLINE_MODE.md",
    "GUIDE_OPTIONAL_DEPS.md",
    "GUIDE_ADAPTER_FAILURES.md",
    "GUIDE_EXTERNAL_CONSENT.md",
    "GUIDE_ADAPTER_CAPABILITY.md",
    "GUIDE_PRIVACY_MODEL.md",
    "GUIDE_SECRETS_HANDLING.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
