"""
Patent + global novelty search for AMP candidates using BLASTp.

Two search layers:
  1. LOCAL pataa — NCBI patent protein sequences (3.96M seqs, GenBank Patent division)
     Requires: /tmp/blastdb/pataa extracted from pataa.tar.gz
     Download: ftp://ftp.ncbi.nlm.nih.gov/blast/db/pataa.tar.gz  (~839 MB compressed)
     Install:  cd /tmp/blastdb && tar xzf pataa.tar.gz

  2. REMOTE nr  — NCBI non-redundant protein (1.1B seqs, web API — too large to download)
     Uses NCBI BLAST API (free, rate-limited): qblast service

Usage:
    .venv/bin/python3 scripts/run_patent_blastp.py --fasta outputs/denovo_top12_final.fasta
    .venv/bin/python3 scripts/run_patent_blastp.py --fasta outputs/denovo_top12_final.fasta --pataa-only
    .venv/bin/python3 scripts/run_patent_blastp.py --fasta outputs/denovo_top12_final.fasta --nr-only

Output:
    outputs/patent_blastp_<timestamp>/
        pataa_results.txt    — local pataa BLASTp output (tabular)
        nr_results.txt       — remote NCBI BLASTp output (tabular)
        summary.csv          — merged hits ≥40% identity per candidate
        lens_queries.txt     — Lens.org search strings for manual patent check
        ip_clearance_report.md — human-readable IP clearance report

Interpretation:
    ≥90% identity to patent seq  → HIGH PATENT RISK — consult IP counsel
    ≥60% identity to patent seq  → MODERATE RISK — IP review recommended
    40–60% identity to patent seq → LOW RISK — note in prior art section
    <40% identity anywhere       → CLEAR for filing
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PATAA_DB_PATH = Path("/tmp/blastdb/pataa")  # path prefix (BLAST adds .phr/.pin/.psq)
NCBI_BLAST_URL = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"
BLAST_EVALUE = "10"
BLAST_MATRIX = "BLOSUM62"
BLAST_WORD_SIZE = "2"       # short sequence optimisation
BLAST_GAPOPEN = "11"
BLAST_GAPEXTEND = "1"
BLAST_MAX_HITS = "50"


def _load_fasta(path: Path) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    header, seq = "", ""
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if header and seq:
                    candidates.append((header.split()[0].lstrip(">"), seq))
                header = line[1:]
                seq = ""
            else:
                seq += line.upper()
    if header and seq:
        candidates.append((header.split()[0].lstrip(">"), seq))
    return candidates


def run_local_pataa(
    candidates: list[tuple[str, str]],
    out_dir: Path,
    db_path: Path = PATAA_DB_PATH,
) -> Path | None:
    """Run BLASTp against local pataa database."""
    # Check DB exists
    if not db_path.with_suffix(".phr").exists() and not Path(str(db_path) + ".phr").exists():
        # Try .00.phr (split DB)
        if not Path(str(db_path) + ".00.phr").exists():
            print(f"  [SKIP] pataa DB not found at {db_path}")
            print(f"  Download: ftp://ftp.ncbi.nlm.nih.gov/blast/db/pataa.tar.gz")
            print(f"  Extract:  cd /tmp/blastdb && tar xzf pataa.tar.gz")
            return None

    # Write query FASTA
    query_fasta = out_dir / "query.fasta"
    with open(query_fasta, "w") as f:
        for cid, seq in candidates:
            f.write(f">{cid}\n{seq}\n")

    out_file = out_dir / "pataa_results.txt"
    cmd = [
        "blastp",
        "-db", str(db_path),
        "-query", str(query_fasta),
        "-out", str(out_file),
        "-outfmt", "6 qseqid sseqid pident length qlen slen evalue bitscore stitle",
        "-evalue", BLAST_EVALUE,
        "-matrix", BLAST_MATRIX,
        "-word_size", BLAST_WORD_SIZE,
        "-gapopen", BLAST_GAPOPEN,
        "-gapextend", BLAST_GAPEXTEND,
        "-max_target_seqs", BLAST_MAX_HITS,
        "-num_threads", str(os.cpu_count() or 4),
    ]
    print(f"  Running local BLASTp vs pataa ({len(candidates)} queries)...")
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  BLASTp error: {result.stderr[:500]}")
        return None
    print(f"  Done in {time.time()-t0:.1f}s → {out_file}")
    return out_file


def _submit_ncbi_blast(fasta_str: str, database: str = "nr") -> str | None:
    """Submit a BLAST job to NCBI web API. Returns RID (request ID)."""
    params = {
        "CMD": "Put",
        "PROGRAM": "blastp",
        "DATABASE": database,
        "QUERY": fasta_str,
        "EXPECT": BLAST_EVALUE,
        "MATRIX_NAME": BLAST_MATRIX,
        "WORD_SIZE": BLAST_WORD_SIZE,
        "GAPCOSTS": f"{BLAST_GAPOPEN} {BLAST_GAPEXTEND}",
        "MAX_NUM_SEQ": BLAST_MAX_HITS,
        "FORMAT_TYPE": "Tabular",
        "SHORT_QUERY_ADJUST": "true",
        "FILTER": "L",      # low complexity filter
        "HITLIST_SIZE": BLAST_MAX_HITS,
        "FORMAT_OBJECT": "Alignment",
    }
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(NCBI_BLAST_URL, data=data,
                                  headers={"User-Agent": "openamp-foundry/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        response = r.read().decode("utf-8")
    # Extract RID
    for line in response.splitlines():
        if "RID = " in line:
            return line.split("RID = ")[1].strip()
    return None


def _fetch_ncbi_blast(rid: str, max_wait: int = 300) -> str | None:
    """Poll NCBI BLAST until results are ready, then fetch tabular output."""
    print(f"    RID={rid}  polling...", end="", flush=True)
    for _ in range(max_wait // 10):
        time.sleep(10)
        params = urllib.parse.urlencode({
            "CMD": "Get", "RID": rid, "FORMAT_TYPE": "Text",
            "FORMAT_OBJECT": "SearchInfo",
        })
        req = urllib.request.Request(f"{NCBI_BLAST_URL}?{params}",
                                      headers={"User-Agent": "openamp-foundry/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.read().decode("utf-8")
        if "Status=READY" in status:
            break
        if "Status=FAILED" in status:
            print(" FAILED")
            return None
        print(".", end="", flush=True)
    else:
        print(" TIMEOUT")
        return None

    # Fetch tabular results
    params = urllib.parse.urlencode({
        "CMD": "Get", "RID": rid,
        "FORMAT_TYPE": "Tabular",
        "FORMAT_OBJECT": "Alignment",
        "NCBI_GI": "false",
        "DESCRIPTIONS": BLAST_MAX_HITS,
        "ALIGNMENTS": BLAST_MAX_HITS,
    })
    req = urllib.request.Request(f"{NCBI_BLAST_URL}?{params}",
                                  headers={"User-Agent": "openamp-foundry/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        result = r.read().decode("utf-8")
    print(" READY")
    return result


def run_remote_nr(candidates: list[tuple[str, str]], out_dir: Path) -> Path | None:
    """Submit all candidates to NCBI BLAST nr, wait for results."""
    print(f"  Submitting {len(candidates)} queries to NCBI BLAST (nr)...")
    print("  Note: NCBI limits to 1 job/second — submitting sequentially\n")

    all_lines: list[str] = []
    for cid, seq in candidates:
        print(f"  → {cid} ({len(seq)} aa)", end="", flush=True)
        fasta_str = f">{cid}\n{seq}"
        try:
            rid = _submit_ncbi_blast(fasta_str, "nr")
            if not rid:
                print(" [no RID returned]")
                continue
            result = _fetch_ncbi_blast(rid)
            if result:
                # Extract only the tabular hit lines
                for line in result.splitlines():
                    if line and not line.startswith("#"):
                        all_lines.append(line)
            time.sleep(3)  # NCBI rate limit: ≤1 req/second
        except Exception as e:
            print(f" ERROR: {e}")

    out_file = out_dir / "nr_results.txt"
    with open(out_file, "w") as f:
        f.write("# qseqid\tsseqid\tpident\tlength\tqlen\tslen\tevalue\tbitscore\tstitle\n")
        f.write("\n".join(all_lines))
    print(f"\n  Done → {out_file}")
    return out_file


def parse_blast_hits(
    blast_file: Path,
    source_label: str,
) -> list[dict]:
    """Parse BLAST tabular output (fmt 6 with stitle) into list of dicts."""
    hits: list[dict] = []
    if not blast_file or not blast_file.exists():
        return hits
    with open(blast_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            try:
                hits.append({
                    "source": source_label,
                    "qseqid": parts[0],
                    "sseqid": parts[1],
                    "pident": float(parts[2]),
                    "length": int(parts[3]),
                    "evalue": float(parts[6]),
                    "bitscore": float(parts[7]),
                    "stitle": "\t".join(parts[8:])[:120] if len(parts) > 8 else "",
                })
            except (ValueError, IndexError):
                continue
    return hits


def _risk_level(pident: float, source: str) -> str:
    is_patent = "pataa" in source.lower()
    if pident >= 90:
        return "HIGH" if is_patent else "MODERATE"
    elif pident >= 60:
        return "MODERATE" if is_patent else "LOW"
    elif pident >= 40:
        return "LOW"
    else:
        return "CLEAR"


def write_summary(
    candidates: list[tuple[str, str]],
    all_hits: list[dict],
    out_dir: Path,
) -> Path:
    out = out_dir / "summary.csv"
    fields = ["candidate_id", "sequence", "source", "sseqid", "pident",
              "length", "evalue", "risk_level", "hit_title"]
    rows: list[dict] = []
    hit_by_cid: dict[str, list[dict]] = {}
    for h in all_hits:
        hit_by_cid.setdefault(h["qseqid"], []).append(h)

    for cid, seq in candidates:
        hits = hit_by_cid.get(cid, [])
        if not hits:
            rows.append({
                "candidate_id": cid, "sequence": seq, "source": "none",
                "sseqid": "NONE", "pident": 0.0, "length": 0,
                "evalue": 999, "risk_level": "CLEAR", "hit_title": "",
            })
        else:
            for h in sorted(hits, key=lambda x: -x["pident"])[:5]:
                rows.append({
                    "candidate_id": cid, "sequence": seq,
                    "source": h["source"], "sseqid": h["sseqid"],
                    "pident": h["pident"], "length": h["length"],
                    "evalue": h["evalue"],
                    "risk_level": _risk_level(h["pident"], h["source"]),
                    "hit_title": h["stitle"],
                })

    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return out


def write_lens_queries(candidates: list[tuple[str, str]], out_dir: Path) -> Path:
    """Generate Lens.org patent search strings for each candidate."""
    out = out_dir / "lens_queries.txt"
    lens_base = "https://www.lens.org/lens/search/patent?q="
    with open(out, "w") as f:
        f.write("# Lens.org patent full-text search strings for AMP candidates\n")
        f.write("# Steps:\n")
        f.write("#   1. Open each URL below in a browser\n")
        f.write("#   2. Filter: 'Claims' + 'Sequence Listing'\n")
        f.write("#   3. Check if exact sequence appears in any patent claim or SEQ ID NO\n")
        f.write("#   4. Also try 3-5aa subsequences if full sequence returns no results\n\n")
        for cid, seq in candidates:
            # Lens.org full-text search — put sequence in quotes
            url = lens_base + urllib.parse.quote(f'"{seq}"')
            # Also a subsequence window (middle 12aa, most specific part)
            mid = len(seq) // 2
            subseq = seq[max(0, mid-6):mid+6]
            url_sub = lens_base + urllib.parse.quote(f'"{subseq}"')
            f.write(f"## {cid} ({len(seq)}aa)\n")
            f.write(f"Full sequence search:\n  {url}\n")
            f.write(f"12aa subsequence ({subseq}):\n  {url_sub}\n\n")
    return out


def write_ip_report(
    candidates: list[tuple[str, str]],
    all_hits: list[dict],
    out_dir: Path,
) -> Path:
    out = out_dir / "ip_clearance_report.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    hit_by_cid: dict[str, list[dict]] = {}
    for h in all_hits:
        hit_by_cid.setdefault(h["qseqid"], []).append(h)

    lines = [
        f"# IP Clearance Report — OpenAMP Foundry De Novo Candidates",
        f"",
        f"**Generated:** {ts}  ",
        f"**Databases searched:** NCBI pataa (patent proteins), NCBI nr (non-redundant)  ",
        f"**Tool:** BLASTp 2.17.0+ (BLOSUM62, E≤10, word_size=2, gap 11/1)  ",
        f"**Candidates:** {len(candidates)}  ",
        f"",
        f"> **IMPORTANT:** This is a computational screen only. Consult qualified patent",
        f"> counsel before filing. Sequence similarity does not automatically determine",
        f"> infringement — claim scope, jurisdiction, and prosecution history all matter.",
        f"",
        f"---",
        f"",
        f"## Risk Classification",
        f"",
        f"| Level | Condition |",
        f"|-------|-----------|",
        f"| HIGH | ≥90% identity to patent sequence |",
        f"| MODERATE | 60–90% identity to patent seq, or ≥90% to public seq |",
        f"| LOW | 40–60% identity to patent seq |",
        f"| CLEAR | <40% to any sequence |",
        f"",
        f"---",
        f"",
        f"## Per-Candidate Summary",
        f"",
    ]

    for cid, seq in candidates:
        hits = sorted(hit_by_cid.get(cid, []), key=lambda x: -x["pident"])
        if not hits:
            risk = "CLEAR"
            lines.append(f"### {cid} — ✓ CLEAR")
            lines.append(f"**Sequence:** `{seq}`  ")
            lines.append(f"**Best hit:** None (no significant similarity found)  ")
            lines.append(f"**IP status:** CLEAR — approved for synthesis and filing  ")
        else:
            best = hits[0]
            risk = _risk_level(best["pident"], best["source"])
            icon = "✓" if risk == "CLEAR" else ("⚠" if risk == "LOW" else "❌")
            lines.append(f"### {cid} — {icon} {risk}")
            lines.append(f"**Sequence:** `{seq}`  ")
            lines.append(f"**Best hit:** {best['sseqid']} ({best['pident']:.1f}% identity, "
                         f"E={best['evalue']:.2e}) — {best['stitle'][:80]}  ")
            lines.append(f"**Source:** {best['source']}  ")
            lines.append(f"**Risk:** {risk}  ")
            if len(hits) > 1:
                lines.append(f"**Other hits:** {len(hits)-1} additional (see summary.csv)  ")
        lines.append(f"")

    lines += [
        f"---",
        f"",
        f"## Manual Steps Required Before Filing",
        f"",
        f"1. **Lens.org patent full-text search** — see `lens_queries.txt`",
        f"   - Search exact sequence string in patent claims and sequence listings",
        f"   - Check USPTO, EPO, WIPO, JPO coverage",
        f"",
        f"2. **WIPO PatentScope sequence search** — https://patentscope.wipo.int/search/en/sequences.jsf",
        f"   - Submit each sequence for international patent sequence listing search",
        f"",
        f"3. **EPO Espacenet** — https://worldwide.espacenet.com/",
        f"   - Search sequence accession numbers from any pataa hits",
        f"",
        f"4. **Attorney review** — have a patent attorney evaluate freedom to operate (FTO)",
        f"   before any synthesis order, publication, or provisional filing",
        f"",
        f"---",
        f"",
        f"*This report was generated by OpenAMP Foundry `scripts/run_patent_blastp.py`.*",
    ]

    with open(out, "w") as f:
        f.write("\n".join(lines))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Patent + global BLASTp for AMP IP clearance")
    parser.add_argument("--fasta", required=True, help="Input FASTA (candidate sequences)")
    parser.add_argument("--pataa-only", action="store_true", help="Skip remote NCBI nr search")
    parser.add_argument("--nr-only",    action="store_true", help="Skip local pataa search")
    parser.add_argument("--pataa-db",   default=str(PATAA_DB_PATH),
                        help=f"Path to local pataa BLAST DB (default: {PATAA_DB_PATH})")
    parser.add_argument("--out-dir",    help="Output directory (default: auto-named in outputs/)")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "outputs" / f"patent_blastp_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== OpenAMP Patent + Global BLASTp IP Clearance ===\n")
    candidates = _load_fasta(Path(args.fasta))
    print(f"Loaded {len(candidates)} candidates from {args.fasta}\n")

    all_hits: list[dict] = []

    if not args.nr_only:
        pataa_file = run_local_pataa(candidates, out_dir, Path(args.pataa_db))
        if pataa_file:
            hits = parse_blast_hits(pataa_file, "pataa")
            print(f"  pataa: {len(hits)} hits")
            all_hits.extend(hits)

    if not args.pataa_only:
        nr_file = run_remote_nr(candidates, out_dir)
        if nr_file:
            hits = parse_blast_hits(nr_file, "nr")
            print(f"  nr: {len(hits)} hits")
            all_hits.extend(hits)

    print(f"\nTotal hits: {len(all_hits)}")

    summary = write_summary(candidates, all_hits, out_dir)
    lens   = write_lens_queries(candidates, out_dir)
    report = write_ip_report(candidates, all_hits, out_dir)

    print(f"\n=== Output files ===")
    for f in [summary, lens, report]:
        print(f"  {f}")
    print(f"\nNext steps: open {report} and {lens}")


if __name__ == "__main__":
    main()
