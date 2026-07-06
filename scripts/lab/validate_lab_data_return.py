"""Validate lab data return files against the lab result schema.

Checks each JSON file in a directory against schemas/lab_result.schema.json
and reports clear per-file error messages.

Usage:
    python scripts/validate_lab_data_return.py --results-dir outputs/lab_results/
    python scripts/validate_lab_data_return.py --results-dir outputs/lab_results/ --verbose
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openamp_foundry.evidence.schemas import validate_json_schema


def validate_lab_results_dir(
    results_dir: str,
    schema_path: str = "schemas/lab_result.schema.json",
) -> dict:
    """Validate all JSON files in a directory against the lab result schema.

    Returns dict with per-file results and summary.
    """
    dir_p = Path(results_dir)
    schema_p = Path(schema_path)

    if not dir_p.exists():
        return {"error": f"Results directory not found: {results_dir}"}
    if not schema_p.exists():
        return {"error": f"Schema not found: {schema_path}"}

    json_files = sorted(f for f in dir_p.iterdir() if f.suffix == ".json")
    if not json_files:
        return {"error": f"No JSON files found in: {results_dir}"}

    passed: list[dict] = []
    failed: list[dict] = []

    for f in json_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            try:
                validate_json_schema(data, schema_p)
                passed.append({
                    "file": f.name,
                    "candidate_id": data.get("candidate_id", "unknown"),
                    "assay_type": data.get("assay_type", "unknown"),
                })
            except Exception as e:
                failed.append({
                    "file": f.name,
                    "candidate_id": data.get("candidate_id", "unknown"),
                    "errors": str(e).split("\n")[0] if str(e) else "Schema validation failed",
                })
        except json.JSONDecodeError as e:
            failed.append({
                "file": f.name,
                "candidate_id": "N/A",
                "errors": f"Invalid JSON: {e}",
            })

    n_passed = len(passed)
    n_failed = len(failed)
    n_total = n_passed + n_failed

    control_failures = []
    for entry in passed + failed:
        f_path = dir_p / entry["file"]
        try:
            data = json.loads(f_path.read_text(encoding="utf-8"))
            if not data.get("positive_control_passed", True):
                control_failures.append({
                    "file": entry["file"],
                    "candidate_id": data.get("candidate_id", "unknown"),
                    "control": "positive",
                })
            if not data.get("negative_control_passed", True):
                control_failures.append({
                    "file": entry["file"],
                    "candidate_id": data.get("candidate_id", "unknown"),
                    "control": "negative",
                })
        except Exception:
            pass

    return {
        "results_dir": results_dir,
        "schema": schema_path,
        "total_files": n_total,
        "passed": n_passed,
        "failed": n_failed,
        "control_failures": control_failures,
        "n_control_failures": len(control_failures),
        "per_file": {
            "passed": passed[:10],
            "failed": failed,
        },
        "all_pass": n_failed == 0,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate lab data return files")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--schema", default="schemas/lab_result.schema.json")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    result = validate_lab_results_dir(
        results_dir=args.results_dir,
        schema_path=args.schema,
    )

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 2

    print(f"Files: {result['total_files']}, Passed: {result['passed']}, Failed: {result['failed']}")
    if result["n_control_failures"] > 0:
        print(f"Control failures: {result['n_control_failures']}")

    if result["failed"] > 0:
        print("\nFailed files:")
        for f in result["per_file"]["failed"]:
            print(f"  ❌ {f['file']} ({f['candidate_id']}): {f['errors']}")

    if args.verbose and result["per_file"]["passed"]:
        print("\nPassed files:")
        for f in result["per_file"]["passed"]:
            print(f"  ✅ {f['file']} ({f['candidate_id']} - {f['assay_type']})")

    return 0 if result["all_pass"] else 3


if __name__ == "__main__":
    sys.exit(main())
