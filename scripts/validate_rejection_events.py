"""Validate a batch of rejection events against the rejection taxonomy.

Reads a JSON list of rejection events, validates each rejection_code against
schemas/rejection_taxonomy.schema.json, checks required fields, and outputs a
PASS/FAIL validation report with per-event errors.

Usage:
    python scripts/validate_rejection_events.py \\
        --input rejection_events.json \\
        --out-json outputs/validation_report.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.utils.io import read_json

REQUIRED_FIELDS = {"candidate_id", "rejection_code", "date", "pipeline_version"}
DATE_FORMAT = "%Y-%m-%d"
_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_DEFAULT_PATH = _ROOT / "examples" / "rejection_taxonomy_example.json"


def load_taxonomy_codes(taxonomy_path: str | Path) -> set[str]:
    taxonomy = read_json(taxonomy_path)
    return {entry["code"] for entry in taxonomy}


def validate_events(
    events: list[dict],
    taxonomy_codes: set[str],
) -> dict:
    total = len(events)
    errors: list[dict] = []
    valid_count = 0

    for i, event in enumerate(events):
        row_errors: list[str] = []

        for field in REQUIRED_FIELDS:
            val = event.get(field)
            if not val or (isinstance(val, str) and not val.strip()):
                row_errors.append(f"Missing required field: {field}")

        rejection_code = event.get("rejection_code", "")
        if rejection_code and rejection_code not in taxonomy_codes:
            row_errors.append(
                f"Unknown rejection_code: {rejection_code}"
            )

        date_val = event.get("date", "")
        if date_val:
            try:
                datetime.strptime(str(date_val), DATE_FORMAT)
            except ValueError:
                row_errors.append(
                    f"Invalid date format: {date_val} (expected YYYY-MM-DD)"
                )

        if row_errors:
            errors.append({
                "index": i,
                "candidate_id": event.get("candidate_id", "?"),
                "errors": row_errors,
            })
        else:
            valid_count += 1

    return {
        "input": {"total_events": total},
        "summary": {
            "valid": valid_count,
            "invalid": len(errors),
            "all_valid": len(errors) == 0,
        },
        "errors": errors,
    }


def build_report(events: list[dict], taxonomy_codes: set[str]) -> dict:
    result = validate_events(events, taxonomy_codes)

    rejection_code_counts: dict[str, int] = {}
    for event in events:
        code = event.get("rejection_code", "unknown")
        rejection_code_counts[code] = rejection_code_counts.get(code, 0) + 1

    result["rejection_code_summary"] = dict(
        sorted(rejection_code_counts.items())
    )

    result["_caveat"] = (
        "This validation report is informational only. "
        "A PASS result confirms structural validity of rejection events, "
        "not biological correctness of rejection decisions. "
        "Unknown rejection codes may indicate a stale taxonomy "
        "rather than an invalid event."
    )
    return result


def generate_markdown(result: dict) -> str:
    lines: list[str] = []
    lines.append("# Rejection Event Validation Report\n")
    lines.append(f"**Total events:** {result['input']['total_events']}\n")
    lines.append(
        f"**Valid:** {result['summary']['valid']} | "
        f"**Invalid:** {result['summary']['invalid']} | "
        f"**All valid:** {result['summary']['all_valid']}\n"
    )

    if result.get("rejection_code_summary"):
        lines.append("\n## Rejection Code Distribution\n")
        lines.append("| Code | Count |")
        lines.append("|------|-------|")
        for code, count in result["rejection_code_summary"].items():
            lines.append(f"| {code} | {count} |")

    errors = result.get("errors", [])
    if errors:
        lines.append(f"\n## Errors ({len(errors)})\n")
        for err in errors:
            lines.append(
                f"- **Event {err['index']}** "
                f"(candidate: {err['candidate_id']}): "
                f"{'; '.join(err['errors'])}"
            )

    lines.append(f"\n## Caveat\n\n{result.get('_caveat', '')}\n")
    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate rejection events against the rejection taxonomy."
    )
    parser.add_argument("--input", required=True, help="Path to JSON events file")
    parser.add_argument(
        "--out-json", default=None, help="Output JSON report path"
    )
    parser.add_argument(
        "--out-md", default=None, help="Output Markdown report path"
    )
    parser.add_argument(
        "--taxonomy",
        default=str(TAXONOMY_DEFAULT_PATH),
        help="Path to rejection taxonomy JSON file (e.g. examples/rejection_taxonomy_example.json)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        return 2

    try:
        events = read_json(input_path)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 2

    if not isinstance(events, list):
        print("Error: Input must be a JSON array of rejection events", file=sys.stderr)
        return 2

    if not events:
        print("Error: Input is an empty list (no events to validate)", file=sys.stderr)
        return 2

    taxonomy_path = Path(args.taxonomy)
    if not taxonomy_path.exists():
        print(f"Error: Taxonomy not found: {args.taxonomy}", file=sys.stderr)
        return 2

    try:
        taxonomy_codes = load_taxonomy_codes(taxonomy_path)
    except Exception as e:
        print(f"Error loading taxonomy: {e}", file=sys.stderr)
        return 2

    result = build_report(events, taxonomy_codes)

    print(json.dumps(result, indent=2))

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(result, indent=2) + "\n")
        print(f"\nJSON report written to: {args.out_json}")

    if args.out_md:
        md = generate_markdown(result)
        Path(args.out_md).write_text(md + "\n")
        print(f"Markdown report written to: {args.out_md}")

    return 0 if result["summary"]["all_valid"] else 3


if __name__ == "__main__":
    sys.exit(main())
