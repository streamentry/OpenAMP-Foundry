"""Normalise an AMPActiPred export into ampactipred_results.csv for the consensus.

AMPActiPred's result page has an 'Export' button. Save that downloaded file as
  outputs/external_validation/ampactipred_raw.csv   (or .tsv / .xlsx → save-as CSV)
then run this script. It auto-detects the ID column (matching XPRT_####) and the
ABP / non-ABP prediction column, and writes the normalised result the consensus reads.

Usage:
    .venv/bin/python3 scripts/convert_ampactipred.py
    .venv/bin/python3 scripts/external_consensus.py     # re-run consensus with it
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VDIR = ROOT / "outputs" / "external_validation"
RAW_CANDIDATES = [VDIR / "ampactipred_raw.csv", VDIR / "ampactipred_raw.tsv"]
OUT = VDIR / "ampactipred_results.csv"


def _read_rows(path: Path) -> list[list[str]]:
    text = path.read_text()
    delim = "\t" if (path.suffix == ".tsv" or "\t" in text.splitlines()[0]) else ","
    return [r for r in csv.reader(text.splitlines(), delimiter=delim) if r]


def main() -> None:
    raw = next((p for p in RAW_CANDIDATES if p.exists()), None)
    if not raw:
        print("No export found. Save AMPActiPred's exported result as:")
        print(f"  {RAW_CANDIDATES[0]}   (CSV)  or  {RAW_CANDIDATES[1]} (TSV)")
        return

    rows = _read_rows(raw)
    # Find header + the ID and prediction columns.
    header = rows[0]
    id_col = pred_col = None
    for i, h in enumerate(header):
        hl = h.strip().lower()
        if id_col is None and hl in ("id", "name", "seq id", "seq. id.", "peptide id", "query"):
            id_col = i
        if pred_col is None and ("predict" in hl or "abp" in hl or "class" in hl or "activ" in hl):
            pred_col = i
    body = rows[1:]

    # Fallbacks: detect by content if headers were ambiguous.
    if id_col is None:
        for i in range(len(header)):
            if any(re.search(r"XPRT_\d+", r[i]) for r in body if len(r) > i):
                id_col = i; break
    if pred_col is None:
        for i in range(len(header)):
            if any(re.search(r"non-?ABP|ABP", r[i], re.I) for r in body if len(r) > i):
                pred_col = i; break
    if id_col is None or pred_col is None:
        print(f"Could not locate ID/prediction columns in header: {header}")
        print("Edit this script's column hints, or save with an 'ID' and 'Prediction' header.")
        return

    out = []
    for r in body:
        if len(r) <= max(id_col, pred_col):
            continue
        m = re.search(r"XPRT_\d+", r[id_col])
        if not m:
            continue
        call = r[pred_col].strip()
        # ABP positive = says ABP and not non-ABP
        is_abp = bool(re.fullmatch(r"\s*ABP\s*", call, re.I)) or (
            "abp" in call.lower() and "non" not in call.lower())
        out.append({"candidate_id": m.group(), "abp_call": call, "is_amp_positive": is_abp})

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "abp_call", "is_amp_positive"])
        w.writeheader(); w.writerows(out)
    pos = sum(1 for r in out if r["is_amp_positive"])
    print(f"Wrote {len(out)} rows -> {OUT}  (ABP+ = {pos})")
    print("Now run: .venv/bin/python3 scripts/external_consensus.py")


if __name__ == "__main__":
    main()
