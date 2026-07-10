from __future__ import annotations
from dataclasses import dataclass, field


REQUIRED_EVIDENCE_SCHEMA_TYPES = frozenset({
    "BSP", "PSC", "BOS", "CPS", "CBA", "CRG",
    "RSR", "PQT", "BTI", "CBA2", "BEG", "SAT",
})

VALID_COMPLETENESS_GRADES = frozenset({"A", "B", "C", "D"})


@dataclass
class SchemaPresenceEntry:
    schema_type: str
    present: bool
    artifact_id: str


@dataclass
class PipelineCompletenessCertificate:
    pcc_id: str
    pipeline_run_id: str
    pipeline_version: str
    schema_presence_entries: list[SchemaPresenceEntry]
    n_required: int
    n_present: int
    n_missing: int
    missing_schema_types: list[str]
    completeness_fraction: float
    completeness_grade: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


@dataclass
class PCCValidationResult:
    valid: bool
    violations: list[str] = field(default_factory=list)


def _compute_completeness_grade(fraction: float) -> str:
    if fraction >= 1.0:
        return "A"
    if fraction >= 0.75:
        return "B"
    if fraction >= 0.5:
        return "C"
    return "D"


def validate_pipeline_completeness_certificate(
    cert: PipelineCompletenessCertificate,
) -> PCCValidationResult:
    violations = []

    if not cert.pcc_id.startswith("PCC-"):
        violations.append("pcc_id must start with 'PCC-'")

    if not cert.dry_lab_only:
        violations.append("dry_lab_only must be True")

    if cert.n_required != len(REQUIRED_EVIDENCE_SCHEMA_TYPES):
        violations.append(
            f"n_required ({cert.n_required}) must equal {len(REQUIRED_EVIDENCE_SCHEMA_TYPES)}"
        )

    expected_n_present = sum(1 for e in cert.schema_presence_entries if e.present)
    if cert.n_present != expected_n_present:
        violations.append(
            f"n_present ({cert.n_present}) must equal count of present entries ({expected_n_present})"
        )

    if cert.n_missing != cert.n_required - cert.n_present:
        violations.append(
            f"n_missing ({cert.n_missing}) must equal n_required - n_present "
            f"({cert.n_required - cert.n_present})"
        )

    expected_missing = sorted(
        e.schema_type for e in cert.schema_presence_entries if not e.present
    )
    if cert.missing_schema_types != expected_missing:
        violations.append(
            f"missing_schema_types {cert.missing_schema_types} must equal sorted absent types {expected_missing}"
        )

    if cert.n_required > 0:
        expected_fraction = cert.n_present / cert.n_required
        if abs(cert.completeness_fraction - expected_fraction) > 1e-9:
            violations.append(
                f"completeness_fraction ({cert.completeness_fraction}) must equal "
                f"n_present/n_required ({expected_fraction})"
            )

    expected_grade = _compute_completeness_grade(cert.completeness_fraction)
    if cert.completeness_grade != expected_grade:
        violations.append(
            f"completeness_grade '{cert.completeness_grade}' must be '{expected_grade}' "
            f"for fraction={cert.completeness_fraction}"
        )

    if cert.completeness_grade not in VALID_COMPLETENESS_GRADES:
        violations.append(
            f"completeness_grade '{cert.completeness_grade}' must be one of {sorted(VALID_COMPLETENESS_GRADES)}"
        )

    covered_types = {e.schema_type for e in cert.schema_presence_entries}
    for required_type in REQUIRED_EVIDENCE_SCHEMA_TYPES:
        if required_type not in covered_types:
            violations.append(f"Required schema type '{required_type}' has no entry in schema_presence_entries")

    if not cert.limitations:
        violations.append("limitations must be non-empty")

    return PCCValidationResult(valid=len(violations) == 0, violations=violations)


def build_pipeline_completeness_certificate(
    pcc_id: str,
    pipeline_run_id: str,
    pipeline_version: str,
    present_schema_artifact_ids: dict[str, str],
    limitations: list[str],
    created_at: str,
) -> PipelineCompletenessCertificate:
    entries: list[SchemaPresenceEntry] = []
    for schema_type in sorted(REQUIRED_EVIDENCE_SCHEMA_TYPES):
        artifact_id = present_schema_artifact_ids.get(schema_type, "")
        entries.append(
            SchemaPresenceEntry(
                schema_type=schema_type,
                present=schema_type in present_schema_artifact_ids,
                artifact_id=artifact_id,
            )
        )

    n_required = len(REQUIRED_EVIDENCE_SCHEMA_TYPES)
    n_present = sum(1 for e in entries if e.present)
    n_missing = n_required - n_present
    missing_schema_types = sorted(e.schema_type for e in entries if not e.present)
    completeness_fraction = n_present / n_required if n_required > 0 else 0.0
    completeness_grade = _compute_completeness_grade(completeness_fraction)

    return PipelineCompletenessCertificate(
        pcc_id=pcc_id,
        pipeline_run_id=pipeline_run_id,
        pipeline_version=pipeline_version,
        schema_presence_entries=entries,
        n_required=n_required,
        n_present=n_present,
        n_missing=n_missing,
        missing_schema_types=missing_schema_types,
        completeness_fraction=completeness_fraction,
        completeness_grade=completeness_grade,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )


def format_pipeline_completeness_certificate(cert: PipelineCompletenessCertificate) -> str:
    lines = [
        f"Pipeline Completeness Certificate — {cert.pcc_id}",
        f"Run: {cert.pipeline_run_id}  |  Pipeline: {cert.pipeline_version}",
        f"Grade: {cert.completeness_grade}  |  "
        f"Present: {cert.n_present}/{cert.n_required}  |  "
        f"Missing: {cert.n_missing}  |  "
        f"Fraction: {cert.completeness_fraction:.4f}",
        f"Missing Types: {', '.join(cert.missing_schema_types) or '(none)'}",
        f"Created: {cert.created_at}",
        f"Limitations: {'; '.join(cert.limitations)}",
        f"dry_lab_only: {cert.dry_lab_only}",
    ]
    return "\n".join(lines)
