"""PTR- pipeline phase timeline report schema.

Ordered sequence of all schema events for a pipeline run, sorted by
created_at; shows progression from nomination to shortlisting with schema
type, artifact ID, and timestamp per event.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_PIPELINE_SCHEMA_TYPES: frozenset[str] = frozenset({
    "BSP", "PSC", "BOS", "CPS", "CBA", "CRG",
    "RSR", "PQT", "BTI", "CBA2", "BEG", "SAT", "PCC",
    "FET", "BRC", "CSV",
})

VALID_TIMELINE_VERDICTS: frozenset[str] = frozenset({
    "complete", "in_progress", "empty",
})

NOMINATION_TYPES: frozenset[str] = frozenset({"BSP", "PSC"})
SCREENING_TYPES: frozenset[str] = frozenset({"BOS", "CPS", "CBA", "CRG"})
RANKING_TYPES: frozenset[str] = frozenset({"RSR", "PQT"})
EVIDENCE_TYPES: frozenset[str] = frozenset({"BTI", "CBA2", "BEG", "SAT", "PCC"})
INTEGRATION_TYPES: frozenset[str] = frozenset({"FET", "BRC", "CSV"})

TERMINAL_SCHEMA_TYPES: frozenset[str] = frozenset({"SAT", "PCC"})


def _phase_for_schema_type(schema_type: str) -> str:
    if schema_type in NOMINATION_TYPES:
        return "nomination"
    if schema_type in SCREENING_TYPES:
        return "screening"
    if schema_type in RANKING_TYPES:
        return "ranking"
    if schema_type in EVIDENCE_TYPES:
        return "evidence"
    if schema_type in INTEGRATION_TYPES:
        return "integration"
    return "unknown"


@dataclass
class TimelineEvent:
    schema_type: str
    artifact_id: str
    phase: str
    created_at: str


@dataclass
class PipelinePhaseTimelineReport:
    ptr_id: str
    pipeline_run_id: str
    pipeline_version: str
    batch_id: str
    events: list[TimelineEvent]
    n_events: int
    schema_types_present: list[str]
    terminal_schemas_present: list[str]
    timeline_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_verdict(events: list[TimelineEvent]) -> str:
    if not events:
        return "empty"
    present = {e.schema_type for e in events}
    if TERMINAL_SCHEMA_TYPES.issubset(present):
        return "complete"
    return "in_progress"


def validate_pipeline_phase_timeline_report(ptr: PipelinePhaseTimelineReport) -> None:
    if not ptr.ptr_id.startswith("PTR-"):
        raise ValueError(f"ptr_id must start with 'PTR-': {ptr.ptr_id!r}")
    if not ptr.pipeline_run_id:
        raise ValueError("pipeline_run_id must be non-empty")
    if not ptr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not ptr.batch_id:
        raise ValueError("batch_id must be non-empty")
    for event in ptr.events:
        if event.schema_type not in VALID_PIPELINE_SCHEMA_TYPES:
            raise ValueError(
                f"schema_type {event.schema_type!r} not in VALID_PIPELINE_SCHEMA_TYPES"
            )
        if not event.artifact_id:
            raise ValueError(
                f"artifact_id must be non-empty for schema_type {event.schema_type!r}"
            )
    if ptr.timeline_verdict not in VALID_TIMELINE_VERDICTS:
        raise ValueError(
            f"timeline_verdict {ptr.timeline_verdict!r} not in VALID_TIMELINE_VERDICTS"
        )
    if not ptr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not ptr.limitations:
        raise ValueError("limitations must be non-empty")
    if not ptr.created_at:
        raise ValueError("created_at must be non-empty")
    if ptr.n_events != len(ptr.events):
        raise ValueError("n_events must equal len(events)")
    expected_types = sorted({e.schema_type for e in ptr.events})
    if ptr.schema_types_present != expected_types:
        raise ValueError("schema_types_present mismatch")
    expected_terminal = sorted(
        TERMINAL_SCHEMA_TYPES & {e.schema_type for e in ptr.events}
    )
    if ptr.terminal_schemas_present != expected_terminal:
        raise ValueError("terminal_schemas_present mismatch")


def build_pipeline_phase_timeline_report(
    *,
    ptr_id: str,
    pipeline_run_id: str,
    pipeline_version: str,
    batch_id: str,
    event_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> PipelinePhaseTimelineReport:
    """Build a pipeline phase timeline report.

    event_dicts: list of dicts with keys: schema_type, artifact_id, created_at.
    Events are sorted by created_at, then schema_type.
    """
    events_raw = [
        TimelineEvent(
            schema_type=d["schema_type"],
            artifact_id=d["artifact_id"],
            phase=_phase_for_schema_type(d["schema_type"]),
            created_at=d["created_at"],
        )
        for d in event_dicts
    ]
    events_sorted = sorted(events_raw, key=lambda e: (e.created_at, e.schema_type))
    schema_types_present = sorted({e.schema_type for e in events_sorted})
    terminal_present = sorted(
        TERMINAL_SCHEMA_TYPES & {e.schema_type for e in events_sorted}
    )
    verdict = _compute_verdict(events_sorted)

    ptr = PipelinePhaseTimelineReport(
        ptr_id=ptr_id,
        pipeline_run_id=pipeline_run_id,
        pipeline_version=pipeline_version,
        batch_id=batch_id,
        events=events_sorted,
        n_events=len(events_sorted),
        schema_types_present=schema_types_present,
        terminal_schemas_present=terminal_present,
        timeline_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_pipeline_phase_timeline_report(ptr)
    return ptr


def format_pipeline_phase_timeline_report(ptr: PipelinePhaseTimelineReport) -> str:
    lines = [
        f"Pipeline Phase Timeline Report — {ptr.ptr_id}",
        f"Run: {ptr.pipeline_run_id}  |  Pipeline: {ptr.pipeline_version}",
        f"Batch: {ptr.batch_id}  |  Verdict: {ptr.timeline_verdict}",
        f"Events: {ptr.n_events}  |  Schema types: {len(ptr.schema_types_present)}",
    ]
    if ptr.schema_types_present:
        lines.append(f"Present: {', '.join(ptr.schema_types_present)}")
    if ptr.terminal_schemas_present:
        lines.append(f"Terminal schemas: {', '.join(ptr.terminal_schemas_present)}")
    if ptr.events:
        lines.append("Timeline:")
        for event in ptr.events:
            lines.append(
                f"  [{event.created_at}] {event.schema_type} ({event.phase}): {event.artifact_id}"
            )
    lines.append(f"Created: {ptr.created_at}")
    lines.append(f"Limitations: {'; '.join(ptr.limitations)}")
    lines.append(f"dry_lab_only: {ptr.dry_lab_only}")
    return "\n".join(lines)
