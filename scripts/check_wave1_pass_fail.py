"""Check Wave 1 lab results against pre-registered pass/fail criteria.

Reads lab result JSON files from a directory, compares against the
pre-registered criteria in configs/wave1_pass_fail.yaml, and reports
which criteria pass or fail.

Exit codes:
  0: All criteria pass
  3: One or more criteria fail
  2: Missing files or parse error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def _load_lab_results(results_dir: str) -> list[dict[str, Any]]:
    results = []
    p = Path(results_dir)
    if not p.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    for f in sorted(p.iterdir()):
        if f.suffix.lower() in (".json",):
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append(data)
    return results


def _check_criteria(
    results: list[dict[str, Any]],
    criteria: dict[str, Any],
) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    all_pass = True

    # Primary endpoint: MIC <= 32 for >= N candidates
    pri = criteria.get("primary_endpoint", {})
    max_mic = pri.get("max_mic_ugml", 32)
    min_pass = pri.get("min_passing_candidates", 3)
    organism = pri.get("organism", "")

    passing_mic = sum(
        1 for r in results
        if r.get("assay_type") == "MIC"
        and r.get("result_value", 999) <= max_mic
        and (not organism or organism in r.get("organism_or_cell_line", ""))
    )
    mic_pass = passing_mic >= min_pass
    checks["primary_endpoint_mic"] = {
        "pass": mic_pass,
        "detail": f"{passing_mic}/{min_pass} candidates with MIC <= {max_mic} ug/mL",
    }
    if not mic_pass:
        all_pass = False

    # Positive control check
    pos_controls = criteria.get("positive_controls", [])
    pos_pass = True
    pos_details = []
    for pc in pos_controls:
        cid = pc.get("candidate_id", "")
        expected_min = pc.get("expected_mic_min_ugml", 0)
        expected_max = pc.get("expected_mic_max_ugml", 999)
        matches = [
            r for r in results
            if r.get("candidate_id") == cid and r.get("assay_type") == "MIC"
        ]
        if not matches:
            pos_pass = False
            pos_details.append(f"{cid}: no results found")
        else:
            for m in matches:
                val = m.get("result_value", -1)
                if val < expected_min or val > expected_max:
                    pos_pass = False
                    pos_details.append(f"{cid}: MIC={val} outside expected [{expected_min}, {expected_max}]")
                else:
                    pos_details.append(f"{cid}: MIC={val} within expected range")
    checks["positive_controls"] = {
        "pass": pos_pass,
        "detail": "; ".join(pos_details) if pos_details else "No positive controls defined",
    }
    if not pos_pass:
        all_pass = False

    # Hemolysis safety: no toxic candidates
    hemo = criteria.get("hemolysis", {})
    toxic_threshold = hemo.get("ti_toxic_threshold", 2)
    max_toxic = hemo.get("max_toxic_candidates", 0)
    toxic_count = 0
    hemo_details = []

    for r in results:
        if r.get("assay_type") == "hemolysis_RBC":
            hc50 = r.get("result_value", 0)
            cid = r.get("candidate_id", "")
            mic_results = [
                x for x in results
                if x.get("candidate_id") == cid and x.get("assay_type") == "MIC"
            ]
            if mic_results:
                mic_val = min(x.get("result_value", 999) for x in mic_results)
                if mic_val > 0:
                    ti = hc50 / mic_val
                    if ti < toxic_threshold:
                        toxic_count += 1
                        hemo_details.append(f"{cid}: TI={ti:.2f} (toxic)")
                    elif ti < hemo.get("ti_selective_threshold", 10):
                        hemo_details.append(f"{cid}: TI={ti:.2f} (borderline)")
                    else:
                        hemo_details.append(f"{cid}: TI={ti:.2f} (selective)")

    hemo_pass = toxic_count <= max_toxic
    checks["hemolysis_safety"] = {
        "pass": hemo_pass,
        "detail": f"{toxic_count} toxic (TI < {toxic_threshold}), max allowed {max_toxic}. " + "; ".join(hemo_details[:5]),
    }
    if not hemo_pass:
        all_pass = False

    # Batch-level: positive/negative controls passed
    batch = criteria.get("batch_level", {})
    total_tested = len(set(r.get("candidate_id", "") for r in results))
    batch_pass = total_tested >= batch.get("min_total_candidates_tested", 1)
    checks["batch_min_tested"] = {
        "pass": batch_pass,
        "detail": f"{total_tested} candidates tested (minimum {batch.get('min_total_candidates_tested', 1)})",
    }
    if not batch_pass:
        all_pass = False

    # Secondary endpoint
    sec = criteria.get("secondary_endpoint", {})
    sec_max_mic = sec.get("max_mic_ugml", 32)
    sec_min_ti = sec.get("min_therapeutic_index", 10)
    sec_min = sec.get("min_passing_candidates", 1)
    sec_count = 0
    for r in results:
        if r.get("assay_type") == "MIC" and r.get("result_value", 999) <= sec_max_mic:
            cid = r.get("candidate_id", "")
            hemo_results = [
                x for x in results
                if x.get("candidate_id") == cid and x.get("assay_type") == "hemolysis_RBC"
            ]
            if hemo_results:
                hc50 = hemo_results[0].get("result_value", 0)
                mic_val = r.get("result_value", 999)
                if mic_val > 0 and (hc50 / mic_val) > sec_min_ti:
                    sec_count += 1
    sec_pass = sec_count >= sec_min
    checks["secondary_endpoint"] = {
        "pass": sec_pass,
        "detail": f"{sec_count}/{sec_min} candidates with MIC <= {sec_max_mic} and TI > {sec_min_ti}",
    }
    if not sec_pass:
        all_pass = False

    return {"all_pass": all_pass, "checks": checks}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Check Wave 1 pass/fail criteria")
    parser.add_argument("--results-dir", required=True, help="Directory with lab result JSONs")
    parser.add_argument("--criteria", default="configs/wave1_pass_fail.yaml", help="Pass/fail criteria YAML")
    parser.add_argument("--out", default=None, help="JSON output path")
    args = parser.parse_args()

    try:
        results = _load_lab_results(args.results_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    criteria_p = Path(args.criteria)
    if not criteria_p.exists():
        print(f"Error: Criteria file not found: {args.criteria}", file=sys.stderr)
        return 2

    criteria = yaml.safe_load(criteria_p.read_text(encoding="utf-8"))
    if not results:
        print("Error: No lab results found", file=sys.stderr)
        return 2

    verdict = _check_criteria(results, criteria)
    output = json.dumps(verdict, indent=2)
    print(output)

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")

    if verdict["all_pass"]:
        print("\nAll criteria PASS")
        return 0
    else:
        print("\nOne or more criteria FAIL")
        return 3


if __name__ == "__main__":
    sys.exit(main())
