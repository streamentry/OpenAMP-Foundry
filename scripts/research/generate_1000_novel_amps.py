"""
Large-scale de novo AMP generator — target 1000 HIGH_CONFIDENCE_NOVEL candidates.

Key improvements over generate_100_novel_amps.py (Wave 1):
  1. Anti-hemolysis biophysical filters:
       - Aromatic fraction (F/W/Y) ≤ 0.25  (Trp-heavy → hemolytic)
       - Tryptophan count ≤ 2
       - Hydrophobic moment capped at 0.48  (melittin-like ≥ 0.50 → hemolytic)
       - Hydrophobic fraction ceiling dropped to 0.50
  2. Alphabet rebalanced toward polar/helix-breaking residues:
       - W reduced 5→2, F reduced 5→3
       - P increased 2→5 (helix breaker → lower hemolysis)
       - G increased 2→4, N 1→3, S 2→3, T 2→3
  3. Multiprocessing: each worker builds its own DB + aligner once.
     Batches of bio-passing candidates are scanned in parallel.
  4. Scaffold diversity bucketing: max 30 candidates per (charge, length, hf) bin.
  5. Checkpoint every 50 candidates so no work is lost.

DB: full 51,503-sequence corpus (APD6 + DRAMP 3.0 + UniProt + ESCAPE + dbAMP3 + DBAASP)

Usage:
    .venv/bin/python3 scripts/generate_1000_novel_amps.py [--workers N]

Output:
    outputs/denovo_1000_candidates.csv
    outputs/denovo_1000_candidates.fasta
"""

from __future__ import annotations

import argparse
import csv
import math
import multiprocessing as mp
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

# ── DB sources — must match run_expanded_novelty_audit.py ────────────────────

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

DB_SOURCE_LIST: list[tuple[str, str, bool]] = [
    ("apd6_natural",       "data/novelty_db/apd6_natural.fasta",          False),
    ("apd6_animal",        "data/novelty_db/apd6_animal.fasta",           False),
    ("apd6_plant",         "data/novelty_db/apd6_plant.fasta",            False),
    ("apd6_bacteria",      "data/novelty_db/apd6_bacteria.fasta",         False),
    ("apd6_human",         "data/novelty_db/apd6_human.fasta",            False),
    ("dramp_general",      "data/novelty_db/dramp_general.fasta",         False),
    ("dramp_patent",       "data/novelty_db/dramp_patent.fasta",          True),
    ("dramp_specific",     "data/novelty_db/dramp_specific.fasta",        False),
    ("uniprot_reviewed",   "data/novelty_db/uniprot_amps_reviewed.fasta", False),
    ("uniprot_unreviewed", "data/novelty_db/uniprot_amps_unreviewed.fasta",False),
    ("uniprot_combined",   "data/novelty_db/uniprot_amps.fasta",          False),
    ("escape_amps",        "data/novelty_db/escape_amps.fasta",           False),
    ("dbamp3",             "data/novelty_db/dbAMP3.fasta",                False),
    ("dbaasp",             "data/novelty_db/dbaasp-peptides.fasta",       False),
]

OUTPUT_CSV   = ROOT / "outputs" / "denovo_1000_candidates.csv"
OUTPUT_FASTA = ROOT / "outputs" / "denovo_1000_candidates.fasta"

FIELDNAMES = [
    "candidate_id", "sequence", "length", "charge", "hydro_frac",
    "amphipathicity", "aromatic_frac", "activity_proxy", "safety_proxy",
    "best_identity", "best_hit_id", "novelty_class", "patent_risk", "seed_family",
]

# ── Biophysics ────────────────────────────────────────────────────────────────

EISENBERG: dict[str, float] = {
    "A": 0.25, "R": -1.76, "N": -0.64, "D": -0.72, "C": 0.04,
    "Q": -0.69, "E": -0.62, "G": 0.16,  "H": -0.40, "I": 0.73,
    "L": 0.53, "K": -1.10, "M": 0.26,  "F": 0.61,  "P": -0.07,
    "S": -0.26, "T": -0.18, "W": 0.37,  "Y": 0.02,  "V": 0.54,
}

CATIONIC    = frozenset("KR")
HYDROPHOBIC = frozenset("LIVWFA")
AROMATIC    = frozenset("FWY")
ANIONIC     = frozenset("DE")
NO_SYNTH    = frozenset("CM")
PYROGLU     = frozenset("QE")


def _net_charge(seq: str) -> int:
    return sum(1 for aa in seq if aa in CATIONIC) - sum(1 for aa in seq if aa in ANIONIC)


def _hydrophobic_moment(seq: str) -> float:
    angle = math.radians(100.0)
    hx = sum(EISENBERG.get(aa, 0.0) * math.cos(i * angle) for i, aa in enumerate(seq))
    hy = sum(EISENBERG.get(aa, 0.0) * math.sin(i * angle) for i, aa in enumerate(seq))
    return math.sqrt(hx * hx + hy * hy) / len(seq)


def _passes_design_filters(seq: str) -> bool:
    n = len(seq)
    if n < 14 or n > 22:
        return False
    if any(aa in NO_SYNTH for aa in seq):
        return False
    if seq[0] in PYROGLU:
        return False

    charge = _net_charge(seq)
    if charge < 3 or charge > 7:
        return False

    hf = sum(1 for aa in seq if aa in HYDROPHOBIC) / n
    if hf < 0.25 or hf > 0.50:
        return False

    # Anti-hemolysis: cap aromatic fraction
    af = sum(1 for aa in seq if aa in AROMATIC) / n
    if af > 0.25:
        return False

    # Anti-hemolysis: limit Trp count specifically
    if seq.count("W") > 2:
        return False

    moment = _hydrophobic_moment(seq)
    if moment < 0.20:
        return False
    # Anti-hemolysis: reject melittin-like high-moment peptides
    if moment > 0.48:
        return False

    return True


def _internal_score(seq: str) -> tuple[float, float]:
    n      = len(seq)
    charge = _net_charge(seq)
    hf     = sum(1 for aa in seq if aa in HYDROPHOBIC) / n
    af     = sum(1 for aa in seq if aa in AROMATIC) / n
    moment = _hydrophobic_moment(seq)

    activity  = min(1.0, (moment * 2.0) * ((charge / n) * 3.0))
    hemo_risk = max(0.0, hf - 0.40) * 2.0 + max(0.0, af - 0.20) * 1.5
    safety    = max(0.0, 1.0 - hemo_risk)
    return round(activity, 4), round(safety, 4)


# ── Alphabet (biased away from hemolysis risk) ────────────────────────────────

# W reduced (hemolysis), F reduced, P/G increased (helix breaker), N/S/T increased (polar)
_WEIGHTS = {
    "A": 3, "D": 1, "E": 1, "F": 3, "G": 4,
    "H": 1, "I": 6, "K": 8, "L": 7, "N": 3,
    "P": 5, "Q": 1, "R": 8, "S": 3, "T": 3,
    "V": 5, "W": 2, "Y": 2,
}
_POOL = [aa for aa, w in _WEIGHTS.items() for _ in range(w)]


def generate_candidate(rng: random.Random, length: int) -> str:
    return "".join(rng.choice(_POOL) for _ in range(length))


# ── DB + alignment (worker-side) ─────────────────────────────────────────────

# Worker-process globals — initialized once per worker
_WDB: list = []
_WALIGNER = None


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    header, parts = "", []
    try:
        with open(path) as f:
            for line in f:
                line = line.rstrip()
                if line.startswith(">"):
                    if header and parts:
                        results.append((header, "".join(parts).upper()))
                    header = line[1:].split()[0] if len(line) > 1 else "UNKNOWN"
                    parts = []
                else:
                    parts.append(line)
        if header and parts:
            results.append((header, "".join(parts).upper()))
    except FileNotFoundError:
        pass
    return results


def _build_db_worker(root_str: str) -> list:
    root = Path(root_str)
    seen: dict[str, tuple[str, bool]] = {}
    for name, rel, is_patent in DB_SOURCE_LIST:
        path = root / rel
        if not path.exists():
            continue
        for header, seq in _load_fasta(path):
            if not seq or not all(c in STANDARD_AA for c in seq) or not (5 <= len(seq) <= 100):
                continue
            seq_id = f"{name}:{header}"
            if seq not in seen:
                seen[seq] = (seq_id, is_patent)
            elif is_patent and not seen[seq][1]:
                seen[seq] = (seen[seq][0], True)
    return [(seq, sid, pat) for seq, (sid, pat) in seen.items()]


def _worker_init(root_str: str) -> None:
    from Bio.Align import PairwiseAligner, substitution_matrices
    global _WDB, _WALIGNER
    _WDB = _build_db_worker(root_str)
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score   = -11.0
    a.extend_gap_score = -1.0
    _WALIGNER = a


def _local_identity(query: str, target: str) -> float:
    try:
        aln = next(iter(_WALIGNER.align(query, target)))
    except Exception:
        return 0.0
    n_matches = 0
    for (qs, qe), (ts, te) in zip(aln.aligned[0], aln.aligned[1]):
        for i in range(qe - qs):
            if query[qs + i] == target[ts + i]:
                n_matches += 1
    return n_matches / len(query) if query else 0.0


def _worker_scan(seq: str) -> tuple[str, float, str, bool]:
    """Returns (seq, best_identity, best_hit_id, is_patent)."""
    n = len(seq)
    min_l, max_l = max(5, n // 3), n * 3
    best_id, best_hit, best_pat = 0.0, "NONE", False
    for db_seq, db_id, db_pat in _WDB:
        if not (min_l <= len(db_seq) <= max_l):
            continue
        if seq in db_seq:
            return seq, 1.0, db_id, db_pat
        identity = _local_identity(seq, db_seq)
        if identity > best_id:
            best_id, best_hit, best_pat = identity, db_id, db_pat
        if best_id >= 0.40:
            return seq, best_id, best_hit, best_pat
    return seq, best_id, best_hit, best_pat


# ── Diversity bucketing ───────────────────────────────────────────────────────

MAX_PER_BIN = 30


def _diversity_bin(seq: str) -> tuple[int, int, int]:
    charge = _net_charge(seq)
    hf     = sum(1 for aa in seq if aa in HYDROPHOBIC) / len(seq)
    return (
        min(charge, 7) // 2,       # charge bucket: 0-1, 2-3, 4-5, 6-7
        len(seq) // 4,             # length bucket: 14-17→3, 18-21→4, 22-25→5
        int(hf * 5),               # hf bucket: 0.25-0.30→1, ..., 0.45-0.50→2
    )


# ── Output ────────────────────────────────────────────────────────────────────

def _write_outputs(results: list[dict]) -> None:
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(results)
    with open(OUTPUT_FASTA, "w") as f:
        for r in results:
            f.write(
                f">{r['candidate_id']} class={r['novelty_class']} "
                f"sim={r['best_identity']:.1%} {r['patent_risk']} "
                f"charge={r['charge']} moment={r['amphipathicity']:.4f} "
                f"activity={r['activity_proxy']:.3f} safety={r['safety_proxy']:.3f} "
                f"note=N_ACETYLATION_RECOMMENDED\n"
            )
            f.write(r["sequence"] + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1),
                        help="Parallel worker processes (default: CPU count - 1)")
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7777)
    args = parser.parse_args()

    N_TARGET       = args.target
    N_WORKERS      = args.workers
    SEED           = args.seed
    BATCH_SIZE     = N_WORKERS * 4    # how many bio-passing candidates to submit per round
    N_MAX_TRIES    = 10_000_000
    CHECKPOINT_EVERY = 50
    LENGTHS        = [14, 15, 16, 17, 18, 19, 20, 21, 22]

    print(f"=== De Novo AMP Generator — Target: {N_TARGET} HIGH_CONFIDENCE_NOVEL ===")
    print(f"DB: APD6 + DRAMP 3.0 + UniProt + ESCAPE NeurIPS-2025 + dbAMP 3.0 + DBAASP")
    print(f"Workers: {N_WORKERS}  |  Seed: {SEED}  |  Batch size: {BATCH_SIZE}")
    print(f"Anti-hemolysis filters: aromatic ≤25%, W ≤2, moment 0.20–0.48")
    print(f"Alphabet: W↓ F↓  P↑ G↑ N↑ S↑ T↑  (helix-breaker / polar bias)\n")

    print(f"Starting {N_WORKERS} worker processes (each loads {len(DB_SOURCE_LIST)} DB sources)...", flush=True)
    t0 = time.time()

    ctx = mp.get_context("spawn")
    pool = ctx.Pool(
        processes=N_WORKERS,
        initializer=_worker_init,
        initargs=(str(ROOT),),
    )

    print(f"Workers ready in {time.time()-t0:.1f}s\n", flush=True)

    rng         = random.Random(SEED)
    results:    list[dict] = []
    seen_seqs:  set[str]  = set()
    bin_counts: dict[tuple, int] = defaultdict(int)

    n_generated = n_bio_pass = n_novel = n_dropped_div = 0
    t_start = time.time()

    print(f"{'#':>5}  {'ID':<14} {'Sequence':<24} {'Ch':>3} {'Moment':>7} {'AromF':>6} {'BestSim':>8}  BestHit")
    print("─" * 120)

    bio_batch: list[str] = []
    attempt   = 0

    try:
        while n_novel < N_TARGET and attempt < N_MAX_TRIES:
            # Fill a batch of bio-passing candidates
            while len(bio_batch) < BATCH_SIZE and attempt < N_MAX_TRIES:
                attempt += 1
                seq = generate_candidate(rng, rng.choice(LENGTHS))
                n_generated += 1
                if seq in seen_seqs:
                    continue
                seen_seqs.add(seq)
                if _passes_design_filters(seq):
                    n_bio_pass += 1
                    bio_batch.append(seq)

            if not bio_batch:
                break

            # Submit batch for parallel novelty scan
            scan_results = pool.map(_worker_scan, bio_batch)
            bio_batch = []

            for seq, best_id, best_hit, is_pat in scan_results:
                if best_id >= 0.40 or is_pat:
                    continue

                # Diversity gate
                div_bin = _diversity_bin(seq)
                if bin_counts[div_bin] >= MAX_PER_BIN:
                    n_dropped_div += 1
                    continue

                n_novel += 1
                bin_counts[div_bin] += 1

                activity, safety = _internal_score(seq)
                charge  = _net_charge(seq)
                hf      = sum(1 for aa in seq if aa in HYDROPHOBIC) / len(seq)
                af      = sum(1 for aa in seq if aa in AROMATIC) / len(seq)
                moment  = _hydrophobic_moment(seq)
                cid     = f"DNVL2_{n_novel:04d}"
                elapsed = time.time() - t_start

                print(
                    f"{n_novel:>5}  {cid:<14} {seq:<24} {charge:>3} {moment:>7.3f} "
                    f"{af:>6.2f} {best_id:>7.1%}  {best_hit}  [{elapsed:.0f}s]",
                    flush=True,
                )

                results.append({
                    "candidate_id":   cid,
                    "sequence":       seq,
                    "length":         len(seq),
                    "charge":         charge,
                    "hydro_frac":     round(hf, 3),
                    "amphipathicity": round(moment, 4),
                    "aromatic_frac":  round(af, 3),
                    "activity_proxy": activity,
                    "safety_proxy":   safety,
                    "best_identity":  round(best_id, 4),
                    "best_hit_id":    best_hit,
                    "novelty_class":  "HIGH_CONFIDENCE_NOVEL",
                    "patent_risk":    "CLEAR",
                    "seed_family":    cid,
                })

                if n_novel % CHECKPOINT_EVERY == 0:
                    _write_outputs(results)
                    elapsed = time.time() - t_start
                    rate    = n_novel / elapsed * 60
                    print(f"\n  [checkpoint {n_novel}/{N_TARGET}] saved → {OUTPUT_CSV.name}  "
                          f"({rate:.1f}/hr, ETA {(N_TARGET-n_novel)/rate*60:.0f}min)\n", flush=True)

                if n_novel >= N_TARGET:
                    break

    finally:
        pool.close()
        pool.join()

    elapsed = time.time() - t_start
    print("\n" + "─" * 120)
    print(f"\n=== FINAL RESULTS ===")
    print(f"  Attempts:                  {n_generated:,}")
    print(f"  Passed bio filters:        {n_bio_pass:,}  ({100*n_bio_pass/max(n_generated,1):.1f}%)")
    print(f"  Passed novelty:            {n_novel + n_dropped_div}")
    print(f"  Dropped (diversity cap):   {n_dropped_div}")
    print(f"  HIGH_CONFIDENCE_NOVEL + CLEAR: {n_novel}")
    print(f"  Time elapsed:              {elapsed:.0f}s  ({elapsed/60:.1f} min)")

    if not results:
        print("\n  No candidates found. Check filters or increase max tries.")
        return

    results.sort(key=lambda x: (-x["safety_proxy"], -x["activity_proxy"]))
    _write_outputs(results)

    print(f"\n  CSV  → {OUTPUT_CSV}")
    print(f"  FASTA→ {OUTPUT_FASTA}")
    print(f"\n  Top 15 by safety then activity:")
    print(f"  {'ID':<14} {'Sequence':<24} {'Ch':>3} {'Moment':>7} {'AromF':>6} {'BestSim':>8} {'Activity':>9} {'Safety':>7}")
    for r in results[:15]:
        print(
            f"  {r['candidate_id']:<14} {r['sequence']:<24} {r['charge']:>3} "
            f"{r['amphipathicity']:>7.3f} {r['aromatic_frac']:>6.2f} {r['best_identity']:>7.1%} "
            f"{r['activity_proxy']:>9.4f} {r['safety_proxy']:>7.4f}"
        )

    print(f"\n  Diversity bins used: {len(bin_counts)}")
    print(f"  Next: run run_expanded_novelty_audit.py --fasta {OUTPUT_FASTA.name} to confirm,")
    print(f"  then submit top 50-80 to AMPScanner / Macrel / HemoFinder / AntiCP2.")


if __name__ == "__main__":
    main()
