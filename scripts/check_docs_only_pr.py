"""Verify that a git diff range contains only safe docs-only files.

Files considered safe for docs-only PRs:
  .md, .json, .yaml, .yml, .toml, .cfg, .txt, .png, .svg, .css

Usage:
    python scripts/check_docs_only_pr.py HEAD~1
    python scripts/check_docs_only_pr.py main...HEAD
    python scripts/check_docs_only_pr.py --diff-range HEAD~1
    make docs-only-check
"""
from __future__ import annotations

import subprocess
import sys

DOCS_EXTENSIONS = frozenset({
    ".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".txt",
    ".png", ".svg", ".css",
})


def get_changed_files(diff_range: str = "HEAD~1") -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", diff_range],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f.strip()]


def check_docs_only(diff_range: str = "HEAD~1") -> dict:
    files = get_changed_files(diff_range)
    code_files = []
    for f in files:
        ext = f[f.rfind("."):] if "." in f else ""
        if ext not in DOCS_EXTENSIONS:
            code_files.append(f)
    return {
        "total_changed": len(files),
        "code_files": code_files,
        "docs_only": len(code_files) == 0,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Verify a git diff range is docs-only"
    )
    parser.add_argument(
        "--diff-range", default="HEAD~1",
        help="Git diff range (default: HEAD~1)",
    )
    args = parser.parse_args()

    result = check_docs_only(args.diff_range)
    print(f"Total changed files: {result['total_changed']}")
    if result["code_files"]:
        print(f"Code files found ({len(result['code_files'])}):")
        for f in result["code_files"]:
            print(f"  ❌ {f}")
        print("Result: NOT docs-only")
        return 3
    else:
        print("Result: docs-only PR ✓")
        return 0


if __name__ == "__main__":
    sys.exit(main())
