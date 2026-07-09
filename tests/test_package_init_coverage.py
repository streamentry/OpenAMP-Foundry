"""Verify all Python packages have __init__.py files."""
from pathlib import Path


def test_all_packages_have_init():
    src = Path("src/openamp_foundry")
    missing = []
    for d in sorted(src.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith("."):
            if not (d / "__init__.py").exists():
                missing.append(d.name)
    assert not missing, f"Packages missing __init__.py: {sorted(missing)}"
