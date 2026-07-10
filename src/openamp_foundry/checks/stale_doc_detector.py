"""
Automated stale-doc detector.

J8: Reduces doc rot over time. Scans markdown documents for backtick-quoted
file paths (like `src/openamp_foundry/evidence/foo.py`) and verifies each
referenced path still exists in the repository. A stale reference is a path
that was once valid but no longer exists — a sign of doc rot.

This is complementary to check_doc_links.py (which checks markdown link
syntax `[text](url)`). This module finds bare path references in prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_BACKTICK_PATH_RE = re.compile(
    r"`([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)`"
)

PATH_PREFIXES: frozenset[str] = frozenset({
    "src/",
    "tests/",
    "scripts/",
    "docs/",
    "schemas/",
    "decision_logs/",
})

SCANNABLE_EXTENSIONS: frozenset[str] = frozenset({".md", ".rst", ".txt"})


@dataclass
class StaleDocReference:
    """A single stale (non-existent) file reference found in a doc."""

    doc_path: str
    line_number: int
    referenced_path: str
    exists: bool


@dataclass
class StaleDocReport:
    """Aggregate report of stale references across scanned docs."""

    total_docs_scanned: int
    total_references_found: int
    stale_references: int
    stale_entries: list[StaleDocReference]
    is_clean: bool
    summary: str


def _looks_like_repo_path(s: str) -> bool:
    """
    Return True if a backtick-quoted string looks like a repo-relative file path.

    Matches strings that start with a known prefix and contain a file extension.
    """
    return any(s.startswith(prefix) for prefix in PATH_PREFIXES)


def _find_path_references(
    content: str,
    doc_path: Path,
    repo_root: Path,
) -> list[StaleDocReference]:
    """
    Scan a doc's content for backtick-quoted repo-relative file paths.

    Returns a list of StaleDocReference for every reference found,
    with exists=True if the path still exists in the repo.
    """
    references: list[StaleDocReference] = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in _BACKTICK_PATH_RE.finditer(line):
            candidate = match.group(1)
            if not _looks_like_repo_path(candidate):
                continue
            target = repo_root / candidate
            references.append(
                StaleDocReference(
                    doc_path=str(doc_path),
                    line_number=line_num,
                    referenced_path=candidate,
                    exists=target.exists(),
                )
            )
    return references


def check_stale_doc_references(
    docs_dir: str | Path,
    repo_root: str | Path,
    extensions: frozenset[str] | None = None,
) -> StaleDocReport:
    """
    Scan all docs in docs_dir for stale (non-existent) file references.

    Args:
        docs_dir: Directory containing docs to scan.
        repo_root: Repository root (used to resolve referenced paths).
        extensions: File extensions to scan (default: .md, .rst, .txt).
    """
    docs_dir = Path(docs_dir)
    repo_root = Path(repo_root)
    if extensions is None:
        extensions = SCANNABLE_EXTENSIONS

    all_references: list[StaleDocReference] = []
    docs_scanned = 0

    for doc_file in sorted(docs_dir.rglob("*")):
        if not doc_file.is_file():
            continue
        if doc_file.suffix not in extensions:
            continue
        try:
            content = doc_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        refs = _find_path_references(content, doc_file, repo_root)
        all_references.extend(refs)
        docs_scanned += 1

    total_refs = len(all_references)
    stale = [r for r in all_references if not r.exists]
    stale_count = len(stale)
    is_clean = stale_count == 0

    if docs_scanned == 0:
        summary = "No docs found to scan."
    elif is_clean:
        summary = (
            f"All {total_refs} reference(s) in {docs_scanned} doc(s) are valid. "
            f"No stale references."
        )
    else:
        summary = (
            f"{stale_count} stale reference(s) found in {docs_scanned} doc(s) "
            f"({total_refs} total references checked)."
        )

    return StaleDocReport(
        total_docs_scanned=docs_scanned,
        total_references_found=total_refs,
        stale_references=stale_count,
        stale_entries=stale,
        is_clean=is_clean,
        summary=summary,
    )


def format_stale_doc_report(report: StaleDocReport) -> str:
    """Return a human-readable stale-doc report."""
    lines: list[str] = [
        "Stale Doc Reference Report",
        f"  {report.summary}",
        "",
        f"  Docs scanned:          {report.total_docs_scanned}",
        f"  Total references:      {report.total_references_found}",
        f"  Stale references:      {report.stale_references}",
        "",
    ]
    if report.stale_entries:
        lines.append("Stale references:")
        for entry in report.stale_entries:
            lines.append(
                f"  {entry.doc_path}:{entry.line_number} "
                f"→ `{entry.referenced_path}` (not found)"
            )
    return "\n".join(lines)
