from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

CHAIN_LINK_FIELDS: list[str] = [
    "has_sequence_input",
    "has_benchmark_results",
    "has_filter_log",
    "has_score_decomposition",
    "has_selection_rationale",
    "has_evidence_certificate",
    "has_claim_mappings",
    "has_pipeline_decision_audit",
    "has_reviewer_briefing",
]

CHAIN_LINK_COUNT: int = len(CHAIN_LINK_FIELDS)
AUDITOR_EMAIL_HINT: str = "@"
IMPLAUSIBLE_YEAR_THRESHOLD: int = 2030


@dataclass
class AuditChainEntry:
    chain_id: str
    batch_id: str
    pipeline_version: str
    audit_date: str
    has_sequence_input: bool
    has_benchmark_results: bool
    has_filter_log: bool
    has_score_decomposition: bool
    has_selection_rationale: bool
    has_evidence_certificate: bool
    has_claim_mappings: bool
    has_pipeline_decision_audit: bool
    has_reviewer_briefing: bool
    missing_links: List[str]
    auditor: str
    dry_lab_only: bool = True


@dataclass
class AuditChainResult:
    chain_id: str
    batch_id: str
    missing_link_count: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def _compute_missing_links(entry: AuditChainEntry) -> list[str]:
    missing = []
    for link in CHAIN_LINK_FIELDS:
        if not getattr(entry, link):
            missing.append(link)
    return missing


def validate_audit_chain(entry: AuditChainEntry) -> AuditChainResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.chain_id.startswith("ACH-"):
        errors.append(f"chain_id must start with 'ACH-', got '{entry.chain_id}'")

    if not entry.auditor:
        errors.append("auditor must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for audit chain completeness entries "
            "(computational pipeline only)"
        )

    computed_missing = _compute_missing_links(entry)
    for link in computed_missing:
        errors.append(f"chain link '{link}' is missing (False); evidence chain has a gap")

    declared_missing_set = set(entry.missing_links)
    computed_missing_set = set(computed_missing)
    if declared_missing_set != computed_missing_set:
        extra = declared_missing_set - computed_missing_set
        overlooked = computed_missing_set - declared_missing_set
        if extra:
            errors.append(
                f"missing_links declares {sorted(extra)} as missing but those fields are True"
            )
        if overlooked:
            errors.append(
                f"missing_links omits {sorted(overlooked)} which are actually False"
            )

    if not errors:
        if entry.auditor and AUDITOR_EMAIL_HINT not in entry.auditor:
            warnings.append(
                "auditor does not appear to be an email address; "
                "a named human auditor with contact information is recommended"
            )

        if entry.audit_date:
            try:
                year = int(entry.audit_date[:4])
                if year > IMPLAUSIBLE_YEAR_THRESHOLD:
                    warnings.append(
                        f"audit_date year {year} > {IMPLAUSIBLE_YEAR_THRESHOLD}; "
                        "please verify this date is correct"
                    )
            except (ValueError, IndexError):
                pass

    passed = len(errors) == 0
    return AuditChainResult(
        chain_id=entry.chain_id,
        batch_id=entry.batch_id,
        missing_link_count=len(computed_missing),
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_audit_chain_dict(d: dict) -> AuditChainResult:
    required_fields = [
        "chain_id",
        "batch_id",
        "pipeline_version",
        "audit_date",
        "has_sequence_input",
        "has_benchmark_results",
        "has_filter_log",
        "has_score_decomposition",
        "has_selection_rationale",
        "has_evidence_certificate",
        "has_claim_mappings",
        "has_pipeline_decision_audit",
        "has_reviewer_briefing",
        "missing_links",
        "auditor",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return AuditChainResult(
            chain_id=d.get("chain_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            missing_link_count=0,
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = AuditChainEntry(
        chain_id=d["chain_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        audit_date=d["audit_date"],
        has_sequence_input=bool(d["has_sequence_input"]),
        has_benchmark_results=bool(d["has_benchmark_results"]),
        has_filter_log=bool(d["has_filter_log"]),
        has_score_decomposition=bool(d["has_score_decomposition"]),
        has_selection_rationale=bool(d["has_selection_rationale"]),
        has_evidence_certificate=bool(d["has_evidence_certificate"]),
        has_claim_mappings=bool(d["has_claim_mappings"]),
        has_pipeline_decision_audit=bool(d["has_pipeline_decision_audit"]),
        has_reviewer_briefing=bool(d["has_reviewer_briefing"]),
        missing_links=list(d["missing_links"]),
        auditor=d["auditor"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_audit_chain(entry)
