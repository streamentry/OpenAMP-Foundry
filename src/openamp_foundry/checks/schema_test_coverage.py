"""Cross-reference checker: ensures schema modules have matching test modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_TEST_COVERAGE_REPORT_ID_PREFIX = "STC-"

SCHEMA_SOURCE_DIRS: frozenset = frozenset(
    {
        "src/openamp_foundry/evidence",
        "src/openamp_foundry/export",
        "src/openamp_foundry/interop",
        "src/openamp_foundry/versioning",
        "src/openamp_foundry/calibration",
        "src/openamp_foundry/scoring",
        "src/openamp_foundry/changelog",
        "src/openamp_foundry/checks",
        "src/openamp_foundry/simulation",
    }
)

TEST_ROOT_DIR: str = "tests"

IGNORED_MODULES: frozenset = frozenset(
    {
        "__init__",
        "conftest",
    }
)

VALID_COVERAGE_TIERS: frozenset = frozenset(
    {"full", "partial", "missing", "excluded"}
)


@dataclass
class SchemaTestCoverageEntry:
    schema_module: str
    schema_path: str
    expected_test_path: str
    test_exists: bool
    coverage_tier: str


@dataclass
class SchemaTestCoverageReport:
    report_id: str
    total_schema_modules: int
    covered_modules: int
    missing_test_modules: int
    coverage_fraction: float
    entries: list = field(default_factory=list)
    is_fully_covered: bool = False
    uncovered_modules: list = field(default_factory=list)
    coverage_summary: str = ""


def _module_name_from_path(schema_path: Path, source_dir: Path) -> str:
    rel = schema_path.relative_to(source_dir)
    parts = list(rel.with_suffix("").parts)
    return ".".join(parts)


def _expected_test_path(schema_path: Path, repo_root: Path) -> Path:
    rel = schema_path.relative_to(repo_root / "src" / "openamp_foundry")
    test_path = repo_root / TEST_ROOT_DIR / rel.with_name("test_" + rel.name)
    return test_path


def check_schema_test_coverage(
    repo_root: Path,
    source_dirs: frozenset | None = None,
) -> SchemaTestCoverageReport:
    if source_dirs is None:
        source_dirs = SCHEMA_SOURCE_DIRS

    entries: list[SchemaTestCoverageEntry] = []

    for dir_rel in sorted(source_dirs):
        dir_path = repo_root / dir_rel
        if not dir_path.exists():
            continue
        for schema_path in sorted(dir_path.glob("*.py")):
            module_stem = schema_path.stem
            if module_stem in IGNORED_MODULES:
                continue
            module_name = _module_name_from_path(schema_path, repo_root / "src" / "openamp_foundry")
            expected_test = _expected_test_path(schema_path, repo_root)
            test_exists = expected_test.exists()
            tier = "full" if test_exists else "missing"
            entries.append(
                SchemaTestCoverageEntry(
                    schema_module=module_name,
                    schema_path=str(schema_path.relative_to(repo_root)),
                    expected_test_path=str(expected_test.relative_to(repo_root)),
                    test_exists=test_exists,
                    coverage_tier=tier,
                )
            )

    total = len(entries)
    covered = sum(1 for e in entries if e.test_exists)
    missing = total - covered
    fraction = covered / total if total > 0 else 1.0
    uncovered = [e.schema_module for e in entries if not e.test_exists]

    return SchemaTestCoverageReport(
        report_id=f"{SCHEMA_TEST_COVERAGE_REPORT_ID_PREFIX}001",
        total_schema_modules=total,
        covered_modules=covered,
        missing_test_modules=missing,
        coverage_fraction=fraction,
        entries=entries,
        is_fully_covered=(missing == 0),
        uncovered_modules=uncovered,
        coverage_summary=(
            f"{covered}/{total} schema modules have test files "
            f"({fraction * 100:.1f}% coverage)"
        ),
    )


def format_schema_test_coverage_report(report: SchemaTestCoverageReport) -> str:
    lines: list[str] = []
    lines.append(f"Schema-Test Coverage Report ({report.report_id})")
    lines.append(f"  {report.coverage_summary}")
    lines.append(f"  Total schema modules: {report.total_schema_modules}")
    lines.append(f"  Covered: {report.covered_modules}")
    lines.append(f"  Missing test files: {report.missing_test_modules}")
    lines.append(f"  Fully covered: {report.is_fully_covered}")
    if report.uncovered_modules:
        lines.append("  Missing test modules:")
        for name in sorted(report.uncovered_modules):
            lines.append(f"    - {name}")
    return "\n".join(lines) + "\n"
