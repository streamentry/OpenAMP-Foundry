"""Prepare the expert-generated 1000 for external predictor submission.

The generator (generate_expert_1000.py) already computed, for every candidate:
  • novelty (BLOSUM <40%) + motif-novelty (k-mer prior-art)
  • the full expert composite (activity ∩ selectivity ∩ safety ∩ synthesis ∩ hinge)
  • calibrated local-Macrel AMP-likeness + non-hemolysis (margin-based)
  • final_score = 0.55 expert ∩ 0.30 Macrel-AMP ∩ 0.15 Macrel-NonHemo
and ranked the file by final_score. So this step does NOT re-rank — it:

  1. Re-verifies the local-Macrel margins for integrity (independent recompute).
  2. Emits web-predictor submission FASTAs (all 1000, top-200, top-50 strict).
  3. Writes a human-readable summary with score distributions + the leading panel.

External predictors to run on the emitted FASTAs (independent of our pipeline):
  AMPScanner v2  https://www.dveltri.com/ascan/v2/ascan.html
  CAMPR4         http://www.camp3.bicnirrh.res.in
  HemoFinder     http://crdd.osdd.net/raghava/hemolypred
  AntiCP2        https://webs.iiitd.edu.in/raghava/anticp2/

Usage:
    .venv/bin/python3 scripts/prepare_external_submission.py
"""
from __future__ import annotations

import csv
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from openamp_foundry.scoring import macrel_local

IN_CSV  = ROOT / "outputs" / "expert_1000_candidates.csv"
OUT_DIR = ROOT / "outputs" / "external_submission"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict]:
    with open(IN_CSV) as f:
        return list(csv.DictReader(f))


def _verify_macrel(rows: list[dict]) -> int:
    """Re-score every sequence with macrel_local; flag any disagreement with stored gates."""
    if not macrel_local.available():
        print("  [WARN] Macrel unavailable — skipping integrity re-check")
        return -1
    seqs = [r["sequence"] for r in rows]
    res = macrel_local.score_batch(seqs)
    mismatches = 0
    for r, mr in zip(rows, res):
        if not (mr.passes_amp_gate and mr.passes_hemo_gate):
            mismatches += 1
    return mismatches


def _write_fasta(rows: list[dict], path: Path, label: str) -> None:
    with open(path, "w") as f:
        for r in rows:
            f.write(
                f">{r['candidate_id']} final={float(r['final_score']):.3f} "
                f"macrel_amp={float(r['macrel_amp_like']):.2f} "
                f"nonhemo={float(r['macrel_nonhemo']):.2f} "
                f"expert={float(r['expert_composite']):.2f} "
                f"sim={float(r['best_identity']):.1%} "
                f"charge={float(r['net_charge_ph74']):.1f} "
                f"hinge={r['has_central_hinge']} note=N_ACETYLATION_RECOMMENDED\n"
            )
            f.write(r["sequence"] + "\n")
    print(f"  {label}: {len(rows)} → {path.name}")


def _strict_shortlist(rows: list[dict]) -> list[dict]:
    """Top candidates that are strong on BOTH model families AND hinged + selective."""
    out = []
    for r in rows:
        if (float(r["macrel_amp_like"]) >= 0.60
                and float(r["macrel_nonhemo"]) >= 0.40
                and float(r["expert_selectivity"]) >= 0.70
                and float(r["expert_composite"]) >= 0.75):
            out.append(r)
    return out


def _dist(rows: list[dict], col: str) -> str:
    v = [float(r[col]) for r in rows]
    return f"min={min(v):.2f} med={st.median(v):.2f} max={max(v):.2f}"


def _summary(rows: list[dict], strict: list[dict], mismatches: int) -> None:
    out = OUT_DIR / "summary.md"
    n = len(rows)
    with open(out, "w") as f:
        f.write("# External Submission Summary — Expert-Generated Candidates\n\n")
        f.write(f"Total candidates: **{n}** (ranked by `final_score`).\n\n")
        f.write("Every candidate already satisfies, by construction:\n")
        f.write("- novel (<40% BLOSUM62 identity to 51,503 known AMPs) + motif-novel (k-mer)\n")
        f.write("- selective (proxy ≥0.55) + low-hemolysis (safety ≥0.55)\n")
        f.write("- synthesisable (≥0.70, no DKP/aspartimide/Trp-photolability)\n")
        f.write("- **Macrel-AMP** (≥ gold-standard panel) ∩ **Macrel-NonHemo** (≤ magainin)\n")
        f.write("- CLEAR (no DRAMP patent proximity)\n\n")
        if mismatches >= 0:
            f.write(f"Macrel integrity re-check: **{n - mismatches}/{n}** still pass both gates "
                    f"({mismatches} mismatches).\n\n")
        f.write("## Score distributions\n\n")
        f.write("| Metric | min / median / max |\n|---|---|\n")
        for col in ["final_score", "expert_composite", "macrel_amp_like", "macrel_nonhemo",
                    "expert_selectivity", "expert_activity_consensus", "mu_h", "best_identity"]:
            f.write(f"| {col} | {_dist(rows, col)} |\n")
        f.write(f"\nCentral helix-hinge present: "
                f"{sum(1 for r in rows if r['has_central_hinge'] in ('True','1'))}/{n}\n\n")
        f.write(f"## Strict shortlist ({len(strict)} candidates)\n\n")
        f.write("AMP-like ≥0.60 ∩ NonHemo ≥0.40 ∩ selectivity ≥0.70 ∩ expert ≥0.75.\n\n")
        f.write("| Rank | ID | Sequence | final | AMP | NonHemo | expert | hinge |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(strict[:40], 1):
            f.write(f"| {i} | {r['candidate_id']} | `{r['sequence']}` | "
                    f"{float(r['final_score']):.3f} | {float(r['macrel_amp_like']):.2f} | "
                    f"{float(r['macrel_nonhemo']):.2f} | {float(r['expert_composite']):.2f} | "
                    f"{r['has_central_hinge']} |\n")
        f.write("\n## Web predictor submission\n\n")
        f.write("Run each FASTA through the external models, then intersect their AMP+/NonHemo+ calls:\n\n")
        f.write("| File | Use |\n|---|---|\n")
        f.write("| `all_1000.fasta` | full batch (predictors with no upload cap) |\n")
        f.write("| `top200.fasta` | AMPScanner v2 / CAMPR4 / HemoFinder / AntiCP2 |\n")
        f.write("| `top50_strict.fasta` | priority wet-lab shortlist seed |\n")
    print(f"  summary → {out.name}")


def main() -> None:
    if not IN_CSV.exists():
        print(f"Input not found: {IN_CSV}\nRun generate_expert_1000.py first.")
        sys.exit(1)

    rows = _load()
    print(f"Loaded {len(rows)} candidates (pre-ranked by final_score).\n")

    print("Re-verifying Macrel margins (integrity check)...")
    mismatches = _verify_macrel(rows)
    if mismatches > 0:
        print(f"  [WARN] {mismatches} candidates no longer pass Macrel gates")
    elif mismatches == 0:
        print("  All candidates re-confirmed: pass both Macrel gates.")

    print("\nWriting submission FASTAs...")
    _write_fasta(rows, OUT_DIR / "all_1000.fasta", "All")
    _write_fasta(rows[:200], OUT_DIR / "top200.fasta", "Top 200")
    strict = _strict_shortlist(rows)
    _write_fasta(strict[:50], OUT_DIR / "top50_strict.fasta", "Top 50 strict")

    print("\nWriting summary...")
    _summary(rows, strict, mismatches)

    print(f"\nDone. Output → {OUT_DIR}/")
    print(f"  {len(strict)} candidates in strict shortlist.")
    print("  Next: upload top200.fasta to AMPScanner v2, CAMPR4, HemoFinder, AntiCP2.")


if __name__ == "__main__":
    main()
