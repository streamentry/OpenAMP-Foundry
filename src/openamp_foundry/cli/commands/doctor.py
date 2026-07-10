"""CLI doctor command: checks environment health and reports issues."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


_REQUIRED_PACKAGES = [
    "numpy",
    "scipy",
    "pandas",
    "pytest",
]

_OPTIONAL_PACKAGES = [
    "opencode",
    "gh",
]

_EXPECTED_DIRS = [
    "src",
    "tests",
    "docs",
    "schemas",
    "scripts",
]

_MIN_PYTHON = (3, 9)


def _check_python_version() -> list[str]:
    """Return list of issues with Python version."""
    issues = []
    major, minor = sys.version_info[:2]
    if (major, minor) < _MIN_PYTHON:
        issues.append(
            f"Python {major}.{minor} is below minimum {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}"
        )
    return issues


def _check_required_packages() -> list[str]:
    """Return list of missing required packages."""
    missing = []
    for pkg in _REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(f"MISSING required package: {pkg}")
    return missing


def _check_openamp_import() -> list[str]:
    """Return list of issues with openamp_foundry import."""
    issues = []
    try:
        import openamp_foundry  # noqa: F401
    except ImportError:
        issues.append(
            "openamp_foundry not importable — run: pip install -e ."
        )
    return issues


def _check_expected_dirs(root: Path) -> list[str]:
    """Return list of missing expected directories."""
    missing = []
    for d in _EXPECTED_DIRS:
        if not (root / d).is_dir():
            missing.append(f"MISSING expected directory: {d}/")
    return missing


def run_doctor(root: Path | None = None) -> dict:
    """Run all environment checks and return a report dict."""
    if root is None:
        root = Path.cwd()

    issues: list[str] = []
    warnings: list[str] = []

    issues.extend(_check_python_version())
    issues.extend(_check_required_packages())
    issues.extend(_check_openamp_import())
    issues.extend(_check_expected_dirs(root))

    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_ok": not any("Python" in i for i in issues),
        "issues": issues,
        "warnings": warnings,
        "passed": len(issues) == 0,
    }


def _run_doctor(args) -> int:
    """CLI entry point for openamp-foundry doctor."""
    report = run_doctor()

    print(f"Python: {report['python_version']} {'OK' if report['python_ok'] else 'FAIL'}")

    if report["passed"]:
        print("doctor: all checks passed")
        return 0

    for issue in report["issues"]:
        print(f"  ERROR: {issue}")

    for warning in report["warnings"]:
        print(f"  WARN: {warning}")

    print(f"doctor: {len(report['issues'])} issue(s) found")
    return 1
