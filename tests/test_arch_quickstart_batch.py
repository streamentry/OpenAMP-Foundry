"""Tests for architecture and quickstart batch."""
from pathlib import Path

FILES = [
    "POLICY_CLI_REFERENCE_GENERATION.md",
    "GUIDE_MAKE_TARGETS.md",
    "GUIDE_QUICKSTART_OUTPUT_GALLERY.md",
    "GUIDE_QUICKSTART_DIAGNOSIS.md",
    "GLOSSARY_BEGINNER_PATH.md",
    "DIAGRAM_ARTIFACT_FLOW.md",
    "ARCHITECTURE_OVERVIEW.md",
    "GUIDE_ARTIFACT_LIFECYCLE.md",
    "DIAGRAM_DATA_FLOW.md",
    "MAP_COMMAND_TO_ARTIFACT.md",
    "DIAGRAM_DEPENDENCY_GRAPH.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"
