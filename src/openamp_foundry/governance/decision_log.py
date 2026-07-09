"""Governance decision log validator.

Ensures all governance decisions have required fields before being added.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_SCOPES: set[str] = {
    "safety", "benchmark", "release", "evidence", "data", "adapter", "contribution", "docs"
}

VALID_STATUSES: set[str] = {
    "active", "superseded", "under_review", "proposed"
}

VALID_REVIEW_CLASSES: set[str] = {"A", "B", "C", "D"}


@dataclass
class GovernanceDecision:
    decision_id: str        # e.g. "GOV-001"
    date: str               # YYYY-MM-DD
    scope: str              # from VALID_SCOPES
    decision: str           # one-sentence summary
    status: str             # from VALID_STATUSES
    rationale: str          # why this decision was made
    review_class: str       # from VALID_REVIEW_CLASSES
    dry_lab_only: bool = True


@dataclass
class DecisionValidationResult:
    decision_id: str
    passed: bool
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


# Canonical log of current governance decisions
GOVERNANCE_DECISIONS: list[GovernanceDecision] = [
    GovernanceDecision(
        decision_id="GOV-001",
        date="2026-07-01",
        scope="safety",
        decision="All artifacts must have dry_lab_only=True; computational outputs are not biological proof.",
        status="active",
        rationale="Prevents overclaiming computational results as wet-lab evidence.",
        review_class="D",
    ),
    GovernanceDecision(
        decision_id="GOV-002",
        date="2026-07-01",
        scope="evidence",
        decision="Dry-lab-only artifacts are capped at evidence level 4; levels 5-6 require wet-lab evidence.",
        status="active",
        rationale="Maintains honest proof-ladder levels that cannot be inflated by simulation alone.",
        review_class="D",
    ),
    GovernanceDecision(
        decision_id="GOV-003",
        date="2026-07-04",
        scope="benchmark",
        decision="Any module claiming ranking authority must beat a cheap baseline benchmark first.",
        status="active",
        rationale="Prevents simulation theater — modules that don't beat trivial baselines must not rank candidates.",
        review_class="B",
    ),
    GovernanceDecision(
        decision_id="GOV-004",
        date="2026-07-09",
        scope="contribution",
        decision="All wet_lab_validation contributions require human_review_required=True.",
        status="active",
        rationale="Experimental data entering the pipeline must be reviewed by a human before use.",
        review_class="D",
    ),
    GovernanceDecision(
        decision_id="GOV-005",
        date="2026-07-09",
        scope="release",
        decision="All external releases must pass the release gate validator before publication.",
        status="active",
        rationale="Prevents skipping required checks during release; gates are documented and enforced.",
        review_class="B",
    ),
    GovernanceDecision(
        decision_id="GOV-006",
        date="2026-07-09",
        scope="docs",
        decision="Documentation files must remain under 200KB each.",
        status="active",
        rationale="Keeps docs readable and prevents runaway history accumulation.",
        review_class="B",
    ),
    GovernanceDecision(
        decision_id="GOV-007",
        date="2026-07-01",
        scope="evidence",
        decision="Proof-ladder levels above 4 require wet-lab evidence and human review class D.",
        status="active",
        rationale="Calibrates claim strength to actual experimental evidence.",
        review_class="D",
    ),
    GovernanceDecision(
        decision_id="GOV-008",
        date="2026-07-04",
        scope="adapter",
        decision="Adapter default mode is off or info; gated mode requires benchmark comparison.",
        status="active",
        rationale="Prevents external adapters from silently influencing rankings without evidence.",
        review_class="B",
    ),
]


def validate_governance_decision(decl: GovernanceDecision) -> DecisionValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not decl.decision_id or not decl.decision_id.startswith("GOV-"):
        errors.append("decision_id must not be empty and must start with 'GOV-'")
    if not decl.date or len(decl.date) != 10 or decl.date[4] != "-" or decl.date[7] != "-":
        errors.append("date must be in YYYY-MM-DD format")
    if decl.scope not in VALID_SCOPES:
        errors.append(f"scope={decl.scope!r} not in {sorted(VALID_SCOPES)}")
    if not decl.decision:
        errors.append("decision must not be empty")
    if decl.status not in VALID_STATUSES:
        errors.append(f"status={decl.status!r} not in {sorted(VALID_STATUSES)}")
    if not decl.rationale:
        errors.append("rationale must not be empty")
    if decl.review_class not in VALID_REVIEW_CLASSES:
        errors.append(f"review_class={decl.review_class!r} not in {sorted(VALID_REVIEW_CLASSES)}")
    if not decl.dry_lab_only:
        errors.append("dry_lab_only must be True")
    if decl.status == "superseded":
        warnings.append("superseded decision — check if a successor decision is referenced")

    return DecisionValidationResult(
        decision_id=decl.decision_id or "<unknown>",
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_all_decisions() -> dict[str, Any]:
    results = [validate_governance_decision(d) for d in GOVERNANCE_DECISIONS]
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "all_passed": len(failed) == 0,
        "results": [vars(r) for r in results],
        "dry_lab_only": True,
    }


def get_decisions_by_scope(scope: str) -> list[GovernanceDecision]:
    return [d for d in GOVERNANCE_DECISIONS if d.scope == scope]


def get_decisions_by_status(status: str) -> list[GovernanceDecision]:
    return [d for d in GOVERNANCE_DECISIONS if d.status == status]
