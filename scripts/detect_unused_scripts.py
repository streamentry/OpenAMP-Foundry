"""Detect scripts not referenced by Makefile, CI, or docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REFERENCE_FILES = ["Makefile", ".github/workflows/ci.yml", "docs/PROJECT_INDEX.md", "AGENTS.md"]

EXEMPT = {"scripts/__init__.py", "scripts/check_doc_links.py", "scripts/safety/check_claims.py"}


def detect_unused(scripts_dir: str = "scripts") -> dict:
    root = Path(scripts_dir)
    if not root.exists():
        return {"error": f"Directory not found: {scripts_dir}"}

    # Collect all .py scripts
    all_scripts = sorted(f.relative_to(root.parent) for f in root.rglob("*.py") if f.name != "__init__.py")

    # Collect all script names from reference files
    referenced_names: set[str] = set()
    for ref_path in REFERENCE_FILES:
        rp = Path(ref_path)
        if rp.exists():
            text = rp.read_text()
            for s in all_scripts:
                if s.name in text or str(s) in text:
                    referenced_names.add(str(s))

    referenced = sorted(referenced_names)
    unreferenced = sorted(set(str(s) for s in all_scripts) - referenced_names - EXEMPT)

    return {
        "scripts_dir": scripts_dir,
        "total_scripts": len(all_scripts),
        "referenced": len(referenced),
        "unreferenced": len(unreferenced),
        "exempt": len(EXEMPT),
        "detailed": {
            "referenced": referenced,
            "unreferenced": unreferenced,
            "exempt": sorted(EXEMPT),
        },
    }


def main() -> int:
    result = detect_unused()
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 2

    print(f"Total scripts: {result['total_scripts']}")
    print(f"Referenced: {result['referenced']}")
    print(f"Unreferenced: {result['unreferenced']}")
    print(f"Exempt: {result['exempt']}")

    if result["unreferenced"]:
        print("\nUnreferenced scripts:")
        for s in result["detailed"]["unreferenced"]:
            print(f"  ❌ {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
