"""Validate negative-result archive CSV entries.

Checks each row against the schema defined in
docs/evidence/NEGATIVE_RESULT_ARCHIVE.md.

Usage:
    python scripts/validate_negative_archive.py \
        --archive outputs/negative_result_archive.csv
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

REQUIRED = {"entry_id", "date", "candidate_id", "sequence", "reason_category",
            "reason_detail", "pipeline_version", "source_batch"}

VALID_CATEGORIES = {"pre_selection_reject", "selected_untested", "lab_inactive",
                    "lab_toxic", "control_failure", "synthesis_failure"}

CONDITIONAL_CATEGORIES = {"lab_inactive", "lab_toxic"}

DATE_FORMAT = "%Y-%m-%d"


def validate_archive(archive_path: str) -> dict:
    p = Path(archive_path)
    if not p.exists():
        return {"error": f"Archive not found: {archive_path}"}

    rows: list[dict] = []
    with p.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return {"error": "Archive is empty"}

    errors: list[dict] = []
    warnings: list[dict] = []
    valid_count = 0

    for i, row in enumerate(rows):
        row_errors = []
        row_warnings = []

        # Required fields
        for field in REQUIRED:
            val = row.get(field, "").strip()
            if not val:
                row_errors.append(f"Missing required field: {field}")

        # Reason category
        cat = row.get("reason_category", "").strip()
        if cat and cat not in VALID_CATEGORIES:
            row_errors.append(f"Invalid reason_category: {cat}")

        # Date format
        date_val = row.get("date", "").strip()
        if date_val:
            try:
                datetime.strptime(date_val, DATE_FORMAT)
            except ValueError:
                row_errors.append(f"Invalid date format: {date_val} (expected YYYY-MM-DD)")

        # Conditional fields for lab-tested categories
        if cat in CONDITIONAL_CATEGORIES:
            for cf in ["assay_type", "assay_result", "assay_unit"]:
                if not row.get(cf, "").strip():
                    row_warnings.append(f"Conditional field '{cf}' recommended for {cat}")

        # Superseded_by should reference an existing entry_id
        superseded = row.get("superseded_by", "").strip()
        if superseded:
            found = any(r.get("entry_id", "").strip() == superseded for r in rows)
            if not found:
                row_warnings.append(f"superseded_by={superseded} does not match any entry_id")

        # pipeline_version should not be empty if present
        pv = row.get("pipeline_version", "").strip()
        if not pv and date_val:
            row_warnings.append("pipeline_version is recommended")

        if row_errors:
            errors.append({
                "row": i + 1,
                "entry_id": row.get("entry_id", "?"),
                "errors": row_errors,
            })
        else:
            valid_count += 1

        if row_warnings:
            warnings.append({
                "row": i + 1,
                "entry_id": row.get("entry_id", "?"),
                "warnings": row_warnings,
            })

    return {
        "archive": archive_path,
        "total_rows": len(rows),
        "valid": valid_count,
        "errors": len(errors),
        "warnings": len(warnings),
        "per_row_errors": errors,
        "per_row_warnings": warnings,
        "all_valid": len(errors) == 0,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate negative-result archive")
    parser.add_argument("--archive", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    result = validate_archive(args.archive)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    print(f"\nValid: {result['valid']}/{result['total_rows']}, "
          f"Errors: {result['errors']}, Warnings: {result['warnings']}")

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n")

    return 0 if result["all_valid"] else 3


if __name__ == "__main__":
    sys.exit(main())
