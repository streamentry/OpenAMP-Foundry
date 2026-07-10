"""BXR- batch explanation report schema.

Per-candidate selection reason tracking for multi-batch pipelines.
Documents the *why* behind each candidate: exploitation, exploration,
safety retest, controls, etc. Makes batch-2 selection auditable.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_BXR_VERDICTS: frozenset[str] = frozenset({
    "explained",
    "partially_explained",
    "unexplained",
})

VALID_SELECTION_REASON_CATEGORIES: frozenset[str] = frozenset({
    "winner_exploit",
    "uncertainty_probe",
    "diversity_anchor",
    "safety_retest",
    "negative_control",
    "calibration_check",
})

VALID_CONFIDENCE_LEVELS: frozenset[str] = frozenset({
    "high",
    "moderate",
    "low",
    "not_assessed",
})

EXPLAINED_FRACTION_THRESHOLD: float = 0.80
PARTIAL_FRACTION_THRESHOLD: float = 0.50


@dataclass
class CandidateExplanationEntry:
    candidate_id: str
    selection_reason: str
    confidence_level: str
    predicted_score: float
    uncertainty_score: float
    safety_cleared: bool
    reason_notes: str


@dataclass
class BatchExplanationReport:
    bxr_id: str
    pipeline_version: str
    batch_id: str
    candidate_explanations: list[CandidateExplanationEntry]
    n_candidates: int
    n_explained: int
    n_safety_cleared: int
    exploit_fraction: float
    probe_fraction: float
    explanation_fraction: float
    verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_verdict(
    n_candidates: int,
    explanation_fraction: float,
) -> str:
    if n_candidates == 0:
        return "unexplained"
    if explanation_fraction >= EXPLAINED_FRACTION_THRESHOLD:
        return "explained"
    if explanation_fraction >= PARTIAL_FRACTION_THRESHOLD:
        return "partially_explained"
    return "unexplained"


def validate_batch_explanation_report(bxr: BatchExplanationReport) -> None:
    if not bxr.bxr_id.startswith("BXR-"):
        raise ValueError(f"bxr_id must start with 'BXR-': {bxr.bxr_id!r}")
    if not bxr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not bxr.batch_id:
        raise ValueError("batch_id must be non-empty")

    for entry in bxr.candidate_explanations:
        if not entry.candidate_id:
            raise ValueError("candidate_id must be non-empty")
        if entry.selection_reason not in VALID_SELECTION_REASON_CATEGORIES:
            raise ValueError(
                f"selection_reason {entry.selection_reason!r} "
                f"not in VALID_SELECTION_REASON_CATEGORIES"
            )
        if entry.confidence_level not in VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"confidence_level {entry.confidence_level!r} "
                f"not in VALID_CONFIDENCE_LEVELS"
            )
        if not (-1.0 <= entry.predicted_score <= 1.0):
            raise ValueError(
                f"predicted_score must be in [-1.0, 1.0]: {entry.predicted_score}"
            )
        if not (-1.0 <= entry.uncertainty_score <= 1.0):
            raise ValueError(
                f"uncertainty_score must be in [-1.0, 1.0]: {entry.uncertainty_score}"
            )
        if len(entry.reason_notes) > 200:
            raise ValueError(
                f"reason_notes must be <= 200 chars: "
                f"got {len(entry.reason_notes)}"
            )

    if bxr.n_candidates != len(bxr.candidate_explanations):
        raise ValueError(
            f"n_candidates {bxr.n_candidates} != "
            f"len(candidate_explanations) {len(bxr.candidate_explanations)}"
        )

    expected_n_safety = sum(1 for e in bxr.candidate_explanations if e.safety_cleared)
    if bxr.n_safety_cleared != expected_n_safety:
        raise ValueError(
            f"n_safety_cleared {bxr.n_safety_cleared} != computed {expected_n_safety}"
        )

    if bxr.n_explained != bxr.n_safety_cleared:
        raise ValueError(
            f"n_explained {bxr.n_explained} must equal n_safety_cleared {bxr.n_safety_cleared}"
        )

    if bxr.n_candidates == 0:
        expected_explanation_fraction = 0.0
    else:
        expected_explanation_fraction = round(
            bxr.n_explained / bxr.n_candidates, 6
        )
    if abs(bxr.explanation_fraction - expected_explanation_fraction) > 0.01:
        raise ValueError(
            f"explanation_fraction {bxr.explanation_fraction} does not match "
            f"computed {expected_explanation_fraction}"
        )

    expected_exploit = sum(
        1 for e in bxr.candidate_explanations
        if e.selection_reason == "winner_exploit"
    )
    expected_exploit_fraction = round(
        expected_exploit / bxr.n_candidates, 6
    ) if bxr.n_candidates > 0 else 0.0
    if abs(bxr.exploit_fraction - expected_exploit_fraction) > 0.01:
        raise ValueError(
            f"exploit_fraction {bxr.exploit_fraction} != computed {expected_exploit_fraction}"
        )

    expected_probe = sum(
        1 for e in bxr.candidate_explanations
        if e.selection_reason == "uncertainty_probe"
    )
    expected_probe_fraction = round(
        expected_probe / bxr.n_candidates, 6
    ) if bxr.n_candidates > 0 else 0.0
    if abs(bxr.probe_fraction - expected_probe_fraction) > 0.01:
        raise ValueError(
            f"probe_fraction {bxr.probe_fraction} != computed {expected_probe_fraction}"
        )

    if bxr.verdict not in VALID_BXR_VERDICTS:
        raise ValueError(f"verdict {bxr.verdict!r} not in VALID_BXR_VERDICTS")

    expected_verdict = _compute_verdict(bxr.n_candidates, bxr.explanation_fraction)
    if bxr.verdict != expected_verdict:
        raise ValueError(
            f"verdict {bxr.verdict!r} does not match computed verdict "
            f"{expected_verdict!r}"
        )

    if not bxr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not bxr.limitations:
        raise ValueError("limitations must be non-empty")
    if not bxr.created_at:
        raise ValueError("created_at must be non-empty")


def build_batch_explanation_report(
    *,
    bxr_id: str,
    pipeline_version: str,
    batch_id: str,
    candidate_explanations: list[dict | CandidateExplanationEntry],
    limitations: list[str],
    created_at: str,
) -> BatchExplanationReport:
    """Build a BatchExplanationReport.

    candidate_explanations: list of dicts with keys:
        candidate_id (str), selection_reason (str),
        confidence_level (str), predicted_score (float),
        uncertainty_score (float), safety_cleared (bool),
        reason_notes (str, optional, default "")
    """
    entries = []
    for item in candidate_explanations:
        if isinstance(item, CandidateExplanationEntry):
            entries.append(item)
        else:
            d = item
            entries.append(
                CandidateExplanationEntry(
                    candidate_id=d["candidate_id"],
                    selection_reason=d["selection_reason"],
                    confidence_level=d["confidence_level"],
                    predicted_score=float(d["predicted_score"]),
                    uncertainty_score=float(d["uncertainty_score"]),
                    safety_cleared=bool(d["safety_cleared"]),
                    reason_notes=d.get("reason_notes", ""),
                )
            )

    n_candidates = len(entries)
    n_safety_cleared = sum(1 for e in entries if e.safety_cleared)
    n_explained = n_safety_cleared
    explanation_fraction = round(n_explained / n_candidates, 6) if n_candidates > 0 else 0.0
    exploit_fraction = round(
        sum(1 for e in entries if e.selection_reason == "winner_exploit") / n_candidates, 6
    ) if n_candidates > 0 else 0.0
    probe_fraction = round(
        sum(1 for e in entries if e.selection_reason == "uncertainty_probe") / n_candidates, 6
    ) if n_candidates > 0 else 0.0
    verdict = _compute_verdict(n_candidates, explanation_fraction)

    bxr = BatchExplanationReport(
        bxr_id=bxr_id,
        pipeline_version=pipeline_version,
        batch_id=batch_id,
        candidate_explanations=entries,
        n_candidates=n_candidates,
        n_explained=n_explained,
        n_safety_cleared=n_safety_cleared,
        exploit_fraction=exploit_fraction,
        probe_fraction=probe_fraction,
        explanation_fraction=explanation_fraction,
        verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_batch_explanation_report(bxr)
    return bxr


def format_batch_explanation_report(bxr: BatchExplanationReport) -> str:
    lines = [
        f"Batch Explanation Report — {bxr.bxr_id}",
        f"Pipeline: {bxr.pipeline_version}  |  Batch: {bxr.batch_id}",
        f"Verdict: {bxr.verdict}",
        f"Candidates: {bxr.n_candidates} total, "
        f"{bxr.n_safety_cleared} safety-cleared "
        f"({bxr.explanation_fraction:.1%} explained)",
        f"Exploit fraction: {bxr.exploit_fraction:.1%}  |  "
        f"Probe fraction: {bxr.probe_fraction:.1%}",
    ]
    if bxr.candidate_explanations:
        lines.append("Candidate explanations:")
        for entry in bxr.candidate_explanations:
            safety_flag = "CLEARED" if entry.safety_cleared else "NOT_CLEARED"
            lines.append(
                f"  {entry.candidate_id}: {entry.selection_reason} "
                f"(confidence={entry.confidence_level}, "
                f"score={entry.predicted_score:.3f}, "
                f"uncertainty={entry.uncertainty_score:.3f}, "
                f"safety={safety_flag})"
            )
            if entry.reason_notes:
                lines.append(f"    {entry.reason_notes}")
    lines.append(f"Created: {bxr.created_at}")
    lines.append(f"Limitations: {'; '.join(bxr.limitations)}")
    lines.append(f"dry_lab_only: {bxr.dry_lab_only}")
    return "\n".join(lines)
