"""Tests for policies and infrastructure batch."""
from pathlib import Path

FILES = [
    "CHECKLIST_DEPENDENCY_UPDATE.md",
    "GUIDE_PRIVACY_THREAT_MODEL.md",
    "POLICY_DEPENDENCY_RISK.md",
    "POLICY_HASH_ALGORITHM.md",
    "POLICY_SAFE_ARCHIVE.md",
    "GUIDE_STRUCTURED_LOGGING_OPTION.md",
    "PROPOSAL_CLI_COMPLETION.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
