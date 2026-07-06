"""Expand the hemolysis reference set using DBAASP hemolytic activity data.

The within-AMP selectivity benchmark (PR #113/#114) runs on 42 peptides:
14 hemolytic (HC50 < 25 ug/ml) vs 21 selective (HC50 >= 100 ug/ml) = 35
for the binary AUROC task. The dedicated hemolysis risk scorer's detection
AUROC=0.9218 (CI 0.82-0.99) is based on this small set.

DBAASP (data/novelty_db/hemolytic-and-cytotoxic-activities.csv) contains
hemolytic activity measurements for ~880 unique peptides against human
erythrocytes. This script extracts 50%-hemolysis (HC50) values, converts
all measurements to ug/ml using peptide molecular weight, deduplicates by
sequence (median of multiple measurements), and appends new peptides to
examples/validation/hemolysis_reference.csv.

Unit conversion: ug/ml = uM * MW(kDa) = uM * MW(Da) / 1000
  MW computed from amino acid residue masses (average isotopic masses,
  water subtracted for peptide bonds, water added for terminal groups).

Classification thresholds (unchanged from existing reference):
  HEMOLYTIC: HC50 < 25 ug/ml
  MODERATE:  25 <= HC50 < 100 ug/ml
  SELECTIVE: HC50 >= 100 ug/ml

Usage: python scripts/expand_hemolysis_benchmark.py
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DBAASP_CSV = REPO_ROOT / "data" / "novelty_db" / "hemolytic-and-cytotoxic-activities.csv"
OUTPUT_CSV = REPO_ROOT / "examples" / "validation" / "hemolysis_reference.csv"

# Amino acid residue masses (average, monoisotopic would also work for relative ranking).
# Values from standard biochemical tables (e.g., Sigma-Aldrich residue mass chart).
# Includes water (18.02) in each entry; peptide bond subtracts one water.
_AA_MW: dict[str, float] = {
    "A": 89.09, "R": 174.20, "N": 132.12, "D": 133.10, "C": 121.16,
    "Q": 146.15, "E": 147.13, "G": 75.03, "H": 155.16, "I": 131.17,
    "L": 131.17, "K": 146.19, "M": 149.21, "F": 165.19, "P": 115.13,
    "S": 105.09, "T": 119.12, "W": 204.23, "Y": 181.19, "V": 117.15,
}
_H2O = 18.02


def peptide_mw(seq: str) -> float:
    """Molecular weight of a peptide in Daltons.

    Sum of amino acid masses minus water for each peptide bond,
    plus one water for the intact termini (already included in residue masses).
    """
    return sum(_AA_MW[aa] for aa in seq) - (len(seq) - 1) * _H2O


def parse_concentration(raw: str) -> tuple[float, bool] | None:
    """Extract numeric value from a concentration string.

    Returns (value, is_greater_than) or None if unparseable.
    Handles formats like "6", "0.5±0.2", ">200", "39±1.5".
    """
    s = raw.strip()
    is_gt = ">" in s
    s = s.replace("±", " ").replace(">", "").replace("<", "").strip()
    m = re.match(r"([\d.]+)", s)
    if m:
        return float(m.group(1)), is_gt
    return None


def classify_hemolysis(hc50_ugml: float) -> str:
    """Classify a peptide by HC50 in ug/ml."""
    if hc50_ugml < 25:
        return "HEMOLYTIC"
    elif hc50_ugml < 100:
        return "MODERATE"
    else:
        return "SELECTIVE"


def load_existing() -> tuple[set[str], list[dict]]:
    """Load existing hemolysis reference entries."""
    existing_seqs: set[str] = set()
    existing_rows: list[dict] = []
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            existing_seqs.add(seq)
            existing_rows.append(row)
    return existing_seqs, existing_rows


def extract_dbaasp() -> dict[str, tuple[str, float, int]]:
    """Extract HC50 values from DBAASP hemolysis data.

    Returns: {sequence: (peptide_id, median_hc50_ugml, n_measurements)}
    Only includes human erythrocyte 50% hemolysis measurements.
    """
    raw: dict[str, list[float]] = defaultdict(list)
    pid_map: dict[str, str] = {}

    with open(DBAASP_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seq = row.get("Peptide Sequence", "").strip().upper()
            pid = row.get("Peptide ID", "").strip()
            target = row.get("Target Cell", "").strip()
            measure = row.get("Activity Measure for Lysis", "").strip()
            conc_raw = row.get("Peptide Concentration", "").strip()
            unit = row.get("Unit", "").strip()

            if not seq:
                continue
            if "human erythrocyte" not in target.lower():
                continue
            if "50%" not in measure.lower() and "hc50" not in measure.lower():
                continue
            if not all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq):
                continue
            if len(seq) < 5 or len(seq) > 60:
                continue

            parsed = parse_concentration(conc_raw)
            if parsed is None:
                continue
            val, is_gt = parsed
            # Skip "greater than" values — they are lower bounds on HC50, not exact
            if is_gt:
                continue

            # Convert to ug/ml
            mw = peptide_mw(seq)
            if unit == "µM":
                hc50_ugml = val * mw / 1000.0
            elif unit in ("µg/ml", "ug/ml", "ug/mL"):
                hc50_ugml = val
            else:
                continue

            raw[seq].append(hc50_ugml)
            if seq not in pid_map:
                pid_map[seq] = pid

    # Deduplicate: take median of multiple measurements
    result: dict[str, tuple[str, float, int]] = {}
    for seq, vals in raw.items():
        median = sorted(vals)[len(vals) // 2]
        result[seq] = (pid_map[seq], round(median, 1), len(vals))

    return result


def main() -> None:
    existing_seqs, existing_rows = load_existing()
    print(f"Existing hemolysis reference: {len(existing_rows)} peptides")

    dbaasp = extract_dbaasp()
    print(f"DBAASP extracted (human erythrocyte HC50, standard AAs, 5-60aa): {len(dbaasp)}")

    # Remove sequences already in the reference
    new_seqs = {s: v for s, v in dbaasp.items() if s not in existing_seqs}
    print(f"New unique peptides (after dedup vs existing): {len(new_seqs)}")

    # Classify and build rows
    new_rows: list[dict] = []
    for seq, (pid, hc50, n_meas) in sorted(new_seqs.items(), key=lambda x: x[1][1]):
        cls = classify_hemolysis(hc50)
        new_rows.append({
            "id": f"DBAASP-{pid}",
            "sequence": seq,
            "family": "dbaasp_hemolysis",
            "hc50_ugml": str(hc50),
            "hemolysis_class": cls,
            "reference": f"DBAASP_v3_{n_meas}meas",
        })

    # Count by class
    from collections import Counter
    new_classes = Counter(r["hemolysis_class"] for r in new_rows)
    print(f"New peptides by class: {dict(new_classes)}")

    # Append to CSV
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "sequence", "family", "hc50_ugml", "hemolysis_class", "reference"],
        )
        for row in new_rows:
            writer.writerow(row)

    print(f"Appended {len(new_rows)} peptides to {OUTPUT_CSV}")

    # Summary after merge
    all_seqs, all_rows = load_existing()
    all_classes = Counter(r["hemolysis_class"] for r in all_rows)
    hemo = sum(1 for r in all_rows if float(r["hc50_ugml"]) < 25)
    sel = sum(1 for r in all_rows if float(r["hc50_ugml"]) >= 100)
    border = sum(1 for r in all_rows if 25 <= float(r["hc50_ugml"]) < 100)
    print(f"\nMerged reference: {len(all_rows)} peptides")
    print(f"  HEMOLYTIC (HC50<25): {hemo}")
    print(f"  MODERATE (25-100): {border}")
    print(f"  SELECTIVE (HC50>=100): {sel}")
    print(f"  Binary task: {hemo} hemolytic vs {sel} selective = {hemo + sel} total")
    print(f"  Previous binary task: 14 vs 21 = 35")
    print(f"  Improvement: {hemo + sel} / 35 = {(hemo + sel) / 35:.1f}x")


if __name__ == "__main__":
    main()
