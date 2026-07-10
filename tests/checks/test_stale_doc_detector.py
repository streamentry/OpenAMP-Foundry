"""Tests for J8 automated stale-doc detector."""

from __future__ import annotations

from pathlib import Path

import pytest

from openamp_foundry.checks.stale_doc_detector import (
    PATH_PREFIXES,
    SCANNABLE_EXTENSIONS,
    StaleDocReference,
    StaleDocReport,
    _find_path_references,
    _looks_like_repo_path,
    check_stale_doc_references,
    format_stale_doc_report,
)


class TestConstants:
    def test_path_prefixes_is_frozenset(self):
        assert isinstance(PATH_PREFIXES, frozenset)

    def test_src_in_prefixes(self):
        assert "src/" in PATH_PREFIXES

    def test_tests_in_prefixes(self):
        assert "tests/" in PATH_PREFIXES

    def test_scripts_in_prefixes(self):
        assert "scripts/" in PATH_PREFIXES

    def test_docs_in_prefixes(self):
        assert "docs/" in PATH_PREFIXES

    def test_schemas_in_prefixes(self):
        assert "schemas/" in PATH_PREFIXES

    def test_scannable_extensions_is_frozenset(self):
        assert isinstance(SCANNABLE_EXTENSIONS, frozenset)

    def test_md_in_extensions(self):
        assert ".md" in SCANNABLE_EXTENSIONS

    def test_rst_in_extensions(self):
        assert ".rst" in SCANNABLE_EXTENSIONS

    def test_txt_in_extensions(self):
        assert ".txt" in SCANNABLE_EXTENSIONS


class TestLooksLikeRepoPath:
    def test_src_prefix(self):
        assert _looks_like_repo_path("src/openamp_foundry/evidence/foo.py")

    def test_tests_prefix(self):
        assert _looks_like_repo_path("tests/evidence/test_foo.py")

    def test_scripts_prefix(self):
        assert _looks_like_repo_path("scripts/generate_changelog.py")

    def test_docs_prefix(self):
        assert _looks_like_repo_path("docs/AGENT_FAILURE_MODES.md")

    def test_schemas_prefix(self):
        assert _looks_like_repo_path("schemas/foo.schema.json")

    def test_http_url_false(self):
        assert not _looks_like_repo_path("http://example.com/file.py")

    def test_no_prefix_false(self):
        assert not _looks_like_repo_path("random_word")

    def test_short_name_false(self):
        assert not _looks_like_repo_path("foo.py")

    def test_decision_logs_prefix(self):
        assert _looks_like_repo_path("decision_logs/INDEX.md")


class TestFindPathReferences:
    def test_finds_src_reference(self, tmp_path):
        doc = tmp_path / "README.md"
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").touch()
        doc.write_text("See `src/foo.py` for details.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert len(refs) == 1
        assert refs[0].referenced_path == "src/foo.py"

    def test_existing_ref_is_valid(self, tmp_path):
        doc = tmp_path / "README.md"
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "foo.py").touch()
        doc.write_text("See `src/foo.py`.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert refs[0].exists is True

    def test_nonexistent_ref_is_stale(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("See `src/deleted_module.py`.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert len(refs) == 1
        assert refs[0].exists is False

    def test_ignores_non_prefix(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("Use `myvar` for this.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert len(refs) == 0

    def test_line_number_correct(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("Line 1\nLine 2\nSee `src/foo.py`.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert refs[0].line_number == 3

    def test_multiple_refs_same_line(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("See `src/a.py` and `src/b.py`.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert len(refs) == 2

    def test_doc_path_stored(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("See `src/x.py`.\n")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert refs[0].doc_path == str(doc)

    def test_empty_content(self, tmp_path):
        doc = tmp_path / "README.md"
        doc.write_text("")
        refs = _find_path_references(doc.read_text(), doc, tmp_path)
        assert refs == []


class TestCheckStaleDocReferences:
    def _setup(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        return docs, tmp_path

    def test_clean_report_when_all_exist(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (root / "src").mkdir()
        (root / "src" / "foo.py").touch()
        (docs / "guide.md").write_text("See `src/foo.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert report.is_clean is True

    def test_stale_ref_detected(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "guide.md").write_text("See `src/deleted.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert not report.is_clean
        assert report.stale_references == 1

    def test_docs_scanned_count(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "a.md").write_text("A\n")
        (docs / "b.md").write_text("B\n")
        report = check_stale_doc_references(docs, root)
        assert report.total_docs_scanned == 2

    def test_empty_docs_dir(self, tmp_path):
        docs, root = self._setup(tmp_path)
        report = check_stale_doc_references(docs, root)
        assert "No docs found" in report.summary

    def test_non_md_ignored_by_default(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "notes.txt").write_text("See `src/x.py`.\n")
        report = check_stale_doc_references(docs, root, extensions=frozenset({".md"}))
        assert report.total_docs_scanned == 0

    def test_txt_scanned_with_extension(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "notes.txt").write_text("See `src/x.py`.\n")
        report = check_stale_doc_references(docs, root, extensions=frozenset({".txt"}))
        assert report.total_docs_scanned == 1

    def test_stale_entries_populated(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "a.md").write_text("See `src/gone.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert len(report.stale_entries) == 1
        assert report.stale_entries[0].referenced_path == "src/gone.py"

    def test_report_type(self, tmp_path):
        docs, root = self._setup(tmp_path)
        report = check_stale_doc_references(docs, root)
        assert isinstance(report, StaleDocReport)

    def test_total_references_counted(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (root / "src").mkdir()
        (root / "src" / "a.py").touch()
        (docs / "a.md").write_text("See `src/a.py` and `src/missing.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert report.total_references_found == 2
        assert report.stale_references == 1

    def test_string_paths_accepted(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "a.md").write_text("text\n")
        report = check_stale_doc_references(str(docs), str(root))
        assert isinstance(report, StaleDocReport)

    def test_clean_summary_message(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (root / "src").mkdir()
        (root / "src" / "x.py").touch()
        (docs / "a.md").write_text("See `src/x.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert "valid" in report.summary.lower() or "No stale" in report.summary

    def test_stale_summary_message(self, tmp_path):
        docs, root = self._setup(tmp_path)
        (docs / "a.md").write_text("See `src/gone.py`.\n")
        report = check_stale_doc_references(docs, root)
        assert "stale" in report.summary.lower()


class TestFormatStaleDocReport:
    def _make_report(self, stale_entries, total_refs=None, docs_scanned=1):
        stale_count = len(stale_entries)
        total = total_refs if total_refs is not None else stale_count
        is_clean = stale_count == 0
        return StaleDocReport(
            total_docs_scanned=docs_scanned,
            total_references_found=total,
            stale_references=stale_count,
            stale_entries=stale_entries,
            is_clean=is_clean,
            summary="Clean." if is_clean else f"{stale_count} stale.",
        )

    def test_returns_string(self):
        report = self._make_report([])
        text = format_stale_doc_report(report)
        assert isinstance(text, str)

    def test_contains_summary(self):
        report = self._make_report([])
        text = format_stale_doc_report(report)
        assert "Clean" in text

    def test_shows_stale_entries(self):
        entries = [
            StaleDocReference("docs/guide.md", 5, "src/gone.py", False),
        ]
        report = self._make_report(entries)
        text = format_stale_doc_report(report)
        assert "src/gone.py" in text
        assert "docs/guide.md" in text

    def test_shows_line_number(self):
        entries = [
            StaleDocReference("docs/a.md", 42, "src/x.py", False),
        ]
        report = self._make_report(entries)
        text = format_stale_doc_report(report)
        assert "42" in text

    def test_no_stale_section_when_clean(self):
        report = self._make_report([])
        text = format_stale_doc_report(report)
        assert "Stale references:" not in text

    def test_shows_counts(self):
        report = self._make_report([], total_refs=5, docs_scanned=3)
        text = format_stale_doc_report(report)
        assert "5" in text
        assert "3" in text
