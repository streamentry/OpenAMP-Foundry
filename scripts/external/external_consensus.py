"""Build the cross-tool consensus from external predictor result CSVs.

Reads every *_results.csv in outputs/external_validation/, joins them on candidate_id
with our internal scores, and produces:
  consensus_matrix.csv            — all tools joined per candidate
  consensus_report.md             — per-tool summary + agreement + strict shortlist
  strict_consensus_shortlist.csv  — ranked wet-lab priority set
  strict_consensus_shortlist.fasta

Strict shortlist = AMP-positive on >=2 independent AMP tools AND non-hemolytic AND
Non-AntiCP. Ranked by (AMP-positive tool count, then internal final_score).
"""
from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VDIR = ROOT / "outputs" / "external_validation"
MASTER = ROOT / "outputs" / "expert_1000_candidates.csv"

# tool file -> (column with bool, axis)
AMP_TOOLS = {
    "camp4_results.csv": "is_amp_positive",
    "ampscanner_results.csv": "is_amp_positive",
    "ampactipred_results.csv": "is_amp_positive",
    "macrel_web_results.csv": "is_amp_positive",
}
HEMO_TOOLS = {
    "hemofinder_results.csv": "is_nonhemolytic",
    "macrel_web_results.csv": "is_nonhemolytic",
}
ANTICP_TOOLS = {"anticp2_results.csv": "is_non_anticp"}


def _load(name: str) -> dict[str, dict]:
    p = VDIR / name
    if not p.exists():
        return {}
    with open(p) as f:
        return {r["candidate_id"]: r for r in csv.DictReader(f)}


def _truthy(v: str | None) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def main() -> None:
    master = {r["candidate_id"]: r for r in csv.DictReader(open(MASTER))}
    ids = list(master)

    amp = {n: _load(n) for n in AMP_TOOLS}
    hemo = {n: _load(n) for n in HEMO_TOOLS}
    anti = {n: _load(n) for n in ANTICP_TOOLS}
    present_amp = [n for n in AMP_TOOLS if amp[n]]
    present_hemo = [n for n in HEMO_TOOLS if hemo[n]]
    present_anti = [n for n in ANTICP_TOOLS if anti[n]]

    matrix = []
    for cid in ids:
        m = master[cid]
        row = {
            "candidate_id": cid, "sequence": m["sequence"],
            "internal_final_score": m["final_score"],
            "internal_expert_composite": m["expert_composite"],
        }
        amp_votes = 0
        for n in present_amp:
            col = AMP_TOOLS[n]
            tag = n.split("_")[0]
            v = amp[n].get(cid, {})
            ispos = _truthy(v.get(col))
            row[f"{tag}_amp"] = ispos
            amp_votes += int(ispos)
        row["amp_positive_count"] = amp_votes
        row["amp_tools_n"] = len(present_amp)

        nonhemo_all = True if present_hemo else None
        for n in present_hemo:
            tag = n.split("_")[0]
            v = hemo[n].get(cid, {})
            isnh = _truthy(v.get(HEMO_TOOLS[n]))
            row[f"{tag}_nonhemo"] = isnh
            nonhemo_all = (nonhemo_all and isnh) if nonhemo_all is not None else isnh
        row["nonhemolytic_all"] = nonhemo_all

        non_anticp = None
        for n in present_anti:
            v = anti[n].get(cid, {})
            non_anticp = _truthy(v.get(ANTICP_TOOLS[n]))
            row["anticp2_non_anticp"] = non_anticp
        row["non_anticp"] = non_anticp
        matrix.append(row)

    # ── Two shortlists ────────────────────────────────────────────────────────
    # 1) STRICT (ultra-conservative): AMP+ on >=2 tools AND non-hemolytic on EVERY hemo
    #    tool (incl. Macrel) AND Non-AntiCP. Macrel over-flags hemolysis (it calls the
    #    large majority hemolytic), so this is the most conservative possible set.
    amp_thresh = min(2, len(present_amp))
    def is_strict(r):
        ok_amp = r["amp_positive_count"] >= amp_thresh
        ok_hemo = (r["nonhemolytic_all"] is True) if present_hemo else True
        ok_anti = (r["non_anticp"] is True) if present_anti else True
        return ok_amp and ok_hemo and ok_anti
    strict = [r for r in matrix if is_strict(r)]
    strict.sort(key=lambda r: (-r["amp_positive_count"], -float(r["internal_final_score"])))

    # 2) ANTIBACTERIAL-PRIORITY (recommended): the goal is antibacterial peptides, so
    #    require AMPActiPred ABP+ (the only antibacterial-SPECIFIC predictor) AND
    #    HemoFinder non-hemolytic (primary hemolysis model; Macrel-hemo treated as
    #    advisory because it over-flags) AND Non-AntiCP AND >=2 general AMP tools.
    has_acti = "ampactipred_results.csv" in present_amp
    has_hf = "hemofinder_results.csv" in present_hemo
    def general_amp_votes(r):
        return sum(int(bool(r.get(f"{n.split('_')[0]}_amp")))
                   for n in present_amp if n != "ampactipred_results.csv")
    def is_recommended(r):
        ok_abp = bool(r.get("ampactipred_amp")) if has_acti else True
        ok_hf = bool(r.get("hemofinder_nonhemo")) if has_hf else (r["nonhemolytic_all"] is True)
        ok_anti = (r["non_anticp"] is True) if present_anti else True
        return ok_abp and ok_hf and ok_anti and general_amp_votes(r) >= 2
    recommended = [r for r in matrix if is_recommended(r)]
    recommended.sort(key=lambda r: -float(r["internal_final_score"]))

    # Write matrix
    cols = list(matrix[0].keys())
    with open(VDIR / "consensus_matrix.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(matrix)

    # Write strict shortlist csv + fasta
    with open(VDIR / "strict_consensus_shortlist.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(strict)
    with open(VDIR / "strict_consensus_shortlist.fasta", "w") as f:
        for r in strict:
            f.write(f">{r['candidate_id']} amp_calls={r['amp_positive_count']}/{r['amp_tools_n']} "
                    f"final={r['internal_final_score']} note=N_ACETYLATION_RECOMMENDED\n{r['sequence']}\n")

    # Write recommended (antibacterial-priority) shortlist csv + fasta
    with open(VDIR / "recommended_shortlist.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(recommended)
    with open(VDIR / "recommended_shortlist.fasta", "w") as f:
        for r in recommended:
            f.write(f">{r['candidate_id']} amp_calls={r['amp_positive_count']}/{r['amp_tools_n']} "
                    f"abp=1 final={r['internal_final_score']} note=N_ACETYLATION_RECOMMENDED\n{r['sequence']}\n")

    # Report
    def tool_stat(name, store, col):
        d = store[name]
        if not d:
            return f"  {name}: NOT RUN / blocked"
        pos = sum(1 for v in d.values() if _truthy(v.get(col)))
        return f"  {name}: {len(d)} scored, {pos} positive ({100*pos/len(d):.0f}%)"

    lines = []
    lines.append("# External Validation — Consensus Report\n")
    lines.append(f"Candidates: {len(ids)} | independent tools run: "
                 f"{len(present_amp)+len(present_hemo)+len(present_anti)} "
                 f"(AMP×{len(present_amp)}, hemo×{len(present_hemo)}, off-target×{len(present_anti)})\n")
    lines.append("## Per-tool summary\n")
    lines.append("**AMP-activity tools:**")
    for n in AMP_TOOLS: lines.append(tool_stat(n, amp, AMP_TOOLS[n]))
    lines.append("\n**Hemolysis tools (positive = non-hemolytic):**")
    for n in HEMO_TOOLS: lines.append(tool_stat(n, hemo, HEMO_TOOLS[n]))
    lines.append("\n**Off-target (positive = Non-AntiCP):**")
    for n in ANTICP_TOOLS: lines.append(tool_stat(n, anti, ANTICP_TOOLS[n]))

    lines.append("\n## AMP-positive agreement distribution\n")
    from collections import Counter
    dist = Counter(r["amp_positive_count"] for r in matrix)
    lines.append(f"(out of {len(present_amp)} AMP tools)\n")
    for k in sorted(dist, reverse=True):
        lines.append(f"  {k}/{len(present_amp)} AMP tools positive: {dist[k]} candidates")

    lines.append(f"\n## Strict consensus shortlist: {len(strict)} candidates\n")
    lines.append(f"Criteria: AMP-positive on ≥{amp_thresh}/{len(present_amp)} tools "
                 f"AND non-hemolytic (all hemo tools) AND Non-AntiCP.\n")
    hdr_tools = [n.split('_')[0] for n in present_amp]
    lines.append("| Rank | ID | Sequence | AMP calls | " + " | ".join(hdr_tools)
                 + " | NonHemo | NonAntiCP | final |")
    lines.append("|---|---|---|---|" + "|".join(["---"]*len(hdr_tools)) + "|---|---|---|")
    for i, r in enumerate(strict[:40], 1):
        cells = ["✓" if r.get(f"{t}_amp") else "·" for t in hdr_tools]
        lines.append(f"| {i} | {r['candidate_id']} | `{r['sequence']}` | "
                     f"{r['amp_positive_count']}/{r['amp_tools_n']} | " + " | ".join(cells)
                     + f" | {'✓' if r['nonhemolytic_all'] else '·'} "
                     f"| {'✓' if r['non_anticp'] else '·'} | {r['internal_final_score']} |")

    # Recommended (antibacterial-priority) shortlist — the practical wet-lab set.
    lines.append(f"\n## ★ Recommended antibacterial shortlist: {len(recommended)} candidates\n")
    lines.append("Criteria: **AMPActiPred ABP+** (antibacterial-specific) AND **HemoFinder "
                 "non-hemolytic** (primary hemolysis model) AND **Non-AntiCP** AND ≥2 general "
                 "AMP tools. Macrel-hemo is treated as advisory only — it over-flags hemolysis "
                 f"({sum(1 for r in matrix if r.get('macrel_nonhemo') is False)}/{len(ids)} called "
                 "hemolytic vs HemoFinder's much lower rate), so gating on it (the strict list "
                 "below) is needlessly punishing. Ranked by internal final_score.\n")
    lines.append("| Rank | ID | Sequence | AMP calls | NonHemo(HF) | ABP | final |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(recommended[:40], 1):
        lines.append(f"| {i} | {r['candidate_id']} | `{r['sequence']}` | "
                     f"{r['amp_positive_count']}/{r['amp_tools_n']} | "
                     f"{'✓' if r.get('hemofinder_nonhemo') else '·'} | "
                     f"{'✓' if r.get('ampactipred_amp') else '·'} | {r['internal_final_score']} |")

    lines.append("\n## Headline\n")
    amp3 = sum(1 for r in matrix if r["amp_positive_count"] >= max(2, len(present_amp)-1))
    lines.append(f"- {amp3}/{len(ids)} are AMP-positive on ≥{max(2,len(present_amp)-1)} independent tools.")
    lines.append(f"- **{len(recommended)}/{len(ids)} recommended** (ABP+ ∩ HemoFinder-NonHemo ∩ "
                 "Non-AntiCP ∩ ≥2 general AMP) — the practical wet-lab pool.")
    lines.append(f"- {len(strict)}/{len(ids)} ultra-strict (also non-hemolytic by Macrel, which over-flags).")
    if recommended:
        t = recommended[0]
        lines.append(f"- Top recommended candidate: **{t['candidate_id']}** "
                     f"({t['sequence']}) — antibacterial (ABP+), {t['amp_positive_count']}/"
                     f"{t['amp_tools_n']} AMP tools, HemoFinder non-hemolytic, Non-AntiCP, "
                     f"internal final={t['internal_final_score']}.")
    (VDIR / "consensus_report.md").write_text("\n".join(lines) + "\n")

    print(f"Tools present: AMP={present_amp} HEMO={present_hemo} ANTICP={present_anti}")
    print(f"Recommended (antibacterial-priority): {len(recommended)} / {len(ids)}")
    print(f"Ultra-strict (incl Macrel-hemo): {len(strict)} / {len(ids)}")
    print("Wrote consensus_matrix.csv, consensus_report.md, "
          "recommended_shortlist.{csv,fasta}, strict_consensus_shortlist.{csv,fasta}")


if __name__ == "__main__":
    main()
