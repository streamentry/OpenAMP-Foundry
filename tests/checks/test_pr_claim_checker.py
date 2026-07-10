"""Tests for pr_claim_checker module (D3)."""
from __future__ import annotations

import pytest
from pathlib import Path

from openamp_foundry.checks.pr_claim_checker import (
    ClaimViolation,
    PRClaimReport,
    PR_ALLOWLIST,
    PR_RISKY_PATTERNS,
    SCANNABLE_EXTENSIONS,
    _is_allowlisted,
    _scan_file,
    check_pr_claims,
    format_pr_claim_report,
)


# --- ClaimViolation ---

class TestClaimViolation:
    def test_is_dataclass(self):
        v = ClaimViolation(
            file_path="docs/foo.md",
            line_number=3,
            matched_text="This is proven",
            pattern=r"\bproven\b",
            explanation="Avoid proven",
        )
        assert isinstance(v, ClaimViolation)

    def test_fields_accessible(self):
        v = ClaimViolation("f.py", 1, "text", r"\bproven\b", "msg")
        assert v.file_path == "f.py"
        assert v.line_number == 1
        assert v.matched_text == "text"
        assert v.pattern == r"\bproven\b"
        assert v.explanation == "msg"

    def test_line_number_stored(self):
        v = ClaimViolation("x.md", 42, "line", "p", "e")
        assert v.line_number == 42

    def test_matched_text_stored(self):
        v = ClaimViolation("x.md", 1, "matched content", "p", "e")
        assert v.matched_text == "matched content"

    def test_explanation_stored(self):
        v = ClaimViolation("x.md", 1, "t", "p", "do not use proven")
        assert "proven" in v.explanation


# --- PRClaimReport ---

class TestPRClaimReport:
    def test_is_dataclass(self):
        r = PRClaimReport(files_scanned=0, files_with_violations=0, total_violations=0)
        assert isinstance(r, PRClaimReport)

    def test_default_is_clean(self):
        r = PRClaimReport(files_scanned=5, files_with_violations=0, total_violations=0)
        assert r.is_clean is True

    def test_default_violations_empty(self):
        r = PRClaimReport(files_scanned=0, files_with_violations=0, total_violations=0)
        assert r.violations == []

    def test_fields_accessible(self):
        r = PRClaimReport(files_scanned=3, files_with_violations=1, total_violations=2)
        assert r.files_scanned == 3
        assert r.files_with_violations == 1
        assert r.total_violations == 2

    def test_summary_stored(self):
        r = PRClaimReport(0, 0, 0, summary="all good")
        assert r.summary == "all good"


# --- _is_allowlisted ---

class TestIsAllowlisted:
    def test_allowlisted_by_name(self, tmp_path):
        f = tmp_path / "AGENTS.md"
        f.write_text("content")
        assert _is_allowlisted(f, PR_ALLOWLIST) is True

    def test_not_allowlisted(self, tmp_path):
        f = tmp_path / "new_doc.md"
        f.write_text("content")
        assert _is_allowlisted(f, PR_ALLOWLIST) is False

    def test_check_claims_allowlisted(self, tmp_path):
        f = tmp_path / "check_claims.py"
        f.write_text("content")
        assert _is_allowlisted(f, PR_ALLOWLIST) is True

    def test_mission_allowlisted(self, tmp_path):
        f = tmp_path / "MISSION.md"
        f.write_text("content")
        assert _is_allowlisted(f, PR_ALLOWLIST) is True

    def test_custom_allowlist(self, tmp_path):
        f = tmp_path / "custom.md"
        f.write_text("content")
        custom = frozenset({"custom.md"})
        assert _is_allowlisted(f, custom) is True

    def test_empty_allowlist_never_matches(self, tmp_path):
        f = tmp_path / "AGENTS.md"
        f.write_text("content")
        assert _is_allowlisted(f, frozenset()) is False


# --- _scan_file ---

class TestScanFile:
    def test_no_violations_clean_file(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("This is a computationally nominated candidate.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert result == []

    def test_detects_proven(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("This peptide is proven to work.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result) >= 1
        assert any(r"\bproven\b" == v.pattern for v in result)

    def test_detects_drug_candidate(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("This is a drug candidate for treatment.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert any("drug candidate" in v.pattern for v in result)

    def test_detects_cure(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("This peptide can cure infections.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert any(r"\bcure\b" == v.pattern for v in result)

    def test_detects_effective_in_humans(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("It is effective in humans.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result) >= 1

    def test_line_number_correct(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("line one\nline two\nThis is proven.\n")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        proven = [v for v in result if r"\bproven\b" == v.pattern]
        assert proven[0].line_number == 3

    def test_matched_text_truncated(self, tmp_path):
        f = tmp_path / "bad.md"
        long_line = "This is proven " + "x" * 200
        f.write_text(long_line)
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result[0].matched_text) <= 120

    def test_case_insensitive(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("PROVEN effective.")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result) >= 1

    def test_python_file_scanned(self, tmp_path):
        f = tmp_path / "module.py"
        f.write_text('"""This is proven to work."""\n')
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result) >= 1

    def test_nonexistent_file_returns_empty(self, tmp_path):
        f = tmp_path / "does_not_exist.md"
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert result == []

    def test_multiple_violations_same_file(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("This is proven.\nAlso effective in humans.\n")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert len(result) >= 2

    def test_file_path_stored(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("proven")
        result = _scan_file(f, PR_RISKY_PATTERNS)
        assert str(f) in result[0].file_path


# --- check_pr_claims ---

class TestCheckPRClaims:
    def test_empty_files_list(self):
        report = check_pr_claims([])
        assert report.files_scanned == 0
        assert report.is_clean is True

    def test_clean_file_no_violations(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("This is a computationally nominated dry-lab candidate.")
        report = check_pr_claims([f])
        assert report.is_clean is True
        assert report.total_violations == 0

    def test_file_with_violation_detected(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("This peptide is proven to work.")
        report = check_pr_claims([f])
        assert report.is_clean is False
        assert report.total_violations >= 1

    def test_returns_prclaim_report(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("clean")
        report = check_pr_claims([f])
        assert isinstance(report, PRClaimReport)

    def test_files_scanned_count(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("clean")
        f2.write_text("also clean")
        report = check_pr_claims([f1, f2])
        assert report.files_scanned == 2

    def test_allowlisted_file_not_scanned(self, tmp_path):
        f = tmp_path / "AGENTS.md"
        f.write_text("proven drug candidate cures")
        report = check_pr_claims([f])
        assert report.files_scanned == 0
        assert report.is_clean is True

    def test_unscannable_extension_skipped(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("proven")
        report = check_pr_claims([f])
        assert report.files_scanned == 0

    def test_nonexistent_file_skipped(self, tmp_path):
        f = tmp_path / "missing.md"
        report = check_pr_claims([f])
        assert report.files_scanned == 0

    def test_files_with_violations_count(self, tmp_path):
        f1 = tmp_path / "bad.md"
        f2 = tmp_path / "ok.md"
        f1.write_text("proven")
        f2.write_text("computationally nominated")
        report = check_pr_claims([f1, f2])
        assert report.files_with_violations == 1

    def test_violations_list_populated(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("this is proven to work")
        report = check_pr_claims([f])
        assert len(report.violations) >= 1
        assert isinstance(report.violations[0], ClaimViolation)

    def test_custom_patterns_used(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("CUSTOM_FORBIDDEN appears here")
        custom = [("CUSTOM_FORBIDDEN", "do not use this")]
        report = check_pr_claims([f], patterns=custom)
        assert report.total_violations >= 1

    def test_custom_allowlist_applied(self, tmp_path):
        f = tmp_path / "skip_me.md"
        f.write_text("proven")
        report = check_pr_claims([f], allowlist=frozenset({"skip_me.md"}))
        assert report.files_scanned == 0

    def test_custom_extensions_applied(self, tmp_path):
        f = tmp_path / "data.xyz"
        f.write_text("proven")
        report = check_pr_claims([f], extensions=frozenset({".xyz"}))
        assert report.files_scanned == 1

    def test_summary_nonempty(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("clean")
        report = check_pr_claims([f])
        assert len(report.summary) > 0

    def test_clean_summary_no_violations(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("clean")
        report = check_pr_claims([f])
        assert "No forbidden" in report.summary or "no forbidden" in report.summary.lower()

    def test_violation_summary_mentions_count(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("this is proven")
        report = check_pr_claims([f])
        assert "1" in report.summary

    def test_python_file_extension_scanned(self, tmp_path):
        f = tmp_path / "module.py"
        f.write_text('"""proven"""')
        report = check_pr_claims([f])
        assert report.files_scanned == 1

    def test_rst_file_scanned(self, tmp_path):
        f = tmp_path / "doc.rst"
        f.write_text("proven")
        report = check_pr_claims([f])
        assert report.files_scanned == 1

    def test_multiple_violations_in_one_file(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("proven\neffective in humans\ncure all infections")
        report = check_pr_claims([f])
        assert report.total_violations >= 2

    def test_is_clean_true_for_no_violations(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("dry-lab candidate selected for review")
        report = check_pr_claims([f])
        assert report.is_clean is True

    def test_is_clean_false_for_violations(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("proven drug candidate")
        report = check_pr_claims([f])
        assert report.is_clean is False

    def test_violation_file_path_matches(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("proven")
        report = check_pr_claims([f])
        assert str(f) in report.violations[0].file_path

    def test_violation_line_number_positive(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("proven")
        report = check_pr_claims([f])
        assert report.violations[0].line_number >= 1

    def test_pr_risky_patterns_not_empty(self):
        assert len(PR_RISKY_PATTERNS) > 0

    def test_pr_allowlist_not_empty(self):
        assert len(PR_ALLOWLIST) > 0

    def test_scannable_extensions_contains_md(self):
        assert ".md" in SCANNABLE_EXTENSIONS


# --- format_pr_claim_report ---

class TestFormatPRClaimReport:
    def _clean_report(self, tmp_path) -> PRClaimReport:
        f = tmp_path / "clean.md"
        f.write_text("computationally nominated")
        return check_pr_claims([f])

    def _violation_report(self, tmp_path) -> PRClaimReport:
        f = tmp_path / "bad.md"
        f.write_text("this is proven to work")
        return check_pr_claims([f])

    def test_returns_string(self, tmp_path):
        r = self._clean_report(tmp_path)
        assert isinstance(format_pr_claim_report(r), str)

    def test_contains_header(self, tmp_path):
        r = self._clean_report(tmp_path)
        assert "PR CLAIM LANGUAGE CHECK" in format_pr_claim_report(r)

    def test_clean_result_shown(self, tmp_path):
        r = self._clean_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "CLEAN" in text

    def test_violation_result_shown(self, tmp_path):
        r = self._violation_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "VIOLATION" in text

    def test_notice_in_violation_report(self, tmp_path):
        r = self._violation_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "NOTICE" in text

    def test_files_scanned_shown(self, tmp_path):
        r = self._clean_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "Files scanned" in text

    def test_violation_count_shown(self, tmp_path):
        r = self._violation_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "Violations" in text

    def test_summary_in_output(self, tmp_path):
        r = self._clean_report(tmp_path)
        text = format_pr_claim_report(r)
        assert r.summary in text

    def test_violation_file_path_in_output(self, tmp_path):
        r = self._violation_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "bad.md" in text

    def test_computational_notice_in_violation(self, tmp_path):
        r = self._violation_report(tmp_path)
        text = format_pr_claim_report(r)
        assert "computational" in text.lower() or "Computational" in text
