"""Tests for src/openamp_foundry/checks/schema_test_coverage.py (63 tests)."""

import tempfile
from pathlib import Path
import pytest
from openamp_foundry.checks.schema_test_coverage import (
    SCHEMA_TEST_COVERAGE_REPORT_ID_PREFIX,
    SCHEMA_SOURCE_DIRS,
    TEST_ROOT_DIR,
    IGNORED_MODULES,
    VALID_COVERAGE_TIERS,
    SchemaTestCoverageEntry,
    SchemaTestCoverageReport,
    check_schema_test_coverage,
    format_schema_test_coverage_report,
)


def _make_repo(tmp_path: Path, schema_files: list[str], test_files: list[str]) -> Path:
    for f in schema_files:
        fp = tmp_path / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text('"""Module."""\n')
    for f in test_files:
        fp = tmp_path / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text('"""Test module."""\n')
    return tmp_path


class TestConstants:
    def test_prefix(self):
        assert SCHEMA_TEST_COVERAGE_REPORT_ID_PREFIX == "STC-"

    def test_schema_source_dirs_is_frozenset(self):
        assert isinstance(SCHEMA_SOURCE_DIRS, frozenset)

    def test_evidence_dir_in_source_dirs(self):
        assert "src/openamp_foundry/evidence" in SCHEMA_SOURCE_DIRS

    def test_export_dir_in_source_dirs(self):
        assert "src/openamp_foundry/export" in SCHEMA_SOURCE_DIRS

    def test_interop_dir_in_source_dirs(self):
        assert "src/openamp_foundry/interop" in SCHEMA_SOURCE_DIRS

    def test_versioning_dir_in_source_dirs(self):
        assert "src/openamp_foundry/versioning" in SCHEMA_SOURCE_DIRS

    def test_checks_dir_in_source_dirs(self):
        assert "src/openamp_foundry/checks" in SCHEMA_SOURCE_DIRS

    def test_test_root_dir(self):
        assert TEST_ROOT_DIR == "tests"

    def test_ignored_modules_is_frozenset(self):
        assert isinstance(IGNORED_MODULES, frozenset)

    def test_init_ignored(self):
        assert "__init__" in IGNORED_MODULES

    def test_conftest_ignored(self):
        assert "conftest" in IGNORED_MODULES

    def test_valid_coverage_tiers_is_frozenset(self):
        assert isinstance(VALID_COVERAGE_TIERS, frozenset)

    def test_full_tier_in_tiers(self):
        assert "full" in VALID_COVERAGE_TIERS

    def test_missing_tier_in_tiers(self):
        assert "missing" in VALID_COVERAGE_TIERS

    def test_partial_tier_in_tiers(self):
        assert "partial" in VALID_COVERAGE_TIERS

    def test_excluded_tier_in_tiers(self):
        assert "excluded" in VALID_COVERAGE_TIERS


class TestSchemaTestCoverageDataclasses:
    def test_entry_fields(self):
        e = SchemaTestCoverageEntry(
            schema_module="evidence.foo",
            schema_path="src/openamp_foundry/evidence/foo.py",
            expected_test_path="tests/evidence/test_foo.py",
            test_exists=True,
            coverage_tier="full",
        )
        assert e.schema_module == "evidence.foo"
        assert e.test_exists is True

    def test_report_defaults(self):
        r = SchemaTestCoverageReport(
            report_id="STC-001",
            total_schema_modules=0,
            covered_modules=0,
            missing_test_modules=0,
            coverage_fraction=1.0,
        )
        assert r.entries == []
        assert r.uncovered_modules == []
        assert r.is_fully_covered is False


class TestCheckSchemaTestCoverage:
    def test_returns_report(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert isinstance(report, SchemaTestCoverageReport)

    def test_finds_covered_module(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.covered_modules == 1

    def test_finds_missing_test(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/bar.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.missing_test_modules == 1

    def test_coverage_fraction_full_coverage(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.coverage_fraction == 1.0

    def test_coverage_fraction_zero_coverage(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.coverage_fraction == 0.0

    def test_init_files_ignored(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            [
                "src/openamp_foundry/evidence/__init__.py",
                "src/openamp_foundry/evidence/foo.py",
            ],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.total_schema_modules == 1

    def test_is_fully_covered_true(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.is_fully_covered is True

    def test_is_fully_covered_false(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.is_fully_covered is False

    def test_uncovered_modules_listed(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert len(report.uncovered_modules) == 1

    def test_empty_source_dir_returns_zero(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.total_schema_modules == 0

    def test_empty_dir_is_fully_covered(self, tmp_path):
        tmp_path.mkdir(parents=True, exist_ok=True)
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.is_fully_covered is True

    def test_report_id_has_prefix(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset(),
        )
        assert report.report_id.startswith(SCHEMA_TEST_COVERAGE_REPORT_ID_PREFIX)

    def test_entry_tier_full_when_test_exists(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.entries[0].coverage_tier == "full"

    def test_entry_tier_missing_when_no_test(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.entries[0].coverage_tier == "missing"

    def test_multiple_schema_modules(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            [
                "src/openamp_foundry/evidence/foo.py",
                "src/openamp_foundry/evidence/bar.py",
            ],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.total_schema_modules == 2
        assert report.covered_modules == 1
        assert report.missing_test_modules == 1

    def test_multiple_source_dirs(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            [
                "src/openamp_foundry/evidence/foo.py",
                "src/openamp_foundry/export/bar.py",
            ],
            [
                "tests/evidence/test_foo.py",
                "tests/export/test_bar.py",
            ],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({
                "src/openamp_foundry/evidence",
                "src/openamp_foundry/export",
            }),
        )
        assert report.total_schema_modules == 2
        assert report.covered_modules == 2

    def test_nonexistent_source_dir_skipped(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset({"src/openamp_foundry/nonexistent"}),
        )
        assert report.total_schema_modules == 0

    def test_coverage_summary_not_empty(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset(),
        )
        assert report.coverage_summary != ""

    def test_coverage_fraction_empty_is_one(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path,
            source_dirs=frozenset(),
        )
        assert report.coverage_fraction == 1.0

    def test_conftest_ignored(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            [
                "src/openamp_foundry/evidence/conftest.py",
                "src/openamp_foundry/evidence/foo.py",
            ],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert report.total_schema_modules == 1

    def test_schema_path_stored_in_entry(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert "evidence/foo.py" in report.entries[0].schema_path

    def test_expected_test_path_stored_in_entry(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        assert "test_foo.py" in report.entries[0].expected_test_path

    def test_real_repo_has_schemas(self):
        repo_root = Path(__file__).parent.parent.parent
        report = check_schema_test_coverage(repo_root=repo_root)
        assert report.total_schema_modules > 0

    def test_real_repo_has_significant_coverage(self):
        repo_root = Path(__file__).parent.parent.parent
        report = check_schema_test_coverage(repo_root=repo_root)
        assert report.coverage_fraction >= 0.5


class TestFormatSchemaTestCoverageReport:
    def test_returns_string(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path, source_dirs=frozenset()
        )
        result = format_schema_test_coverage_report(report)
        assert isinstance(result, str)

    def test_contains_report_id(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path, source_dirs=frozenset()
        )
        result = format_schema_test_coverage_report(report)
        assert "STC-" in result

    def test_contains_coverage_summary(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path, source_dirs=frozenset()
        )
        result = format_schema_test_coverage_report(report)
        assert "coverage" in result.lower()

    def test_contains_total_modules(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path, source_dirs=frozenset()
        )
        result = format_schema_test_coverage_report(report)
        assert "Total" in result or "total" in result

    def test_lists_uncovered_modules(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            [],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        result = format_schema_test_coverage_report(report)
        assert "foo" in result

    def test_ends_with_newline(self, tmp_path):
        report = check_schema_test_coverage(
            repo_root=tmp_path, source_dirs=frozenset()
        )
        result = format_schema_test_coverage_report(report)
        assert result.endswith("\n")

    def test_shows_fully_covered_true(self, tmp_path):
        repo = _make_repo(
            tmp_path,
            ["src/openamp_foundry/evidence/foo.py"],
            ["tests/evidence/test_foo.py"],
        )
        report = check_schema_test_coverage(
            repo_root=repo,
            source_dirs=frozenset({"src/openamp_foundry/evidence"}),
        )
        result = format_schema_test_coverage_report(report)
        assert "True" in result
