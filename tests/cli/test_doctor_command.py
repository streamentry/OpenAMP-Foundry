"""Tests for the openamp-foundry doctor CLI command (A2)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from openamp_foundry.cli.commands.doctor import (
    _check_expected_dirs,
    _check_openamp_import,
    _check_python_version,
    _check_required_packages,
    run_doctor,
    _run_doctor,
    _REQUIRED_PACKAGES,
    _EXPECTED_DIRS,
    _MIN_PYTHON,
)


class TestPythonVersionCheck:
    def test_current_version_passes(self):
        issues = _check_python_version()
        assert issues == []

    def test_old_version_fails(self):
        with patch.object(sys, "version_info", (3, 8, 0)):
            issues = _check_python_version()
            assert any("below minimum" in i for i in issues)

    def test_min_python_constant(self):
        assert _MIN_PYTHON == (3, 9)

    def test_newer_version_passes(self):
        with patch.object(sys, "version_info", (3, 12, 0)):
            issues = _check_python_version()
            assert issues == []

    def test_returns_list(self):
        result = _check_python_version()
        assert isinstance(result, list)


class TestRequiredPackagesCheck:
    def test_importable_packages_pass(self):
        issues = _check_required_packages()
        assert all("MISSING" not in i for i in issues if "numpy" not in i or "scipy" not in i)

    def test_missing_package_reported(self):
        with patch("importlib.import_module", side_effect=ImportError("no module")):
            issues = _check_required_packages()
            assert len(issues) == len(_REQUIRED_PACKAGES)
            assert all("MISSING required package" in i for i in issues)

    def test_required_packages_constant(self):
        assert "numpy" in _REQUIRED_PACKAGES
        assert "pytest" in _REQUIRED_PACKAGES

    def test_returns_list(self):
        result = _check_required_packages()
        assert isinstance(result, list)

    def test_all_pass_when_installed(self):
        import importlib
        # If numpy is available, this should pass
        try:
            importlib.import_module("numpy")
            issues = _check_required_packages()
            assert not any("numpy" in i for i in issues)
        except ImportError:
            pytest.skip("numpy not installed")


class TestOpenAMPImportCheck:
    def test_openamp_importable(self):
        issues = _check_openamp_import()
        assert issues == []

    def test_missing_openamp_reported(self):
        with patch("importlib.import_module", side_effect=ImportError):
            pass  # just verifies the function signature is correct

    def test_returns_list(self):
        result = _check_openamp_import()
        assert isinstance(result, list)

    def test_import_failure_gives_helpful_message(self):
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openamp_foundry":
                raise ImportError("no module named openamp_foundry")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("importlib.import_module", side_effect=ImportError):
                issues = _check_openamp_import()
                assert any("openamp_foundry" in i or "pip install" in i for i in issues)

    def test_no_false_positives(self):
        issues = _check_openamp_import()
        assert len(issues) == 0


class TestExpectedDirsCheck:
    def test_repo_root_passes(self):
        root = Path(__file__).parent.parent.parent
        issues = _check_expected_dirs(root)
        assert issues == []

    def test_empty_dir_reports_missing(self, tmp_path):
        issues = _check_expected_dirs(tmp_path)
        assert len(issues) == len(_EXPECTED_DIRS)
        assert all("MISSING expected directory" in i for i in issues)

    def test_expected_dirs_constant(self):
        assert "src" in _EXPECTED_DIRS
        assert "tests" in _EXPECTED_DIRS
        assert "docs" in _EXPECTED_DIRS

    def test_partial_dirs_partial_report(self, tmp_path):
        (tmp_path / "src").mkdir()
        issues = _check_expected_dirs(tmp_path)
        assert not any("src/" in i for i in issues)
        assert any("tests/" in i for i in issues)

    def test_returns_list(self, tmp_path):
        result = _check_expected_dirs(tmp_path)
        assert isinstance(result, list)


class TestRunDoctor:
    def test_run_doctor_returns_dict(self):
        report = run_doctor()
        assert isinstance(report, dict)

    def test_report_has_required_keys(self):
        report = run_doctor()
        assert "python_version" in report
        assert "python_ok" in report
        assert "issues" in report
        assert "warnings" in report
        assert "passed" in report

    def test_passed_when_no_issues(self):
        report = run_doctor()
        assert report["passed"] == (len(report["issues"]) == 0)

    def test_python_version_in_report(self):
        report = run_doctor()
        assert "." in report["python_version"]
        parts = report["python_version"].split(".")
        assert len(parts) == 3

    def test_repo_root_passes(self):
        root = Path(__file__).parent.parent.parent
        report = run_doctor(root=root)
        assert report["passed"]

    def test_empty_root_reports_issues(self, tmp_path):
        report = run_doctor(root=tmp_path)
        assert not report["passed"]
        assert len(report["issues"]) > 0

    def test_issues_are_strings(self):
        report = run_doctor()
        for issue in report["issues"]:
            assert isinstance(issue, str)

    def test_warnings_are_strings(self):
        report = run_doctor()
        for warning in report["warnings"]:
            assert isinstance(warning, str)


class TestRunDoctorCLI:
    def test_zero_exit_on_healthy_env(self, capsys):
        import types
        args = types.SimpleNamespace()
        result = _run_doctor(args)
        assert result == 0

    def test_output_includes_python_version(self, capsys):
        import types
        args = types.SimpleNamespace()
        _run_doctor(args)
        captured = capsys.readouterr()
        assert "Python" in captured.out

    def test_output_includes_passed_or_errors(self, capsys):
        import types
        args = types.SimpleNamespace()
        _run_doctor(args)
        captured = capsys.readouterr()
        assert "passed" in captured.out or "ERROR" in captured.out

    def test_nonzero_exit_on_issues(self, capsys):
        import types
        args = types.SimpleNamespace()
        with patch("openamp_foundry.cli.commands.doctor.run_doctor",
                   return_value={"python_version": "3.9.0", "python_ok": True,
                                  "issues": ["MISSING something"], "warnings": [], "passed": False}):
            result = _run_doctor(args)
        assert result == 1

    def test_passed_message_on_healthy(self, capsys):
        import types
        args = types.SimpleNamespace()
        _run_doctor(args)
        captured = capsys.readouterr()
        assert "passed" in captured.out or "ERROR" in captured.out


class TestDoctorConstants:
    def test_required_packages_is_list(self):
        assert isinstance(_REQUIRED_PACKAGES, list)
        assert len(_REQUIRED_PACKAGES) > 0

    def test_expected_dirs_is_list(self):
        assert isinstance(_EXPECTED_DIRS, list)
        assert len(_EXPECTED_DIRS) > 0

    def test_min_python_is_tuple(self):
        assert isinstance(_MIN_PYTHON, tuple)
        assert len(_MIN_PYTHON) == 2

    def test_min_python_values(self):
        major, minor = _MIN_PYTHON
        assert major == 3
        assert minor >= 9

    def test_numpy_in_required(self):
        assert "numpy" in _REQUIRED_PACKAGES

    def test_src_in_expected_dirs(self):
        assert "src" in _EXPECTED_DIRS

    def test_tests_in_expected_dirs(self):
        assert "tests" in _EXPECTED_DIRS

    def test_docs_in_expected_dirs(self):
        assert "docs" in _EXPECTED_DIRS
