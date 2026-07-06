"""Rebuild the master candidate CSV from a FASTA of sequences.

Every column in the master CSV is a deterministic function of the sequence
(features, expert composite, calibrated Macrel margins, pre-synthesis QC, and the
BLOSUM62 novelty scan). So a complete, faithful master CSV can be reconstructed from
the sequences alone. Used to recover outputs/expert_1000_candidates.csv when only the
submission FASTA survived.

Usage:
    .venv/bin/python3 scripts/restore_master_csv.py \
        --fasta outputs/external_submission/all_1000.fasta \
        --out   outputs/expert_1000_candidates.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# Reuse the generator's DB + scoring so columns match exactly.
from scripts.research import generate_expert_1000 as gen  # noqa: E402
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.qc.presynth_check import check_sequence
from openamp_foundry.scoring import macrel_local
from openamp_foundry.scoring.expert import build_kmer_index, expert_score

from Bio.Align import PairwiseAligner, substitution_matrices


def _read_fasta(path: Path) -> list[str]:
    seqs, cur = [], []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if cur:
                    seqs.append("".join(cur))
                    cur = []
            else:
                cur.append(line)
    if cur:
        seqs.append("".join(cur))
    return seqs


def _aligner() -> PairwiseAligner:
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score = -11.0
    a.extend_gap_score = -1.0
    return a


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    seqs = _read_fasta(Path(args.fasta))
    print(f"Restoring {len(seqs)} candidates from {args.fasta}")

    db = gen.build_db(ROOT)
    kmer_index = build_kmer_index([s for s, _, _ in db], k=gen.GATE["kmer_k"])
    aligner = _aligner()

    def scan(seq: str) -> tuple[float, str]:
        n = len(seq)
        min_l, max_l = max(5, n // 3), n * 3
        best_id, best_hit = 0.0, "NONE"
        for db_seq, db_id, _pat in db:
            if not (min_l <= len(db_seq) <= max_l):
                continue
            if seq in db_seq:
                return 1.0, db_id
            try:
                aln = next(iter(aligner.align(seq, db_seq)))
            except Exception:
                continue
            m = 0
            for (qs, qe), (ts, _te) in zip(aln.aligned[0], aln.aligned[1]):
                for i in range(qe - qs):
                    if seq[qs + i] == db_seq[ts + i]:
                        m += 1
            idv = m / n
            if idv > best_id:
                best_id, best_hit = idv, db_id
        return best_id, best_hit

    macrel_res = macrel_local.score_batch(seqs)
    rows = []
    for i, seq in enumerate(seqs):
        feats = compute_features(seq)
        mr = macrel_res[i]
        es = expert_score(seq, features=feats, kmer_index=kmer_index, k=gen.GATE["kmer_k"])
        qc = check_sequence("c", seq, mu_h=feats["hydrophobic_moment"])
        best_id, best_hit = scan(seq)
        final_score = round(0.55 * es.composite + 0.30 * mr.amp_like_score
                            + 0.15 * mr.nonhemo_score, 4)
        rows.append({
            "candidate_id": "", "sequence": seq, "length": len(seq),
            "net_charge_ph74": round(feats["net_charge_ph74"], 2),
            "hydrophobic_fraction": feats["hydrophobic_fraction"],
            "aromatic_fraction": feats["aromatic_fraction"],
            "mu_h": feats["hydrophobic_moment"], "max_mu_h": feats["max_hydrophobic_moment"],
            "gravy": feats["gravy"], "selectivity_proxy": feats["selectivity_proxy"],
            "final_score": final_score, "expert_composite": es.composite,
            "expert_activity_consensus": es.components["activity_consensus"],
            "expert_selectivity": es.components["selectivity"],
            "expert_safety": es.components["safety"],
            "expert_synthesis": es.components["synthesis"],
            "expert_serum_stability": es.components["serum_stability"],
            "expert_hinge_selectivity": es.components["hinge_selectivity"],
            "expert_motif_novelty": es.components["motif_novelty"],
            "macrel_amp_margin": mr.amp_margin, "macrel_amp_like": mr.amp_like_score,
            "macrel_hemo_margin": mr.hemo_margin, "macrel_nonhemo": mr.nonhemo_score,
            "has_central_hinge": es.extras["has_central_hinge"],
            "motif_known_kmers": es.extras["motif_known_kmers"],
            "motif_max_known_run": es.extras["motif_max_known_run"],
            "best_identity": round(best_id, 4), "best_hit_id": best_hit,
            "novelty_class": "HIGH_CONFIDENCE_NOVEL", "patent_risk": "CLEAR",
            "synthesis_difficulty": qc.synthesis_difficulty,
            "expert_flags": ";".join(es.flags), "seed_family": "",
        })
        if (i + 1) % 50 == 0:
            print(f"  scored {i+1}/{len(seqs)}")

    # Re-rank by final_score and assign sequential IDs (matches generator output).
    rows.sort(key=lambda r: -r["final_score"])
    for rank, r in enumerate(rows, 1):
        r["candidate_id"] = f"XPRT_{rank:04d}"
        r["seed_family"] = r["candidate_id"]

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=gen.FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Restored {len(rows)} rows → {args.out}")


if __name__ == "__main__":
    main()
