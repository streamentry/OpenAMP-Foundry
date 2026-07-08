"""Scan benchmark card YAML files and report deprecated benchmarks.

Usage:
    python scripts/check_benchmark_deprecation.py
    python scripts/check_benchmark_deprecation.py --fail-on-deprecated
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


CARDS_DIR = Path("configs/benchmark_cards")


def _load_card(path: Path) -> dict | None:
    if yaml is None:
        try:
            import json
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return None
    try:
        return yaml.safe_load(path.read_text())
    except Exception:
        return None


def scan_cards(cards_dir: str | Path = CARDS_DIR) -> list[dict]:
    cards_path = Path(cards_dir)
    if not cards_path.exists():
        return []
    deprecated = []
    for f in sorted(cards_path.glob("*.yaml")):
        card = _load_card(f)
        if card and card.get("deprecated"):
            deprecated.append({
                "file": f.name,
                "name": card.get("name", "unknown"),
                "superseded_by": card.get("superseded_by", ""),
                "deprecation_note": card.get("deprecation_note", ""),
            })
    return deprecated


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on-deprecated", action="store_true",
                        help="Exit 3 if any deprecated benchmarks exist")
    args = parser.parse_args()

    deprecated = scan_cards()
    if not deprecated:
        print("No deprecated benchmarks found.")
        return 0

    print(f"Deprecated benchmarks ({len(deprecated)}):")
    for d in deprecated:
        print(f"  ❌ {d['name']} ({d['file']})")
        if d['superseded_by']:
            print(f"     Superseded by: {d['superseded_by']}")
        if d['deprecation_note']:
            print(f"     Note: {d['deprecation_note']}")

    if args.fail_on_deprecated:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
