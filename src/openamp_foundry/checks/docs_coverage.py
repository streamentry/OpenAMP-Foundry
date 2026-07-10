"""
Docs coverage report for Python modules.

J3: Shows what is and isn't documented. Scans Python modules in a source
directory and reports which ones have module-level docstrings.
A module without a docstring is an undocumented module — a gap in the
knowledge base that agents and reviewers may trip over.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocsCoverageEntry:
    """Coverage entry for a single Python module."""

    module_path: str
    module_name: str
    has_module_docstring: bool
    docstring_preview: str


@dataclass
class DocsCoverageReport:
    """Aggregate docs coverage report for a source directory."""

    total_modules: int
    covered_modules: int
    uncovered_modules: int
    coverage_fraction: float
    entries: list[DocsCoverageEntry]
    is_fully_covered: bool
    coverage_summary: str


def _extract_module_name(module_path: Path, source_dir: Path) -> str:
    """
    Convert an absolute module path to a dotted module name relative to source_dir.

    e.g. /path/to/src/openamp_foundry/evidence/foo.py
         -> openamp_foundry.evidence.foo
    """
    try:
        relative = module_path.relative_to(source_dir)
    except ValueError:
        return module_path.stem
    parts = list(relative.parts)
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else module_path.stem


def _has_module_docstring(source_path: Path) -> tuple[bool, str]:
    """
    Return (has_docstring, preview) by parsing the module's AST.

    Returns (False, "") if the file cannot be parsed.
    """
    try:
        source = source_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return False, ""

    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        docstring = tree.body[0].value.value.strip()
        preview = docstring[:80] + ("..." if len(docstring) > 80 else "")
        return True, preview

    return False, ""


def check_docs_coverage(
    source_dir: str | Path,
    glob_pattern: str = "**/*.py",
    exclude_init: bool = False,
) -> DocsCoverageReport:
    """
    Scan all Python modules in source_dir and report module-level docstring coverage.

    Args:
        source_dir: Root directory to scan.
        glob_pattern: Glob pattern for Python files (default: all .py files).
        exclude_init: If True, skip __init__.py files (they rarely have docstrings).
    """
    source_dir = Path(source_dir)
    entries: list[DocsCoverageEntry] = []

    for py_file in sorted(source_dir.glob(glob_pattern)):
        if not py_file.is_file():
            continue
        if exclude_init and py_file.name == "__init__.py":
            continue

        module_name = _extract_module_name(py_file, source_dir)
        has_docstring, preview = _has_module_docstring(py_file)

        entries.append(
            DocsCoverageEntry(
                module_path=str(py_file),
                module_name=module_name,
                has_module_docstring=has_docstring,
                docstring_preview=preview,
            )
        )

    total = len(entries)
    covered = sum(1 for e in entries if e.has_module_docstring)
    uncovered = total - covered
    fraction = covered / total if total > 0 else 0.0
    is_fully = uncovered == 0 and total > 0

    if total == 0:
        summary = "No Python modules found."
    elif is_fully:
        summary = f"All {total} module(s) have docstrings. Coverage: 100%."
    else:
        summary = (
            f"{covered}/{total} module(s) have docstrings "
            f"({fraction:.0%} coverage). "
            f"{uncovered} undocumented."
        )

    return DocsCoverageReport(
        total_modules=total,
        covered_modules=covered,
        uncovered_modules=uncovered,
        coverage_fraction=fraction,
        entries=entries,
        is_fully_covered=is_fully,
        coverage_summary=summary,
    )


def format_docs_coverage_report(report: DocsCoverageReport) -> str:
    """Return a human-readable docs coverage report."""
    lines: list[str] = [
        "Docs Coverage Report",
        f"  {report.coverage_summary}",
        "",
    ]

    if report.uncovered_modules > 0:
        lines.append(f"Undocumented modules ({report.uncovered_modules}):")
        for entry in report.entries:
            if not entry.has_module_docstring:
                lines.append(f"  - {entry.module_name}")
        lines.append("")

    if report.covered_modules > 0:
        lines.append(f"Documented modules ({report.covered_modules}):")
        for entry in report.entries:
            if entry.has_module_docstring:
                preview = f" — {entry.docstring_preview}" if entry.docstring_preview else ""
                lines.append(f"  + {entry.module_name}{preview}")

    return "\n".join(lines)
