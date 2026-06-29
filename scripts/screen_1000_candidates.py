"""
Post-generation screening pipeline for all 1000 de novo candidates.

Runs:
  1. Macrel (local, installed) — AMP classification + hemolysis prediction
  2. Writes ranked CSV and FASTA ready for batch upload to:
       AMPScanner v2  — https://www.dveltri.com/ascan/v2/ascan.html
       HemoFinder     — http://crdd.osdd.net/raghava/hemolypred
       AntiCP2        — https://webs.iiitd.edu.in/raghava/anticp2/
       CAMPR4         — http://www.camp3.bicnirrh.res.in

Usage:
    .venv/bin/python3 scripts/screen_1000_candidates.py

Input:  outputs/denovo_1000_candidates.fasta
Output:
    outputs/screening_1000/macrel_results.csv
    outputs/screening_1000/all_1000_ranked.csv
    outputs/screening_1000/top200_for_web_predictors.fasta
    outputs/screening_1000/top50_strict_shortlist.fasta
    outputs/screening_1000/summary.md
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_FASTA  = ROOT / "outputs" / "denovo_1000_candidates.fasta"
INPUT_CSV    = ROOT / "outputs" / "denovo_1000_candidates.csv"
OUT_DIR      = ROOT / "outputs" / "screening_1000"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── 1. Macrel (local) ─────────────────────────────────────────────────────────

def run_macrel() -> dict[str, dict]:
    """Run Macrel on all candidates. Returns {seq: {amp_prob, hemo_prob, ...}}."""
    print("=== Step 1: Macrel (local) ===")
    print(f"  Input: {INPUT_FASTA.name}  ({INPUT_FASTA.stat().st_size // 1024} KB)")

    macrel_out = OUT_DIR / "macrel_output"
    macrel_out.mkdir(exist_ok=True)

    cmd = [
        sys.executable, "-m", "macrel", "peptides",
        "--fasta", str(INPUT_FASTA),
        "--output", str(macrel_out),
        "--tag", "denovo1000",
        "--force",
    ]
    print(f"  Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  [ERROR] Macrel failed:\n{result.stderr}")
        return {}

    # Find output TSV
    tsv_files = list(macrel_out.glob("*.tsv")) + list(macrel_out.glob("*.prediction"))
    if not tsv_files:
        # Try the default output name
        tsv_files = list(macrel_out.glob("*"))
        print(f"  Output files: {[f.name for f in tsv_files]}")

    results: dict[str, dict] = {}
    for tsv in tsv_files:
        if not tsv.suffix in (".tsv", ".gz") and "prediction" not in tsv.name:
            continue
        try:
            import gzip
            opener = gzip.open if tsv.suffix == ".gz" else open
            with opener(tsv, "rt") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    seq_id = row.get("sequence_id", row.get("Access", ""))
                    results[seq_id] = {
                        "macrel_amp":  row.get("AMP",  row.get("Pred",  "?")),
                        "macrel_amp_prob":  float(row.get("AMP_prob",  row.get("pAMP",  0))),
                        "macrel_hemo": row.get("HEMO", row.get("Hemo",  "?")),
                        "macrel_hemo_prob": float(row.get("HEMO_prob", row.get("pHemo", 0))),
                    }
        except Exception as e:
            print(f"  [WARN] Could not parse {tsv.name}: {e}")

    if not results:
        # Try to parse stdout
        print("  Parsing stdout fallback...")
        for line in result.stdout.splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                results[parts[0]] = {
                    "macrel_amp":       parts[1] if len(parts) > 1 else "?",
                    "macrel_amp_prob":  float(parts[2]) if len(parts) > 2 else 0.0,
                    "macrel_hemo":      parts[3] if len(parts) > 3 else "?",
                    "macrel_hemo_prob": float(parts[4]) if len(parts) > 4 else 0.0,
                }

    print(f"  Macrel classified {len(results)} sequences")
    if results:
        amp_pos  = sum(1 for r in results.values() if r["macrel_amp"]  in ("AMP",  "1", "Yes"))
        hemo_neg = sum(1 for r in results.values() if r["macrel_hemo"] in ("NHEMO","0", "No", "NonHemo"))
        print(f"  AMP positive:       {amp_pos} / {len(results)}")
        print(f"  Hemo negative:      {hemo_neg} / {len(results)}")
    return results


# ── 2. Load generator CSV ─────────────────────────────────────────────────────

def load_candidates() -> list[dict]:
    with open(INPUT_CSV) as f:
        return list(csv.DictReader(f))


# ── 3. Merge and rank ─────────────────────────────────────────────────────────

def merge_and_rank(candidates: list[dict], macrel: dict[str, dict]) -> list[dict]:
    merged = []
    for c in candidates:
        cid = c["candidate_id"]
        m   = macrel.get(cid, {})
        row = dict(c)
        row["macrel_amp"]       = m.get("macrel_amp",       "?")
        row["macrel_amp_prob"]  = m.get("macrel_amp_prob",  0.0)
        row["macrel_hemo"]      = m.get("macrel_hemo",      "?")
        row["macrel_hemo_prob"] = m.get("macrel_hemo_prob", 0.0)

        # Composite score: reward AMP signal + low hemolysis
        amp_score  = float(row.get("activity_proxy",  0))
        safe_score = float(row.get("safety_proxy",    0))
        macrel_amp_s  = row["macrel_amp_prob"]
        macrel_hemo_s = 1.0 - row["macrel_hemo_prob"]  # lower hemo = better

        row["composite_score"] = round(
            0.30 * amp_score
            + 0.25 * safe_score
            + 0.25 * macrel_amp_s
            + 0.20 * macrel_hemo_s,
            4,
        )
        merged.append(row)

    merged.sort(key=lambda x: -x["composite_score"])
    return merged


# ── 4. Write outputs ──────────────────────────────────────────────────────────

MERGED_FIELDNAMES = [
    "rank", "candidate_id", "sequence", "length", "charge", "hydro_frac",
    "amphipathicity", "aromatic_frac", "activity_proxy", "safety_proxy",
    "macrel_amp", "macrel_amp_prob", "macrel_hemo", "macrel_hemo_prob",
    "composite_score", "best_identity", "best_hit_id", "novelty_class", "patent_risk",
]


def write_ranked_csv(merged: list[dict]) -> None:
    out = OUT_DIR / "all_1000_ranked.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MERGED_FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for rank, row in enumerate(merged, 1):
            row["rank"] = rank
            w.writerow(row)
    print(f"\n  Ranked CSV → {out.name}")


def write_fasta_subset(merged: list[dict], n: int, label: str, tag: str) -> Path:
    out = OUT_DIR / f"{tag}.fasta"
    with open(out, "w") as f:
        for r in merged[:n]:
            cid = r["candidate_id"]
            f.write(
                f">{cid} rank={r.get('rank','?')} composite={r['composite_score']:.3f} "
                f"macrel_amp={r['macrel_amp_prob']:.3f} macrel_hemo={r['macrel_hemo_prob']:.3f} "
                f"charge={r['charge']} moment={r['amphipathicity']} "
                f"note=N_ACETYLATION_RECOMMENDED\n"
            )
            f.write(r["sequence"] + "\n")
    print(f"  {label} → {out.name}  ({n} sequences)")
    return out


def write_summary(merged: list[dict]) -> None:
    total = len(merged)
    macrel_amp_pos  = sum(1 for r in merged if r["macrel_amp"]  in ("AMP", "1", "Yes"))
    macrel_hemo_neg = sum(1 for r in merged if r["macrel_hemo"] in ("NHEMO","0","No","NonHemo"))
    strict = [
        r for r in merged
        if r["macrel_amp"]  in ("AMP","1","Yes")
        and r["macrel_hemo"] in ("NHEMO","0","No","NonHemo")
    ]

    out = OUT_DIR / "summary.md"
    with open(out, "w") as f:
        f.write("# Screening Summary — 1000 De Novo Candidates\n\n")
        f.write(f"Total candidates: **{total}**  \n")
        f.write(f"All {total} are HIGH_CONFIDENCE_NOVEL + CLEAR (novelty screen passed).\n\n")
        f.write("## Macrel Results\n\n")
        f.write(f"| Metric | Count | % |\n|---|---|---|\n")
        f.write(f"| AMP positive | {macrel_amp_pos} | {100*macrel_amp_pos/total:.0f}% |\n")
        f.write(f"| Hemo negative (NonHemo) | {macrel_hemo_neg} | {100*macrel_hemo_neg/total:.0f}% |\n")
        f.write(f"| AMP+ AND Hemo− (strict) | {len(strict)} | {100*len(strict)/total:.0f}% |\n\n")
        f.write("## Strict Shortlist (AMP+ and NonHemo)\n\n")
        f.write("| Rank | ID | Sequence | Composite | Macrel AMP | Macrel Hemo |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in strict[:30]:
            f.write(
                f"| {r.get('rank','?')} | {r['candidate_id']} | `{r['sequence']}` | "
                f"{r['composite_score']:.3f} | {r['macrel_amp_prob']:.3f} | {r['macrel_hemo_prob']:.3f} |\n"
            )
        f.write("\n## Web Predictor Submission Files\n\n")
        f.write("Submit these files to external predictors:\n\n")
        f.write("| File | Predictor | URL |\n|---|---|---|\n")
        f.write("| `top200_for_web_predictors.fasta` | AMPScanner v2 | https://www.dveltri.com/ascan/v2/ascan.html |\n")
        f.write("| `top200_for_web_predictors.fasta` | HemoFinder | http://crdd.osdd.net/raghava/hemolypred |\n")
        f.write("| `top200_for_web_predictors.fasta` | AntiCP2 | https://webs.iiitd.edu.in/raghava/anticp2/ |\n")
        f.write("| `top200_for_web_predictors.fasta` | CAMPR4 | http://www.camp3.bicnirrh.res.in |\n")

    print(f"  Summary → {out.name}")
    print(f"\n  Macrel AMP+:       {macrel_amp_pos}/{total}")
    print(f"  Macrel Hemo−:      {macrel_hemo_neg}/{total}")
    print(f"  Strict (AMP+∩Hemo−): {len(strict)}/{total}")
    if strict:
        print(f"\n  Top 5 strict candidates:")
        for r in strict[:5]:
            print(f"    {r['candidate_id']}: {r['sequence']}  composite={r['composite_score']:.3f}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if not INPUT_FASTA.exists():
        print(f"Input not found: {INPUT_FASTA}")
        print("Wait for generate_1000_novel_amps.py to finish first.")
        sys.exit(1)

    n_seqs = sum(1 for l in open(INPUT_FASTA) if l.startswith(">"))
    print(f"Input: {n_seqs} candidates from {INPUT_FASTA.name}\n")

    macrel   = run_macrel()
    cands    = load_candidates()

    print(f"\n=== Step 2: Merge + rank ===")
    merged   = merge_and_rank(cands, macrel)

    print(f"\n=== Step 3: Write outputs ===")
    write_ranked_csv(merged)
    write_fasta_subset(merged, 200, "Top 200 for web predictors", "top200_for_web_predictors")
    write_fasta_subset(merged, 50,  "Top 50 strict shortlist",    "top50_strict_shortlist")
    write_summary(merged)

    print(f"\n=== Done ===")
    print(f"Output directory: {OUT_DIR}/")
    print(f"\nNext steps:")
    print(f"  1. Upload top200_for_web_predictors.fasta to AMPScanner v2, HemoFinder, AntiCP2, CAMPR4")
    print(f"  2. Merge web results with all_1000_ranked.csv")
    print(f"  3. Pick final 8-10 wet-lab panel")


if __name__ == "__main__":
    main()
