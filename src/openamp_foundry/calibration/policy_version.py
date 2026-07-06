"""Policy version tracking for recalibration policy.

Every recalibration event must:
1. Have a higher ``policy_version`` than the previously committed policy.
2. Preserve all ``locked_changes`` entries from the previous version.
3. Have a dated decision-log entry within the last 30 days.

CI guard: When ``configs/recalibration_policy.yaml`` changes in a PR, run
``validate_policy_version()`` to ensure none of the above rules are violated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .policy import RecalibrationPolicy


class VersionValidationError(ValueError):
    """Raised when policy version validation fails."""

    def __init__(self, *reasons: str) -> None:
        self.reasons = list(reasons)
        msg = "; ".join(reasons) if reasons else "Policy version validation failed"
        super().__init__(msg)


@dataclass(frozen=True)
class VersionValidation:
    """Result of validating a policy version against its predecessor."""

    passed: bool
    version_valid: bool
    locked_changes_preserved: bool
    decision_log_valid: bool
    reasons: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.passed


_DECISION_LOG_PATTERN = re.compile(r"DECISION_LOG_(\d{4}-\d{2}-\d{2})\.md$")


def _parse_decision_log_date(path: Path) -> date | None:
    """Extract the date from a decision-log filename like DECISION_LOG_2026-07-05.md."""
    m = _DECISION_LOG_PATTERN.match(path.name)
    if m is None:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def _find_latest_decision_log(decision_log_dir: str | Path) -> Path | None:
    """Find the most recent decision-log file in a directory.

    Looks for files matching ``DECISION_LOG_<YYYY-MM-DD>.md`` and returns
    the one with the latest date. Returns None if none found.
    """
    d = Path(decision_log_dir)
    if not d.is_dir():
        return None
    best: tuple[date, Path] | None = None
    for f in d.iterdir():
        if not f.is_file():
            continue
        log_date = _parse_decision_log_date(f)
        if log_date is not None:
            if best is None or log_date > best[0]:
                best = (log_date, f)
    return best[1] if best is not None else None


def _locked_change_ids(policy: RecalibrationPolicy) -> set[str]:
    return {lc.rule_id for lc in policy.locked_changes}


def validate_policy_version(
    current_policy: RecalibrationPolicy,
    previous_policy: RecalibrationPolicy,
    decision_log_dir: str | Path | None = None,
    today: str | None = None,
) -> VersionValidation:
    """Validate a policy version against its predecessor.

    Checks:
    1. ``current_policy.policy_version > previous_policy.policy_version``
       (must be strictly higher).
    2. All ``locked_changes`` entries from *previous* are still present
       in *current* — ensures locked rules have not been silently removed.
    3. If ``decision_log_dir`` is provided, the latest decision-log file
       is dated within 30 days of ``today`` (default: today's date).

    Args:
        current_policy: The proposed new policy.
        previous_policy: The previously committed policy.
        decision_log_dir: Optional directory to scan for decision-log files.
        today: ISO date string (YYYY-MM-DD) for "today". Defaults to
            ``datetime.date.today().isoformat()``.

    Returns:
        A ``VersionValidation`` with per-check status and reasons.
    """
    reasons: list[str] = []
    version_valid = True
    locked_ok = True
    log_valid = True

    # 1. Version must be strictly higher.
    if current_policy.policy_version <= previous_policy.policy_version:
        version_valid = False
        reasons.append(
            f"policy_version must increase: {current_policy.policy_version} <= "
            f"{previous_policy.policy_version}"
        )

    # 2. All previous locked_changes must be preserved.
    prev_locked = _locked_change_ids(previous_policy)
    curr_locked = _locked_change_ids(current_policy)
    removed = prev_locked - curr_locked
    if removed:
        locked_ok = False
        reasons.append(
            f"locked_changes removed (not present in current policy): "
            f"{', '.join(sorted(removed))}"
        )

    # 3. Decision-log entry within 30 days.
    if decision_log_dir is not None:
        log_path = _find_latest_decision_log(str(decision_log_dir))
        if log_path is None:
            log_valid = False
            reasons.append(
                f"No decision-log file (DECISION_LOG_<date>.md) found "
                f"in {decision_log_dir}"
            )
        else:
            log_date = _parse_decision_log_date(log_path)
            assert log_date is not None
            ref_date: date
            if today is not None:
                ref_date = datetime.strptime(today, "%Y-%m-%d").date()
            else:
                ref_date = date.today()
            if log_date < ref_date - timedelta(days=30):
                log_valid = False
                reasons.append(
                    f"Latest decision log ({log_path.name}) dated {log_date} "
                    f"is more than 30 days before reference date {ref_date}"
                )
            if log_date > ref_date:
                log_valid = False
                reasons.append(
                    f"Latest decision log ({log_path.name}) dated {log_date} "
                    f"is in the future relative to reference date {ref_date}"
                )

    passed = version_valid and locked_ok and log_valid
    return VersionValidation(
        passed=passed,
        version_valid=version_valid,
        locked_changes_preserved=locked_ok,
        decision_log_valid=log_valid,
        reasons=tuple(reasons),
    )


def auto_increment_version(
    current_policy: RecalibrationPolicy,
    new_locked_at: str,
    new_reviewer: str,
    policy_dir: str | Path | None = None,
) -> dict:
    """Produce a new policy YAML dict with ``policy_version`` +1 and updated metadata.

    The returned dict can be written back to the YAML file to finalize
    the version bump. It preserves all existing fields and only changes
    ``policy_version``, ``locked_at``, and ``human_reviewer``.

    Args:
        current_policy: The policy to bump.
        new_locked_at: ISO 8601 date string for ``locked_at``.
        new_reviewer: Human-readable reviewer name for ``human_reviewer``.
        policy_dir: If provided, adjust ``source_path`` to find the YAML.

    Returns:
        A dict matching the YAML structure with version +1.
    """
    source_path = current_policy.source_path
    if policy_dir is not None:
        source_path = Path(policy_dir) / source_path.name

    raw = _yaml_dict_from_policy(current_policy, source_path)
    raw["policy_version"] = current_policy.policy_version + 1
    raw["locked_at"] = new_locked_at
    raw["human_reviewer"] = new_reviewer
    return raw


def _yaml_dict_from_policy(policy: RecalibrationPolicy, source_path: Path) -> dict:
    """Reconstruct a YAML-serialisable dict from a RecalibrationPolicy.

    Uses the original YAML file as source when available (preserves
    comments and formatting). Otherwise constructs a minimal dict.
    """
    import yaml

    try:
        with open(source_path) as f:
            raw = yaml.safe_load(f)
        if isinstance(raw, dict):
            return raw
    except (FileNotFoundError, yaml.YAMLError, OSError):
        pass

    raw: dict = {}
    raw["policy_version"] = policy.policy_version
    raw["locked_at"] = policy.locked_at
    raw["human_reviewer"] = policy.human_reviewer
    raw["minimum_conditions"] = [
        {
            "id": r.id,
            "description": r.description,
            "threshold": r.threshold,
            "applies_to": r.applies_to,
            "rationale": r.rationale,
        }
        for r in policy.minimum_conditions
    ]
    raw["prohibited_actions"] = [
        {"id": a.id, "description": a.description, "rationale": a.rationale}
        for a in policy.prohibited_actions
    ]
    raw["rate_limits"] = [
        {
            "id": r.id,
            "description": r.description,
            "threshold": r.threshold,
            "applies_to": r.applies_to,
            "rationale": r.rationale,
        }
        for r in policy.rate_limits
    ]
    raw["required_reviewer_artefacts"] = [
        {
            "id": a.id,
            "description": a.description,
            "expected_path": a.expected_path,
            "kind": a.kind,
        }
        for a in policy.required_reviewer_artefacts
    ]
    raw["locked_changes"] = [
        {"rule_id": c.rule_id, "locked_at": c.locked_at, "reason": c.reason}
        for c in policy.locked_changes
    ]
    raw["notes"] = list(policy.notes)
    return raw
