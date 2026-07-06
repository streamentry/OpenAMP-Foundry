"""Curate an expanded AMP benchmark set (500+ AMPs + 500+ decoys).

Sources:
  - examples/validation/known_amps.csv       (95 existing curated AMPs)
  - data/novelty_db/uniprot_amps_reviewed.fasta (CC BY 4.0)
  - data/novelty_db/apd6_natural.fasta          (academic use with citation)

Output:
  examples/validation/known_amps_500.csv
  examples/validation/random_background_500.csv

Usage: python scripts/curate_500_amp_benchmark.py
"""

import csv
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_DIR = REPO_ROOT / "examples" / "validation"

EXISTING_AMPS_CSV = VALIDATION_DIR / "known_amps.csv"
UNIPROT_FASTA = REPO_ROOT / "data" / "novelty_db" / "uniprot_amps_reviewed.fasta"
APD6_FASTA = REPO_ROOT / "data" / "novelty_db" / "apd6_natural.fasta"
KNOWN_AMPS_500_PATH = VALIDATION_DIR / "known_amps_500.csv"
BACKGROUND_500_PATH = VALIDATION_DIR / "random_background_500.csv"

AMP_CHARS = set("ACDEFGHIKLMNPQRSTVWY")
TARGET_AMP_COUNT = 500
RNG_SEED = 20260705

# Swiss-Prot background frequencies
UNIPROT_FREQ = {
    "A": 0.0826, "R": 0.0553, "N": 0.0406, "D": 0.0546, "C": 0.0138,
    "Q": 0.0393, "E": 0.0675, "G": 0.0708, "H": 0.0227, "I": 0.0594,
    "L": 0.0965, "K": 0.0581, "M": 0.0242, "F": 0.0386, "P": 0.0474,
    "S": 0.0656, "T": 0.0534, "W": 0.0109, "Y": 0.0292, "V": 0.0687,
}
AA_TYPES = list(UNIPROT_FREQ.keys())
AA_WEIGHTS = [UNIPROT_FREQ[a] for a in AA_TYPES]


def parse_fasta(path: Path) -> list[dict]:
    """Parse a FASTA file into (id, sequence) dicts.

    Extracts the first token of the header (after '>') as the identifier.
    """
    records = []
    with open(path) as f:
        header = None
        seq_parts = []
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if header is not None and seq_parts:
                    seq = "".join(seq_parts).upper()
                    records.append({"id": header, "sequence": seq})
                header = line[1:].split()[0]
                seq_parts = []
            elif line:
                seq_parts.append(line)
        if header is not None and seq_parts:
            seq = "".join(seq_parts).upper()
            records.append({"id": header, "sequence": seq})
    return records


def is_valid_amp(seq: str) -> bool:
    """Check if a sequence is a valid short AMP: 10-30 AA, standard residues only."""
    return 10 <= len(seq) <= 30 and all(c in AMP_CHARS for c in seq)


def load_existing_amps(path: Path) -> list[dict]:
    """Load AMPs from known_amps.csv."""
    amps = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row["sequence"].strip().upper()
            if is_valid_amp(seq):
                amps.append({
                    "id": row["id"],
                    "sequence": seq,
                    "family": row.get("family", ""),
                    "source": f"existing_benchmark:{row.get('reference', '')}",
                })
    return amps


def filter_amps(records: list[dict], source_label: str) -> list[dict]:
    """Filter FASTA records to valid short AMPs and assign source label."""
    result = []
    seen_seqs = set()
    for rec in records:
        seq = rec["sequence"].upper()
        if not is_valid_amp(seq):
            continue
        if seq in seen_seqs:
            continue
        seen_seqs.add(seq)
        short_id = rec["id"].replace("/", "_").replace("|", "_")
        result.append({
            "id": f"EXT-{short_id}",
            "sequence": seq,
            "family": source_label,
            "source": source_label,
        })
    return result


def generate_decoys(
    amps: list[dict], rng: random.Random
) -> list[dict]:
    """Generate length-matched Swiss-Prot frequency decoys for each AMP.

    For each AMP, generate one decoy of the same length using Swiss-Prot
    amino acid frequencies. This matches the method in expand_benchmark.py.
    """
    decoys = []
    for i, amp in enumerate(amps):
        seq_len = len(amp["sequence"])
        decoy_seq = "".join(rng.choices(AA_TYPES, weights=AA_WEIGHTS, k=seq_len))
        decoys.append({
            "id": f"BG-500-{i + 1:04d}",
            "sequence": decoy_seq,
            "family": "background",
            "source": f"uniprot_freq_rng{RNG_SEED}_500",
            "label": "0",
        })
    return decoys


def main():
    rng = random.Random(RNG_SEED)

    # ── Load existing AMPs ──
    existing = load_existing_amps(EXISTING_AMPS_CSV)
    print(f"Existing AMPs loaded: {len(existing)}")

    # ── Load UniProt-reviewed AMPs ──
    uniprot_records = parse_fasta(UNIPROT_FASTA) if UNIPROT_FASTA.exists() else []
    uniprot_amps = filter_amps(uniprot_records, "uniprot_reviewed")
    print(f"UniProt-reviewed AMPs (10-30 AA, standard): {len(uniprot_amps)}")

    # ── Load APD6 natural AMPs ──
    apd6_records = parse_fasta(APD6_FASTA) if APD6_FASTA.exists() else []
    apd6_amps = filter_amps(apd6_records, "apd6_natural")
    print(f"APD6 natural AMPs (10-30 AA, standard): {len(apd6_amps)}")

    # ── Combine and deduplicate ──
    seen_seqs: set[str] = set()
    all_amps: list[dict] = []

    def add_amps(amps: list[dict], label: str):
        count = 0
        for a in amps:
            if a["sequence"] not in seen_seqs:
                seen_seqs.add(a["sequence"])
                all_amps.append(a)
                count += 1
        print(f"  Added {count} new from {label}")

    add_amps(existing, "existing_benchmark")
    add_amps(uniprot_amps, "uniprot_reviewed")
    add_amps(apd6_amps, "apd6_natural")

    print(f"\nTotal unique AMPs after dedup: {len(all_amps)}")

    # ── Sample if over target ──
    if len(all_amps) > TARGET_AMP_COUNT:
        rng.shuffle(all_amps)
        # Keep existing AMPs at the front
        existing_count = len(existing)
        keep_existing = all_amps[:existing_count]
        sample_rest = all_amps[existing_count:]
        rng.shuffle(sample_rest)
        needed = TARGET_AMP_COUNT - existing_count
        all_amps = keep_existing + sample_rest[:max(0, needed)]
        print(f"Sampled to {len(all_amps)} AMPs (kept all {existing_count} existing)")

    # ── Write expanded AMP CSV ──
    with open(KNOWN_AMPS_500_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "sequence", "family", "source", "label"])
        for i, amp in enumerate(all_amps):
            writer.writerow([
                amp["id"],
                amp["sequence"],
                amp.get("family", ""),
                amp.get("source", ""),
                "1",
            ])
    print(f"\nWrote {len(all_amps)} AMPs to {KNOWN_AMPS_500_PATH}")

    # ── Generate decoys ──
    decoys = generate_decoys(all_amps, rng)
    with open(BACKGROUND_500_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "sequence", "family", "source", "label"])
        for dec in decoys:
            writer.writerow([
                dec["id"],
                dec["sequence"],
                dec["family"],
                dec["source"],
                dec["label"],
            ])
    print(f"Wrote {len(decoys)} decoys to {BACKGROUND_500_PATH}")

    total_n = len(all_amps) + len(decoys)
    print(f"\nTotal benchmark size: {len(all_amps)} AMPs + {len(decoys)} decoys = {total_n}")

    # ── Source breakdown ──
    from collections import Counter
    source_counts = Counter(a["source"].split(":")[0] for a in all_amps)
    print("\nSource breakdown:")
    for src, cnt in source_counts.most_common():
        print(f"  {src}: {cnt}")

    print("\nDone. Next: run full benchmark validation on the expanded set.")


if __name__ == "__main__":
    main()
