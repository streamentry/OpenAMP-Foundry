from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


REQUIRED_SRG_ARTIFACT_TYPES = frozenset({
    "CFC",   # candidate family clustering
    "FNR",   # family novelty report
    "ATR",   # audit trail report
    "PQG",   # Phase Q completeness gate
})

VALID_READINESS_VERDICTS = frozenset({
    "ready_for_external_review",   # all gates passed; safe for external scientific review
    "not_ready",                   # one or more gates failed
    "conditionally_ready",         # minor issues noted; external reviewer must be informed
    "review_blocked_by_safety",    # safety flag unresolved; must not proceed
})

VALID_SAFETY_FLAG_TYPES = frozenset({
    "unresolved_hemolysis",
    "unresolved_toxicity",
    "dual_use_concern",
    "off_target_risk",
    "contamination_suspected",
    "no_flags",
})

VALID_REVIEW_SCOPE_TYPES = frozenset({
    "internal_only",
    "trusted_partner",
    "open_preprint",
    "peer_review_submission",
})


@dataclass
class ScientificReviewReadinessGate:
    srg_id: str
    candidate_family_id: str
    cfc_id: str
    fnr_id: str
    atr_id: str
    pqg_id: str
    readiness_verdict: str
    safety_flags: List[str]
    failed_gates: List[str]
    review_scope: str
    n_confirmed_hits: int
    n_total_candidates: int
    dry_lab_only: bool
    limitations: str
    notes: str = ""


@dataclass
class SRGValidationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)


def validate_scientific_review_readiness_gate(gate: ScientificReviewReadinessGate) -> SRGValidationResult:
    violations = []

    if not gate.srg_id.startswith("SRG-"):
        violations.append("srg_id must start with 'SRG-'")

    if not gate.candidate_family_id:
        violations.append("candidate_family_id is required")

    if gate.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real SRG- records")

    if not gate.cfc_id.startswith("CFC-"):
        violations.append("cfc_id must start with 'CFC-'")

    if not gate.fnr_id.startswith("FNR-"):
        violations.append("fnr_id must start with 'FNR-'")

    if not gate.atr_id.startswith("ATR-"):
        violations.append("atr_id must start with 'ATR-'")

    if not gate.pqg_id.startswith("PQG-"):
        violations.append("pqg_id must start with 'PQG-'")

    if gate.readiness_verdict not in VALID_READINESS_VERDICTS:
        violations.append(
            f"readiness_verdict '{gate.readiness_verdict}' must be one of {sorted(VALID_READINESS_VERDICTS)}"
        )

    for sf in gate.safety_flags:
        if sf not in VALID_SAFETY_FLAG_TYPES:
            violations.append(
                f"safety_flag '{sf}' must be one of {sorted(VALID_SAFETY_FLAG_TYPES)}"
            )

    if gate.review_scope not in VALID_REVIEW_SCOPE_TYPES:
        violations.append(
            f"review_scope '{gate.review_scope}' must be one of {sorted(VALID_REVIEW_SCOPE_TYPES)}"
        )

    if gate.n_confirmed_hits < 0:
        violations.append("n_confirmed_hits must be >= 0")

    if gate.n_total_candidates < 1:
        violations.append("n_total_candidates must be >= 1")

    if gate.n_confirmed_hits > gate.n_total_candidates:
        violations.append(
            f"n_confirmed_hits ({gate.n_confirmed_hits}) cannot exceed n_total_candidates ({gate.n_total_candidates})"
        )

    # review_blocked_by_safety requires a real safety flag
    if gate.readiness_verdict == "review_blocked_by_safety":
        blocking_flags = VALID_SAFETY_FLAG_TYPES - {"no_flags"}
        if not any(sf in blocking_flags for sf in gate.safety_flags):
            violations.append(
                "readiness_verdict='review_blocked_by_safety' requires at least one real safety flag "
                "(not 'no_flags')"
            )

    # ready_for_external_review must not have unresolved safety flags
    if gate.readiness_verdict == "ready_for_external_review":
        blocking_flags = VALID_SAFETY_FLAG_TYPES - {"no_flags"}
        if any(sf in blocking_flags for sf in gate.safety_flags):
            violations.append(
                "readiness_verdict='ready_for_external_review' cannot have unresolved safety flags"
            )
        if gate.failed_gates:
            violations.append(
                "readiness_verdict='ready_for_external_review' requires empty failed_gates"
            )
        if gate.n_confirmed_hits < 1:
            violations.append(
                "readiness_verdict='ready_for_external_review' requires n_confirmed_hits >= 1"
            )

    # no_flags and real flags cannot coexist
    if "no_flags" in gate.safety_flags and len(gate.safety_flags) > 1:
        violations.append("safety_flag 'no_flags' cannot coexist with other flags")

    # open_preprint requires ready_for_external_review or conditionally_ready
    if gate.review_scope in ("open_preprint", "peer_review_submission"):
        if gate.readiness_verdict == "review_blocked_by_safety":
            violations.append(
                f"review_scope='{gate.review_scope}' is not allowed with readiness_verdict='review_blocked_by_safety'"
            )
        if gate.readiness_verdict == "not_ready":
            violations.append(
                f"review_scope='{gate.review_scope}' is not allowed with readiness_verdict='not_ready'"
            )

    if not gate.dry_lab_only:
        violations.append(
            "dry_lab_only must be True for SRG- records (readiness gate is a documentation artifact)"
        )

    if not gate.limitations or len(gate.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return SRGValidationResult(passed=len(violations) == 0, violations=violations)


def build_scientific_review_readiness_gate(
    srg_id: str,
    candidate_family_id: str,
    cfc_id: str,
    fnr_id: str,
    atr_id: str,
    pqg_id: str,
    readiness_verdict: str,
    safety_flags: List[str],
    failed_gates: List[str],
    review_scope: str,
    n_confirmed_hits: int,
    n_total_candidates: int,
    limitations: str,
    notes: str = "",
) -> ScientificReviewReadinessGate:
    gate = ScientificReviewReadinessGate(
        srg_id=srg_id,
        candidate_family_id=candidate_family_id,
        cfc_id=cfc_id,
        fnr_id=fnr_id,
        atr_id=atr_id,
        pqg_id=pqg_id,
        readiness_verdict=readiness_verdict,
        safety_flags=safety_flags,
        failed_gates=failed_gates,
        review_scope=review_scope,
        n_confirmed_hits=n_confirmed_hits,
        n_total_candidates=n_total_candidates,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
    )
    result = validate_scientific_review_readiness_gate(gate)
    if not result.passed:
        raise ValueError(f"Invalid SRG: {result.violations}")
    return gate


def format_scientific_review_readiness_gate(gate: ScientificReviewReadinessGate) -> str:
    lines = [
        f"Scientific Review Readiness Gate — {gate.srg_id}",
        f"Candidate Family: {gate.candidate_family_id}",
        f"Readiness Verdict: {gate.readiness_verdict}",
        f"Review Scope: {gate.review_scope}",
        f"Confirmed Hits: {gate.n_confirmed_hits}/{gate.n_total_candidates}",
        f"CFC: {gate.cfc_id}  |  FNR: {gate.fnr_id}",
        f"ATR: {gate.atr_id}  |  PQG: {gate.pqg_id}",
        f"Safety Flags: {', '.join(gate.safety_flags) if gate.safety_flags else 'none'}",
    ]
    if gate.failed_gates:
        lines.append(f"Failed Gates: {', '.join(gate.failed_gates)}")
    lines.append(f"Limitations: {gate.limitations}")
    if gate.notes:
        lines.append(f"Notes: {gate.notes}")
    lines.append("dry_lab_only: True (readiness gate is a documentation artifact)")
    return "\n".join(lines)
