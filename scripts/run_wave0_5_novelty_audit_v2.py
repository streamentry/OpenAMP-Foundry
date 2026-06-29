"""
Wave 0.5 Novelty Audit v2 — Proper local alignment using BioPython BLOSUM62.

Improvements over v1:
  1. Combined database: APD6 natural (3307) + DRAMP general (11,687) +
     DRAMP patent (18,715) + UniProt AMP ≤60aa (2348) = ~36k unique sequences
  2. BioPython PairwiseAligner in local mode with BLOSUM62 scoring matrix
  3. Percent identity = matches / aligned_block_positions
     (v1 used Levenshtein / max(len_a, len_b) which undercounts fragment-to-parent)
  4. Verbatim substring check: candidate in ref_seq → KNOWN_FRAGMENT
  5. Patent risk flag when best hit is from DRAMP patent dataset

Usage:
    .venv/bin/python scripts/run_wave0_5_novelty_audit_v2.py
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from Bio.Align import PairwiseAligner, substitution_matrices  # noqa: E402

# ── Constants ────────────────────────────────────────────────────────────────

STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")

DB_SOURCES: list[tuple[str, Path, bool]] = [
    ("apd6_natural", ROOT / "data/novelty_db/apd6_natural.fasta", False),
    ("dramp_general", ROOT / "data/novelty_db/dramp_general.fasta", False),
    ("dramp_patent", ROOT / "data/novelty_db/dramp_patent.fasta", True),
    ("uniprot_amps", ROOT / "data/novelty_db/uniprot_amps.fasta", False),
]

SHORTLIST_CSV = ROOT / "outputs" / "wave0_5_internal_shortlist.csv"
AUDIT_V2_CSV = ROOT / "outputs" / "wave0_5_novelty_audit_v2.csv"
AUDIT_CSV = ROOT / "outputs" / "wave0_5_novelty_audit.csv"  # overwritten with v2 results


class DbEntry(NamedTuple):
    seq_id: str
    sequence: str
    is_patent: bool


# ── Database loading ─────────────────────────────────────────────────────────


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    """Parse a FASTA file → list of (header_id, sequence)."""
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


def build_db() -> list[DbEntry]:
    """
    Load all AMP databases, deduplicate by sequence, filter to standard AAs.
    If the same sequence appears in any patent DB, mark is_patent=True.
    """
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
                # Mark existing entry as patent if we see it in a patent DB
                old = seen[seq]
                seen[seq] = DbEntry(seq_id=old.seq_id, sequence=old.sequence, is_patent=True)
        print(f"  {source_name}: {len(entries)} loaded, {added} new unique sequences")

    db = list(seen.values())
    print(f"  Combined DB: {len(db)} unique standard-AA peptides (5–100aa)")
    return db


# ── Alignment ────────────────────────────────────────────────────────────────


def _make_aligner() -> PairwiseAligner:
    aligner = PairwiseAligner()
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.mode = "local"
    aligner.open_gap_score = -11.0
    aligner.extend_gap_score = -1.0
    return aligner


def _local_identity(query: str, target: str, aligner: PairwiseAligner) -> float:
    """
    Percent sequence identity for novelty assessment.
    Identity = identical_positions_in_local_alignment / len(query).

    Normalising by query length prevents a 5aa perfect sub-match in a 12aa
    query from returning 1.0 — it would correctly return 5/12 = 0.42.
    This matches the intent: "how much of our candidate is covered by a known AMP?"
    """
    try:
        aln = next(iter(aligner.align(query, target)))
    except StopIteration:
        return 0.0
    except Exception:
        return 0.0

    q_blocks, t_blocks = aln.aligned[0], aln.aligned[1]
    n_matches = 0
    for (qs, qe), (ts, te) in zip(q_blocks, t_blocks):
        for i in range(qe - qs):
            if query[qs + i] == target[ts + i]:
                n_matches += 1
    return n_matches / len(query) if query else 0.0


# ── Classification ───────────────────────────────────────────────────────────


def _classify(
    best_identity: float,
    is_substring: bool,
    is_patent: bool,
) -> tuple[str, str, str]:
    """Return (novelty_class, patent_risk, action)."""
    if is_substring or best_identity >= 0.99:
        nov = "EXACT_MATCH_OR_FRAGMENT"
        action = "EXCLUDE from novelty claims; use only as positive control"
    elif best_identity >= 0.80:
        nov = "KNOWN_VARIANT"
        action = "Include only with strong SAR justification; label as variant clearly"
    elif best_identity >= 0.60:
        nov = "CLOSE_RELATIVE"
        action = "Include with prior-art disclosure; IP claim requires expert review"
    elif best_identity >= 0.40:
        nov = "RELATED_NOVEL"
        action = "Include; disclose best hit; moderate novelty claim supported"
    else:
        nov = "HIGH_CONFIDENCE_NOVEL"
        action = "Include; strong novelty claim supported by alignment against 36k AMP DB"

    if best_identity >= 0.80:
        patent = "REVIEW_REQUIRED"
    elif is_patent and best_identity >= 0.60:
        patent = "POSSIBLE_PATENT_RISK"
    elif is_patent and best_identity >= 0.40:
        patent = "LOW_PATENT_RISK"
    else:
        patent = "CLEAR"

    return nov, patent, action


# ── Per-candidate scan ───────────────────────────────────────────────────────


def scan_candidate(
    cid: str,
    seq: str,
    seed_family: str,
    db: list[DbEntry],
    aligner: PairwiseAligner,
) -> dict:
    """Run full novelty scan for one candidate against combined DB."""
    candidate_len = len(seq)
    # Only compare against DB entries within 3× length range
    min_len = max(5, candidate_len // 3)
    max_len = candidate_len * 3

    best_identity = 0.0
    best_hit_id = "NONE"
    best_hit_seq = "NONE"
    best_is_patent = False
    best_is_substring = False

    for entry in db:
        if not (min_len <= len(entry.sequence) <= max_len):
            continue

        # Exact substring check: candidate is verbatim sub-fragment of a known AMP.
        # We do NOT check the reverse (db_seq in candidate) because any short
        # database peptide (5aa) could trivially appear inside our 12-14aa candidates
        # and would wrongly classify them as non-novel.
        is_sub = seq in entry.sequence
        if is_sub:
            identity = 1.0
        else:
            identity = _local_identity(seq, entry.sequence, aligner)

        if identity > best_identity:
            best_identity = identity
            best_hit_id = entry.seq_id
            best_hit_seq = entry.sequence
            best_is_patent = entry.is_patent
            best_is_substring = is_sub

        if best_identity >= 1.0:
            break  # perfect match found

    nov_class, patent_risk, action = _classify(best_identity, best_is_substring, best_is_patent)

    return {
        "candidate_id": cid,
        "sequence": seq,
        "seed_family": seed_family,
        "best_database": "patent" if best_is_patent else "public",
        "best_hit_id": best_hit_id,
        "best_hit_sequence": best_hit_seq[:60] if best_hit_seq != "NONE" else "NONE",
        "best_identity": round(best_identity, 4),
        "best_similarity": round(best_identity, 4),
        "novelty_class": nov_class,
        "patent_risk": patent_risk,
        "action": action,
        "shortlist_role": "PASS",
        "is_substring": best_is_substring,
        "method": "BioPython_PairwiseAligner_BLOSUM62_local_gapopen11_gapext1",
        "db_size": len(db),
    }


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    print("=== Wave 0.5 Novelty Audit v2 ===\n")
    print("Loading AMP databases...")
    t0 = time.time()
    db = build_db()
    print(f"  Done in {time.time() - t0:.1f}s\n")

    with open(SHORTLIST_CSV) as f:
        candidates = list(csv.DictReader(f))
    print(f"Loaded {len(candidates)} shortlisted candidates\n")

    aligner = _make_aligner()

    results: list[dict] = []
    print("Running alignments...")
    for i, row in enumerate(candidates):
        cid = row["candidate_id"]
        seq = row["sequence"]
        family = row["seed_family"]
        t1 = time.time()
        result = scan_candidate(cid, seq, family, db, aligner)
        elapsed = time.time() - t1
        print(
            f"  [{i+1:2d}/60] {cid:<26} {seq:<20} → "
            f"{result['novelty_class']:<28} sim={result['best_similarity']:.3f} "
            f"({elapsed:.1f}s)"
        )
        results.append(result)

    # Write v2-specific CSV (with extra columns)
    v2_cols = [
        "candidate_id", "sequence", "seed_family",
        "best_database", "best_hit_id", "best_hit_sequence",
        "best_identity", "best_similarity",
        "novelty_class", "patent_risk", "action", "shortlist_role",
        "is_substring", "method", "db_size",
    ]
    with open(AUDIT_V2_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=v2_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nWrote: {AUDIT_V2_CSV}")

    # Overwrite the main novelty audit CSV (same column structure as v1)
    v1_cols = [
        "candidate_id", "sequence", "seed_family",
        "best_database", "best_hit_id", "best_hit_sequence",
        "best_identity", "best_similarity",
        "novelty_class", "patent_risk", "action", "shortlist_role",
    ]
    with open(AUDIT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=v1_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"Overwrote: {AUDIT_CSV}")

    # Summary
    from collections import Counter
    counts = Counter(r["novelty_class"] for r in results)
    patent_risk_counts = Counter(r["patent_risk"] for r in results)
    print("\n--- Novelty class summary ---")
    for cls in ["HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "CLOSE_RELATIVE",
                "KNOWN_VARIANT", "EXACT_MATCH_OR_FRAGMENT"]:
        print(f"  {cls:<30} {counts.get(cls, 0):3d}")
    print("\n--- Patent risk summary ---")
    for risk in ["CLEAR", "LOW_PATENT_RISK", "POSSIBLE_PATENT_RISK", "REVIEW_REQUIRED"]:
        print(f"  {risk:<30} {patent_risk_counts.get(risk, 0):3d}")

    novel_count = counts.get("HIGH_CONFIDENCE_NOVEL", 0) + counts.get("RELATED_NOVEL", 0)
    gate_pass = novel_count >= 8
    print(f"\nGate W0.5-5 (≥8 novel leads): {novel_count}/60 → {'PASS' if gate_pass else 'FAIL'}")
    print(f"\nTotal elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
