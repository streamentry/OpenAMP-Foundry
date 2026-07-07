"""Check review requests for completeness before submission."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "request_id": "Unique identifier for the review request",
    "reviewer_role": "Role being requested (e.g., domain_expert, safety_reviewer)",
    "artifact_refs": "List of artifacts to review (PR URLs, doc paths)",
    "claim_boundary": "What claim the review is expected to evaluate",
    "decision_needed": "What decision is needed (approve, reject, defer)",
    "requested_by": "Name or ID of the person requesting review",
}

OPTIONAL_FIELDS = {
    "deadline": "ISO 8601 deadline for the review",
    "context_notes": "Additional context for the reviewer",
    "safety_relevant": "Whether the request touches safety policy",
}


def check_completeness(request_path: str) -> dict:
    p = Path(request_path)
    if not p.exists():
        return {"error": f"Request file not found: {request_path}"}

    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    if not isinstance(data, dict):
        return {"error": "Request must be a JSON object"}

    missing = []
    present = []

    for field, desc in REQUIRED_FIELDS.items():
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing.append({"field": field, "description": desc})
        else:
            present.append(field)

    optional_present = [f for f in OPTIONAL_FIELDS if f in data and data[f]]

    return {
        "request_path": request_path,
        "valid_json": True,
        "is_complete": len(missing) == 0,
        "required_fields_present": len(present),
        "required_fields_total": len(REQUIRED_FIELDS),
        "optional_fields_present": len(optional_present),
        "missing_fields": missing,
        "fields_present": present,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check review request completeness")
    parser.add_argument("--request", required=True, help="Path to review request JSON")
    args = parser.parse_args()

    result = check_completeness(args.request)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    if not result["is_complete"]:
        print(f"\nMissing {len(result['missing_fields'])} required fields.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
