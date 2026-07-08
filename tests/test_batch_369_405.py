"""Tests for latest batch of 10 docs."""
from pathlib import Path

FILES = [
    "STANDARD_SOURCE_TRUTH_TAGS.md",
    "STANDARD_DOC_OWNERSHIP.md",
    "GUIDE_GLOSSARY_LINTER.md",
    "REGISTRY_ACRONYMS.md",
    "PROPOSAL_DEVCONTAINER.md",
    "REGISTRY_DEPENDENCY_PIN_RATIONALE.md",
    "REPORT_PACKAGE_INVENTORY.md",
    "REPORT_LICENSE_COMPATIBILITY.md",
    "GUIDE_PACKAGE_METADATA_CHECKER.md",
    "GUIDE_SENSITIVE_FIELD_SCANNER.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
