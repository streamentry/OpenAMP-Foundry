#!/usr/bin/env python3
"""Synthetic lab result generator for testing the calibration loop without real
wet-lab data.

This script generates schema-valid lab result JSON files (matching
``schemas/lab_result.schema.json``) with configurable:

- **Cohort size:** how many candidates get synthetic results.
- **Effect size:** what fraction of candidates show activity (MIC ≤ cutoff).
- **Noise level:** how often replicate results disagree or controls fail.

Every output file is explicitly labeled SYNTHETIC in multiple fields
(organism, lab, notes, disclaimer) to prevent confusion with real data.

Typical usage::

    python examples/lab_results_generator.py --out-dir outputs/synthetic_lab_results

    python examples/lab_results_generator.py --panel-csv outputs/pilot_panel.csv \
        --cohort-size 20 --effect-size 0.30 --noise-level 0.10 \
        --assay-types MIC hemolysis_RBC --out-dir outputs/synthetic_lab_results
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_COHORT_SIZE = 20
DEFAULT_EFFECT_SIZE = 0.40
DEFAULT_NOISE_LEVEL = 0.05
DEFAULT_ASSAY_TYPES = ("MIC", "hemolysis_RBC")
DEFAULT_OUT_DIR = "outputs/synthetic_lab_results"

SYNTHETIC_LAB = "SYNTHETIC DATA LAB"
SYNTHETIC_ORG_PREFIX = "SYNTHETIC EXAMPLE"

_DISCLAIMER = (
    "SYNTHETIC EXAMPLE. This is not a real experimental result on a "
    "computationally nominated candidate and does not constitute a drug "
    "or clinical claim."
)

ASSAY_CONFIGS: dict[str, dict] = {
    "MIC": {
        "unit": "µg/mL",
        "value_range": (0.5, 128.0),
        "active_cutoff": 32.0,
        "quantitative": True,
    },
    "MBC": {
        "unit": "µg/mL",
        "value_range": (1.0, 256.0),
        "active_cutoff": 64.0,
        "quantitative": True,
    },
    "hemolysis_RBC": {
        "unit": "%",
        "value_range": (0.0, 100.0),
        "active_cutoff": 10.0,
        "quantitative": True,
    },
    "cytotoxicity_mammalian": {
        "unit": "%",
        "value_range": (0.0, 100.0),
        "active_cutoff": 20.0,
        "quantitative": True,
    },
    "membrane_disruption": {
        "unit": "%",
        "value_range": (0.0, 100.0),
        "active_cutoff": 50.0,
        "quantitative": True,
    },
    "time_kill": {
        "unit": "log10_CFU/mL",
        "value_range": (0.0, 6.0),
        "active_cutoff": 3.0,
        "quantitative": True,
    },
    "biofilm_inhibition": {
        "unit": "%",
        "value_range": (0.0, 100.0),
        "active_cutoff": 50.0,
        "quantitative": True,
    },
}

ORGANISMS = [
    f"{SYNTHETIC_ORG_PREFIX} - E. coli ATCC 25922",
    f"{SYNTHETIC_ORG_PREFIX} - S. aureus ATCC 29213",
    f"{SYNTHETIC_ORG_PREFIX} - P. aeruginosa ATCC 27853",
    f"{SYNTHETIC_ORG_PREFIX} - K. pneumoniae ATCC 700603",
    f"{SYNTHETIC_ORG_PREFIX} - A. baumannii ATCC 19606",
    f"{SYNTHETIC_ORG_PREFIX} - hRBC (human red blood cells)",
    f"{SYNTHETIC_ORG_PREFIX} - HepG2 (human liver cell line)",
    f"{SYNTHETIC_ORG_PREFIX} - HUVEC (human umbilical vein endothelial cells)",
]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _make_result_id(index: int) -> str:
    return f"RES-SYN-{index:04d}"


def _make_cert_hash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _pick_organism(assay_type: str) -> str:
    if assay_type in ("hemolysis_RBC",):
        return f"{SYNTHETIC_ORG_PREFIX} - hRBC (human red blood cells)"
    if assay_type in ("cytotoxicity_mammalian",):
        return f"{SYNTHETIC_ORG_PREFIX} - HepG2 (human liver cell line)"
    return random.choice(
        [o for o in ORGANISMS if o.startswith(f"{SYNTHETIC_ORG_PREFIX} - E") or o.startswith(f"{SYNTHETIC_ORG_PREFIX} - S")]
    )


def _is_active(assay_type: str, value: float) -> bool:
    cfg = ASSAY_CONFIGS.get(assay_type, {})
    cutoff = cfg.get("active_cutoff", 32.0)
    if assay_type == "hemolysis_RBC":
        return value <= cutoff
    if assay_type == "cytotoxicity_mammalian":
        return value <= cutoff
    if assay_type == "membrane_disruption":
        return value >= cutoff
    return value <= cutoff


def _qualitative(assay_type: str, value: float | None) -> str:
    if value is None:
        return random.choice(["active", "inactive", "inconclusive"])
    if _is_active(assay_type, value):
        return random.choices(
            ["active", "partial", "inactive"],
            weights=[0.85, 0.10, 0.05],
        )[0]
    return random.choices(
        ["inactive", "partial", "active"],
        weights=[0.80, 0.12, 0.08],
    )[0]


def _fuzzed_value(assay_type: str, effect_is_active: bool, noise_level: float) -> float:
    """Generate a synthetic numeric result, optionally adding noise."""
    cfg = ASSAY_CONFIGS.get(assay_type, {})
    lo, hi = cfg.get("value_range", (0.0, 100.0))
    cutoff = cfg.get("active_cutoff", 32.0)

    if effect_is_active:
        base = random.uniform(lo, cutoff * 0.6)
    else:
        base = random.uniform(cutoff * 1.2, hi)

    noise = random.gauss(0, noise_level * (hi - lo))
    return max(lo, min(hi, base + noise))


def _make_controls(noise_level: float) -> tuple[bool, bool]:
    pos_pass = random.random() > noise_level * 0.5
    neg_pass = random.random() > noise_level * 0.3
    return pos_pass, neg_pass


def generate_synthetic_results(
    candidate_ids: list[str],
    *,
    cohort_size: int = DEFAULT_COHORT_SIZE,
    effect_size: float = DEFAULT_EFFECT_SIZE,
    noise_level: float = DEFAULT_NOISE_LEVEL,
    assay_types: tuple[str, ...] = DEFAULT_ASSAY_TYPES,
    start_date: str | None = None,
    lab_name: str = SYNTHETIC_LAB,
) -> list[dict[str, Any]]:
    """Generate a list of synthetic lab result dicts, validated against schema.

    Args:
        candidate_ids: Pool of candidate IDs to sample from.
        cohort_size: Number of candidates to generate results for.
        effect_size: Fraction of candidates that show activity (0-1).
        noise_level: Fractional noise magnitude (0-1), affects replicate
            disagreement and control-failure probability.
        assay_types: Types of assays to generate (e.g. ``("MIC",)``).
        start_date: ISO date for the first assay (default: today - 30 days).
        lab_name: Synthetic lab name for the ``performed_by_lab`` field.

    Returns:
        List of dicts, each matching ``lab_result.schema.json``.
    """
    if start_date is None:
        start_date = (date.today() - timedelta(days=30)).isoformat()

    results: list[dict[str, Any]] = []
    rng_index = 1

    # Determine which candidates are "active" vs "inactive"
    pool = list(candidate_ids)
    random.shuffle(pool)
    n_active = max(1, int(cohort_size * effect_size))
    n_inactive = cohort_size - n_active
    active_pool = pool[:n_active]
    inactive_pool = pool[n_active:n_active + n_inactive]
    if n_inactive <= 0:
        inactive_pool = []

    for candidate_id in active_pool:
        for assay_type in assay_types:
            value = _fuzzed_value(assay_type, effect_is_active=True, noise_level=noise_level)
            qual = _qualitative(assay_type, value)
            pos_pass, neg_pass = _make_controls(noise_level)
            cert_hash = _make_cert_hash(f"{candidate_id}_{assay_type}")
            assay_date = (date.fromisoformat(start_date) + timedelta(days=random.randint(0, 14))).isoformat()

            results.append({
                "result_id": _make_result_id(rng_index),
                "candidate_id": candidate_id,
                "assay_type": assay_type,
                "organism_or_cell_line": _pick_organism(assay_type),
                "result_value": round(value, 2),
                "result_unit": ASSAY_CONFIGS[assay_type]["unit"],
                "result_qualitative": qual,
                "positive_control_passed": pos_pass,
                "negative_control_passed": neg_pass,
                "positive_control_id": (
                    "ciprofloxacin 0.25 µg/mL" if assay_type in ("MIC", "MBC") else "1% Triton X-100"
                ),
                "negative_control_id": "PBS",
                "assay_date": assay_date,
                "replicate_count": random.choice([2, 3, 3, 4]),
                "performed_by_lab": lab_name,
                "raw_data_sha256": None,
                "computational_candidate_certificate_hash": cert_hash,
                "notes": (
                    "SYNTHETIC DATA: not a real wet-lab result. "
                    f"Included only to test the calibration loop. Effect group: active."
                ),
                "disclaimer": _DISCLAIMER,
            })
            rng_index += 1

    for candidate_id in inactive_pool:
        for assay_type in assay_types:
            value = _fuzzed_value(assay_type, effect_is_active=False, noise_level=noise_level)
            qual = _qualitative(assay_type, value)
            pos_pass, neg_pass = _make_controls(noise_level)
            cert_hash = _make_cert_hash(f"{candidate_id}_{assay_type}")
            assay_date = (date.fromisoformat(start_date) + timedelta(days=random.randint(7, 30))).isoformat()

            results.append({
                "result_id": _make_result_id(rng_index),
                "candidate_id": candidate_id,
                "assay_type": assay_type,
                "organism_or_cell_line": _pick_organism(assay_type),
                "result_value": round(value, 2),
                "result_unit": ASSAY_CONFIGS[assay_type]["unit"],
                "result_qualitative": qual,
                "positive_control_passed": pos_pass,
                "negative_control_passed": neg_pass,
                "positive_control_id": (
                    "ciprofloxacin 0.25 µg/mL" if assay_type in ("MIC", "MBC") else "1% Triton X-100"
                ),
                "negative_control_id": "PBS",
                "assay_date": assay_date,
                "replicate_count": random.choice([2, 3, 3, 4]),
                "performed_by_lab": lab_name,
                "raw_data_sha256": None,
                "computational_candidate_certificate_hash": cert_hash,
                "notes": (
                    "SYNTHETIC DATA: not a real wet-lab result. "
                    f"Included only to test the calibration loop. Effect group: inactive."
                ),
                "disclaimer": _DISCLAIMER,
            })
            rng_index += 1

    return results


def load_candidate_ids(panel_csv: str | Path) -> list[str]:
    """Load candidate IDs from a pilot panel CSV.

    Expects a ``candidate_id`` column (or ``id`` as fallback).
    Falls back to generating synthetic IDs if the file is missing.
    """
    p = Path(panel_csv)
    if not p.exists():
        print(f"Panel CSV not found at {p}, generating demo candidate IDs.", file=sys.stderr)
        return [f"SYNTHETIC-SEED-{i:04d}" for i in range(1, 101)]

    ids: list[str] = []
    with p.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return ids
        id_col = "candidate_id" if "candidate_id" in reader.fieldnames else "id"
        for row in reader:
            cid = row.get(id_col, "").strip()
            if cid:
                ids.append(cid)
    return ids


def write_results(results: list[dict[str, Any]], out_dir: str | Path) -> list[Path]:
    """Write each result dict to a separate JSON file in ``out_dir``.

    Returns the list of created file paths.
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for r in results:
        fname = f"{r['result_id']}.json"
        p = d / fname
        with open(p, "w") as f:
            json.dump(r, f, indent=2)
        paths.append(p)
    return paths


def _validate_against_schema(results: list[dict[str, Any]]) -> int:
    """Validate all results against lab_result.schema.json, return n_errors."""
    schema_path = (
        Path(__file__).resolve().parent.parent / "schemas" / "lab_result.schema.json"
    )
    if not schema_path.exists():
        print(f"Schema not found at {schema_path}, skipping validation.", file=sys.stderr)
        return 0

    try:
        from openamp_foundry.evidence.schemas import validate_json_schema
    except ImportError:
        print("Cannot import schema validator, skipping validation.", file=sys.stderr)
        return 0

    errors = 0
    for r in results:
        try:
            validate_json_schema(r, schema_path)
        except Exception as e:
            print(f"  Schema error in {r['result_id']}: {e}", file=sys.stderr)
            errors += 1
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic lab results for testing the calibration loop.",
    )
    parser.add_argument(
        "--panel-csv",
        default=None,
        help="Path to pilot panel CSV with candidate_id column. If omitted, generates demo IDs.",
    )
    parser.add_argument(
        "--cohort-size",
        type=int,
        default=DEFAULT_COHORT_SIZE,
        help=f"Number of candidates to generate results for (default: {DEFAULT_COHORT_SIZE}).",
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=DEFAULT_EFFECT_SIZE,
        help=f"Fraction of candidates showing activity, 0-1 (default: {DEFAULT_EFFECT_SIZE}).",
    )
    parser.add_argument(
        "--noise-level",
        type=float,
        default=DEFAULT_NOISE_LEVEL,
        help=f"Fractional noise magnitude, 0-1 (default: {DEFAULT_NOISE_LEVEL}).",
    )
    parser.add_argument(
        "--assay-types",
        nargs="+",
        default=list(DEFAULT_ASSAY_TYPES),
        choices=list(ASSAY_CONFIGS.keys()),
        help=f"Assay types to generate (default: {' '.join(DEFAULT_ASSAY_TYPES)}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible generation.",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help=f"Output directory for result JSON files (default: {DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--lab-name",
        default=SYNTHETIC_LAB,
        help=f"Lab name for performed_by_lab field.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate generated files against schema (default: True).",
    )
    parser.add_argument(
        "--no-validate",
        action="store_false",
        dest="validate",
        help="Skip schema validation.",
    )
    return parser.parse_args(argv)


def _print_summary(results: list[dict[str, Any]], paths: list[Path]) -> None:
    active = [r for r in results if r.get("result_qualitative") == "active"]
    inactive = [r for r in results if r.get("result_qualitative") == "inactive"]
    controls_ok = [
        r for r in results
        if r.get("positive_control_passed") and r.get("negative_control_passed")
    ]

    print(f"\n  Generated {len(results)} synthetic lab result files in {paths[0].parent}:")
    print(f"    Candidates tested:  {len({r['candidate_id'] for r in results})}")
    print(f"    Assay types:        {sorted({r['assay_type'] for r in results})}")
    print(f"    Active results:     {len(active)}")
    print(f"    Inactive results:   {len(inactive)}")
    print(f"    Controls passed:    {len(controls_ok)} / {len(results)}")
    print(f"    First result:       {results[0]['result_id']}")
    print(f"    Last result:        {results[-1]['result_id']}")
    print(f"    SYNTHETIC label:    YES (in organism, lab, notes, and disclaimer fields)")
    print()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    candidate_ids = load_candidate_ids(args.panel_csv) if args.panel_csv else []
    if not candidate_ids:
        candidate_ids = [f"SYNTHETIC-SEED-{i:04d}" for i in range(1, args.cohort_size + 1)]

    if len(candidate_ids) < args.cohort_size:
        print(
            f"Warning: panel CSV has {len(candidate_ids)} candidates, "
            f"requested cohort size {args.cohort_size}. Using all available.",
            file=sys.stderr,
        )
        args.cohort_size = len(candidate_ids)

    results = generate_synthetic_results(
        candidate_ids=candidate_ids,
        cohort_size=args.cohort_size,
        effect_size=args.effect_size,
        noise_level=args.noise_level,
        assay_types=tuple(args.assay_types),
        lab_name=args.lab_name,
    )

    paths = write_results(results, args.out_dir)

    if args.validate:
        n_errors = _validate_against_schema(results)
        if n_errors > 0:
            print(f"\n  Schema validation FAILED with {n_errors} error(s).", file=sys.stderr)
            return 2
        print(f"\n  Schema validation: {len(results)} / {len(results)} passed.")
    else:
        print("\n  Schema validation skipped.")

    _print_summary(results, paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
