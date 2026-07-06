"""
Full BLOSUM62 novelty audit for all 20 pilot panel candidates (Wave 0 + Wave 0.5 controls).

This is the definitive check: have SEED-006/007/008/009 candidates — which carry
HIGH_CONFIDENCE_NOVEL labels from the old v1 audit — actually survived the full
27,234-sequence (APD6 + DRAMP general + DRAMP patent + UniProt) BLOSUM62 audit?

Output: outputs/wave0_pilot_novelty_audit.csv
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

OUTPUT_CSV = ROOT / "outputs" / "wave0_pilot_novelty_audit.csv"

PILOT_CANDIDATES = [
    ("SEED-009_VAR_033", "RRLPRPGYMPRP",    "SEED-009"),
    ("SEED-009_VAR_027", "RRLPRGPYLPKP",    "SEED-009"),
    ("SEED-007_VAR_009", "IKFTTMLRKLG",     "SEED-007"),
    ("SEED-007_VAR_001", "AKITTMLKKLG",     "SEED-007"),
    ("SEED-007_VAR_018", "IKISTMLKKAG",     "SEED-007"),
    ("SEED-009_VAR_039", "RRLPRPPYIPRG",    "SEED-009"),
    ("SEED-009_VAR_017", "RRLGRPPYLGRP",    "SEED-009"),
    ("SEED-007_VAR_035", "IKITTMAKKVG",     "SEED-007"),
    ("SEED-006_VAR_059", "INWKPIAAMAKKLV",  "SEED-006"),
    ("SEED-006_VAR_071", "IQWKGIAAMAKRLL",  "SEED-006"),
    ("SEED-006_VAR_062", "INWRGIAAMAKKFL",  "SEED-006"),
    ("SEED-006_VAR_006", "INFKGIALMAKKLL",  "SEED-006"),
    ("SEED-008_VAR_032", "FPVTWRFWRWWKG",   "SEED-008"),
    ("SEED-008_VAR_009", "FPITWRWFKWWKG",   "SEED-008"),
    ("SEED-008_VAR_019", "FPVSWRWWKFWKG",   "SEED-008"),
    ("SEED-003_VAR_017", "RRWNWRMKKMG",     "SEED-003"),
    ("SEED-003_VAR_012", "RKWQYRMKKLG",     "SEED-003"),
    ("SEED-008_VAR_044", "FPVTWRWWKWYRG",   "SEED-008"),
    ("SEED-005_VAR_019", "KRLFKKAGSALKFL",  "SEED-005"),
    ("SEED-001_VAR_064", "KWKLFRKIGAVLRVL", "SEED-001"),
]


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    header, seq_parts = "", []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if header and seq_parts:
                    results.append((header, "".join(seq_parts).upper()))
                header = line[1:].split()[0] if len(line) > 1 else "UNKNOWN"
                seq_parts = []
            else:
                seq_parts.append(line)
    if header and seq_parts:
        results.append((header, "".join(seq_parts).upper()))
    return results


class DbEntry:
    __slots__ = ("seq_id", "sequence", "is_patent")
    def __init__(self, seq_id: str, sequence: str, is_patent: bool) -> None:
        self.seq_id, self.sequence, self.is_patent = seq_id, sequence, is_patent


def build_db() -> list[DbEntry]:
    seen: dict[str, DbEntry] = {}
    for source_name, path, is_patent in DB_SOURCES:
        if not path.exists():
            print(f"  [WARN] {path.name} not found — skipping")
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
        print(f"  {source_name}: {len(entries)} loaded, {added} new unique sequences")
    db = list(seen.values())
    print(f"  Combined DB: {len(db)} unique standard-AA peptides (5–100aa)")
    return db


def _make_aligner() -> PairwiseAligner:
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score   = -11.0
    a.extend_gap_score = -1.0
    return a


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


def _classify(best_id: float, is_sub: bool, is_patent: bool) -> tuple[str, str]:
    if is_sub or best_id >= 0.99:
        return "EXACT_MATCH_OR_FRAGMENT", "REVIEW_REQUIRED"
    elif best_id >= 0.80:
        return "KNOWN_VARIANT", "REVIEW_REQUIRED"
    elif best_id >= 0.60:
        return ("CLOSE_RELATIVE",
                "POSSIBLE_PATENT_RISK" if is_patent else "CLEAR")
    elif best_id >= 0.40:
        return ("RELATED_NOVEL",
                "LOW_PATENT_RISK" if is_patent else "CLEAR")
    else:
        return "HIGH_CONFIDENCE_NOVEL", "CLEAR"


def scan(cid: str, seq: str, seed: str, db: list[DbEntry], aligner: PairwiseAligner) -> dict:
    clen = len(seq)
    min_l, max_l = max(5, clen // 3), clen * 3
    best_id, best_hit_id, best_hit_seq, best_pat, best_sub = 0.0, "NONE", "NONE", False, False
    for e in db:
        if not (min_l <= len(e.sequence) <= max_l):
            continue
        is_sub   = seq in e.sequence
        identity = 1.0 if is_sub else _local_identity(seq, e.sequence, aligner)
        if identity > best_id:
            best_id, best_hit_id, best_hit_seq, best_pat, best_sub = (
                identity, e.seq_id, e.sequence, e.is_patent, is_sub)
        if best_id >= 1.0:
            break
    nov, pat = _classify(best_id, best_sub, best_pat)
    return {
        "candidate_id": cid, "sequence": seq, "seed_family": seed,
        "best_database": "patent" if best_pat else "public",
        "best_hit_id": best_hit_id,
        "best_hit_seq": best_hit_seq[:80] if best_hit_seq != "NONE" else "NONE",
        "best_identity": round(best_id, 4),
        "novelty_class": nov, "patent_risk": pat,
        "is_substring": best_sub,
    }


FIELDS = ["candidate_id","sequence","seed_family","best_database","best_hit_id",
          "best_hit_seq","best_identity","novelty_class","patent_risk","is_substring"]


def main() -> None:
    print("=== Wave 0 Pilot Panel — Full BLOSUM62 Novelty Audit (27,234-seq DB) ===\n")
    print("Loading databases...")
    t0 = time.time()
    db = build_db()
    print(f"  Done in {time.time()-t0:.1f}s\n")

    aligner = _make_aligner()
    results = []

    print(f"{'#':>3}  {'Candidate':<22} {'Sequence':<16} {'Result':<26} {'Identity':>8}  {'IP':<24}  BestHit")
    print("─" * 130)

    for i, (cid, seq, seed) in enumerate(PILOT_CANDIDATES, 1):
        t1 = time.time()
        r  = scan(cid, seq, seed, db, aligner)
        flag = "⚠ " if r["patent_risk"] in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
        print(f"{i:>3}  {cid:<22} {seq:<16} {flag}{r['novelty_class']:<24} "
              f"{r['best_identity']:>7.1%}  {r['patent_risk']:<24}  {r['best_hit_id']}  ({time.time()-t1:.1f}s)")
        results.append(r)

    print("\n" + "─" * 130)
    print("\n=== SUMMARY ===\n")
    from collections import Counter
    for cls, cnt in Counter(r["novelty_class"] for r in results).most_common():
        members = [r["candidate_id"] for r in results if r["novelty_class"] == cls]
        print(f"  {cls}: {cnt}  →  {', '.join(members)}")
    print()
    for risk, cnt in Counter(r["patent_risk"] for r in results).most_common():
        flag = "⚠ " if risk in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
        members = [r["candidate_id"] for r in results if r["patent_risk"] == risk]
        print(f"  {flag}{risk}: {cnt}  →  {', '.join(members)}")

    with open(OUTPUT_CSV, "w", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        for r in results:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(r)
    print(f"\nSaved → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
