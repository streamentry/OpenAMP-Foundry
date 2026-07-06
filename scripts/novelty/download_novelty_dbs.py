"""
Download / refresh all AMP novelty databases into data/novelty_db/.

Run annually or whenever DRAMP/APD6/UniProt release new versions.

Usage:
    .venv/bin/python3 scripts/download_novelty_dbs.py [--all] [--apd6] [--dramp] [--uniprot]

See docs/NOVELTY_AUDIT_GUIDE.md for full context.
"""

from __future__ import annotations

import argparse
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_DIR = ROOT / "data" / "novelty_db"
DB_DIR.mkdir(parents=True, exist_ok=True)

APD6_FILES = [
    ("apd6_natural.fasta",  "https://aps.unmc.edu/assets/sequences/naturalAMPs_APD2024a.fasta"),
    ("apd6_animal.fasta",   "https://aps.unmc.edu/assets/sequences/animalAMPs_APD2024a.fasta"),
    ("apd6_plant.fasta",    "https://aps.unmc.edu/assets/sequences/plantAMPs_APD2024.fasta"),
    ("apd6_bacteria.fasta", "https://aps.unmc.edu/assets/sequences/bacteriaAMPs_APD2024.fasta"),
]

_DRAMP_BASE = "https://dramp.cpu-bioinfor.org/downloads/download.php?filename=download_data/DRAMP3.0_new"
DRAMP_FILES = [
    ("dramp_general.fasta",  f"{_DRAMP_BASE}/general_amps.fasta"),
    ("dramp_patent.fasta",   f"{_DRAMP_BASE}/patent_amps.fasta"),
    ("dramp_specific.fasta", f"{_DRAMP_BASE}/specific_amps.fasta"),
]


def _download(url: str, dest: Path, label: str) -> None:
    print(f"  Downloading {label} ... ", end="", flush=True)
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "openamp-foundry/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        dest.write_bytes(data)
        count = data.count(b">")
        print(f"{count:,} sequences  ({time.time()-t0:.1f}s)")
    except Exception as e:
        print(f"FAILED — {e}")


def download_apd6() -> None:
    print("\n=== APD6 ===")
    for fname, url in APD6_FILES:
        _download(url, DB_DIR / fname, fname)


def download_dramp() -> None:
    print("\n=== DRAMP 3.0 ===")
    for fname, url in DRAMP_FILES:
        _download(url, DB_DIR / fname, fname)


def download_uniprot() -> None:
    print("\n=== UniProt (KW-0929 Antimicrobial) ===")
    _download_uniprot_paged(
        query="keyword:KW-0929 AND length:[1 TO 100] AND reviewed:true",
        dest=DB_DIR / "uniprot_amps_reviewed.fasta",
        label="uniprot_amps_reviewed.fasta (reviewed ≤100aa)",
    )
    _download_uniprot_paged(
        query="keyword:KW-0929 AND length:[1 TO 60] AND reviewed:false",
        dest=DB_DIR / "uniprot_amps_unreviewed.fasta",
        label="uniprot_amps_unreviewed.fasta (unreviewed ≤60aa)",
        max_pages=25,
    )


def _download_uniprot_paged(
    query: str, dest: Path, label: str, max_pages: int = 50
) -> None:
    print(f"  Downloading {label} ... ", flush=True)
    parts: list[str] = []
    cursor = None
    page = 0

    while page < max_pages:
        params: dict[str, str] = {"query": query, "format": "fasta", "size": "500"}
        if cursor:
            params["cursor"] = cursor
        url = "https://rest.uniprot.org/uniprotkb/search?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read().decode("utf-8")
                link = r.getheader("Link", "")
        except Exception as e:
            print(f"    Page {page+1} error: {e}")
            break
        parts.append(data)
        page += 1
        print(f"    Page {page}: {data.count('>')} sequences")

        if 'rel="next"' not in link:
            break
        import re
        m = re.search(r"cursor=([^&>]+)", link)
        if not m:
            break
        cursor = m.group(1)
        time.sleep(0.2)

    combined = "".join(parts)
    dest.write_text(combined, encoding="utf-8")
    print(f"  → {combined.count('>')} total sequences saved to {dest.name}")


def download_escape() -> None:
    """Download ESCAPE NeurIPS-2025 benchmark AMP sequences from Harvard Dataverse."""
    import io
    print("\n=== ESCAPE (Harvard Dataverse DOI:10.7910/DVN/C69MCD) ===")
    STANDARD_AA = frozenset("ACDEFGHIKLMNPQRSTVWY")
    FILE_IDS = [11466751, 11466752, 11467604]  # Test, Fold1, Fold2

    all_seqs: set[str] = set()
    for fid in FILE_IDS:
        url = f"https://dataverse.harvard.edu/api/access/datafile/{fid}"
        req = urllib.request.Request(url, headers={"User-Agent": "openamp-foundry/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read().decode("utf-8")
        lines = data.strip().split("\n")
        header = lines[0].split("\t")
        seq_col = header.index("Sequence")
        amp_col = header.index("Antimicrobial") if "Antimicrobial" in header else None
        added = 0
        for line in lines[1:]:
            parts = line.split("\t")
            seq = parts[seq_col].strip('"').upper()
            is_amp = parts[amp_col].strip('"') == "1" if amp_col is not None else True
            if is_amp and all(c in STANDARD_AA for c in seq) and 5 <= len(seq) <= 100:
                if seq not in all_seqs:
                    all_seqs.add(seq)
                    added += 1
        print(f"  Datafile {fid}: {added} new unique clean AMPs")

    dest = DB_DIR / "escape_amps.fasta"
    with open(dest, "w") as f:
        for i, seq in enumerate(sorted(all_seqs), 1):
            f.write(f">ESCAPE_{i:06d}\n{seq}\n")
    print(f"  → {len(all_seqs)} total unique AMPs saved to {dest.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download AMP novelty databases")
    parser.add_argument("--all",     action="store_true", help="Download all databases")
    parser.add_argument("--apd6",    action="store_true", help="Download APD6 datasets")
    parser.add_argument("--dramp",   action="store_true", help="Download DRAMP 3.0 datasets")
    parser.add_argument("--uniprot", action="store_true", help="Download UniProt AMP datasets")
    parser.add_argument("--escape",  action="store_true", help="Download ESCAPE NeurIPS-2025 dataset")
    args = parser.parse_args()

    if not any([args.all, args.apd6, args.dramp, args.uniprot, args.escape]):
        args.all = True

    print(f"Saving to: {DB_DIR}/\n")
    if args.all or args.apd6:
        download_apd6()
    if args.all or args.dramp:
        download_dramp()
    if args.all or args.uniprot:
        download_uniprot()
    if args.all or args.escape:
        download_escape()

    print("\n=== DB Summary ===")
    total = 0
    for f in sorted(DB_DIR.glob("*.fasta")):
        count = f.read_text().count(">")
        total += count
        print(f"  {f.name:<40} {count:>6,} sequences")
    print(f"\n  Total (with overlaps): {total:,}")
    print("\nNext: run_expanded_novelty_audit.py to check your candidates.")


if __name__ == "__main__":
    main()
