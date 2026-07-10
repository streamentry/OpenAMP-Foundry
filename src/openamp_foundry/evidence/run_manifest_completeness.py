"""RMC- Run manifest completeness schema.

Validates that a pipeline run's output manifest carries the fields needed
for external reproducibility. An output manifest is not releasable until it
passes this check.
Verdict: complete / incomplete / partial.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "commit_hash",
    "config_path",
    "config_hash",
    "input_path",
    "input_hash",
    "random_seed",
    "package_version",
    "generation_command",
    "run_timestamp",
)

VALID_RMC_VERDICTS: frozenset[str] = frozenset({
    "complete",
    "incomplete",
    "partial",
})

PLACEHOLDER_SENTINELS: frozenset[str] = frozenset({
    "UNKNOWN", "N/A", "TBD", "TODO", "PLACEHOLDER", "", "null", "none"
})


@dataclass
class FieldPresenceRecord:
    field_name: str
    is_present: bool
    is_non_empty: bool
    value_snippet: str


@dataclass
class RunManifestCompleteness:
    rmc_id: str
    pipeline_version: str
    run_id: str
    field_records: list[FieldPresenceRecord]
    n_fields_required: int
    n_fields_present: int
    n_fields_complete: int
    missing_fields: list[str]
    placeholder_fields: list[str]
    verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_verdict(
    n_fields_present: int,
    n_fields_complete: int,
    placeholder_fields: list[str],
) -> str:
    if n_fields_present < len(REQUIRED_MANIFEST_FIELDS):
        return "incomplete"
    if len(placeholder_fields) > 0:
        return "partial"
    return "complete"


def _scan_manifest_dict(manifest_dict: dict) -> list[FieldPresenceRecord]:
    records: list[FieldPresenceRecord] = []
    for field in REQUIRED_MANIFEST_FIELDS:
        is_present = field in manifest_dict
        raw_value = str(manifest_dict.get(field, ""))
        is_non_empty = (
            is_present
            and raw_value.strip() != ""
            and raw_value.strip().lower() not in {s.lower() for s in PLACEHOLDER_SENTINELS}
        )
        value_snippet = raw_value[:40]
        records.append(FieldPresenceRecord(
            field_name=field,
            is_present=is_present,
            is_non_empty=is_non_empty,
            value_snippet=value_snippet,
        ))
    return records


def build_run_manifest_completeness(
    *,
    rmc_id: str,
    pipeline_version: str,
    run_id: str,
    manifest_dict: dict,
    limitations: list[str],
    created_at: str,
) -> RunManifestCompleteness:
    field_records = _scan_manifest_dict(manifest_dict)
    n_fields_required = len(REQUIRED_MANIFEST_FIELDS)
    n_fields_present = sum(1 for r in field_records if r.is_present)
    n_fields_complete = sum(1 for r in field_records if r.is_non_empty)
    missing_fields = [r.field_name for r in field_records if not r.is_present]
    placeholder_fields = [
        r.field_name for r in field_records if r.is_present and not r.is_non_empty
    ]
    verdict = _compute_verdict(n_fields_present, n_fields_complete, placeholder_fields)
    rmc = RunManifestCompleteness(
        rmc_id=rmc_id,
        pipeline_version=pipeline_version,
        run_id=run_id,
        field_records=field_records,
        n_fields_required=n_fields_required,
        n_fields_present=n_fields_present,
        n_fields_complete=n_fields_complete,
        missing_fields=missing_fields,
        placeholder_fields=placeholder_fields,
        verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_run_manifest_completeness(rmc)
    return rmc


def validate_run_manifest_completeness(rmc: RunManifestCompleteness) -> None:
    if not rmc.rmc_id.startswith("RMC-"):
        raise ValueError(f"rmc_id must start with 'RMC-': {rmc.rmc_id!r}")
    if not rmc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not rmc.run_id:
        raise ValueError("run_id must be non-empty")
    if rmc.n_fields_required != len(REQUIRED_MANIFEST_FIELDS):
        raise ValueError(
            f"n_fields_required must be {len(REQUIRED_MANIFEST_FIELDS)}, got {rmc.n_fields_required}"
        )
    expected_present = sum(1 for r in rmc.field_records if r.is_present)
    if rmc.n_fields_present != expected_present:
        raise ValueError("n_fields_present mismatch")
    expected_complete = sum(1 for r in rmc.field_records if r.is_non_empty)
    if rmc.n_fields_complete != expected_complete:
        raise ValueError("n_fields_complete mismatch")
    expected_missing = [r.field_name for r in rmc.field_records if not r.is_present]
    if rmc.missing_fields != expected_missing:
        raise ValueError("missing_fields mismatch")
    expected_placeholder = [
        r.field_name for r in rmc.field_records if r.is_present and not r.is_non_empty
    ]
    if rmc.placeholder_fields != expected_placeholder:
        raise ValueError("placeholder_fields mismatch")
    if rmc.verdict not in VALID_RMC_VERDICTS:
        raise ValueError(f"verdict {rmc.verdict!r} not in VALID_RMC_VERDICTS")
    expected_verdict = _compute_verdict(
        rmc.n_fields_present, rmc.n_fields_complete, rmc.placeholder_fields
    )
    if rmc.verdict != expected_verdict:
        raise ValueError(
            f"verdict {rmc.verdict!r} inconsistent with "
            f"n_fields_present={rmc.n_fields_present}, "
            f"n_fields_complete={rmc.n_fields_complete}, "
            f"placeholder_fields={rmc.placeholder_fields}"
        )
    if not rmc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not rmc.limitations:
        raise ValueError("limitations must be non-empty")
    if not rmc.created_at:
        raise ValueError("created_at must be non-empty")


def format_run_manifest_completeness(rmc: RunManifestCompleteness) -> str:
    lines = [
        f"Run Manifest Completeness — {rmc.rmc_id}",
        f"Pipeline: {rmc.pipeline_version}",
        f"Run ID: {rmc.run_id}",
        f"Verdict: {rmc.verdict}",
        f"Fields: {rmc.n_fields_complete}/{rmc.n_fields_required} complete, "
        f"{rmc.n_fields_present}/{rmc.n_fields_required} present",
    ]
    if rmc.missing_fields:
        lines.append(f"Missing: {', '.join(rmc.missing_fields)}")
    if rmc.placeholder_fields:
        lines.append(f"Placeholders: {', '.join(rmc.placeholder_fields)}")
    lines.append("Field details:")
    for rec in rmc.field_records:
        status = "OK" if rec.is_non_empty else ("MISSING" if not rec.is_present else "PLACEHOLDER")
        snippet = f" ({rec.value_snippet!r})" if rec.value_snippet else ""
        lines.append(f"  {rec.field_name}: {status}{snippet}")
    if rmc.limitations:
        lines.append(f"Limitations: {'; '.join(rmc.limitations)}")
    lines.append(f"Created: {rmc.created_at}")
    lines.append(f"dry_lab_only: {rmc.dry_lab_only}")
    return "\n".join(lines)
