"""
Wave 0.5b Novelty Audit — Full BLOSUM62 scan of all 23 wave 0.5b candidates.

Uses the same 27,234-sequence database and alignment method as the wave 0.5 audit v2:
  - APD6 natural (3,306 seqs)
  - DRAMP general (11,687 seqs)
  - DRAMP patent (18,715 seqs)  ← patent risk detection
  - UniProt AMPs ≤60aa (2,348 seqs)

Identity = matches / query_length (BLOSUM62 local alignment)
Thresholds: ≥99%=EXACT_MATCH, ≥80%=KNOWN_VARIANT, ≥60%=CLOSE_RELATIVE, ≥40%=RELATED_NOVEL, <40%=HIGH_CONFIDENCE_NOVEL
Patent risk: POSSIBLE_PATENT_RISK if best hit is from dramp_patent and identity ≥60%

Output: outputs/wave0_5b_novelty_audit.csv
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from Bio.Align import PairwiseAligner, substitution_matrices

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

DB_SOURCES: list[tuple[str, Path, bool]] = [
    ("apd6_natural",  ROOT / "data/novelty_db/apd6_natural.fasta",  False),
    ("dramp_general", ROOT / "data/novelty_db/dramp_general.fasta", False),
    ("dramp_patent",  ROOT / "data/novelty_db/dramp_patent.fasta",  True),
    ("uniprot_amps",  ROOT / "data/novelty_db/uniprot_amps.fasta",  False),
]

INPUT_CSV  = ROOT / "outputs" / "wave05b_combined_consensus.csv"
OUTPUT_CSV = ROOT / "outputs" / "wave0_5b_novelty_audit.csv"

WAVE0_5B_CANDIDATES = [
    ("SEED-020_VAR_001", "RVRIRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_002", "KVRIRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_003", "RIRIRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_004", "RLRIRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_005", "RVKIRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_006", "RVRLRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_007", "RVRVRVLKRLLK", "SEED-020"),
    ("SEED-020_VAR_008", "RVRIKVLKRLLK", "SEED-020"),
    ("SEED-021_VAR_001", "GKRKILIKRLK",  "SEED-021"),
    ("SEED-021_VAR_002", "AKRKILIKRLK",  "SEED-021"),
    ("SEED-021_VAR_003", "GRRKILIKRLK",  "SEED-021"),
    ("SEED-021_VAR_004", "GKKKILIKRLK",  "SEED-021"),
    ("SEED-021_VAR_005", "GKRRILIKRLK",  "SEED-021"),
    ("SEED-021_VAR_006", "GKRKLLIKRLK",  "SEED-021"),
    ("SEED-021_VAR_007", "GKRKVLIKRLK",  "SEED-021"),
    ("SEED-021_VAR_008", "GKRKIIIKRLK",  "SEED-021"),
    ("SEED-023_VAR_002", "RLALKLALK",    "SEED-023"),
    ("SEED-023_VAR_005", "KLGLKLALK",    "SEED-023"),
    ("SEED-023_VAR_008", "KLALRLALK",    "SEED-023"),
    ("SEED-024_VAR_002", "KKIRPILKRL",   "SEED-024"),
    ("SEED-024_VAR_004", "RKLRPILKRL",   "SEED-024"),
    ("SEED-024_VAR_005", "RKVRPILKRL",   "SEED-024"),
    ("SEED-024_VAR_006", "RKIKPILKRL",   "SEED-024"),
]


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    header = ""
    seq_parts: list[str] = []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if header and seq_parts:
                    seq = "".join(seq_parts).upper()
                    if seq:
                        results.append((header, seq))
                header = line[1:].split()[0] if len(line) > 1 else "UNKNOWN"
                seq_parts = []
            else:
                seq_parts.append(line)
    if header and seq_parts:
        seq = "".join(seq_parts).upper()
        if seq:
            results.append((header, seq))
    return results


class DbEntry:
    __slots__ = ("seq_id", "sequence", "is_patent")
    def __init__(self, seq_id: str, sequence: str, is_patent: bool) -> None:
        self.seq_id   = seq_id
        self.sequence = sequence
        self.is_patent = is_patent


def build_db() -> list[DbEntry]:
    seen: dict[str, DbEntry] = {}
    for source_name, path, is_patent in DB_SOURCES:
        if not path.exists():
            print(f"  [WARN] {path.name} not found — skipping")
            continue
        entries = _load_fasta(path)
        added = 0
        for header, seq in entries:
            if not seq:
                continue
            if not all(c in STANDARD_AA for c in seq):
                continue
            if not (5 <= len(seq) <= 100):
                continue
            seq_id = f"{source_name}:{header}"
            if seq not in seen:
                seen[seq] = DbEntry(seq_id=seq_id, sequence=seq, is_patent=is_patent)
                added += 1
            elif is_patent and not seen[seq].is_patent:
                old = seen[seq]
                seen[seq] = DbEntry(seq_id=old.seq_id, sequence=old.sequence, is_patent=True)
        print(f"  {source_name}: {len(entries)} loaded, {added} new unique sequences")
    db = list(seen.values())
    print(f"  Combined DB: {len(db)} unique standard-AA peptides (5–100aa)")
    return db


def _make_aligner() -> PairwiseAligner:
    aligner = PairwiseAligner()
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.mode = "local"
    aligner.open_gap_score  = -11.0
    aligner.extend_gap_score = -1.0
    return aligner


def _local_identity(query: str, target: str, aligner: PairwiseAligner) -> float:
    try:
        aln = next(iter(aligner.align(query, target)))
    except (StopIteration, Exception):
        return 0.0
    q_blocks, t_blocks = aln.aligned[0], aln.aligned[1]
    n_matches = 0
    for (qs, qe), (ts, te) in zip(q_blocks, t_blocks):
        for i in range(qe - qs):
            if query[qs + i] == target[ts + i]:
                n_matches += 1
    return n_matches / len(query) if query else 0.0


def _classify(best_identity: float, is_substring: bool, is_patent: bool) -> tuple[str, str, str]:
    if is_substring or best_identity >= 0.99:
        nov    = "EXACT_MATCH_OR_FRAGMENT"
        action = "EXCLUDE from novelty claims; use only as positive control"
    elif best_identity >= 0.80:
        nov    = "KNOWN_VARIANT"
        action = "Include only with strong SAR justification; label as variant clearly"
    elif best_identity >= 0.60:
        nov    = "CLOSE_RELATIVE"
        action = "Include with prior-art disclosure; IP claim requires expert review"
    elif best_identity >= 0.40:
        nov    = "RELATED_NOVEL"
        action = "Include; disclose best hit; moderate novelty claim supported"
    else:
        nov    = "HIGH_CONFIDENCE_NOVEL"
        action = "Include; strong novelty claim supported"

    if best_identity >= 0.80:
        patent = "REVIEW_REQUIRED"
    elif is_patent and best_identity >= 0.60:
        patent = "POSSIBLE_PATENT_RISK"
    elif is_patent and best_identity >= 0.40:
        patent = "LOW_PATENT_RISK"
    else:
        patent = "CLEAR"

    return nov, patent, action


def scan_candidate(
    cid: str, seq: str, seed_family: str,
    db: list[DbEntry], aligner: PairwiseAligner,
) -> dict:
    candidate_len = len(seq)
    min_len = max(5, candidate_len // 3)
    max_len = candidate_len * 3

    best_identity   = 0.0
    best_hit_id     = "NONE"
    best_hit_seq    = "NONE"
    best_is_patent  = False
    best_is_sub     = False

    for entry in db:
        if not (min_len <= len(entry.sequence) <= max_len):
            continue
        is_sub   = seq in entry.sequence
        identity = 1.0 if is_sub else _local_identity(seq, entry.sequence, aligner)
        if identity > best_identity:
            best_identity  = identity
            best_hit_id    = entry.seq_id
            best_hit_seq   = entry.sequence
            best_is_patent = entry.is_patent
            best_is_sub    = is_sub
        if best_identity >= 1.0:
            break

    nov_class, patent_risk, action = _classify(best_identity, best_is_sub, best_is_patent)
    return {
        "candidate_id":   cid,
        "sequence":       seq,
        "seed_family":    seed_family,
        "best_database":  "patent" if best_is_patent else "public",
        "best_hit_id":    best_hit_id,
        "best_hit_seq":   best_hit_seq[:80] if best_hit_seq != "NONE" else "NONE",
        "best_identity":  round(best_identity, 4),
        "novelty_class":  nov_class,
        "patent_risk":    patent_risk,
        "action":         action,
        "is_substring":   best_is_sub,
        "db_size":        len(db),
    }


FIELDNAMES = [
    "candidate_id", "sequence", "seed_family",
    "best_database", "best_hit_id", "best_hit_seq",
    "best_identity", "novelty_class", "patent_risk",
    "action", "is_substring", "db_size",
]


def main() -> None:
    print("=== Wave 0.5b Novelty Audit — Full BLOSUM62 (27,234-seq DB) ===\n")
    print("Loading AMP databases...")
    t0 = time.time()
    db = build_db()
    print(f"  Done in {time.time() - t0:.1f}s\n")

    aligner = _make_aligner()
    results: list[dict] = []

    print(f"Scanning {len(WAVE0_5B_CANDIDATES)} wave 0.5b candidates...\n")
    print(f"{'#':>4}  {'Candidate':<22} {'Sequence':<16} {'Result':<28} {'Identity':>8}  {'PatentRisk':<24}  BestHit")
    print("─" * 140)

    for i, (cid, seq, family) in enumerate(WAVE0_5B_CANDIDATES, 1):
        t1 = time.time()
        r  = scan_candidate(cid, seq, family, db, aligner)
        elapsed = time.time() - t1

        flag = "⚠ " if r["patent_risk"] in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
        print(
            f"{i:>4}  {cid:<22} {seq:<16} "
            f"{flag}{r['novelty_class']:<26} {r['best_identity']:>7.1%}  "
            f"{r['patent_risk']:<24}  {r['best_hit_id']}  ({elapsed:.1f}s)"
        )
        results.append(r)

    print("\n" + "─" * 140)
    print("\n=== SUMMARY ===\n")

    by_class: dict[str, list[str]] = {}
    by_risk:  dict[str, list[str]] = {}
    for r in results:
        by_class.setdefault(r["novelty_class"], []).append(r["candidate_id"])
        by_risk.setdefault(r["patent_risk"],    []).append(r["candidate_id"])

    for cls, ids in sorted(by_class.items()):
        print(f"  {cls}: {len(ids)} — {', '.join(ids)}")

    print()
    for risk, ids in sorted(by_risk.items()):
        flag = "⚠ " if risk in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
        print(f"  {flag}{risk}: {len(ids)} — {', '.join(ids)}")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults written → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
