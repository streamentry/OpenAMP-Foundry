from __future__ import annotations

import csv
from pathlib import Path

from openamp_foundry.types import PeptideCandidate


CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")


def normalize_sequence(seq: str) -> str:
    return "".join(seq.strip().upper().split())


def is_valid_sequence(seq: str, allowed: set[str] | None = None) -> bool:
    allowed = allowed or CANONICAL_AA
    seq = normalize_sequence(seq)
    return bool(seq) and all(ch in allowed for ch in seq)


def load_candidates_csv(path: str | Path) -> list[PeptideCandidate]:
    rows: list[PeptideCandidate] = []
    with Path(path).open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if "sequence" not in fieldnames:
            raise ValueError(
                f"CSV header is missing required 'sequence' column. "
                f"Found columns: {list(fieldnames)!r}. "
                "Check that the CSV header spells it exactly as 'sequence'."
            )
        for i, row in enumerate(reader, start=1):
            cid = row.get("id") or f"candidate-{i:06d}"
            seq = normalize_sequence(row["sequence"])
            source = row.get("source", "csv")
            rows.append(PeptideCandidate(candidate_id=cid, sequence=seq, source=source))
    return rows
