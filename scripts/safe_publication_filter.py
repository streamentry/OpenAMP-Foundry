"""Safe-publication filter for candidate panels and negative-result reports.

Fail-closed: default reject unless ALL checks pass.

Checks:
  - dry_lab_only must be true
  - global proof_ladder_level must be <= 4
  - toxicity_screened must be true
  - hemolysis_screened must be true
  - dual_use_reviewed must be true
  - per-candidate proof_ladder_level must be <= 4

Usage:
    python scripts/safe_publication_filter.py \
        --input examples/safe_publication_filter_example_input.json \
        --out-json outputs/safe_publication_filter_result.json

    python scripts/safe_publication_filter.py \
        --input examples/safe_publication_filter_example_input.json

Exit codes:
    0  ALL PASS — publication safety checks satisfied
    1  FAIL — one or more checks failed (fail-closed)
    2  INPUT ERROR — missing file, invalid JSON, or bad data
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_input(input_path: str | Path) -> dict[str, Any]:
    """Load and validate input JSON file."""
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    try:
        with p.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in {p}: {e}"
        raise ValueError(msg) from e


def run_global_checks(data: dict[str, Any]) -> dict[str, Any]:
    """Run global-level publication safety checks.

    Returns {checks: dict of check results, all_passed: bool}.
    FAIL-CLOSED: any missing or false check fails the global gate.
    """
    checks: dict[str, Any] = {}
    all_passed = True

    # 1. dry_lab_only must be True
    dry_lab = data.get("dry_lab_only", False)
    dry_ok = dry_lab is True
    if not dry_ok:
        all_passed = False
    dry_result: dict[str, Any] = {
        "required": True,
        "actual": dry_lab,
        "passed": dry_ok,
        "description": "dry_lab_only must be true — computational outputs are hypotheses, not biological proof",
    }
    if not dry_ok:
        dry_result["reason"] = (
            f"dry_lab_only is {dry_lab!r}, must be true. "
            "Publication-ready packets must explicitly acknowledge dry-lab-only status."
        )
    checks["dry_lab_only"] = dry_result

    # 2. Global proof_ladder_level must be <= 4
    max_allowed = 4
    global_pll = data.get("proof_ladder_level", None)
    pll_ok = isinstance(global_pll, (int, float)) and global_pll <= max_allowed
    if not pll_ok:
        all_passed = False
    pll_result: dict[str, Any] = {
        "required": f"\u2264 {max_allowed}",
        "max_allowed": max_allowed,
        "actual": global_pll if isinstance(global_pll, (int, float)) else None,
        "passed": pll_ok,
        "description": "Global proof ladder level must be \u2264 4 — levels \u2265 5 require biological validation data",
    }
    if not pll_ok:
        if global_pll is None:
            pll_result["reason"] = "proof_ladder_level is not specified in input."
        else:
            pll_result["reason"] = (
                f"proof_ladder_level is {global_pll}, exceeds max allowed ({max_allowed})."
            )
    checks["global_proof_ladder_level"] = pll_result

    # 3. Safety sub-checks
    safety = data.get("safety_checks", {})
    safety_check_names = ["toxicity_screened", "hemolysis_screened", "dual_use_reviewed"]
    safety_results: dict[str, Any] = {}
    safety_all_ok = True
    for name in safety_check_names:
        actual = safety.get(name, False)
        ok = actual is True
        if not ok:
            safety_all_ok = False
            all_passed = False
        sr: dict[str, Any] = {
            "required": True,
            "actual": actual if isinstance(actual, bool) else False,
            "passed": ok,
        }
        if not ok:
            sr["reason"] = f"{name} is {actual!r}, must be true."
        safety_results[name] = sr

    checks["safety_checks"] = {
        "all_passed": safety_all_ok,
        "checks": safety_results,
    }

    return {"all_passed": all_passed, "checks": checks}


def run_candidate_checks(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run per-candidate publication safety checks.

    Checks:
      - proof_ladder_level must be <= 4 (PASS), == 4 → WARN, > 4 or missing → FAIL
    """
    results: list[dict[str, Any]] = []
    max_allowed_pll = 4

    for c in candidates:
        cid = c.get("candidate_id", "?")
        candidate_pll = c.get("proof_ladder_level", None)

        check_results: dict[str, Any] = {}
        issues: list[str] = []

        # proof_ladder_level check
        if candidate_pll is None:
            check_results["proof_ladder_level"] = {
                "value": None,
                "max_allowed": max_allowed_pll,
                "passed": False,
                "reason": "proof_ladder_level not specified for candidate",
            }
            issues.append("PROOF_LADDER_MISSING")
        elif not isinstance(candidate_pll, (int, float)):
            check_results["proof_ladder_level"] = {
                "value": candidate_pll,
                "max_allowed": max_allowed_pll,
                "passed": False,
                "reason": f"proof_ladder_level must be an integer, got {type(candidate_pll).__name__}",
            }
            issues.append("PROOF_LADDER_INVALID")
        elif candidate_pll > max_allowed_pll:
            check_results["proof_ladder_level"] = {
                "value": candidate_pll,
                "max_allowed": max_allowed_pll,
                "passed": False,
                "reason": f"proof_ladder_level {candidate_pll} exceeds max allowed {max_allowed_pll}",
            }
            issues.append("PROOF_LADDER_EXCEEDED")
        else:
            check_results["proof_ladder_level"] = {
                "value": candidate_pll,
                "max_allowed": max_allowed_pll,
                "passed": True,
            }

        # Determine overall: PASS if all pass, WARN if at boundary, FAIL otherwise
        pll_check = check_results["proof_ladder_level"]
        if not pll_check["passed"]:
            overall = "FAIL"
        elif isinstance(candidate_pll, (int, float)) and candidate_pll == max_allowed_pll:
            overall = "WARN"
        else:
            overall = "PASS"

        result: dict[str, Any] = {
            "candidate_id": cid,
            "overall": overall,
            "checks": check_results,
        }
        if issues:
            result["issues"] = issues
        results.append(result)

    return results


def build_filter_result(
    input_data: dict[str, Any],
    global_results: dict[str, Any],
    candidate_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the structured safe-publication filter result dict."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    passed = sum(1 for c in candidate_results if c["overall"] == "PASS")
    warned = sum(1 for c in candidate_results if c["overall"] == "WARN")
    failed = sum(1 for c in candidate_results if c["overall"] == "FAIL")
    total = len(candidate_results)

    global_pass = global_results["all_passed"]
    overall_filter_pass = global_pass and failed == 0

    return {
        "filter_metadata": {
            "generated_at": now,
            "filter_type": "safe_publication_filter",
            "filter_version": "1.0.0",
            "input_source": input_data.get("source", "unknown"),
            "pipeline_version": input_data.get("pipeline_version", "unknown"),
        },
        "global_checks": global_results["checks"],
        "global_pass": global_pass,
        "candidates": candidate_results,
        "summary": {
            "total_candidates": total,
            "passed": passed,
            "failed": failed,
            "warned": warned,
            "overall_filter_pass": overall_filter_pass,
        },
        "caveats": [
            "Computational outputs are hypotheses and review aids. They are not biological proof.",
            "This filter checks structural publication safety constraints, not scientific validity.",
            "A PASS result does not mean the candidate is biologically active or safe.",
            "A FAIL result does not mean the candidate is biologically inactive — it means publication safety checks are not satisfied.",
            "Proof ladder levels are self-reported by the pipeline; independent verification is recommended.",
            "Safety checks (toxicity, hemolysis, dual-use) are computational assessments and require qualified human review.",
            "dry_lab_only attestation is a safety-constraint field; it relies on the generator's honesty.",
        ],
        "dry_lab_only": input_data.get("dry_lab_only", False),
    }


def build_markdown_result(result: dict[str, Any]) -> str:
    """Generate a Markdown summary from the filter result."""
    meta = result["filter_metadata"]
    summary = result["summary"]
    lines: list[str] = []

    lines.append("# Safe Publication Filter Result")
    lines.append("")
    lines.append("> **FAIL-CLOSED:** Default reject unless all checks pass. "
                 "Computational outputs are hypotheses and review aids. They are not biological proof.")
    lines.append("")

    lines.append("## Filter Metadata")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Generated at | {meta['generated_at']} |")
    lines.append(f"| Input source | {meta['input_source']} |")
    lines.append(f"| Pipeline version | {meta['pipeline_version']} |")
    lines.append(f"| Filter version | {meta['filter_version']} |")
    lines.append("")

    lines.append("## Global Checks")
    lines.append("")
    global_pass = result["global_pass"]
    status = "PASS" if global_pass else "FAIL"
    lines.append(f"**Overall global check status: {status}**")
    lines.append("")

    gc = result["global_checks"]

    dry = gc.get("dry_lab_only", {})
    lines.append(f"**dry_lab_only:** {'✅ PASS' if dry.get('passed') else '❌ FAIL'}")
    lines.append(f"- Required: {dry.get('required')}, Actual: {dry.get('actual')}")
    if dry.get("reason"):
        lines.append(f"- Reason: {dry['reason']}")
    lines.append("")

    pll = gc.get("global_proof_ladder_level", {})
    lines.append(f"**Global proof_ladder_level:** {'✅ PASS' if pll.get('passed') else '❌ FAIL'}")
    lines.append(f"- Max allowed: {pll.get('max_allowed')}, Actual: {pll.get('actual')}")
    if pll.get("reason"):
        lines.append(f"- Reason: {pll['reason']}")
    lines.append("")

    sc = gc.get("safety_checks", {})
    lines.append(f"**Safety checks:** {'✅ ALL PASS' if sc.get('all_passed') else '❌ SOME FAILED'}")
    for name, sr in sc.get("checks", {}).items():
        icon = "✅" if sr.get("passed") else "❌"
        lines.append(f"  - {icon} {name}: {sr.get('actual')}")
        if sr.get("reason"):
            lines.append(f"    - Reason: {sr['reason']}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total candidates | {summary['total_candidates']} |")
    lines.append(f"| Passed | {summary['passed']} |")
    lines.append(f"| Warned | {summary['warned']} |")
    lines.append(f"| Failed | {summary['failed']} |")
    pass_status = "PASS" if summary["overall_filter_pass"] else "FAIL"
    lines.append(f"| **Overall filter verdict** | **{pass_status}** |")
    lines.append("")

    if result["candidates"]:
        lines.append("## Per-Candidate Results")
        lines.append("")
        lines.append("| Candidate | Overall | Proof Ladder Level | Issues |")
        lines.append("|-----------|---------|-------------------|--------|")
        for c in result["candidates"]:
            pll_check = c["checks"].get("proof_ladder_level", {})
            pll_val = pll_check.get("value", "?")
            icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(c["overall"], "?")
            issues_str = ", ".join(c.get("issues", [])) if c.get("issues") else ""
            lines.append(f"| {c['candidate_id']} | {icon} {c['overall']} | {pll_val} | {issues_str} |")
        lines.append("")

    lines.append("## Caveats")
    lines.append("")
    for caveat in result.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by `scripts/safe_publication_filter.py` — "
                 f"`{meta['pipeline_version']}`*")

    return "\n".join(lines)


def validate_schema(result: dict[str, Any], schema_path: str | Path | None = None) -> bool:
    """Validate filter result against the schema file."""
    schema_p = Path(schema_path) if schema_path else (
        Path(__file__).resolve().parent.parent / "schemas" / "safe_publication_filter.schema.json"
    )
    if not schema_p.exists():
        raise FileNotFoundError(f"Schema not found: {schema_p}")
    try:
        import jsonschema
    except ImportError:
        return True  # skip validation if jsonschema not available
    with schema_p.open("r") as f:
        schema = json.load(f)
    try:
        jsonschema.validate(result, schema)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}") from e


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safe-publication filter — checks candidate panels against "
                    "publication safety constraints before external release.",
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="Path to input JSON file (candidate panel with safety metadata)",
    )
    parser.add_argument(
        "--out-json", type=Path, default=None,
        help="Path to write JSON filter result (default: not written)",
    )
    parser.add_argument(
        "--out-md", type=Path, default=None,
        help="Path to write Markdown summary (default: not written)",
    )
    parser.add_argument(
        "--validate-schema", action="store_true",
        help="Validate filter result against schema (requires jsonschema)",
    )
    parser.add_argument(
        "--pipeline-version", default=None,
        help="Override pipeline version (default: from input file metadata)",
    )

    args = parser.parse_args(argv)

    # Load input
    try:
        input_data = load_input(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading input: {e}", file=sys.stderr)
        return 2

    candidates = input_data.get("candidates", [])
    if not candidates:
        print("Error: No candidates in input file", file=sys.stderr)
        return 2

    pipeline_version = args.pipeline_version or input_data.get(
        "pipeline_version", "unknown"
    )
    input_data.setdefault("pipeline_version", pipeline_version)

    # Run filter
    global_results = run_global_checks(input_data)
    candidate_results = run_candidate_checks(candidates)

    result = build_filter_result(input_data, global_results, candidate_results)

    # Validate schema if requested
    if args.validate_schema:
        try:
            validate_schema(result)
        except (FileNotFoundError, ValueError) as e:
            print(f"Schema validation error: {e}", file=sys.stderr)
            return 2

    # Write JSON output
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"Wrote filter result to {args.out_json}")

    # Write Markdown output
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        md_content = build_markdown_result(result)
        args.out_md.write_text(md_content)
        print(f"Wrote Markdown summary to {args.out_md}")

    if not args.out_json and not args.out_md:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code: 0 = all pass, 1 = any fail (FAIL-CLOSED)
    if result["summary"]["overall_filter_pass"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
