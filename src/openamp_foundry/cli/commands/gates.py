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


