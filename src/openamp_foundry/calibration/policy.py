"""Pre-registered recalibration policy loader and validator.

This module is the MACHINE-READABLE CONTRACT that gates any pipeline
recalibration. The accompanying YAML file
``configs/recalibration_policy.yaml`` is the human-authored source of
truth; this module loads, schema-checks, and exposes its rules so that
the ``recalibration_gate`` module can evaluate intake reports against
the policy without silently bypassing it.

Honesty rules (encoded both in the YAML and enforced here):

* ``minimum_conditions`` are required. Every ``id`` listed in
  ``minimum_conditions`` must also appear in ``locked_changes`` or the
  policy file is rejected.
* ``prohibited_actions`` are permanent. Their ``id``s are required to
  be present and cannot be removed without bumping ``policy_version``
  AND recording a human decision log entry. The validator rejects a
  policy file whose prohibited_actions list shrinks compared to the
  canonical baseline (see ``_CANONICAL_PROHIBITED_ACTIONS`` below).
* ``locked_changes`` lists every rule whose presence is enforced. A
  missing entry causes the policy to be rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# Permanent baseline of prohibited actions. These cannot be removed
# from any future policy file without bumping policy_version and
# rewriting this list together with the policy file. They mirror the
# non-negotiable safety floors in AGENTS.md / MISSION.md.
_CANONICAL_PROHIBITED_ACTIONS: tuple[str, ...] = (
    "NO_TOXICITY_RELAXATION",
    "NO_HEMOLYSIS_RELAXATION",
    "NO_NOVELTY_RELAXATION",
    "NO_DANGEROUS_PATHGEN_OPTIMIZATION",
    "NO_POST_HOC_SUCCESS_REDEFINITION",
)


@dataclass(frozen=True)
class PolicyRule:
    """A single rule in the recalibration policy."""

    id: str
    description: str
    threshold: Any
    applies_to: str
    rationale: str


@dataclass(frozen=True)
class ProhibitedAction:
    """A permanent floor that any recalibration must respect."""

    id: str
    description: str
    rationale: str


@dataclass(frozen=True)
class RateLimit:
    """A soft cap on recalibration cadence or magnitude."""

    id: str
    description: str
    threshold: Any
    applies_to: str
    rationale: str


@dataclass(frozen=True)
class ReviewerArtefact:
    """An artefact a human reviewer must produce for a recalibration to be considered valid."""

    id: str
    description: str
    expected_path: str
    kind: str


@dataclass(frozen=True)
class LockedChange:
    """A change-record entry that the policy file must preserve."""

    rule_id: str
    locked_at: str
    reason: str


@dataclass(frozen=True)
class RecalibrationPolicy:
    """The full recalibration policy loaded from YAML."""

    policy_version: int
    locked_at: str
    human_reviewer: str
    minimum_conditions: tuple[PolicyRule, ...]
    prohibited_actions: tuple[ProhibitedAction, ...]
    rate_limits: tuple[RateLimit, ...]
    required_reviewer_artefacts: tuple[ReviewerArtefact, ...]
    locked_changes: tuple[LockedChange, ...]
    notes: tuple[str, ...]
    source_path: Path

    def rule_by_id(self, rule_id: str) -> PolicyRule | None:
        """Return the minimum_condition rule with this id, or None."""

        for rule in self.minimum_conditions:
            if rule.id == rule_id:
                return rule
        return None

    def prohibited_by_id(self, action_id: str) -> ProhibitedAction | None:
        """Return the prohibited_action with this id, or None."""

        for action in self.prohibited_actions:
            if action.id == action_id:
                return action
        return None

    def is_locked(self, rule_id: str) -> bool:
        """Return True if rule_id appears in locked_changes."""

        return any(change.rule_id == rule_id for change in self.locked_changes)


class PolicyLoadError(ValueError):
    """Raised when a policy file fails validation."""


def _require(cond: bool, msg: str) -> None:
    """Raise PolicyLoadError if cond is False."""

    if not cond:
        raise PolicyLoadError(msg)


def _as_str(value: Any, field_name: str) -> str:
    """Coerce value to str or raise."""

    if not isinstance(value, str):
        raise PolicyLoadError(
            f"{field_name!r} must be a string, got {type(value).__name__}"
        )
    return value


def _as_int(value: Any, field_name: str) -> int:
    """Coerce value to int or raise."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise PolicyLoadError(
            f"{field_name!r} must be an integer, got {type(value).__name__}"
        )
    return value


def _as_float_or_int(value: Any, field_name: str) -> float | int:
    """Coerce value to a numeric scalar or raise."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PolicyLoadError(
            f"{field_name!r} must be numeric, got {type(value).__name__}"
        )
    return value


def _as_bool(value: Any, field_name: str) -> bool:
    """Coerce value to bool or raise."""

    if not isinstance(value, bool):
        raise PolicyLoadError(
            f"{field_name!r} must be a boolean, got {type(value).__name__}"
        )
    return value


def _parse_rules(raw: Any, label: str) -> tuple[PolicyRule, ...]:
    """Parse the minimum_conditions block."""

    _require(isinstance(raw, list), f"{label!r} must be a list")
    parsed: list[PolicyRule] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw):
        _require(isinstance(entry, dict), f"{label}[{i}] must be a mapping")
        rid = _as_str(entry.get("id"), f"{label}[{i}].id")
        _require(rid not in seen_ids, f"{label} contains duplicate id: {rid!r}")
        seen_ids.add(rid)
        threshold = entry.get("threshold")
        _require(
            threshold is not None,
            f"{label}[{i}].threshold is required",
        )
        parsed.append(
            PolicyRule(
                id=rid,
                description=_as_str(entry.get("description"), f"{label}[{i}].description"),
                threshold=threshold,
                applies_to=_as_str(entry.get("applies_to"), f"{label}[{i}].applies_to"),
                rationale=_as_str(entry.get("rationale"), f"{label}[{i}].rationale"),
            )
        )
    return tuple(parsed)


def _parse_prohibited(raw: Any) -> tuple[ProhibitedAction, ...]:
    """Parse the prohibited_actions block."""

    _require(isinstance(raw, list), "'prohibited_actions' must be a list")
    parsed: list[ProhibitedAction] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw):
        _require(isinstance(entry, dict), f"prohibited_actions[{i}] must be a mapping")
        aid = _as_str(entry.get("id"), f"prohibited_actions[{i}].id")
        _require(aid not in seen_ids, f"prohibited_actions contains duplicate id: {aid!r}")
        seen_ids.add(aid)
        parsed.append(
            ProhibitedAction(
                id=aid,
                description=_as_str(
                    entry.get("description"), f"prohibited_actions[{i}].description"
                ),
                rationale=_as_str(
                    entry.get("rationale"), f"prohibited_actions[{i}].rationale"
                ),
            )
        )
    return tuple(parsed)


def _parse_rate_limits(raw: Any) -> tuple[RateLimit, ...]:
    """Parse the rate_limits block."""

    _require(isinstance(raw, list), "'rate_limits' must be a list")
    parsed: list[RateLimit] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw):
        _require(isinstance(entry, dict), f"rate_limits[{i}] must be a mapping")
        rid = _as_str(entry.get("id"), f"rate_limits[{i}].id")
        _require(rid not in seen_ids, f"rate_limits contains duplicate id: {rid!r}")
        seen_ids.add(rid)
        threshold = entry.get("threshold")
        _require(threshold is not None, f"rate_limits[{i}].threshold is required")
        parsed.append(
            RateLimit(
                id=rid,
                description=_as_str(entry.get("description"), f"rate_limits[{i}].description"),
                threshold=threshold,
                applies_to=_as_str(entry.get("applies_to"), f"rate_limits[{i}].applies_to"),
                rationale=_as_str(entry.get("rationale"), f"rate_limits[{i}].rationale"),
            )
        )
    return tuple(parsed)


def _parse_reviewer_artefacts(raw: Any) -> tuple[ReviewerArtefact, ...]:
    """Parse the required_reviewer_artefacts block."""

    _require(isinstance(raw, list), "'required_reviewer_artefacts' must be a list")
    parsed: list[ReviewerArtefact] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw):
        _require(isinstance(entry, dict), f"required_reviewer_artefacts[{i}] must be a mapping")
        rid = _as_str(entry.get("id"), f"required_reviewer_artefacts[{i}].id")
        _require(
            rid not in seen_ids,
            f"required_reviewer_artefacts contains duplicate id: {rid!r}",
        )
        seen_ids.add(rid)
        parsed.append(
            ReviewerArtefact(
                id=rid,
                description=_as_str(
                    entry.get("description"),
                    f"required_reviewer_artefacts[{i}].description",
                ),
                expected_path=_as_str(
                    entry.get("expected_path"),
                    f"required_reviewer_artefacts[{i}].expected_path",
                ),
                kind=_as_str(
                    entry.get("kind"),
                    f"required_reviewer_artefacts[{i}].kind",
                ),
            )
        )
    return tuple(parsed)


def _parse_locked_changes(raw: Any) -> tuple[LockedChange, ...]:
    """Parse the locked_changes block."""

    _require(isinstance(raw, list), "'locked_changes' must be a list")
    parsed: list[LockedChange] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw):
        _require(isinstance(entry, dict), f"locked_changes[{i}] must be a mapping")
        rid = _as_str(entry.get("rule_id"), f"locked_changes[{i}].rule_id")
        _require(rid not in seen_ids, f"locked_changes contains duplicate rule_id: {rid!r}")
        seen_ids.add(rid)
        parsed.append(
            LockedChange(
                rule_id=rid,
                locked_at=_as_str(
                    entry.get("locked_at"), f"locked_changes[{i}].locked_at"
                ),
                reason=_as_str(
                    entry.get("reason"), f"locked_changes[{i}].reason"
                ),
            )
        )
    return tuple(parsed)


def load_recalibration_policy(path: str | Path) -> RecalibrationPolicy:
    """Load and validate a recalibration policy file.

    Args:
        path: Path to the policy YAML file.

    Returns:
        A validated RecalibrationPolicy.

    Raises:
        PolicyLoadError: if the file is missing required fields, has
            duplicate ids, or attempts to remove a canonical
            prohibited_action.
    """

    p = Path(path)
    _require(p.exists(), f"policy file does not exist: {p}")

    with p.open() as f:
        raw = yaml.safe_load(f)
    _require(isinstance(raw, dict), "policy root must be a mapping")

    policy_version = _as_int(raw.get("policy_version"), "policy_version")
    _require(policy_version >= 1, "policy_version must be >= 1")
    locked_at = _as_str(raw.get("locked_at"), "locked_at")
    human_reviewer = _as_str(raw.get("human_reviewer"), "human_reviewer")

    minimum_conditions = _parse_rules(
        raw.get("minimum_conditions", []), "minimum_conditions"
    )
    prohibited_actions = _parse_prohibited(raw.get("prohibited_actions", []))
    rate_limits = _parse_rate_limits(raw.get("rate_limits", []))
    reviewer_artefacts = _parse_reviewer_artefacts(
        raw.get("required_reviewer_artefacts", [])
    )
    locked_changes = _parse_locked_changes(raw.get("locked_changes", []))

    # Enforce that every minimum_condition rule is also locked.
    locked_rule_ids = {change.rule_id for change in locked_changes}
    for rule in minimum_conditions:
        _require(
            rule.id in locked_rule_ids,
            f"minimum_condition rule {rule.id!r} is not present in locked_changes",
        )

    # Enforce that the canonical prohibited_actions are all present.
    present_prohibited = {action.id for action in prohibited_actions}
    for canonical in _CANONICAL_PROHIBITED_ACTIONS:
        _require(
            canonical in present_prohibited,
            (
                f"prohibited_action {canonical!r} is missing from policy file. "
                "This is a permanent safety floor and cannot be removed."
            ),
        )

    # Enforce that each prohibited_action is locked.
    for action in prohibited_actions:
        _require(
            action.id in locked_rule_ids,
            f"prohibited_action {action.id!r} is not present in locked_changes",
        )

    notes_raw = raw.get("notes", [])
    _require(isinstance(notes_raw, list), "'notes' must be a list")
    notes: list[str] = []
    for i, n in enumerate(notes_raw):
        _require(isinstance(n, str), f"notes[{i}] must be a string")
        notes.append(n)

    return RecalibrationPolicy(
        policy_version=policy_version,
        locked_at=locked_at,
        human_reviewer=human_reviewer,
        minimum_conditions=minimum_conditions,
        prohibited_actions=prohibited_actions,
        rate_limits=rate_limits,
        required_reviewer_artefacts=reviewer_artefacts,
        locked_changes=locked_changes,
        notes=tuple(notes),
        source_path=p,
    )


def canonical_prohibited_action_ids() -> tuple[str, ...]:
    """Return the immutable tuple of canonical prohibited-action ids."""

    return _CANONICAL_PROHIBITED_ACTIONS
