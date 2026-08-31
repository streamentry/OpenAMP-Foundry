"""Pilot pre-registration schema — Phase E E5.

PRR- records freeze the candidate selection criteria, score thresholds, and
primary hypothesis BEFORE any wet-lab experiment begins. This prevents
post-hoc threshold adjustment to match results — the most common form of
silent overclaiming in computational-to-experimental pipelines.

A locked PRR- record is the pre-registration contract between the dry-lab
pipeline and the wet-lab team.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace


VALID_OUTCOME_METRICS: frozenset[str] = frozenset({
    "mic_reduction",
    "zone_of_inhibition",
    "minimum_inhibitory_concentration",
    "percent_viability",
    "auc_growth_curve",
    "colony_forming_units",
    "optical_density",
    "time_to_kill",
})

VALID_AMENDMENT_REASONS: frozenset[str] = frozenset({
    "clerical_error_correction",
    "scope_reduction",
    "control_substitution",
    "metric_clarification",
    "timeline_extension",
})


@dataclass
class ScoreThreshold:
    score_name: str
    threshold_value: float
    direction: str


@dataclass
class PilotPreregistration:
    record_id: str
    version: str
    frozen_at: str
    pipeline_version: str
    git_sha: str
    primary_hypothesis: str
    selection_criteria: list[str] = field(default_factory=list)
    score_thresholds: list[ScoreThreshold] = field(default_factory=list)
    n_candidates_planned: int = 0
    positive_control: str = ""
    negative_control: str = ""
    outcome_metric: str = ""
    dry_lab_only_declaration: bool = True
    is_locked: bool = False
    amendment_count: int = 0
    amendment_reasons: list[str] = field(default_factory=list)
    notes: str = ""
    freeze_sha256: str = ""


@dataclass
class PreregistrationValidationResult:
    is_valid: bool
    violations: list[str]
    warnings: list[str]
    record_id: str
    validation_summary: str


_SEMVER_RE = __import__("re").compile(r"^\d+\.\d+\.\d+$")
_GIT_SHA_RE = __import__("re").compile(r"^[a-f0-9]{7,40}$")
_SHA256_RE = __import__("re").compile(r"^[a-f0-9]{64}$")


def compute_pilot_preregistration_sha256(
    record: PilotPreregistration,
) -> str:
    """Compute the canonical integrity digest for a pre-registration.

    The digest covers every record field except freeze_sha256 itself. It binds
    the frozen selection criteria and thresholds to the exact structured
    record content, but it does not authenticate the person who approved it.
    """
    payload = {
        "record_id": record.record_id,
        "version": record.version,
        "frozen_at": record.frozen_at,
        "pipeline_version": record.pipeline_version,
        "git_sha": record.git_sha,
        "primary_hypothesis": record.primary_hypothesis,
        "selection_criteria": list(record.selection_criteria),
        "score_thresholds": [
            {
                "score_name": threshold.score_name,
                "threshold_value": threshold.threshold_value,
                "direction": threshold.direction,
            }
            for threshold in record.score_thresholds
        ],
        "n_candidates_planned": record.n_candidates_planned,
        "positive_control": record.positive_control,
        "negative_control": record.negative_control,
        "outcome_metric": record.outcome_metric,
        "dry_lab_only_declaration": record.dry_lab_only_declaration,
        "is_locked": record.is_locked,
        "amendment_count": record.amendment_count,
        "amendment_reasons": list(record.amendment_reasons),
        "notes": record.notes,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def lock_pilot_preregistration(
    record: PilotPreregistration,
) -> PilotPreregistration:
    """Return a locked copy of an editable draft with its content digest.

    The input record is never mutated. An already locked record is rejected so
    callers cannot silently re-freeze a record after its original digest was
    issued; amendments must be represented and reviewed separately.
    """
    if record.is_locked:
        raise ValueError(
            "cannot lock an already locked pre-registration; record an amendment"
        )
    locked = replace(record, is_locked=True, freeze_sha256="")
    return replace(
        locked,
        freeze_sha256=compute_pilot_preregistration_sha256(locked),
    )


def validate_pilot_preregistration(
    record: PilotPreregistration,
) -> PreregistrationValidationResult:
    """Validate a PilotPreregistration against PRR- schema rules.

    Returns a PreregistrationValidationResult with all violations.
    A record is valid only when violations is empty.
    """
    violations: list[str] = []
    warnings: list[str] = []

    # Rule 1: record_id prefix
    if not record.record_id.startswith("PRR-"):
        violations.append(
            f"record_id must start with 'PRR-', got '{record.record_id}'"
        )

    # Rule 2: version semver
    if not _SEMVER_RE.match(record.version):
        violations.append(
            f"version must be semver (X.Y.Z), got '{record.version}'"
        )

    # Rule 3: git_sha hex
    if not _GIT_SHA_RE.match(record.git_sha):
        violations.append(
            f"git_sha must be 7-40 lowercase hex chars, got '{record.git_sha}'"
        )

    # Rule 4: dry_lab_only_declaration must be True
    if not record.dry_lab_only_declaration:
        violations.append(
            "dry_lab_only_declaration must be True — "
            "pre-registration captures dry-lab selection logic only"
        )

    # Rule 5: selection_criteria non-empty
    if not record.selection_criteria:
        violations.append(
            "selection_criteria must contain at least one criterion"
        )

    # Rule 6: score_thresholds non-empty
    if not record.score_thresholds:
        violations.append(
            "score_thresholds must contain at least one threshold — "
            "thresholds must be declared before the experiment"
        )

    # Rule 7: n_candidates_planned >= 1
    if record.n_candidates_planned < 1:
        violations.append(
            f"n_candidates_planned must be >= 1, got {record.n_candidates_planned}"
        )

    # Rule 8: outcome_metric vocabulary
    if record.outcome_metric not in VALID_OUTCOME_METRICS:
        violations.append(
            f"outcome_metric must be one of {sorted(VALID_OUTCOME_METRICS)}, "
            f"got '{record.outcome_metric}'"
        )

    # Rule 9: primary_hypothesis not empty
    if not record.primary_hypothesis.strip():
        violations.append("primary_hypothesis must not be empty")

    # Rule 10: positive_control not empty
    if not record.positive_control.strip():
        violations.append(
            "positive_control must not be empty — "
            "a pre-registered experiment without a positive control cannot be interpreted"
        )

    # Rule 11: negative_control not empty
    if not record.negative_control.strip():
        violations.append(
            "negative_control must not be empty — "
            "a pre-registered experiment without a negative control cannot be interpreted"
        )

    # Rule 12: frozen_at not empty
    if not record.frozen_at.strip():
        violations.append("frozen_at must not be empty")

    # Rule 13: lock required before a record can be valid
    if not record.is_locked:
        violations.append(
            "is_locked must be True — selection criteria and thresholds must be "
            "frozen before any experiment begins"
        )
    elif not _SHA256_RE.fullmatch(record.freeze_sha256):
        violations.append(
            "freeze_sha256 must be a 64-character lowercase SHA-256 digest "
            "for a locked record"
        )
    elif record.freeze_sha256 != compute_pilot_preregistration_sha256(record):
        violations.append(
            "freeze_sha256 does not match the canonical pre-registration content"
        )

    # Rule 14: threshold values in [0, 1]
    for t in record.score_thresholds:
        if not (0.0 <= t.threshold_value <= 1.0):
            violations.append(
                f"score_thresholds[{t.score_name}].threshold_value must be in [0, 1], "
                f"got {t.threshold_value}"
            )

    # Rule 15: amendment_reasons vocabulary
    for reason in record.amendment_reasons:
        if reason not in VALID_AMENDMENT_REASONS:
            violations.append(
                f"amendment_reasons contains invalid entry '{reason}'. "
                f"Valid reasons: {sorted(VALID_AMENDMENT_REASONS)}"
            )

    # Warning: locked record with amendments
    if record.is_locked and record.amendment_count > 0:
        warnings.append(
            f"Record is locked with {record.amendment_count} amendment(s). "
            "Amendments after lock require human review."
        )

    is_valid = len(violations) == 0

    if is_valid:
        summary = (
            f"PRR- record '{record.record_id}' is valid: "
            f"{record.n_candidates_planned} candidate(s) planned, "
            f"outcome_metric='{record.outcome_metric}', "
            f"locked={record.is_locked}."
        )
    else:
        summary = (
            f"PRR- record '{record.record_id}' has {len(violations)} violation(s). "
            "Fix all violations before beginning any wet-lab experiment."
        )

    return PreregistrationValidationResult(
        is_valid=is_valid,
        violations=violations,
        warnings=warnings,
        record_id=record.record_id,
        validation_summary=summary,
    )


def format_pilot_preregistration(record: PilotPreregistration) -> str:
    """Format a PilotPreregistration as a human-readable string."""
    result = validate_pilot_preregistration(record)
    lines = [
        "=== PILOT PRE-REGISTRATION RECORD ===",
        f"Record ID: {record.record_id}",
        f"Version: {record.version}",
        f"Frozen at: {record.frozen_at}",
        f"Pipeline: {record.pipeline_version} ({record.git_sha})",
        f"Locked: {'YES' if record.is_locked else 'NO'}",
        f"Amendment count: {record.amendment_count}",
        "",
        "-- HYPOTHESIS --",
        f"  {record.primary_hypothesis}",
        "",
        "-- SELECTION CRITERIA --",
    ]
    for criterion in record.selection_criteria:
        lines.append(f"  • {criterion}")
    lines.extend(["", "-- SCORE THRESHOLDS (frozen) --"])
    for t in record.score_thresholds:
        lines.append(f"  {t.score_name}: {t.threshold_value:.4f} ({t.direction})")
    lines.extend([
        "",
        "-- EXPERIMENT DESIGN --",
        f"  Candidates planned: {record.n_candidates_planned}",
        f"  Outcome metric: {record.outcome_metric}",
        f"  Positive control: {record.positive_control}",
        f"  Negative control: {record.negative_control}",
        f"  Dry-lab only declaration: {'YES' if record.dry_lab_only_declaration else 'NO'}",
        "",
        "-- VALIDATION --",
    ])
    if result.is_valid:
        lines.append("  STATUS: VALID")
    else:
        lines.append(f"  STATUS: INVALID ({len(result.violations)} violation(s))")
        for v in result.violations:
            lines.append(f"  ✗ {v}")
    if result.warnings:
        lines.append("")
        for w in result.warnings:
            lines.append(f"  ⚠ {w}")
    lines.extend(["", result.validation_summary])
    if not result.is_valid:
        lines.extend([
            "",
            "NOTICE: Do not begin any wet-lab experiment until all violations are resolved.",
            "A valid, locked PRR- record is required before experiment start.",
        ])
    return "\n".join(lines)
