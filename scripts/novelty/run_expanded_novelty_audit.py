"""
Expanded BLOSUM62 novelty audit against a multi-source AMP database.

Database sources (see data/novelty_db/ and NOVELTY_AUDIT_GUIDE.md):
  APD6 natural  (3,307)    — high-quality canonical AMPs
  APD6 animal   (2,581)    — non-natural-subset animal AMPs
  APD6 plant    (269)      — plant defensins & thionins
  APD6 bacteria (411)      — bacteriocins & lantibiotics
  APD6 human    (155)      — human host-defense peptides (cathelicidins, defensins)
  DRAMP general (11,687)   — broad AMP collection, public
  DRAMP patent  (18,715)   — patent-protected AMPs   ← IP-risk detection
  DRAMP specific (6,321)   — clinical/stability/structural DRAMP entries
  UniProt reviewed (2,673) — Swiss-Prot reviewed AMPs ≤100aa
  UniProt unreviewed (1,692) — TrEMBL unreviewed AMPs ≤60aa
  UniProt combined (2,348) — separate UniProt KW-0929 download (partial overlap)
  ESCAPE NeurIPS-2025 (3,542) — 21k exp. validated AMPs from 27 repos
  dbAMP 3.0 (35,599)       — largest dedicated AMP database
  DBAASP (1,988)           — Database of Antimicrobial Activity and Structure of Peptides

Combined before dedup: ~91,088 sequences
After dedup, clean standard-AA 5-100aa: ~53,000 (exact count printed at runtime)

Novelty thresholds (identity = matches / query_length, BLOSUM62 local):
  ≥99%  EXACT_MATCH_OR_FRAGMENT
  ≥80%  KNOWN_VARIANT
  ≥60%  CLOSE_RELATIVE
  ≥40%  RELATED_NOVEL
  <40%  HIGH_CONFIDENCE_NOVEL

Patent risk:
  POSSIBLE_PATENT_RISK  if best hit in dramp_patent AND identity ≥60%
  LOW_PATENT_RISK       if best hit in dramp_patent AND identity ≥40%
  CLEAR                 otherwise (including <40% patent hits)

Usage:
    python scripts/run_expanded_novelty_audit.py --input path/to/candidates.csv
    python scripts/run_expanded_novelty_audit.py --fasta path/to/candidates.fasta

Input CSV must have columns: candidate_id, sequence
Output: outputs/expanded_novelty_audit_<timestamp>.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from Bio.Align import PairwiseAligner, substitution_matrices

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

# All DB sources with patent flag
DB_SOURCES: list[tuple[str, Path, bool]] = [
    # APD6 subsets — all public
    ("apd6_natural",   ROOT / "data/novelty_db/apd6_natural.fasta",   False),
    ("apd6_animal",    ROOT / "data/novelty_db/apd6_animal.fasta",    False),
    ("apd6_plant",     ROOT / "data/novelty_db/apd6_plant.fasta",     False),
    ("apd6_bacteria",  ROOT / "data/novelty_db/apd6_bacteria.fasta",  False),
    # DRAMP
    ("dramp_general",  ROOT / "data/novelty_db/dramp_general.fasta",  False),
    ("dramp_patent",   ROOT / "data/novelty_db/dramp_patent.fasta",   True),   # ← IP risk
    ("dramp_specific", ROOT / "data/novelty_db/dramp_specific.fasta", False),
    # UniProt
    ("uniprot_reviewed",   ROOT / "data/novelty_db/uniprot_amps_reviewed.fasta",   False),
    ("uniprot_unreviewed", ROOT / "data/novelty_db/uniprot_amps_unreviewed.fasta", False),
    # APD6 human — human host-defense peptides (cathelicidins, defensins, histatins)
    ("apd6_human",         ROOT / "data/novelty_db/apd6_human.fasta",              False),
    # ESCAPE benchmark (NeurIPS 2025) — 21k experimentally validated AMPs from 27 repositories
    ("escape_amps",        ROOT / "data/novelty_db/escape_amps.fasta",             False),
    # dbAMP 3.0 — 35,599 AMPs, largest dedicated AMP database
    ("dbamp3",             ROOT / "data/novelty_db/dbAMP3.fasta",                  False),
    # DBAASP — Database of Antimicrobial Activity and Structure of Peptides
    ("dbaasp",             ROOT / "data/novelty_db/dbaasp-peptides.fasta",         False),
    # UniProt combined — separate KW-0929 pull (partial overlap with reviewed/unreviewed above)
    ("uniprot_combined",   ROOT / "data/novelty_db/uniprot_amps.fasta",            False),
]


class DbEntry:
    __slots__ = ("seq_id", "sequence", "is_patent")

    def __init__(self, seq_id: str, sequence: str, is_patent: bool) -> None:
        self.seq_id = seq_id
        self.sequence = sequence
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


def build_db(verbose: bool = True) -> list[DbEntry]:
    seen: dict[str, DbEntry] = {}
    total_raw = 0
    for source_name, path, is_patent in DB_SOURCES:
        if not path.exists():
            if verbose:
                print(f"  [WARN] {path.name} not found — skipping")
            continue
        entries = _load_fasta(path)
        added = 0
        for header, seq in entries:
            total_raw += 1
            if not seq or not all(c in STANDARD_AA for c in seq) or not (5 <= len(seq) <= 100):
                continue
            seq_id = f"{source_name}:{header}"
            if seq not in seen:
                seen[seq] = DbEntry(seq_id=seq_id, sequence=seq, is_patent=is_patent)
                added += 1
            elif is_patent and not seen[seq].is_patent:
                old = seen[seq]
                seen[seq] = DbEntry(seq_id=old.seq_id, sequence=old.sequence, is_patent=True)
        if verbose:
            print(f"  {source_name}: {len(entries)} entries → {added} new unique clean sequences")
    db = list(seen.values())
    if verbose:
        patent_count = sum(1 for e in db if e.is_patent)
        print(f"\n  Combined DB: {len(db)} unique clean standard-AA sequences (5–100aa)")
        print(f"  Patent-flagged: {patent_count}")
    return db


def _make_aligner() -> PairwiseAligner:
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.mode = "local"
    a.open_gap_score = -11.0
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


def scan(
    cid: str,
    seq: str,
    db: list[DbEntry],
    aligner: PairwiseAligner,
) -> dict:
    clen = len(seq)
    min_l, max_l = max(5, clen // 3), clen * 3
    best_id, best_hit_id, best_hit_seq, best_pat, best_sub = 0.0, "NONE", "NONE", False, False

    for e in db:
        if not (min_l <= len(e.sequence) <= max_l):
            continue
        is_sub = seq in e.sequence
        identity = 1.0 if is_sub else _local_identity(seq, e.sequence, aligner)
        if identity > best_id:
            best_id, best_hit_id, best_hit_seq = identity, e.seq_id, e.sequence
            best_pat, best_sub = e.is_patent, is_sub

    nov, pat = _classify(best_id, best_sub, best_pat)
    return {
        "candidate_id": cid,
        "sequence": seq,
        "best_identity": round(best_id, 4),
        "best_hit_id": best_hit_id,
        "best_hit_seq": best_hit_seq[:80] if best_hit_seq != "NONE" else "NONE",
        "best_database": "patent" if best_pat else "public",
        "is_substring": best_sub,
        "novelty_class": nov,
        "patent_risk": pat,
    }


def _classify(best_id: float, is_sub: bool, is_patent: bool) -> tuple[str, str]:
    if is_sub or best_id >= 0.99:
        return "EXACT_MATCH_OR_FRAGMENT", "REVIEW_REQUIRED"
    elif best_id >= 0.80:
        return "KNOWN_VARIANT", "REVIEW_REQUIRED"
    elif best_id >= 0.60:
        return "CLOSE_RELATIVE", "POSSIBLE_PATENT_RISK" if is_patent else "CLEAR"
    elif best_id >= 0.40:
        return "RELATED_NOVEL", "LOW_PATENT_RISK" if is_patent else "CLEAR"
    else:
        return "HIGH_CONFIDENCE_NOVEL", "CLEAR"


FIELDNAMES = [
    "candidate_id", "sequence",
    "best_identity", "best_hit_id", "best_hit_seq", "best_database",
    "is_substring", "novelty_class", "patent_risk",
]


def _load_candidates(args: argparse.Namespace) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    if args.input:
        with open(args.input) as f:
            for row in csv.DictReader(f):
                candidates.append((row["candidate_id"], row["sequence"].strip().upper()))
    elif args.fasta:
        header, seq = "", ""
        with open(args.fasta) as f:
            for line in f:
                line = line.rstrip()
                if line.startswith(">"):
                    if header and seq:
                        candidates.append((header.split()[0], seq))
                    header = line[1:]
                    seq = ""
                else:
                    seq += line.upper()
        if header and seq:
            candidates.append((header.split()[0], seq))
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Expanded AMP novelty audit")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--input", help="CSV with candidate_id,sequence columns")
    grp.add_argument("--fasta", help="FASTA input file")
    parser.add_argument("--out", help="Output CSV path (default: auto-named in outputs/)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-candidate output")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else ROOT / "outputs" / f"expanded_novelty_audit_{ts}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=== OpenAMP Expanded Novelty Audit ===")
    print(f"DB version: APD6 + DRAMP 3.0 + UniProt + ESCAPE NeurIPS-2025 + dbAMP 3.0 + DBAASP\n")
    print("Loading databases...")
    t0 = time.time()
    db = build_db(verbose=not args.quiet)
    print(f"  Loaded in {time.time()-t0:.1f}s\n")

    aligner = _make_aligner()
    candidates = _load_candidates(args)
    print(f"Scanning {len(candidates)} candidate(s)...\n")

    if not args.quiet:
        print(f"{'#':>4}  {'ID':<20} {'Sequence':<22} {'Class':<28} {'Identity':>8}  {'IP':<24}  BestHit")
        print("─" * 130)

    results: list[dict] = []
    for i, (cid, seq) in enumerate(candidates, 1):
        t1 = time.time()
        r = scan(cid, seq, db, aligner)
        results.append(r)
        if not args.quiet:
            flag = "⚠ " if r["patent_risk"] in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
            print(
                f"{i:>4}  {cid:<20} {seq:<22} {flag}{r['novelty_class']:<26} "
                f"{r['best_identity']:>7.1%}  {r['patent_risk']:<24}  "
                f"{r['best_hit_id']}  ({time.time()-t1:.1f}s)"
            )

    print("\n" + "─" * 130)
    print("\n=== SUMMARY ===\n")
    from collections import Counter
    for cls, cnt in Counter(r["novelty_class"] for r in results).most_common():
        members = [r["candidate_id"] for r in results if r["novelty_class"] == cls]
        print(f"  {cls}: {cnt}  →  {', '.join(members[:5])}{'...' if len(members) > 5 else ''}")
    print()
    for risk, cnt in Counter(r["patent_risk"] for r in results).most_common():
        flag = "⚠ " if risk in ("POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED") else "✓ "
        members = [r["candidate_id"] for r in results if r["patent_risk"] == risk]
        print(f"  {flag}{risk}: {cnt}  →  {', '.join(members[:5])}{'...' if len(members) > 5 else ''}")

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(results)
    print(f"\nResults → {out_path}")


if __name__ == "__main__":
    main()
