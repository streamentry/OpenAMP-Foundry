"""PR claim checker — Phase D D3.

Scans files staged for a PR for forbidden claim language in both
markdown prose and Python docstrings/comments. Agents can run this
before creating a PR to catch overclaiming before review.

Extends scripts/safety/check_claims.py (markdown-only) to cover
Python source files as well.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


PR_RISKY_PATTERNS: list[tuple[str, str]] = [
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
]

PR_ALLOWLIST: frozenset[str] = frozenset({
    "AGENTS.md",
    "CLAIM_REVIEW_CHECKLIST.md",
    "MISSION.md",
    "check_claims.py",
    "pr_claim_checker.py",
    "test_pr_claim_checker.py",
    "test_certificate_claim_discipline.py",
})

SCANNABLE_EXTENSIONS: frozenset[str] = frozenset({".md", ".py", ".rst", ".txt"})


@dataclass
class ClaimViolation:
    file_path: str
    line_number: int
    matched_text: str
    pattern: str
    explanation: str


@dataclass
class PRClaimReport:
    files_scanned: int
    files_with_violations: int
    total_violations: int
    violations: list[ClaimViolation] = field(default_factory=list)
    is_clean: bool = True
    summary: str = ""


def _is_allowlisted(path: Path, allowlist: frozenset[str]) -> bool:
    """Check if a path's filename is in the allowlist."""
    return path.name in allowlist


def _scan_file(path: Path, patterns: list[tuple[str, str]]) -> list[ClaimViolation]:
    """Scan a single file for forbidden claim patterns."""
    violations: list[ClaimViolation] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations
    for i, line in enumerate(text.splitlines(), 1):
        for pattern, explanation in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(ClaimViolation(
                    file_path=str(path),
                    line_number=i,
                    matched_text=line.strip()[:120],
                    pattern=pattern,
                    explanation=explanation,
                ))
    return violations


def check_pr_claims(
    files: list[Path],
    patterns: list[tuple[str, str]] | None = None,
    allowlist: frozenset[str] | None = None,
    extensions: frozenset[str] | None = None,
) -> PRClaimReport:
    """Scan a list of files for forbidden claim language.

    Args:
        files: List of file paths to scan.
        patterns: Override default PR_RISKY_PATTERNS.
        allowlist: Files to skip (by name). Defaults to PR_ALLOWLIST.
        extensions: Only scan these file extensions. Defaults to SCANNABLE_EXTENSIONS.

    Returns:
        PRClaimReport with all violations found.
    """
    if patterns is None:
        patterns = PR_RISKY_PATTERNS
    if allowlist is None:
        allowlist = PR_ALLOWLIST
    if extensions is None:
        extensions = SCANNABLE_EXTENSIONS

    all_violations: list[ClaimViolation] = []
    files_scanned = 0
    files_with_violations = 0

    for path in files:
        if not path.exists() or not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        if _is_allowlisted(path, allowlist):
            continue
        files_scanned += 1
        file_violations = _scan_file(path, patterns)
        if file_violations:
            files_with_violations += 1
            all_violations.extend(file_violations)

    is_clean = len(all_violations) == 0

    if is_clean:
        summary = f"No forbidden claim language found in {files_scanned} scanned files."
    else:
        summary = (
            f"Found {len(all_violations)} potential overclaiming violation(s) "
            f"in {files_with_violations}/{files_scanned} files. "
            "Review and fix before PR creation."
        )

    return PRClaimReport(
        files_scanned=files_scanned,
        files_with_violations=files_with_violations,
        total_violations=len(all_violations),
        violations=all_violations,
        is_clean=is_clean,
        summary=summary,
    )


def format_pr_claim_report(report: PRClaimReport) -> str:
    """Format a PRClaimReport as a human-readable string."""
    lines = [
        "=== PR CLAIM LANGUAGE CHECK ===",
        f"Files scanned: {report.files_scanned}",
        f"Violations: {report.total_violations}",
        f"Files with violations: {report.files_with_violations}",
        "",
    ]
    if report.is_clean:
        lines.append("RESULT: CLEAN — no forbidden claim language found.")
    else:
        lines.append(f"RESULT: {report.total_violations} VIOLATION(S) FOUND")
        lines.append("")
        lines.append("-- VIOLATIONS --")
        for v in report.violations:
            lines.extend([
                f"  File: {v.file_path}:{v.line_number}",
                f"  Text: {v.matched_text}",
                f"  Rule: {v.explanation}",
                "",
            ])
        lines.extend([
            "NOTICE: Fix all violations before creating a PR.",
            "Computational outputs are not biological proof.",
            "Use 'computationally nominated', 'dry-lab candidate', or",
            "'selected for review' instead of proven/validated language.",
        ])
    lines.extend(["", report.summary])
    return "\n".join(lines)
