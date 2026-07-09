"""Gate commands."""
from __future__ import annotations
import argparse

def _run_gate_check(args: argparse.Namespace) -> int:
    import json as _json
    from openamp_foundry.gates.gate_checker import check_all_gates

    with open(args.validation_json, encoding="utf-8") as f:
        validation_data = _json.load(f)

    results = check_all_gates(validation_data, args.gate)
    print(_json.dumps({
        "status": "ok",
        "gates": [r._asdict() for r in results],
        "all_pass": all(r.passed for r in results),
    }, indent=2))
    return 0


def _run_release_gate_check(args: argparse.Namespace) -> int:
    """Run the release gate validator and print pass/fail."""
    import json as _json
    from openamp_foundry.governance.release_gate import validate_release_gate

    gate_statuses = _json.loads(args.gates_json)
    result = validate_release_gate(args.release_type, args.artifact_id, gate_statuses)

    if args.format == "json":
        print(_json.dumps({
            "release_type": result.release_type,
            "artifact_id": result.artifact_id,
            "passed": result.passed,
            "gates_passed": result.gates_passed,
            "gates_failed": result.gates_failed,
            "errors": result.errors,
            "warnings": result.warnings,
            "dry_lab_only": result.dry_lab_only,
        }, indent=2))
    else:
        print(f"Release gate check: {result.release_type}/{result.artifact_id}")
        print(f"  Passed: {result.passed}")
        if result.gates_passed:
            for g in result.gates_passed:
                print(f"  [PASS] {g}")
        for g in result.gates_failed:
            print(f"  [FAIL] {g}")
        for e in result.errors:
            print(f"  ERROR: {e}")
        for w in result.warnings:
            print(f"  WARN:  {w}")
        print(f"  dry_lab_only: {result.dry_lab_only}")

    return 0 if result.passed else 3


