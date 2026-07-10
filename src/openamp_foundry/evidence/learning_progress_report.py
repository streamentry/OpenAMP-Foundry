"""LPR- learning progress report schema.

Human-readable summary of what the pipeline has learned from all batches to
date. References a CIT- tracker for trend data, lists which candidate feature
categories proved predictive vs not, and links to calibration decision logs.
Gives a scientist a single document to understand the pipeline's learning
trajectory.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_LPR_VERDICTS: frozenset[str] = frozenset({
    "learning_confirmed",
    "learning_inconclusive",
    "no_learning_signal",
    "insufficient_data",
})

VALID_FEATURE_PREDICTIVITY: frozenset[str] = frozenset({
    "predictive",
    "not_predictive",
    "uncertain",
})

VALID_FEATURE_CATEGORIES: frozenset[str] = frozenset({
    "charge",
    "hydrophobicity",
    "length",
    "amphipathicity",
    "helicity",
    "sequence_motif",
    "secondary_structure",
    "physicochemical_composite",
})


@dataclass
class FeatureLearningEntry:
    feature_category: str
    predictivity: str
    evidence_summary: str


@dataclass
class LearningProgressReport:
    lpr_id: str
    pipeline_version: str
    cit_id: str
    n_batches_summarized: int
    feature_entries: list[FeatureLearningEntry]
    n_predictive_features: int
    n_non_predictive_features: int
    lpr_verdict: str
    key_findings: list[str]
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_learning_progress_report(lpr: LearningProgressReport) -> None:
    if not lpr.lpr_id.startswith("LPR-"):
        raise ValueError(f"lpr_id must start with 'LPR-': {lpr.lpr_id!r}")
    if not lpr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not lpr.cit_id.startswith("CIT-"):
        raise ValueError(f"cit_id must start with 'CIT-': {lpr.cit_id!r}")
    if lpr.n_batches_summarized < 0:
        raise ValueError("n_batches_summarized must be non-negative")
    for entry in lpr.feature_entries:
        if entry.feature_category not in VALID_FEATURE_CATEGORIES:
            raise ValueError(
                f"feature_category {entry.feature_category!r} not in VALID_FEATURE_CATEGORIES"
            )
        if entry.predictivity not in VALID_FEATURE_PREDICTIVITY:
            raise ValueError(
                f"predictivity {entry.predictivity!r} not in VALID_FEATURE_PREDICTIVITY"
            )
    n_pred = sum(1 for e in lpr.feature_entries if e.predictivity == "predictive")
    n_non = sum(1 for e in lpr.feature_entries if e.predictivity == "not_predictive")
    if lpr.n_predictive_features != n_pred:
        raise ValueError("n_predictive_features mismatch")
    if lpr.n_non_predictive_features != n_non:
        raise ValueError("n_non_predictive_features mismatch")
    if lpr.lpr_verdict not in VALID_LPR_VERDICTS:
        raise ValueError(
            f"lpr_verdict {lpr.lpr_verdict!r} not in VALID_LPR_VERDICTS"
        )
    if not lpr.key_findings:
        raise ValueError("key_findings must be non-empty")
    if not lpr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not lpr.limitations:
        raise ValueError("limitations must be non-empty")
    if not lpr.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    n_batches: int,
    n_predictive: int,
    n_non_predictive: int,
) -> str:
    if n_batches == 0:
        return "insufficient_data"
    if n_predictive == 0 and n_non_predictive == 0:
        return "insufficient_data"
    if n_predictive > n_non_predictive:
        return "learning_confirmed"
    if n_predictive == n_non_predictive and n_predictive > 0:
        return "learning_inconclusive"
    return "no_learning_signal"


def build_learning_progress_report(
    *,
    lpr_id: str,
    pipeline_version: str,
    cit_id: str,
    n_batches_summarized: int,
    feature_entry_dicts: list[dict],
    key_findings: list[str],
    limitations: list[str],
    created_at: str,
) -> LearningProgressReport:
    """Build a LearningProgressReport.

    feature_entry_dicts: list of dicts with keys:
        feature_category, predictivity, evidence_summary (optional, default "")
    """
    entries = [
        FeatureLearningEntry(
            feature_category=d["feature_category"],
            predictivity=d["predictivity"],
            evidence_summary=d.get("evidence_summary", ""),
        )
        for d in feature_entry_dicts
    ]
    n_pred = sum(1 for e in entries if e.predictivity == "predictive")
    n_non = sum(1 for e in entries if e.predictivity == "not_predictive")
    verdict = _compute_verdict(n_batches_summarized, n_pred, n_non)
    lpr = LearningProgressReport(
        lpr_id=lpr_id,
        pipeline_version=pipeline_version,
        cit_id=cit_id,
        n_batches_summarized=n_batches_summarized,
        feature_entries=entries,
        n_predictive_features=n_pred,
        n_non_predictive_features=n_non,
        lpr_verdict=verdict,
        key_findings=list(key_findings),
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_learning_progress_report(lpr)
    return lpr


def format_learning_progress_report(lpr: LearningProgressReport) -> str:
    lines = [
        f"Learning Progress Report — {lpr.lpr_id}",
        f"Pipeline: {lpr.pipeline_version}  |  CIT: {lpr.cit_id}",
        f"Verdict: {lpr.lpr_verdict}",
        f"Batches summarized: {lpr.n_batches_summarized}",
        f"Features: {lpr.n_predictive_features} predictive, "
        f"{lpr.n_non_predictive_features} not predictive",
    ]
    if lpr.feature_entries:
        lines.append("Feature categories:")
        for entry in lpr.feature_entries:
            lines.append(f"  {entry.feature_category}: {entry.predictivity}")
    lines.append("Key findings:")
    for finding in lpr.key_findings:
        lines.append(f"  - {finding}")
    lines.append(f"Created: {lpr.created_at}")
    lines.append(f"Limitations: {'; '.join(lpr.limitations)}")
    lines.append(f"dry_lab_only: {lpr.dry_lab_only}")
    return "\n".join(lines)
