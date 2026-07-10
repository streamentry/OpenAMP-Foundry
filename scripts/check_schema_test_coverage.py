"""Check that every schema in schemas/ is referenced in at least one test.

Usage:
    python scripts/check_schema_test_coverage.py
    python scripts/check_schema_test_coverage.py --warn-only
    make schema-test-check
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openamp_foundry.checks.schema_test_coverage import (
    check_schema_test_coverage,
    format_schema_coverage_report,
)

SCHEMAS_DIR = Path("schemas")
TESTS_DIR = Path("tests")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check schema-test cross-reference coverage")
    parser.add_argument("--warn-only", action="store_true",
                        help="Print gaps but always exit 0")
    args = parser.parse_args()

    if not SCHEMAS_DIR.exists():
        print(f"schemas/ directory not found at {SCHEMAS_DIR.absolute()}")
        return 1

    report = check_schema_test_coverage(SCHEMAS_DIR, TESTS_DIR)
    print(format_schema_coverage_report(report))

    if report.is_complete:
        return 0
    if args.warn_only:
        print("\n(advisory — schema-test coverage expected to improve over time)")
        return 0
    return 3


if __name__ == "__main__":
    sys.exit(main())
