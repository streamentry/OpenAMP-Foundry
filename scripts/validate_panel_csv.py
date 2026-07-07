"""Validate panel CSV files against expected columns and content."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REQUIRED = {"candidate_id", "sequence"}


def validate_panel_csv(csv_path: str) -> dict:
    p = Path(csv_path)
    if not p.exists():
        return {"error": f"Panel CSV not found: {csv_path}"}

    with p.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {"error": "Empty or unreadable CSV"}
        headers = set(reader.fieldnames)
        rows = list(reader)

    missing = REQUIRED - headers
    if missing:
        return {"error": f"Missing required columns: {missing}"}

    row_errors = []
    for i, row in enumerate(rows, 1):
        errs = []
        cid = row.get("candidate_id", "").strip()
        seq = row.get("sequence", "").strip()
        if not cid:
            errs.append("Missing candidate_id")
        if not seq:
            errs.append("Missing sequence")
        if seq and not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq.upper()):
            errs.append(f"Invalid amino acid in sequence: {seq[:20]}")
        if errs:
            row_errors.append({"row": i, "candidate_id": cid or "?", "errors": errs})

    return {
        "csv": csv_path,
        "columns": sorted(headers),
        "missing_required": sorted(missing),
        "total_rows": len(rows),
        "valid_rows": len(rows) - len(row_errors),
        "row_errors": len(row_errors),
        "per_row_errors": row_errors,
        "all_valid": len(row_errors) == 0,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate panel CSV")
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    result = validate_panel_csv(args.csv)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["all_valid"] else 3


if __name__ == "__main__":
    sys.exit(main())
