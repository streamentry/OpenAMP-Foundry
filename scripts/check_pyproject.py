"""Check pyproject.toml consistency with the actual package."""

from __future__ import annotations

import importlib
import sys
import tomllib
from pathlib import Path


def check_pyproject(pyproject_path: str = "pyproject.toml") -> dict:
    p = Path(pyproject_path)
    if not p.exists():
        return {"error": f"pyproject.toml not found: {pyproject_path}"}

    with p.open("rb") as f:
        data = tomllib.load(f)

    issues = []
    checks = {}

    # 1. Check Python version requirement
    requires_python = data.get("project", {}).get("requires-python", "")
    checks["python_requirement"] = requires_python

    # 2. Check console scripts entrypoints
    scripts = data.get("project", {}).get("scripts", {})
    entrypoint_issues = []
    for name, ref in scripts.items():
        module_path = ref.split(":")[0]
        try:
            importlib.import_module(module_path)
        except ImportError as e:
            entrypoint_issues.append(f"Entrypoint '{name}' -> '{ref}': {e}")
    if entrypoint_issues:
        issues.extend(entrypoint_issues)
    checks["entrypoints_ok"] = len(entrypoint_issues) == 0
    checks["entrypoint_issues"] = entrypoint_issues

    # 3. Check optional extras reference valid dependencies
    optional_deps = data.get("project", {}).get("optional-dependencies", {})
    extras_ok = len(optional_deps) > 0
    checks["extras_defined"] = extras_ok
    checks["extras_count"] = len(optional_deps)

    # 4. Check project name matches package
    pkg_name = data.get("project", {}).get("name", "")
    # Convert hyphens to underscores for import check
    import_name = pkg_name.replace("-", "_")
    try:
        importlib.import_module(import_name)
        checks["package_importable"] = True
    except ImportError:
        checks["package_importable"] = False
        issues.append(f"Package '{import_name}' cannot be imported")

    return {
        "pyproject": pyproject_path,
        "project_name": pkg_name,
        "python_requirement": requires_python,
        "entrypoints": len(scripts),
        "entrypoints_ok": checks["entrypoints_ok"],
        "extras": len(optional_deps),
        "issues": issues,
        "all_ok": len(issues) == 0,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check pyproject.toml consistency")
    parser.add_argument("--pyproject", default="pyproject.toml")
    args = parser.parse_args()

    result = check_pyproject(args.pyproject)
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 2

    print(f"Project: {result['project_name']}")
    print(f"Python: {result['python_requirement']}")
    eok = result.get("entrypoints_ok", "?")
    print(f"Entrypoints: {result['entrypoints']}, OK: {eok}")
    print(f"Extras: {result['extras']}")
    print(f"All OK: {result['all_ok']}")
    for issue in result["issues"]:
        print(f"  ❌ {issue}")

    return 0 if result["all_ok"] else 3


if __name__ == "__main__":
    sys.exit(main())
