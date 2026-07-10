"""WEA- wet-lab evidence annotation schema.

Annotates a dry-lab computational prediction with its corresponding wet-lab
outcome.  Closes the feedback loop: every computational prediction that gets
a wet-lab result must be annotated so the pipeline can learn from both
successes and failures.

The annotation record is computational (dry_lab_only=True) — it contains no
raw wet-lab data, only a comparison between the dry-lab prediction and the
WHR- wet-lab hit record.  The WHR- itself holds the actual experimental data.

This makes the prediction-vs-outcome comparison machine-checkable:
  - prediction_confirmed: dry-lab correctly predicted the activity label.
  - prediction_refuted: dry-lab got it wrong.
  - prediction_inconclusive: one or both labels were inconclusive.
  - no_wet_lab_comparison_possible: insufficient data for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_PREDICTION_OUTCOMES: frozenset[str] = frozenset({
    "prediction_confirmed",
    "prediction_refuted",
    "prediction_inconclusive",
    "no_wet_lab_comparison_possible",
})

VALID_ACTIVITY_LABELS: frozenset[str] = frozenset({
    "active",
    "inactive",
    "inconclusive",
    "not_tested",
})

INCONCLUSIVE_LABELS: frozenset[str] = frozenset({"inconclusive", "not_tested"})


@dataclass
class WetlabEvidenceAnnotation:
    wea_id: str
    dry_lab_artifact_id: str
    whr_id: str
    pipeline_version: str
    dry_lab_predicted_activity: str
    wetlab_observed_activity: str
    prediction_outcome: str
    is_preliminary_wet_lab: bool
    is_example_data: bool
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_wetlab_evidence_annotation(wea: WetlabEvidenceAnnotation) -> None:
    if not wea.wea_id.startswith("WEA-"):
        raise ValueError(f"wea_id must start with 'WEA-': {wea.wea_id!r}")
    if not wea.dry_lab_artifact_id:
        raise ValueError("dry_lab_artifact_id must be non-empty")
    if not wea.whr_id.startswith("WHR-"):
        raise ValueError(f"whr_id must start with 'WHR-': {wea.whr_id!r}")
    if not wea.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if wea.dry_lab_predicted_activity not in VALID_ACTIVITY_LABELS:
        raise ValueError(
            f"dry_lab_predicted_activity {wea.dry_lab_predicted_activity!r} "
            f"not in VALID_ACTIVITY_LABELS"
        )
    if wea.wetlab_observed_activity not in VALID_ACTIVITY_LABELS:
        raise ValueError(
            f"wetlab_observed_activity {wea.wetlab_observed_activity!r} "
            f"not in VALID_ACTIVITY_LABELS"
        )
    if wea.prediction_outcome not in VALID_PREDICTION_OUTCOMES:
        raise ValueError(
            f"prediction_outcome {wea.prediction_outcome!r} not in VALID_PREDICTION_OUTCOMES"
        )
    expected = _compute_outcome(
        wea.dry_lab_predicted_activity, wea.wetlab_observed_activity
    )
    if wea.prediction_outcome != expected:
        raise ValueError(
            f"prediction_outcome {wea.prediction_outcome!r} inconsistent with "
            f"predicted={wea.dry_lab_predicted_activity!r}, "
            f"observed={wea.wetlab_observed_activity!r} (expected {expected!r})"
        )
    if not wea.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not wea.limitations:
        raise ValueError("limitations must be non-empty")
    if not wea.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_outcome(predicted: str, observed: str) -> str:
    if predicted in INCONCLUSIVE_LABELS or observed in INCONCLUSIVE_LABELS:
        return "prediction_inconclusive"
    if predicted == observed:
        return "prediction_confirmed"
    return "prediction_refuted"


def build_wetlab_evidence_annotation(
    *,
    wea_id: str,
    dry_lab_artifact_id: str,
    whr_id: str,
    pipeline_version: str,
    dry_lab_predicted_activity: str,
    wetlab_observed_activity: str,
    is_preliminary_wet_lab: bool = True,
    is_example_data: bool = False,
    limitations: list[str],
    created_at: str,
) -> WetlabEvidenceAnnotation:
    """Build a WetlabEvidenceAnnotation.

    prediction_outcome is auto-computed from dry_lab_predicted_activity
    and wetlab_observed_activity.
    """
    outcome = _compute_outcome(dry_lab_predicted_activity, wetlab_observed_activity)
    wea = WetlabEvidenceAnnotation(
        wea_id=wea_id,
        dry_lab_artifact_id=dry_lab_artifact_id,
        whr_id=whr_id,
        pipeline_version=pipeline_version,
        dry_lab_predicted_activity=dry_lab_predicted_activity,
        wetlab_observed_activity=wetlab_observed_activity,
        prediction_outcome=outcome,
        is_preliminary_wet_lab=is_preliminary_wet_lab,
        is_example_data=is_example_data,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_wetlab_evidence_annotation(wea)
    return wea


def format_wetlab_evidence_annotation(wea: WetlabEvidenceAnnotation) -> str:
    lines = [
        f"Wet-lab Evidence Annotation — {wea.wea_id}",
        f"Dry-lab artifact: {wea.dry_lab_artifact_id}  |  WHR: {wea.whr_id}",
        f"Pipeline: {wea.pipeline_version}",
        f"Predicted: {wea.dry_lab_predicted_activity}  "
        f"Observed: {wea.wetlab_observed_activity}",
        f"Outcome: {wea.prediction_outcome}",
        f"Preliminary wet-lab: {wea.is_preliminary_wet_lab}",
        f"Example data: {wea.is_example_data}",
        f"Limitations: {'; '.join(wea.limitations)}",
        f"Created: {wea.created_at}",
        f"dry_lab_only: {wea.dry_lab_only}",
    ]
    return "\n".join(lines)
