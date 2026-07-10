"""Schema-test cross-reference checker — Phase J J9.

Ensures every schema file in schemas/ has at least one test file that
references it. Prevents schema drift where schemas are added or modified
without corresponding tests being updated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SchemaCoverageEntry:
    schema_name: str
    schema_path: str
    is_covered: bool
    referencing_tests: list[str] = field(default_factory=list)


@dataclass
class SchemaCoverageReport:
    total_schemas: int
    covered_schemas: int
    uncovered_schemas: int
    entries: list[SchemaCoverageEntry] = field(default_factory=list)
    is_complete: bool = False
    coverage_summary: str = ""


def _extract_schema_name(schema_path: Path) -> str:
    """Extract the base schema name from a .schema.json path."""
    name = schema_path.name
    if name.endswith(".schema.json"):
        return name[: -len(".schema.json")]
    return schema_path.stem


def _find_test_references(
    schema_name: str,
    tests_dir: Path,
    pattern: str | None = None,
) -> list[str]:
    """Find test files that reference the given schema name.

    A test file 'references' a schema if:
    - The schema_name appears verbatim in the file content, OR
    - A test filename contains the schema_name (without separators).

    Returns a sorted list of matching test file paths (relative to tests_dir).
    """
    if pattern is None:
        escaped = re.escape(schema_name)
        pattern = escaped

    references: list[str] = []
    for test_file in sorted(tests_dir.rglob("test_*.py")):
        try:
            content = test_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if re.search(pattern, content, re.IGNORECASE):
            references.append(str(test_file.relative_to(tests_dir.parent)))
            continue
        # Also match if schema_name (with underscores→hyphens or vice versa) appears
        alt_name = schema_name.replace("_", "-")
        if re.search(re.escape(alt_name), content, re.IGNORECASE):
            references.append(str(test_file.relative_to(tests_dir.parent)))
    return sorted(set(references))


def check_schema_test_coverage(
    schemas_dir: Path,
    tests_dir: Path,
    schema_glob: str = "*.schema.json",
) -> SchemaCoverageReport:
    """Check that every schema in schemas_dir is referenced in at least one test.

    Args:
        schemas_dir: Directory containing *.schema.json files.
        tests_dir: Root directory for test files (searched recursively).
        schema_glob: Glob pattern for schema files. Default: '*.schema.json'.

    Returns:
        SchemaCoverageReport listing covered and uncovered schemas.
    """
    schema_files = sorted(schemas_dir.glob(schema_glob))
    entries: list[SchemaCoverageEntry] = []

    for schema_path in schema_files:
        name = _extract_schema_name(schema_path)
        refs = _find_test_references(name, tests_dir)
        entries.append(SchemaCoverageEntry(
            schema_name=name,
            schema_path=str(schema_path),
            is_covered=len(refs) > 0,
            referencing_tests=refs,
        ))

    covered = sum(1 for e in entries if e.is_covered)
    uncovered = len(entries) - covered
    is_complete = uncovered == 0

    if is_complete and entries:
        summary = (
            f"All {len(entries)} schema(s) have at least one referencing test."
        )
    elif not entries:
        summary = "No schemas found — check schemas_dir path."
    else:
        missing = [e.schema_name for e in entries if not e.is_covered]
        summary = (
            f"{uncovered}/{len(entries)} schema(s) have no referencing tests: "
            f"{missing}. Add tests or update existing ones to reference these schemas."
        )

    return SchemaCoverageReport(
        total_schemas=len(entries),
        covered_schemas=covered,
        uncovered_schemas=uncovered,
        entries=entries,
        is_complete=is_complete,
        coverage_summary=summary,
    )


def format_schema_coverage_report(report: SchemaCoverageReport) -> str:
    """Format a SchemaCoverageReport as a human-readable string."""
    lines = [
        "=== SCHEMA-TEST COVERAGE REPORT ===",
        f"Total schemas: {report.total_schemas}",
        f"Covered: {report.covered_schemas}",
        f"Uncovered: {report.uncovered_schemas}",
        "",
        "-- SCHEMA COVERAGE --",
    ]
    for entry in sorted(report.entries, key=lambda e: e.schema_name):
        status = "OK" if entry.is_covered else "MISSING"
        lines.append(f"  [{status}] {entry.schema_name}")
        if entry.referencing_tests:
            for ref in entry.referencing_tests[:3]:
                lines.append(f"         ← {ref}")
            if len(entry.referencing_tests) > 3:
                lines.append(f"         ← ... and {len(entry.referencing_tests) - 3} more")
    lines.extend([
        "",
        f"COMPLETE: {'YES' if report.is_complete else 'NO'}",
        "",
        report.coverage_summary,
    ])
    if not report.is_complete:
        lines.extend([
            "",
            "ACTION REQUIRED: Add or update tests to reference uncovered schemas.",
            "A schema without tests can drift silently — schema changes go undetected.",
        ])
    return "\n".join(lines)
