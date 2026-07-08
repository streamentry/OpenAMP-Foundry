"""Check that all .md files under docs/ are referenced in PROJECT_INDEX.md.

Usage:
    python scripts/check_docs_index_coverage.py
    make docs-index-check
"""
from __future__ import annotations

import sys
import re
from pathlib import Path

PROJECT_INDEX = Path("docs/PROJECT_INDEX.md")
DOCS_DIR = Path("docs")

ALLOWLIST = {
    "docs/AGENTS.md",
    "docs/PROJECT_INDEX.md",
    "docs/README.md",
}


def get_indexed_docs() -> set[str]:
    text = PROJECT_INDEX.read_text()
    refs = set()
    for m in re.finditer(r'\(([^)]+\.md)\)', text):
        ref = m.group(1)
        if "http" not in ref:
            refs.add(ref)
    return refs


def get_docs_files() -> set[str]:
    files = set()
    for f in DOCS_DIR.rglob("*.md"):
        rel = str(f.relative_to(DOCS_DIR.parent))
        if rel not in ALLOWLIST:
            files.add(rel)
    return files


def check_coverage() -> dict:
    indexed = get_indexed_docs()
    all_docs = get_docs_files()
    missing = sorted(all_docs - indexed)
    return {
        "total_docs": len(all_docs),
        "indexed": len(indexed & all_docs),
        "missing": missing,
        "missing_count": len(missing),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check PROJECT_INDEX.md coverage")
    parser.add_argument("--warn-only", action="store_true",
                        help="Print missing files but always exit 0")
    args = parser.parse_args()
    result = check_coverage()
    print(f"Total docs: {result['total_docs']}, Indexed: {result['indexed']}, Missing: {result['missing_count']}")
    if result["missing"]:
        print("\nFiles not referenced in PROJECT_INDEX.md:")
        for f in result["missing"]:
            print(f"  ❌ {f}")
        if args.warn_only:
            return 0
        return 3
    print("All docs are referenced in PROJECT_INDEX.md ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
