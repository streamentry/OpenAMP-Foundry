"""Tests for J3 docs coverage report."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from openamp_foundry.checks.docs_coverage import (
    DocsCoverageEntry,
    DocsCoverageReport,
    _extract_module_name,
    _has_module_docstring,
    check_docs_coverage,
    format_docs_coverage_report,
)


class TestDocsCoverageEntryConstants:
    def test_entry_is_dataclass(self):
        entry = DocsCoverageEntry(
            module_path="/x/y.py",
            module_name="y",
            has_module_docstring=True,
            docstring_preview="A module.",
        )
        assert entry.module_path == "/x/y.py"

    def test_entry_no_docstring(self):
        entry = DocsCoverageEntry(
            module_path="/x/y.py",
            module_name="y",
            has_module_docstring=False,
            docstring_preview="",
        )
        assert not entry.has_module_docstring

    def test_report_is_dataclass(self):
        report = DocsCoverageReport(
            total_modules=2,
            covered_modules=1,
            uncovered_modules=1,
            coverage_fraction=0.5,
            entries=[],
            is_fully_covered=False,
            coverage_summary="1/2 covered.",
        )
        assert report.total_modules == 2


class TestExtractModuleName:
    def test_simple_module(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        py = src / "foo.py"
        py.touch()
        name = _extract_module_name(py, src)
        assert name == "foo"

    def test_nested_module(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        py = pkg / "bar.py"
        py.touch()
        name = _extract_module_name(py, src)
        assert name == "pkg.bar"

    def test_init_stripped(self, tmp_path):
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        init = pkg / "__init__.py"
        init.touch()
        name = _extract_module_name(init, src)
        assert name == "pkg"

    def test_deeply_nested(self, tmp_path):
        src = tmp_path / "src"
        deep = src / "a" / "b" / "c"
        deep.mkdir(parents=True)
        py = deep / "module.py"
        py.touch()
        name = _extract_module_name(py, src)
        assert name == "a.b.c.module"

    def test_outside_source_dir(self, tmp_path):
        other = tmp_path / "other" / "x.py"
        other.parent.mkdir(parents=True)
        other.touch()
        name = _extract_module_name(other, tmp_path / "src")
        assert name == "x"


class TestHasModuleDocstring:
    def test_with_docstring(self, tmp_path):
        py = tmp_path / "a.py"
        py.write_text('"""Module docstring."""\n\nx = 1\n')
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is True
        assert "Module docstring" in preview

    def test_without_docstring(self, tmp_path):
        py = tmp_path / "b.py"
        py.write_text("x = 1\n")
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is False
        assert preview == ""

    def test_comment_not_docstring(self, tmp_path):
        py = tmp_path / "c.py"
        py.write_text("# This is a comment\nx = 1\n")
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is False

    def test_multiline_docstring(self, tmp_path):
        py = tmp_path / "d.py"
        py.write_text('"""\nFirst line.\nSecond line.\n"""\n\nx = 1\n')
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is True

    def test_long_docstring_truncated(self, tmp_path):
        py = tmp_path / "e.py"
        long_doc = "A" * 200
        py.write_text(f'"""{long_doc}"""\n')
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is True
        assert len(preview) <= 83

    def test_empty_file(self, tmp_path):
        py = tmp_path / "f.py"
        py.write_text("")
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is False

    def test_syntax_error_returns_false(self, tmp_path):
        py = tmp_path / "g.py"
        py.write_text("def broken(:\n")
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is False

    def test_single_quoted_docstring(self, tmp_path):
        py = tmp_path / "h.py"
        py.write_text("'Single quoted docstring.'\n\nx = 1\n")
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is True

    def test_string_not_first_stmt_not_docstring(self, tmp_path):
        py = tmp_path / "i.py"
        py.write_text('x = 1\n"""Not a docstring."""\n')
        has_doc, preview = _has_module_docstring(py)
        assert has_doc is False


class TestCheckDocsCoverage:
    def _make_src(self, tmp_path, modules: dict) -> Path:
        src = tmp_path / "src"
        src.mkdir()
        for name, content in modules.items():
            parts = name.split("/")
            parent = src
            for part in parts[:-1]:
                parent = parent / part
                parent.mkdir(exist_ok=True)
            (parent / parts[-1]).write_text(content)
        return src

    def test_all_documented(self, tmp_path):
        src = self._make_src(tmp_path, {
            "a.py": '"""Module A."""\n',
            "b.py": '"""Module B."""\n',
        })
        report = check_docs_coverage(src)
        assert report.is_fully_covered is True

    def test_some_undocumented(self, tmp_path):
        src = self._make_src(tmp_path, {
            "a.py": '"""Module A."""\n',
            "b.py": "x = 1\n",
        })
        report = check_docs_coverage(src)
        assert report.total_modules == 2
        assert report.covered_modules == 1
        assert report.uncovered_modules == 1
        assert not report.is_fully_covered

    def test_empty_directory(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        report = check_docs_coverage(src)
        assert report.total_modules == 0
        assert "No Python modules found" in report.coverage_summary

    def test_coverage_fraction(self, tmp_path):
        src = self._make_src(tmp_path, {
            "a.py": '"""A."""\n',
            "b.py": '"""B."""\n',
            "c.py": "x = 1\n",
            "d.py": "y = 2\n",
        })
        report = check_docs_coverage(src)
        assert abs(report.coverage_fraction - 0.5) < 0.01

    def test_exclude_init(self, tmp_path):
        src = self._make_src(tmp_path, {
            "__init__.py": "",
            "a.py": '"""A."""\n',
        })
        report = check_docs_coverage(src, exclude_init=True)
        assert report.total_modules == 1

    def test_include_init_by_default(self, tmp_path):
        src = self._make_src(tmp_path, {
            "__init__.py": "",
            "a.py": '"""A."""\n',
        })
        report = check_docs_coverage(src)
        assert report.total_modules == 2

    def test_returns_report(self, tmp_path):
        src = self._make_src(tmp_path, {"a.py": '"""A."""\n'})
        report = check_docs_coverage(src)
        assert isinstance(report, DocsCoverageReport)

    def test_entries_list(self, tmp_path):
        src = self._make_src(tmp_path, {
            "a.py": '"""A."""\n',
            "b.py": "x = 1\n",
        })
        report = check_docs_coverage(src)
        assert len(report.entries) == 2

    def test_nested_modules_found(self, tmp_path):
        src = self._make_src(tmp_path, {
            "pkg/a.py": '"""A."""\n',
            "pkg/b.py": "x = 1\n",
        })
        report = check_docs_coverage(src)
        assert report.total_modules == 2

    def test_string_path_accepted(self, tmp_path):
        src = self._make_src(tmp_path, {"a.py": '"""A."""\n'})
        report = check_docs_coverage(str(src))
        assert report.total_modules == 1

    def test_100_percent_message(self, tmp_path):
        src = self._make_src(tmp_path, {"a.py": '"""A."""\n'})
        report = check_docs_coverage(src)
        assert "100%" in report.coverage_summary

    def test_partial_message_shows_fraction(self, tmp_path):
        src = self._make_src(tmp_path, {
            "a.py": '"""A."""\n',
            "b.py": "x = 1\n",
        })
        report = check_docs_coverage(src)
        assert "50%" in report.coverage_summary or "1/2" in report.coverage_summary


class TestFormatDocsCoverageReport:
    def _make_report(self, entries):
        covered = sum(1 for e in entries if e.has_module_docstring)
        uncovered = len(entries) - covered
        total = len(entries)
        fraction = covered / total if total > 0 else 0.0
        return DocsCoverageReport(
            total_modules=total,
            covered_modules=covered,
            uncovered_modules=uncovered,
            coverage_fraction=fraction,
            entries=entries,
            is_fully_covered=uncovered == 0 and total > 0,
            coverage_summary=f"{covered}/{total} covered",
        )

    def test_returns_string(self):
        report = self._make_report([])
        text = format_docs_coverage_report(report)
        assert isinstance(text, str)

    def test_contains_summary(self):
        report = self._make_report([])
        text = format_docs_coverage_report(report)
        assert "0/0 covered" in text

    def test_shows_undocumented_section(self):
        entries = [
            DocsCoverageEntry("x.py", "x", False, ""),
        ]
        report = self._make_report(entries)
        text = format_docs_coverage_report(report)
        assert "Undocumented" in text
        assert "x" in text

    def test_shows_documented_section(self):
        entries = [
            DocsCoverageEntry("y.py", "y", True, "Module Y."),
        ]
        report = self._make_report(entries)
        text = format_docs_coverage_report(report)
        assert "Documented" in text
        assert "y" in text

    def test_preview_shown_for_documented(self):
        entries = [
            DocsCoverageEntry("z.py", "z", True, "Module for testing things."),
        ]
        report = self._make_report(entries)
        text = format_docs_coverage_report(report)
        assert "Module for testing things" in text

    def test_no_undocumented_section_when_all_covered(self):
        entries = [
            DocsCoverageEntry("a.py", "a", True, "Module A."),
        ]
        report = self._make_report(entries)
        text = format_docs_coverage_report(report)
        assert "Undocumented modules" not in text

    def test_no_documented_section_when_none_covered(self):
        entries = [
            DocsCoverageEntry("a.py", "a", False, ""),
        ]
        report = self._make_report(entries)
        text = format_docs_coverage_report(report)
        assert "Documented modules" not in text
