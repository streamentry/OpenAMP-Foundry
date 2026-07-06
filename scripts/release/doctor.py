#!/usr/bin/env python3
"""Environment readiness checks for OpenAMP Foundry contributors.

This is intentionally lightweight: it does not run the scientific pipeline and it
does not validate claims. It answers the first onboarding question: does this
checkout look ready to run the documented commands?
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Callable, Iterable

REQUIRED_PATHS = [
    "pyproject.toml",
    "README.md",
    "Makefile",
    "src/openamp_foundry",
    "configs",
    "examples",
    "schemas",
    "tests",
    "outputs",
]

OPTIONAL_TOOLS = ["git", "ruff", "pytest"]


def _status(ok: bool, label: str, detail: str) -> dict[str, str | bool]:
    return {"ok": ok, "label": label, "detail": detail}


def _check_python_version(
    version_info: tuple[int, int, int],
    minimum: tuple[int, int],
) -> dict[str, str | bool]:
    current = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
    required = f"{minimum[0]}.{minimum[1]}+"
    ok = (version_info[0], version_info[1]) >= minimum
    detail = f"Python {current}; required {required}"
    return _status(ok, "python_version", detail)


def _check_required_paths(root: Path, paths: Iterable[str]) -> list[dict[str, str | bool]]:
    checks = []
    for rel in paths:
        path = root / rel
        checks.append(_status(path.exists(), f"path:{rel}", "present" if path.exists() else "missing"))
    return checks


def _check_optional_tools(
    tools: Iterable[str],
    which: Callable[[str], str | None],
) -> list[dict[str, str | bool]]:
    checks = []
    for tool in tools:
        found = which(tool)
        detail = found if found else "not found on PATH"
        checks.append(_status(found is not None, f"tool:{tool}", detail))
    return checks


def run_doctor(
    root: str | Path = ".",
    version_info: tuple[int, int, int] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, object]:
    """Return a machine-readable readiness report for this checkout."""
    root_p = Path(root).resolve()
    if version_info is None:
        version_info = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

    required_checks = [_check_python_version(version_info, (3, 11))]
    required_checks.extend(_check_required_paths(root_p, REQUIRED_PATHS))
    optional_checks = _check_optional_tools(OPTIONAL_TOOLS, which)

    failures = [check for check in required_checks if not check["ok"]]
    warnings = [check for check in optional_checks if not check["ok"]]
    return {
        "ok": not failures,
        "root": str(root_p),
        "required": required_checks,
        "optional": optional_checks,
        "failure_count": len(failures),
        "warning_count": len(warnings),
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = ["# OpenAMP Foundry doctor", ""]
    lines.append("Status: **PASS**" if report["ok"] else "Status: **FAIL**")
    lines.append(f"Root: `{report['root']}`")
    lines.append("")
    lines.append("## Required checks")
    for check in report["required"]:  # type: ignore[index]
        marker = "✅" if check["ok"] else "❌"
        lines.append(f"- {marker} `{check['label']}` — {check['detail']}")
    lines.append("")
    lines.append("## Optional tools")
    for check in report["optional"]:  # type: ignore[index]
        marker = "✅" if check["ok"] else "⚠️"
        lines.append(f"- {marker} `{check['label']}` — {check['detail']}")
    lines.append("")
    lines.append("Doctor only checks environment/readiness. It does not prove scientific validity.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether this checkout is ready to run OpenAMP")
    parser.add_argument("--root", default=".", help="Repository root to check")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    report = run_doctor(args.root)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_render_markdown(report))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
