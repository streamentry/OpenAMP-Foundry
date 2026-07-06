"""Tests for the contributor doctor helper."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "release" / "doctor.py"
_SPEC = importlib.util.spec_from_file_location("_doctor", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
_doctor = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_doctor)


def _make_minimal_checkout(root: Path) -> None:
    for rel in [
        "src/openamp_foundry",
        "configs",
        "examples",
        "schemas",
        "tests",
        "outputs",
    ]:
        (root / rel).mkdir(parents=True)
    for rel in ["pyproject.toml", "README.md", "Makefile"]:
        (root / rel).write_text("placeholder\n", encoding="utf-8")


def _found_tool(tool: str) -> str:
    return f"/tool/{tool}"


def _missing_tool(_tool: str) -> None:
    return None


def test_run_doctor_passes_for_minimal_checkout(tmp_path: Path) -> None:
    _make_minimal_checkout(tmp_path)

    report = _doctor.run_doctor(
        root=tmp_path,
        version_info=(3, 11, 0),
        which=_found_tool,
    )

    assert report["ok"] is True
    assert report["failure_count"] == 0
    assert report["warning_count"] == 0


def test_run_doctor_fails_for_missing_required_path(tmp_path: Path) -> None:
    _make_minimal_checkout(tmp_path)
    (tmp_path / "schemas").rmdir()

    report = _doctor.run_doctor(
        root=tmp_path,
        version_info=(3, 11, 0),
        which=_found_tool,
    )

    assert report["ok"] is False
    assert report["failure_count"] == 1
    assert any(check["label"] == "path:schemas" for check in report["required"])


def test_run_doctor_warns_for_missing_optional_tool(tmp_path: Path) -> None:
    _make_minimal_checkout(tmp_path)

    report = _doctor.run_doctor(
        root=tmp_path,
        version_info=(3, 11, 0),
        which=_missing_tool,
    )

    assert report["ok"] is True
    assert report["warning_count"] == len(_doctor.OPTIONAL_TOOLS)
