"""Normalise a Macrel web/CLI export (macrel.tsv) into macrel_web_results.csv.

Macrel's output has a leading '# Prediction from macrel ...' comment line, then a TSV
with: Access, Sequence, AMP_family, is_AMP, AMP_probability, Hemolytic, Hemolytic_probability.
This is the TRUSTED Macrel reference (proper calibrated probabilities), unlike the local
ONNX scorer used as a generation gate.

Usage:
    .venv/bin/python3 scripts/convert_macrel_web.py
    .venv/bin/python3 scripts/external_consensus.py
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VDIR = ROOT / "outputs" / "external_validation"
RAW = VDIR / "macrel.tsv"
OUT = VDIR / "macrel_web_results.csv"


def main() -> None:
    if not RAW.exists():
        print(f"Not found: {RAW}")
        return
    lines = [ln for ln in RAW.read_text().splitlines() if ln and not ln.startswith("#")]
    reader = csv.DictReader(lines, delimiter="\t")
    out = []
    for r in reader:
        cid = r.get("Access", "").strip()
        if not cid.startswith("XPRT"):
            continue
        is_amp = r.get("is_AMP", "").strip().lower() == "true"
        hemo = r.get("Hemolytic", "").strip()
        out.append({
            "candidate_id": cid,
            "macrel_amp": "AMP" if is_amp else "non-AMP",
            "macrel_amp_prob": r.get("AMP_probability", ""),
            "macrel_hemo": hemo,
            "macrel_hemo_prob": r.get("Hemolytic_probability", ""),
            "is_amp_positive": is_amp,
            "is_nonhemolytic": hemo.lower().startswith("nonhemo"),
        })
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    amp = sum(1 for r in out if r["is_amp_positive"])
    nh = sum(1 for r in out if r["is_nonhemolytic"])
    print(f"Wrote {len(out)} rows -> {OUT}  (AMP+={amp}, NonHemo={nh})")


if __name__ == "__main__":
    main()
