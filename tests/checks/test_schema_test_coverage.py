"""Tests for schema_test_coverage module (J9)."""
from __future__ import annotations

import pytest
from pathlib import Path

from openamp_foundry.checks.schema_test_coverage import (
    SchemaCoverageEntry,
    SchemaCoverageReport,
    _extract_schema_name,
    _find_test_references,
    check_schema_test_coverage,
    format_schema_coverage_report,
)


# --- SchemaCoverageEntry ---

class TestSchemaCoverageEntry:
    def test_is_dataclass(self):
        e = SchemaCoverageEntry("my_schema", "/schemas/my_schema.schema.json", True)
        assert isinstance(e, SchemaCoverageEntry)

    def test_fields_accessible(self):
        e = SchemaCoverageEntry("benchmark_card", "/s/benchmark_card.schema.json", False)
        assert e.schema_name == "benchmark_card"
        assert e.is_covered is False

    def test_default_referencing_tests_empty(self):
        e = SchemaCoverageEntry("x", "/x.schema.json", True)
        assert e.referencing_tests == []

    def test_referencing_tests_stored(self):
        e = SchemaCoverageEntry("x", "/x.schema.json", True, ["tests/test_x.py"])
        assert e.referencing_tests == ["tests/test_x.py"]


# --- SchemaCoverageReport ---

class TestSchemaCoverageReport:
    def test_is_dataclass(self):
        r = SchemaCoverageReport(5, 3, 2)
        assert isinstance(r, SchemaCoverageReport)

    def test_fields_accessible(self):
        r = SchemaCoverageReport(10, 8, 2)
        assert r.total_schemas == 10
        assert r.covered_schemas == 8
        assert r.uncovered_schemas == 2

    def test_default_entries_empty(self):
        r = SchemaCoverageReport(0, 0, 0)
        assert r.entries == []

    def test_summary_stored(self):
        r = SchemaCoverageReport(1, 1, 0, summary="all good")
        assert r.coverage_summary == "all good"


# --- _extract_schema_name ---

class TestExtractSchemaName:
    def test_removes_schema_json_suffix(self, tmp_path):
        f = tmp_path / "benchmark_card.schema.json"
        assert _extract_schema_name(f) == "benchmark_card"

    def test_removes_double_suffix(self, tmp_path):
        f = tmp_path / "negative_result_entry.schema.json"
        assert _extract_schema_name(f) == "negative_result_entry"

    def test_plain_json_uses_stem(self, tmp_path):
        f = tmp_path / "myfile.json"
        assert _extract_schema_name(f) == "myfile"

    def test_underscore_preserved(self, tmp_path):
        f = tmp_path / "external_review_packet.schema.json"
        assert _extract_schema_name(f) == "external_review_packet"

    def test_short_name(self, tmp_path):
        f = tmp_path / "lab.schema.json"
        assert _extract_schema_name(f) == "lab"

    def test_name_only_no_path(self, tmp_path):
        f = tmp_path / "candidate.schema.json"
        result = _extract_schema_name(f)
        assert "candidate" in result


# --- _find_test_references ---

class TestFindTestReferences:
    def test_finds_reference_in_content(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_benchmark_card.py"
        tf.write_text("from x import benchmark_card\n")
        refs = _find_test_references("benchmark_card", tests)
        assert len(refs) >= 1

    def test_no_reference_returns_empty(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_other.py"
        tf.write_text("import something_else\n")
        refs = _find_test_references("benchmark_card", tests)
        assert refs == []

    def test_case_insensitive_match(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_x.py"
        tf.write_text("BENCHMARK_CARD schema is tested here\n")
        refs = _find_test_references("benchmark_card", tests)
        assert len(refs) >= 1

    def test_hyphen_alias_matched(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_x.py"
        tf.write_text("Uses benchmark-card schema here\n")
        refs = _find_test_references("benchmark_card", tests)
        assert len(refs) >= 1

    def test_nonexistent_tests_dir_returns_empty(self, tmp_path):
        missing = tmp_path / "nonexistent"
        refs = _find_test_references("anything", missing)
        assert refs == []

    def test_returns_sorted_list(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_z.py").write_text("my_schema")
        (tests / "test_a.py").write_text("my_schema")
        refs = _find_test_references("my_schema", tests)
        assert refs == sorted(refs)

    def test_multiple_test_files_all_found(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_one.py").write_text("my_schema content")
        (tests / "test_two.py").write_text("import my_schema")
        refs = _find_test_references("my_schema", tests)
        assert len(refs) == 2

    def test_only_test_py_files_scanned(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "helper.py").write_text("my_schema")
        (tests / "README.md").write_text("my_schema")
        refs = _find_test_references("my_schema", tests)
        assert refs == []

    def test_nested_test_files_found(self, tmp_path):
        tests = tmp_path / "tests"
        sub = tests / "evidence"
        sub.mkdir(parents=True)
        (sub / "test_nested.py").write_text("my_schema referenced here")
        refs = _find_test_references("my_schema", tests)
        assert len(refs) >= 1

    def test_custom_pattern_used(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_x.py").write_text("CUSTOM_PATTERN appears")
        refs = _find_test_references("anything", tests, pattern="CUSTOM_PATTERN")
        assert len(refs) >= 1

    def test_deduplication(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_x.py"
        tf.write_text("my_schema my_schema my_schema")
        refs = _find_test_references("my_schema", tests)
        assert len(refs) == 1

    def test_unreadable_file_skipped(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        tf = tests / "test_readable.py"
        tf.write_text("my_schema")
        refs = _find_test_references("my_schema", tests)
        assert len(refs) == 1


# --- check_schema_test_coverage ---

class TestCheckSchemaCoverage:
    def _make_schema(self, schemas_dir, name):
        f = schemas_dir / f"{name}.schema.json"
        f.write_text('{"title": "test"}')
        return f

    def _make_test(self, tests_dir, name, content):
        tests_dir.mkdir(parents=True, exist_ok=True)
        f = tests_dir / f"test_{name}.py"
        f.write_text(content)
        return f

    def test_returns_report(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "my_schema")
        self._make_test(tests, "my_schema", "my_schema referenced")
        report = check_schema_test_coverage(schemas, tests)
        assert isinstance(report, SchemaCoverageReport)

    def test_covered_schema_detected(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "benchmark_card")
        self._make_test(tests, "benchmark_card", "benchmark_card schema")
        report = check_schema_test_coverage(schemas, tests)
        assert report.covered_schemas == 1

    def test_uncovered_schema_detected(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "orphan_schema")
        report = check_schema_test_coverage(schemas, tests)
        assert report.uncovered_schemas == 1
        assert not report.is_complete

    def test_empty_schemas_dir(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        report = check_schema_test_coverage(schemas, tests)
        assert report.total_schemas == 0

    def test_multiple_schemas_mixed_coverage(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "covered")
        self._make_schema(schemas, "uncovered")
        self._make_test(tests, "covered", "covered schema here")
        report = check_schema_test_coverage(schemas, tests)
        assert report.covered_schemas == 1
        assert report.uncovered_schemas == 1

    def test_is_complete_when_all_covered(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "schema_a")
        self._make_schema(schemas, "schema_b")
        self._make_test(tests, "all", "schema_a and schema_b are both here")
        report = check_schema_test_coverage(schemas, tests)
        assert report.is_complete is True

    def test_not_complete_when_any_uncovered(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "covered")
        self._make_schema(schemas, "gap")
        self._make_test(tests, "covered", "covered mentioned here")
        report = check_schema_test_coverage(schemas, tests)
        assert report.is_complete is False

    def test_entries_count_matches_schemas(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        for i in range(3):
            self._make_schema(schemas, f"schema_{i}")
        report = check_schema_test_coverage(schemas, tests)
        assert len(report.entries) == 3

    def test_entry_schema_name_correct(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "my_schema")
        report = check_schema_test_coverage(schemas, tests)
        assert report.entries[0].schema_name == "my_schema"

    def test_total_schemas_correct(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "a")
        self._make_schema(schemas, "b")
        self._make_schema(schemas, "c")
        report = check_schema_test_coverage(schemas, tests)
        assert report.total_schemas == 3

    def test_summary_nonempty(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "s")
        report = check_schema_test_coverage(schemas, tests)
        assert len(report.coverage_summary) > 0

    def test_complete_summary_positive(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "x")
        self._make_test(tests, "x", "x schema")
        report = check_schema_test_coverage(schemas, tests)
        assert "all" in report.coverage_summary.lower() or report.is_complete

    def test_incomplete_summary_lists_names(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "orphan_xyz")
        report = check_schema_test_coverage(schemas, tests)
        assert "orphan_xyz" in report.coverage_summary

    def test_covered_entry_has_referencing_tests(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "my_schema")
        self._make_test(tests, "my", "my_schema is referenced")
        report = check_schema_test_coverage(schemas, tests)
        covered = [e for e in report.entries if e.is_covered]
        assert len(covered) == 1
        assert len(covered[0].referencing_tests) >= 1

    def test_uncovered_entry_has_empty_referencing_tests(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "lonely")
        report = check_schema_test_coverage(schemas, tests)
        assert report.entries[0].referencing_tests == []

    def test_non_schema_files_ignored(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        (schemas / "README.md").write_text("doc")
        (schemas / "config.json").write_text("{}")
        report = check_schema_test_coverage(schemas, tests)
        assert report.total_schemas == 0

    def test_custom_glob_pattern(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        (schemas / "only.schema.json").write_text("{}")
        (schemas / "other.json").write_text("{}")
        report = check_schema_test_coverage(schemas, tests, schema_glob="*.schema.json")
        assert report.total_schemas == 1

    def test_covered_and_uncovered_counts_sum_to_total(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "a")
        self._make_schema(schemas, "b")
        self._make_test(tests, "a", "a schema")
        report = check_schema_test_coverage(schemas, tests)
        assert report.covered_schemas + report.uncovered_schemas == report.total_schemas

    def test_nested_test_files_counted(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        sub = tests / "evidence"
        sub.mkdir(parents=True)
        self._make_schema(schemas, "nested_ref")
        (sub / "test_nested.py").write_text("nested_ref schema used here")
        report = check_schema_test_coverage(schemas, tests)
        assert report.covered_schemas == 1

    def test_single_test_covers_multiple_schemas(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "schema_a")
        self._make_schema(schemas, "schema_b")
        self._make_test(tests, "all", "schema_a and schema_b both covered")
        report = check_schema_test_coverage(schemas, tests)
        assert report.covered_schemas == 2

    def test_entry_schema_path_contains_name(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "named_schema")
        report = check_schema_test_coverage(schemas, tests)
        assert "named_schema" in report.entries[0].schema_path

    def test_is_complete_false_for_empty_schemas(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        report = check_schema_test_coverage(schemas, tests)
        assert not report.is_complete

    def test_all_entries_have_schema_path(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        self._make_schema(schemas, "x")
        report = check_schema_test_coverage(schemas, tests)
        assert all(e.schema_path for e in report.entries)

    def test_report_entries_list_length_matches(self, tmp_path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        for i in range(4):
            self._make_schema(schemas, f"s{i}")
        report = check_schema_test_coverage(schemas, tests)
        assert len(report.entries) == 4 == report.total_schemas


# --- format_schema_coverage_report ---

class TestFormatSchemaCoverageReport:
    def _covered_report(self, tmp_path) -> SchemaCoverageReport:
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        (schemas / "my_schema.schema.json").write_text("{}")
        (tests / "test_my.py").write_text("my_schema is here")
        return check_schema_test_coverage(schemas, tests)

    def _uncovered_report(self, tmp_path) -> SchemaCoverageReport:
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        (schemas / "orphan.schema.json").write_text("{}")
        return check_schema_test_coverage(schemas, tests)

    def test_returns_string(self, tmp_path):
        r = self._covered_report(tmp_path)
        assert isinstance(format_schema_coverage_report(r), str)

    def test_contains_header(self, tmp_path):
        r = self._covered_report(tmp_path)
        assert "SCHEMA-TEST COVERAGE" in format_schema_coverage_report(r)

    def test_covered_shows_ok(self, tmp_path):
        r = self._covered_report(tmp_path)
        assert "[OK]" in format_schema_coverage_report(r)

    def test_uncovered_shows_missing(self, tmp_path):
        r = self._uncovered_report(tmp_path)
        assert "[MISSING]" in format_schema_coverage_report(r)

    def test_complete_shows_yes(self, tmp_path):
        r = self._covered_report(tmp_path)
        assert "YES" in format_schema_coverage_report(r)

    def test_incomplete_shows_no(self, tmp_path):
        r = self._uncovered_report(tmp_path)
        assert "NO" in format_schema_coverage_report(r)

    def test_action_required_in_incomplete(self, tmp_path):
        r = self._uncovered_report(tmp_path)
        assert "ACTION REQUIRED" in format_schema_coverage_report(r)

    def test_summary_in_output(self, tmp_path):
        r = self._covered_report(tmp_path)
        text = format_schema_coverage_report(r)
        assert r.coverage_summary in text

    def test_schema_name_shown(self, tmp_path):
        r = self._uncovered_report(tmp_path)
        text = format_schema_coverage_report(r)
        assert "orphan" in text

    def test_counts_shown(self, tmp_path):
        r = self._covered_report(tmp_path)
        text = format_schema_coverage_report(r)
        assert "Total schemas" in text

    def test_covered_count_shown(self, tmp_path):
        r = self._covered_report(tmp_path)
        text = format_schema_coverage_report(r)
        assert "Covered" in text

    def test_no_action_required_when_complete(self, tmp_path):
        r = self._covered_report(tmp_path)
        text = format_schema_coverage_report(r)
        assert "ACTION REQUIRED" not in text
