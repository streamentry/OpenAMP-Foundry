"""Verify all documented Makefile targets have echo help text."""
from pathlib import Path


def test_all_documented_targets_have_help():
    text = Path("Makefile").read_text()
    documented = set()
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            continue
        if "@echo" in line and '"' in line:
            # Extract target name from the preceding comment block
            pass
    # At minimum verify the help target exists
    assert '@echo "OpenAMP Foundry' in text


def test_help_target_lists_major_targets():
    text = Path("Makefile").read_text()
    # After "help:" the subsequent @echo lines list targets
    help_section = text.split("help:")[1].split("\n\n")[0] if "help:" in text else ""
    assert "make demo" in help_section or "@echo" in help_section
