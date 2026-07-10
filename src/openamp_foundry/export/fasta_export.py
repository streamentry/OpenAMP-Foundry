"""FASTA export module for dry-lab AMP candidate sets."""

from __future__ import annotations

from dataclasses import dataclass, field

FASTA_EXPORT_ID_PREFIX = "FAE-"

VALID_EXPORT_CONTEXTS: frozenset = frozenset(
    {"dry_lab_only", "partner_review", "internal_use", "public_release"}
)

VALID_CANDIDATE_STATUSES: frozenset = frozenset(
    {"nominated", "selected", "under_review", "cleared", "retracted"}
)

VALID_AMINO_ACIDS: frozenset = frozenset("ACDEFGHIKLMNPQRSTVWY")

DRY_LAB_SAFE_CONTEXTS: frozenset = frozenset(
    {"dry_lab_only", "partner_review", "internal_use"}
)

TOY_ID_PREFIXES: frozenset = frozenset(
    {"TOY-", "MOCK-", "EXAMPLE-", "DEMO-", "TEST-"}
)

MIN_SEQUENCE_LENGTH: int = 5
MAX_SEQUENCE_LENGTH: int = 100
DRY_LAB_CLAIM_TERMS: frozenset = frozenset(
    {"computational", "dry-lab", "dry_lab", "in silico", "in-silico"}
)


@dataclass
class FastaExportEntry:
    candidate_id: str
    sequence: str
    description: str
    export_context: str
    status: str
    is_toy_data: bool


@dataclass
class FastaExportRecord:
    export_id: str
    export_timestamp_utc: str
    total_candidates: int
    entries: list = field(default_factory=list)
    dry_lab_only: bool = True
    export_context: str = "dry_lab_only"
    export_note: str = ""


@dataclass
class FastaExportValidationResult:
    is_valid: bool
    violations: list = field(default_factory=list)


def build_fasta_entry(
    candidate_id: str,
    sequence: str,
    description: str,
    export_context: str,
    status: str,
    is_toy_data: bool,
) -> FastaExportEntry:
    return FastaExportEntry(
        candidate_id=candidate_id,
        sequence=sequence.upper(),
        description=description,
        export_context=export_context,
        status=status,
        is_toy_data=is_toy_data,
    )


def build_fasta_export_record(
    export_id: str,
    entries: list,
    dry_lab_only: bool,
    export_context: str,
    export_note: str,
    export_timestamp_utc: str = "",
) -> FastaExportRecord:
    return FastaExportRecord(
        export_id=export_id,
        export_timestamp_utc=export_timestamp_utc or "1970-01-01T00:00:00Z",
        total_candidates=len(entries),
        entries=list(entries),
        dry_lab_only=dry_lab_only,
        export_context=export_context,
        export_note=export_note,
    )


def validate_fasta_export_record(record: FastaExportRecord) -> FastaExportValidationResult:
    violations: list[str] = []

    if not record.export_id.startswith(FASTA_EXPORT_ID_PREFIX):
        violations.append(
            f"export_id must start with '{FASTA_EXPORT_ID_PREFIX}', got '{record.export_id}'"
        )

    if record.export_context not in VALID_EXPORT_CONTEXTS:
        violations.append(
            f"export_context '{record.export_context}' not in VALID_EXPORT_CONTEXTS"
        )

    if record.dry_lab_only and record.export_context not in DRY_LAB_SAFE_CONTEXTS:
        violations.append(
            f"dry_lab_only=True requires export_context in {sorted(DRY_LAB_SAFE_CONTEXTS)}, "
            f"got '{record.export_context}'"
        )

    if record.total_candidates != len(record.entries):
        violations.append(
            f"total_candidates={record.total_candidates} does not match "
            f"len(entries)={len(record.entries)}"
        )

    note_lower = record.export_note.lower()
    if not any(term in note_lower for term in DRY_LAB_CLAIM_TERMS):
        violations.append(
            "export_note must contain at least one dry-lab claim term: "
            + str(sorted(DRY_LAB_CLAIM_TERMS))
        )

    for i, entry in enumerate(record.entries):
        prefix = f"Entry[{i}] (id={entry.candidate_id})"

        seq_upper = entry.sequence.upper()
        invalid_chars = set(seq_upper) - VALID_AMINO_ACIDS
        if invalid_chars:
            violations.append(
                f"{prefix}: sequence contains invalid amino acid characters: {sorted(invalid_chars)}"
            )

        seq_len = len(entry.sequence)
        if not (MIN_SEQUENCE_LENGTH <= seq_len <= MAX_SEQUENCE_LENGTH):
            violations.append(
                f"{prefix}: sequence length {seq_len} outside [{MIN_SEQUENCE_LENGTH}, {MAX_SEQUENCE_LENGTH}]"
            )

        if entry.export_context not in VALID_EXPORT_CONTEXTS:
            violations.append(
                f"{prefix}: export_context '{entry.export_context}' not in VALID_EXPORT_CONTEXTS"
            )

        if entry.status not in VALID_CANDIDATE_STATUSES:
            violations.append(
                f"{prefix}: status '{entry.status}' not in VALID_CANDIDATE_STATUSES"
            )

        if record.dry_lab_only:
            is_toy_id = any(entry.candidate_id.startswith(p) for p in TOY_ID_PREFIXES)
            if not (entry.is_toy_data or is_toy_id):
                violations.append(
                    f"{prefix}: dry_lab_only=True requires is_toy_data=True or "
                    f"candidate_id prefixed with one of {sorted(TOY_ID_PREFIXES)}"
                )

    return FastaExportValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def format_fasta_export(record: FastaExportRecord) -> str:
    lines: list[str] = []
    lines.append(f"; FASTA export {record.export_id}")
    lines.append(f"; timestamp: {record.export_timestamp_utc}")
    lines.append(f"; context: {record.export_context}")
    lines.append(f"; dry_lab_only: {record.dry_lab_only}")
    lines.append(f"; note: {record.export_note}")
    lines.append(f"; total_candidates: {record.total_candidates}")
    lines.append("")
    for entry in record.entries:
        header = (
            f">{entry.candidate_id} {entry.description} "
            f"[status={entry.status}] [context={entry.export_context}]"
        )
        lines.append(header)
        seq = entry.sequence.upper()
        for chunk_start in range(0, len(seq), 60):
            lines.append(seq[chunk_start : chunk_start + 60])
    return "\n".join(lines) + "\n"
