"""Environment diagnostic script.

Usage:
    python scripts/doctor.py
    make doctor
"""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


def check() -> list[dict]:
    results = []

    # Python version
    py_version = sys.version.split()[0]
    major, minor, *_ = py_version.split(".")
    ok = int(major) >= 3 and int(minor) >= 11
    results.append({"check": "python_version", "status": "pass" if ok else "fail",
                     "detail": f"Python {py_version} (need >=3.11)"})

    # Package installed
    try:
        import openamp_foundry  # noqa: F401
        results.append({"check": "package_installed", "status": "pass",
                         "detail": "openamp-foundry package found"})
    except ImportError:
        results.append({"check": "package_installed", "status": "fail",
                         "detail": "openamp-foundry not importable (run: pip install -e .)"})

    # Required directories
    for d in ["configs", "schemas", "examples/sequences", "examples/validation"]:
        exists = Path(d).exists()
        results.append({"check": f"dir_{d.replace('/', '_')}", "status": "pass" if exists else "fail",
                         "detail": f"{'/' + d}"})

    # Key dependencies
    for mod in ["yaml", "jsonschema"]:
        try:
            importlib.import_module(mod)
            results.append({"check": f"dep_{mod}", "status": "pass", "detail": f"{mod} installed"})
        except ImportError:
            results.append({"check": f"dep_{mod}", "status": "fail", "detail": f"{mod} not installed"})

    return results


def main() -> int:
    results = check()
    n_pass = sum(1 for r in results if r["status"] == "pass")
    n_total = len(results)
    print(f"OpenAMP Foundry — Environment Diagnostic ({n_pass}/{n_total} checks passed)")
    print()
    for r in results:
        mark = "✓" if r["status"] == "pass" else "✗"
        print(f"  [{mark}] {r['check']}: {r['detail']}")
    print()
    if n_pass == n_total:
        print("All checks passed.")
        return 0
    else:
        print(f"{n_total - n_pass} check(s) failed. See detail above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
