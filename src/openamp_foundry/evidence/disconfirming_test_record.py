"""DTR- Disconfirming Test Record schema.

Machine-readable record of one explicit attempt to prove a claim wrong.
Makes the CLAUDE.md "disconfirming pass" requirement auditable.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_DTR_TEST_TYPES: frozenset[str] = frozenset({
    "cheapest_explanation_check",
    "leakage_check",
    "scope_creep_check",
    "hidden_certainty_check",
    "uninformative_uncertainty_check",
    "charge_matched_enemy_check",
    "train_test_split_check",
})

VALID_DTR_TEST_OUTCOMES: frozenset[str] = frozenset({
    "not_refuted",
    "refuted",
    "inconclusive",
    "skipped",
})

VALID_DTR_REQUIRED_ACTIONS: frozenset[str] = frozenset({
    "none",
    "investigate",
    "downgrade_claim",
    "retract_claim",
})

_OUTCOME_TO_ACTION: dict[str, str] = {
    "refuted": "downgrade_claim",
    "inconclusive": "investigate",
    "not_refuted": "none",
    "skipped": "none",
}


@dataclass
class DisconfirmingTestRecord:
    dtr_id: str
    pipeline_version: str
    claim_tested: str
    test_type: str
    test_description: str
    test_outcome: str
    evidence_summary: str
    limitations: list[str]
    is_claim_affected: bool = False
    required_action: str = ""
    dry_lab_only: bool = True
    created_at: str = ""


def build_disconfirming_test_record(
    *,
    dtr_id: str,
    pipeline_version: str,
    claim_tested: str,
    test_type: str,
    test_description: str,
    test_outcome: str,
    evidence_summary: str,
    limitations: list[str],
    created_at: str,
) -> DisconfirmingTestRecord:
    is_claim_affected = test_outcome == "refuted"
    required_action = _OUTCOME_TO_ACTION.get(test_outcome, "none")
    dtr = DisconfirmingTestRecord(
        dtr_id=dtr_id,
        pipeline_version=pipeline_version,
        claim_tested=claim_tested,
        test_type=test_type,
        test_description=test_description,
        test_outcome=test_outcome,
        evidence_summary=evidence_summary,
        is_claim_affected=is_claim_affected,
        required_action=required_action,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_disconfirming_test_record(dtr)
    return dtr


def validate_disconfirming_test_record(
    dtr: DisconfirmingTestRecord,
) -> None:
    if not dtr.dtr_id.startswith("DTR-"):
        raise ValueError(
            f"dtr_id must start with 'DTR-': {dtr.dtr_id!r}"
        )
    if not dtr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not dtr.claim_tested:
        raise ValueError("claim_tested must be non-empty")
    if len(dtr.claim_tested) > 400:
        raise ValueError(
            f"claim_tested exceeds 400 chars: {len(dtr.claim_tested)}"
        )
    if dtr.test_type not in VALID_DTR_TEST_TYPES:
        raise ValueError(
            f"test_type {dtr.test_type!r} not in VALID_DTR_TEST_TYPES"
        )
    if not dtr.test_description:
        raise ValueError("test_description must be non-empty")
    if dtr.test_outcome not in VALID_DTR_TEST_OUTCOMES:
        raise ValueError(
            f"test_outcome {dtr.test_outcome!r} not in VALID_DTR_TEST_OUTCOMES"
        )
    if not dtr.evidence_summary:
        raise ValueError("evidence_summary must be non-empty")
    if dtr.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not dtr.limitations:
        raise ValueError("limitations must be non-empty")
    if not dtr.created_at:
        raise ValueError("created_at must be non-empty")


def format_disconfirming_test_record(
    dtr: DisconfirmingTestRecord,
) -> str:
    lines = [
        f"Disconfirming Test Record — {dtr.dtr_id}",
        f"Pipeline: {dtr.pipeline_version}",
        f"Claim tested: {dtr.claim_tested}",
        f"Test type: {dtr.test_type}",
        f"Test description: {dtr.test_description}",
        f"Test outcome: {dtr.test_outcome}",
        f"Required action: {dtr.required_action}",
        f"Is claim affected: {dtr.is_claim_affected}",
        f"Evidence summary: {dtr.evidence_summary}",
    ]
    for lim in dtr.limitations:
        lines.append(f"  Limitation: {lim}")
    lines.append(f"Dry lab only: {dtr.dry_lab_only}")
    lines.append(f"Created: {dtr.created_at}")
    return "\n".join(lines)
