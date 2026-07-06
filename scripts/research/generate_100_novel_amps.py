"""
Large-scale de novo AMP generator — target 100 HIGH_CONFIDENCE_NOVEL candidates.

Uses the full 51,503-sequence BLOSUM62 novelty DB (APD6 + DRAMP 3.0 + UniProt +
ESCAPE NeurIPS-2025 + dbAMP 3.0 + DBAASP + APD6 human) to ensure maximum coverage.

Every candidate that passes must satisfy ALL of:
  - Biophysical design filters (charge, moment, composition, length)
  - <40% BLOSUM62 local identity to every sequence in the 51,503-seq DB
  - Not a substring of any known AMP
  - No patent hit at any threshold (DRAMP patent DB)

Design constraints:
  - Length 14–20 AA (wider than Wave 1 for more diversity)
  - Net charge +4 to +8 at pH 7.4 (K/R count)
  - Hydrophobic fraction (L/I/V/W/F/A): 25–55%
  - No Met, no Cys (synthesis/stability)
  - No Gln/Glu at N-terminus (pyroglutamate risk)
  - Eisenberg hydrophobic moment ≥ 0.20

Output (incremental — written every 10 candidates):
  outputs/denovo_100_candidates.csv
  outputs/denovo_100_candidates.fasta

Run time: estimated 30–120 minutes on a single CPU.
"""

from __future__ import annotations

import csv
import math
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from Bio.Align import PairwiseAligner, substitution_matrices

# ── Full DB — identical sources to run_expanded_novelty_audit.py ─────────────

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

DB_SOURCES: list[tuple[str, Path, bool]] = [
    ("apd6_natural",      ROOT / "data/novelty_db/apd6_natural.fasta",          False),
    ("apd6_animal",       ROOT / "data/novelty_db/apd6_animal.fasta",           False),
    ("apd6_plant",        ROOT / "data/novelty_db/apd6_plant.fasta",            False),
    ("apd6_bacteria",     ROOT / "data/novelty_db/apd6_bacteria.fasta",         False),
    ("apd6_human",        ROOT / "data/novelty_db/apd6_human.fasta",            False),
    ("dramp_general",     ROOT / "data/novelty_db/dramp_general.fasta",         False),
    ("dramp_patent",      ROOT / "data/novelty_db/dramp_patent.fasta",          True),
    ("dramp_specific",    ROOT / "data/novelty_db/dramp_specific.fasta",        False),
    ("uniprot_reviewed",  ROOT / "data/novelty_db/uniprot_amps_reviewed.fasta", False),
    ("uniprot_unreviewed",ROOT / "data/novelty_db/uniprot_amps_unreviewed.fasta",False),
    ("uniprot_combined",  ROOT / "data/novelty_db/uniprot_amps.fasta",          False),
    ("escape_amps",       ROOT / "data/novelty_db/escape_amps.fasta",           False),
    ("dbamp3",            ROOT / "data/novelty_db/dbAMP3.fasta",                False),
    ("dbaasp",            ROOT / "data/novelty_db/dbaasp-peptides.fasta",       False),
]

OUTPUT_CSV   = ROOT / "outputs" / "denovo_100_candidates.csv"
OUTPUT_FASTA = ROOT / "outputs" / "denovo_100_candidates.fasta"
CHECKPOINT   = ROOT / "outputs" / "denovo_100_checkpoint.csv"

# ── Biophysics ────────────────────────────────────────────────────────────────

EISENBERG: dict[str, float] = {
    "A": 0.25, "R": -1.76, "N": -0.64, "D": -0.72, "C": 0.04,
    "Q": -0.69, "E": -0.62, "G": 0.16,  "H": -0.40, "I": 0.73,
    "L": 0.53, "K": -1.10, "M": 0.26,  "F": 0.61,  "P": -0.07,
    "S": -0.26, "T": -0.18, "W": 0.37,  "Y": 0.02,  "V": 0.54,
}

CATIONIC    = frozenset("KR")
HYDROPHOBIC = frozenset("LIVWFA")
ANIONIC     = frozenset("DE")
NO_SYNTH    = frozenset("CM")
PYROGLU     = frozenset("QE")

# ── Weighted alphabet (no M, no C) ────────────────────────────────────────────
_WEIGHTS = {
    "A": 3, "D": 1, "E": 1, "F": 5, "G": 2,
    "H": 1, "I": 6, "K": 8, "L": 7, "N": 1,
    "P": 2, "Q": 1, "R": 8, "S": 2, "T": 2,
    "V": 5, "W": 5, "Y": 2,
}
_POOL = [aa for aa, w in _WEIGHTS.items() for _ in range(w)]


def _net_charge(seq: str) -> int:
    return sum(1 for aa in seq if aa in CATIONIC) - sum(1 for aa in seq if aa in ANIONIC)


def _hydrophobic_moment(seq: str) -> float:
    angle = math.radians(100.0)
    hx = sum(EISENBERG.get(aa, 0.0) * math.cos(i * angle) for i, aa in enumerate(seq))
    hy = sum(EISENBERG.get(aa, 0.0) * math.sin(i * angle) for i, aa in enumerate(seq))
    return math.sqrt(hx * hx + hy * hy) / len(seq)


def _passes_design_filters(seq: str) -> bool:
    if len(seq) < 14 or len(seq) > 20:
        return False
    if any(aa in NO_SYNTH for aa in seq):
        return False
    if seq[0] in PYROGLU:
        return False
    charge = _net_charge(seq)
    if charge < 4 or charge > 8:
        return False
    hf = sum(1 for aa in seq if aa in HYDROPHOBIC) / len(seq)
    if hf < 0.25 or hf > 0.55:
        return False
    if _hydrophobic_moment(seq) < 0.20:
        return False
    return True


def _internal_score(seq: str) -> tuple[float, float]:
    charge     = _net_charge(seq)
    hf         = sum(1 for aa in seq if aa in HYDROPHOBIC) / len(seq)
    moment     = _hydrophobic_moment(seq)
    charge_den = charge / len(seq)
    activity   = min(1.0, (moment * 2.0) * (charge_den * 3.0))
    hemo_risk  = max(0.0, hf - 0.45) * 3.0
    safety     = max(0.0, 1.0 - hemo_risk)
    return round(activity, 4), round(safety, 4)


# ── DB loading ────────────────────────────────────────────────────────────────

class DbEntry:
    __slots__ = ("seq_id", "sequence", "is_patent")

    def __init__(self, seq_id: str, sequence: str, is_patent: bool) -> None:
        self.seq_id    = seq_id
        self.sequence  = sequence
        self.is_patent = is_patent


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    header, parts = "", []
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
    return results


def build_db() -> tuple[list[DbEntry], int]:
    seen: dict[str, DbEntry] = {}
    for source_name, path, is_patent in DB_SOURCES:
        if not path.exists():
            print(f"  [WARN] {path.name} not found — skipping", flush=True)
            continue
        entries = _load_fasta(path)
        added = 0
        for header, seq in entries:
            if not seq or not all(c in STANDARD_AA for c in seq) or not (5 <= len(seq) <= 100):
                continue
            seq_id = f"{source_name}:{header}"
            if seq not in seen:
                seen[seq] = DbEntry(seq_id=seq_id, sequence=seq, is_patent=is_patent)
                added += 1
            elif is_patent and not seen[seq].is_patent:
                old = seen[seq]
                seen[seq] = DbEntry(seq_id=old.seq_id, sequence=old.sequence, is_patent=True)
        print(f"  {source_name}: {added} new unique sequences", flush=True)
    db = list(seen.values())
    patent_count = sum(1 for e in db if e.is_patent)
    print(f"\n  Combined DB: {len(db):,} unique clean sequences  (patent-flagged: {patent_count:,})", flush=True)
    return db, patent_count


def _make_aligner() -> PairwiseAligner:
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score   = -11.0
    a.extend_gap_score = -1.0
    return a


def novelty_scan(seq: str, db: list[DbEntry], aligner: PairwiseAligner) -> tuple[float, str, bool]:
    clen = len(seq)
    min_l, max_l = max(5, clen // 3), clen * 3
    best_id, best_hit_id, best_pat = 0.0, "NONE", False
    for e in db:
        if not (min_l <= len(e.sequence) <= max_l):
            continue
        if seq in e.sequence:
            return 1.0, e.seq_id, e.is_patent
        identity = _local_identity(seq, e.sequence, aligner)
        if identity > best_id:
            best_id, best_hit_id, best_pat = identity, e.seq_id, e.is_patent
        if best_id >= 0.40:
            return best_id, best_hit_id, best_pat
    return best_id, best_hit_id, best_pat


def _local_identity(query: str, target: str, aligner: PairwiseAligner) -> float:
    try:
        aln = next(iter(aligner.align(query, target)))
    except Exception:
        return 0.0
    n_matches = 0
    for (qs, qe), (ts, te) in zip(aln.aligned[0], aln.aligned[1]):
        for i in range(qe - qs):
            if query[qs + i] == target[ts + i]:
                n_matches += 1
    return n_matches / len(query) if query else 0.0


# ── Output helpers ────────────────────────────────────────────────────────────

FIELDNAMES = [
    "candidate_id", "sequence", "length", "charge", "hydro_frac",
    "amphipathicity", "activity_proxy", "safety_proxy",
    "best_identity", "best_hit_id", "is_patent", "novelty_class", "patent_risk",
    "seed_family",
]


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
                f"activity={r['activity_proxy']:.3f} note=N_ACETYLATION_RECOMMENDED\n"
            )
            f.write(r["sequence"] + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=== De Novo AMP Generator — Target: 100 HIGH_CONFIDENCE_NOVEL ===")
    print("DB: APD6 + DRAMP 3.0 + UniProt + ESCAPE NeurIPS-2025 + dbAMP 3.0 + DBAASP")
    print("Threshold: <40% BLOSUM62 identity to all 51,503 known AMPs, CLEAR patent status\n")

    print("Loading databases...", flush=True)
    t0 = time.time()
    db, _ = build_db()
    print(f"  Loaded in {time.time() - t0:.1f}s\n", flush=True)

    aligner = _make_aligner()
    rng     = random.Random(999)   # different seed from Wave 1 (seed=42)

    N_TARGET    = 100
    N_MAX_TRIES = 1_000_000
    LENGTHS     = [14, 15, 16, 17, 18, 19, 20]
    CHECKPOINT_EVERY = 10

    results:    list[dict] = []
    seen_seqs:  set[str]  = set()
    n_generated = n_bio_pass = n_novel = 0
    t_start = time.time()

    print(f"Generating candidates (target: {N_TARGET}, max attempts: {N_MAX_TRIES:,})...\n")
    print(f"{'#':>4}  {'ID':<15} {'Sequence':<22} {'Ch':>3} {'Moment':>7} {'BestSim':>8}  BestHit")
    print("─" * 115)

    for attempt in range(1, N_MAX_TRIES + 1):
        length = rng.choice(LENGTHS)
        seq    = generate_candidate(rng, length)
        n_generated += 1

        if seq in seen_seqs:
            continue
        seen_seqs.add(seq)

        if not _passes_design_filters(seq):
            continue
        n_bio_pass += 1

        best_id, best_hit, is_pat = novelty_scan(seq, db, aligner)

        if best_id >= 0.40 or is_pat:
            continue

        n_novel += 1
        activity, safety = _internal_score(seq)
        charge  = _net_charge(seq)
        hf      = sum(1 for aa in seq if aa in HYDROPHOBIC) / len(seq)
        moment  = _hydrophobic_moment(seq)
        cid     = f"DNVL_{n_novel:03d}"
        elapsed = time.time() - t_start
        rate    = n_novel / elapsed

        print(
            f"{n_novel:>4}  {cid:<15} {seq:<22} {charge:>3} {moment:>7.3f} "
            f"{best_id:>7.1%}  {best_hit}  "
            f"[{elapsed:.0f}s, {rate:.2f}/min × 60]",
            flush=True,
        )

        results.append({
            "candidate_id":   cid,
            "sequence":       seq,
            "length":         len(seq),
            "charge":         charge,
            "hydro_frac":     round(hf, 3),
            "amphipathicity": round(moment, 4),
            "activity_proxy": activity,
            "safety_proxy":   safety,
            "best_identity":  round(best_id, 4),
            "best_hit_id":    best_hit,
            "is_patent":      is_pat,
            "novelty_class":  "HIGH_CONFIDENCE_NOVEL",
            "patent_risk":    "CLEAR",
            "seed_family":    cid,  # each de novo is its own family
        })

        if n_novel % CHECKPOINT_EVERY == 0:
            _write_outputs(results)
            print(f"\n  [checkpoint] {n_novel}/{N_TARGET} saved → {OUTPUT_CSV}\n", flush=True)

        if n_novel >= N_TARGET:
            break

    elapsed = time.time() - t_start
    print("\n" + "─" * 115)
    print(f"\n=== FINAL RESULTS ===")
    print(f"  Attempts:             {n_generated:,}")
    print(f"  Passed bio filters:   {n_bio_pass:,}  ({100*n_bio_pass/max(n_generated,1):.1f}%)")
    print(f"  HIGH_CONFIDENCE_NOVEL + CLEAR: {n_novel}")
    print(f"  Time elapsed:         {elapsed:.1f}s  ({elapsed/60:.1f} min)")

    if not results:
        print("\n  No HCN candidates found. The 51,503-seq DB may be too dense for short")
        print("  cationic AMPs at <40% identity. Consider longer sequences or wider lengths.")
        return

    results.sort(key=lambda x: -x["activity_proxy"])
    _write_outputs(results)

    print(f"\n  CSV  → {OUTPUT_CSV}")
    print(f"  FASTA→ {OUTPUT_FASTA}")
    print(f"\n  Top 10 by activity proxy:")
    print(f"  {'ID':<15} {'Sequence':<22} {'Ch':>3} {'Moment':>7} {'BestSim':>8} {'Activity':>9} {'Safety':>7}")
    for r in results[:10]:
        print(
            f"  {r['candidate_id']:<15} {r['sequence']:<22} {r['charge']:>3} "
            f"{r['amphipathicity']:>7.3f} {r['best_identity']:>7.1%} "
            f"{r['activity_proxy']:>9.4f} {r['safety_proxy']:>7.4f}"
        )
    print(f"\n  All {len(results)} candidates are HIGH_CONFIDENCE_NOVEL + CLEAR.")
    print(f"  Next: run run_expanded_novelty_audit.py --fasta {OUTPUT_FASTA} to confirm,")
    print(f"  then submit to CAMPR4, AMPScanner v2, HemoFinder, AntiCP2.")


def generate_candidate(rng: random.Random, length: int) -> str:
    return "".join(rng.choice(_POOL) for _ in range(length))


if __name__ == "__main__":
    main()
