"""Adapter stub: OpenAMP output → external tool format."""

from __future__ import annotations

from dataclasses import dataclass, field

ADAPTER_STUB_ID_PREFIX = "ADS-"

VALID_TARGET_TOOLS: frozenset = frozenset(
    {
        "ampscanner",
        "campr3",
        "dbaasp",
        "dramp",
        "hmmer",
        "iamp2l",
        "modlamp",
        "peptide_ranker",
        "propedia",
        "rosetta_fold",
    }
)

VALID_OUTPUT_FORMATS: frozenset = frozenset(
    {"fasta", "csv", "json", "tsv", "pdb_sequence_list", "sdf"}
)

VALID_ADAPTER_STATUSES: frozenset = frozenset(
    {"stub", "partial", "complete", "deprecated"}
)

TOY_ID_PREFIXES: frozenset = frozenset(
    {"TOY-", "MOCK-", "EXAMPLE-", "DEMO-", "TEST-"}
)

STUB_DISCLAIMER = (
    "This is a stub adapter. Outputs are computational nominees only. "
    "No biological activity is implied. Human review required before wet-lab use."
)


@dataclass
class AdapterField:
    source_field: str
    target_field: str
    transform: str
    is_required: bool = True
    notes: str = ""


@dataclass
class AdapterStubRecord:
    adapter_id: str
    target_tool: str
    output_format: str
    adapter_status: str
    field_mappings: list = field(default_factory=list)
    dry_lab_only: bool = True
    disclaimer: str = STUB_DISCLAIMER
    version: str = "0.1.0"
    implementation_notes: str = ""


@dataclass
class AdapterValidationResult:
    is_valid: bool
    violations: list = field(default_factory=list)


def build_adapter_field(
    source_field: str,
    target_field: str,
    transform: str = "identity",
    is_required: bool = True,
    notes: str = "",
) -> AdapterField:
    return AdapterField(
        source_field=source_field,
        target_field=target_field,
        transform=transform,
        is_required=is_required,
        notes=notes,
    )


def build_adapter_stub_record(
    adapter_id: str,
    target_tool: str,
    output_format: str,
    adapter_status: str = "stub",
    field_mappings: list | None = None,
    dry_lab_only: bool = True,
    disclaimer: str = STUB_DISCLAIMER,
    version: str = "0.1.0",
    implementation_notes: str = "",
) -> AdapterStubRecord:
    return AdapterStubRecord(
        adapter_id=adapter_id,
        target_tool=target_tool,
        output_format=output_format,
        adapter_status=adapter_status,
        field_mappings=list(field_mappings) if field_mappings else [],
        dry_lab_only=dry_lab_only,
        disclaimer=disclaimer,
        version=version,
        implementation_notes=implementation_notes or f"Stub adapter for {target_tool}",
    )


def validate_adapter_stub_record(record: AdapterStubRecord) -> AdapterValidationResult:
    violations: list[str] = []

    if not record.adapter_id.startswith(ADAPTER_STUB_ID_PREFIX):
        violations.append(
            f"adapter_id must start with '{ADAPTER_STUB_ID_PREFIX}', got '{record.adapter_id}'"
        )

    if record.target_tool not in VALID_TARGET_TOOLS:
        violations.append(
            f"target_tool '{record.target_tool}' not in VALID_TARGET_TOOLS"
        )

    if record.output_format not in VALID_OUTPUT_FORMATS:
        violations.append(
            f"output_format '{record.output_format}' not in VALID_OUTPUT_FORMATS"
        )

    if record.adapter_status not in VALID_ADAPTER_STATUSES:
        violations.append(
            f"adapter_status '{record.adapter_status}' not in VALID_ADAPTER_STATUSES"
        )

    if not record.dry_lab_only:
        violations.append(
            "dry_lab_only must be True; wet-lab adapter configuration requires human review"
        )

    if not record.disclaimer:
        violations.append("disclaimer must not be empty")

    if "biological activity" not in record.disclaimer.lower() and "biological" not in record.disclaimer.lower():
        violations.append(
            "disclaimer must mention that no biological activity is implied"
        )

    if not record.version:
        violations.append("version must not be empty")

    if not record.implementation_notes:
        violations.append("implementation_notes must not be empty")

    for i, fm in enumerate(record.field_mappings):
        if not fm.source_field:
            violations.append(f"field_mappings[{i}]: source_field must not be empty")
        if not fm.target_field:
            violations.append(f"field_mappings[{i}]: target_field must not be empty")
        if not fm.transform:
            violations.append(f"field_mappings[{i}]: transform must not be empty")

    return AdapterValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
    )


def format_adapter_stub_record(record: AdapterStubRecord) -> str:
    lines: list[str] = []
    lines.append(f"Adapter: {record.adapter_id}")
    lines.append(f"Target tool: {record.target_tool}")
    lines.append(f"Output format: {record.output_format}")
    lines.append(f"Status: {record.adapter_status}")
    lines.append(f"Version: {record.version}")
    lines.append(f"Dry-lab only: {record.dry_lab_only}")
    lines.append(f"Disclaimer: {record.disclaimer}")
    lines.append(f"Notes: {record.implementation_notes}")
    if record.field_mappings:
        lines.append(f"Field mappings ({len(record.field_mappings)}):")
        for fm in record.field_mappings:
            req = "required" if fm.is_required else "optional"
            lines.append(
                f"  {fm.source_field} -> {fm.target_field} [{fm.transform}] ({req})"
            )
            if fm.notes:
                lines.append(f"    note: {fm.notes}")
    else:
        lines.append("Field mappings: none defined (stub)")
    return "\n".join(lines) + "\n"
