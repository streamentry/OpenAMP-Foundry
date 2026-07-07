"""Scan markdown files for overclaiming language.

Usage:
    python scripts/check_claims.py
    python scripts/check_claims.py --path docs/review/
    make claim-check
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RISKY_PATTERNS: list[tuple[str, str]] = [
    (r"\bproven\b", "Avoid 'proven' — computational scores do not prove biological efficacy"),
    (r"\bsafe in humans\b", "Do not claim human safety without clinical evidence"),
    (r"\bclinically useful\b", "Do not claim clinical utility without clinical evidence"),
    (r"\bAI discovered an antibiotic\b", "Use 'computationally nominated candidate' instead"),
    (r"\bvalidated by computation\b", "Computation triages, does not validate biology"),
    (r"\bdrug candidate\b", "Use 'computationally nominated candidate' until wet-lab confirmation"),
    (r"\bcure\b", "Do not claim curative effects"),
    (r"\bbreakthrough therapy\b", "Do not claim therapeutic breakthroughs"),
    (r"\beffective in humans\b", "No human data exists"),
    (r"\bworld.?first\b", "Avoid 'world-first' unless independently verified"),
    (r"\bproven antimicrobial\b", "Computational prediction is not proof of antimicrobial activity"),
    (r"\btherapeutic\b(?!\s*(?:target|index|agent|peptide|area|window))", "Use cautiously — 'therapeutic' implies clinical application"),
]

ALLOWLIST = [
    "AGENTS.md",
    "CLAIM_REVIEW_CHECKLIST.md",
    "MISSION.md",
]


def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings
    for i, line in enumerate(text.split("\n"), 1):
        for pattern, msg in RISKY_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "file": str(path),
                    "line": i,
                    "matched": line.strip()[:120],
                    "pattern": pattern,
                    "message": msg,
                })
    return findings


def scan_docs(docs_dir: str = "docs", allowlist: list[str] | None = None) -> dict:
    allow = set(allowlist or ALLOWLIST)
    findings = []
    for md in sorted(Path(docs_dir).rglob("*.md")):
        if md.name in allow:
            continue
        findings.extend(scan_file(md))

    by_file: dict[str, list] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    return {
        "files_scanned": len(list(Path(docs_dir).rglob("*.md"))),
        "total_findings": len(findings),
        "files_with_findings": len(by_file),
        "findings": findings[:50],
        "detail_by_file": {k: len(v) for k, v in by_file.items()},
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check for overclaiming language")
    parser.add_argument("--path", default="docs", help="Directory to scan")
    parser.add_argument("--fail-on-findings", action="store_true",
                        help="Exit 3 if findings exist")
    args = parser.parse_args()

    result = scan_docs(docs_dir=args.path)
    print(f"Files scanned: {result['files_scanned']}")
    print(f"Finding count: {result['total_findings']}")
    if result["detail_by_file"]:
        print("\nFiles with findings:")
        for f, count in sorted(result["detail_by_file"].items()):
            print(f"  {f}: {count}")
    for f in result["findings"][:10]:
        print(f"\n  ❌ {f['file']}:{f['line']}")
        print(f"     {f['matched']}")
        print(f"     → {f['message']}")

    if args.fail_on_findings and result["total_findings"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
