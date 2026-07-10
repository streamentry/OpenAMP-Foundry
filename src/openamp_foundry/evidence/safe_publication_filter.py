"""SPF- safe-publication filter for negative results.

Determines whether a negative-result record is safe to publish externally,
requires redaction before publication, or must be blocked entirely.

Negative results are scientifically valuable — showing what failed and why
improves reproducibility and prevents others from repeating dead ends. But
they can also contain sensitive content: dual-use sequences, proprietary
candidate identifiers, or privacy-sensitive data from collaboration partners.

This filter makes the publication decision machine-checkable rather than
relying on ad-hoc human judgment. Every negative result intended for public
release must pass through an SPF- record.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_SPF_VERDICTS: frozenset[str] = frozenset({
    "safe_to_publish",
    "requires_redaction",
    "publication_blocked",
})

VALID_SPF_BLOCK_REASONS: frozenset[str] = frozenset({
    "dual_use_concern",
    "sequence_privacy_violation",
    "proprietary_candidate_id_present",
    "collaborator_identity_exposed",
    "preliminary_wet_lab_data_present",
    "regulatory_restriction",
})

VALID_REDACTION_TYPES: frozenset[str] = frozenset({
    "candidate_id_anonymised",
    "sequence_truncated",
    "collaborator_name_removed",
    "batch_id_removed",
    "score_precision_reduced",
})


@dataclass
class SafePublicationFilter:
    spf_id: str
    nrr_id: str
    pipeline_version: str
    publication_verdict: str
    dual_use_clear: bool
    sequence_privacy_clear: bool
    informative_as_negative: bool
    blocked_reasons: list[str]
    redactions_applied: list[str]
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_safe_publication_filter(spf: SafePublicationFilter) -> None:
    if not spf.spf_id.startswith("SPF-"):
        raise ValueError(f"spf_id must start with 'SPF-': {spf.spf_id!r}")
    if not spf.nrr_id.startswith("NRR-"):
        raise ValueError(f"nrr_id must start with 'NRR-': {spf.nrr_id!r}")
    if not spf.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if spf.publication_verdict not in VALID_SPF_VERDICTS:
        raise ValueError(
            f"publication_verdict {spf.publication_verdict!r} not in VALID_SPF_VERDICTS"
        )
    for reason in spf.blocked_reasons:
        if reason not in VALID_SPF_BLOCK_REASONS:
            raise ValueError(
                f"block reason {reason!r} not in VALID_SPF_BLOCK_REASONS"
            )
    for redaction in spf.redactions_applied:
        if redaction not in VALID_REDACTION_TYPES:
            raise ValueError(
                f"redaction type {redaction!r} not in VALID_REDACTION_TYPES"
            )
    if spf.publication_verdict == "publication_blocked" and not spf.blocked_reasons:
        raise ValueError(
            "blocked_reasons must be non-empty when publication_verdict='publication_blocked'"
        )
    if spf.publication_verdict == "requires_redaction" and not spf.redactions_applied:
        raise ValueError(
            "redactions_applied must be non-empty when publication_verdict='requires_redaction'"
        )
    if spf.publication_verdict == "safe_to_publish":
        if not spf.dual_use_clear:
            raise ValueError(
                "dual_use_clear must be True when publication_verdict='safe_to_publish'"
            )
        if not spf.sequence_privacy_clear:
            raise ValueError(
                "sequence_privacy_clear must be True when publication_verdict='safe_to_publish'"
            )
    if not spf.dual_use_clear and spf.publication_verdict != "publication_blocked":
        raise ValueError(
            "dual_use_clear=False requires publication_verdict='publication_blocked'"
        )
    if not spf.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not spf.limitations:
        raise ValueError("limitations must be non-empty")
    if not spf.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    dual_use_clear: bool,
    sequence_privacy_clear: bool,
    has_block_reasons: bool,
    has_redactions: bool,
) -> str:
    if not dual_use_clear or has_block_reasons:
        return "publication_blocked"
    if not sequence_privacy_clear or has_redactions:
        return "requires_redaction"
    return "safe_to_publish"


def build_safe_publication_filter(
    *,
    spf_id: str,
    nrr_id: str,
    pipeline_version: str,
    dual_use_clear: bool,
    sequence_privacy_clear: bool,
    informative_as_negative: bool = True,
    blocked_reasons: list[str] | None = None,
    redactions_applied: list[str] | None = None,
    limitations: list[str],
    created_at: str,
) -> SafePublicationFilter:
    """Build a SafePublicationFilter.

    publication_verdict is auto-computed from dual_use_clear,
    sequence_privacy_clear, blocked_reasons, and redactions_applied.
    """
    blocked_reasons = list(blocked_reasons) if blocked_reasons else []
    redactions_applied = list(redactions_applied) if redactions_applied else []
    verdict = _compute_verdict(
        dual_use_clear=dual_use_clear,
        sequence_privacy_clear=sequence_privacy_clear,
        has_block_reasons=bool(blocked_reasons),
        has_redactions=bool(redactions_applied),
    )
    spf = SafePublicationFilter(
        spf_id=spf_id,
        nrr_id=nrr_id,
        pipeline_version=pipeline_version,
        publication_verdict=verdict,
        dual_use_clear=dual_use_clear,
        sequence_privacy_clear=sequence_privacy_clear,
        informative_as_negative=informative_as_negative,
        blocked_reasons=blocked_reasons,
        redactions_applied=redactions_applied,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_safe_publication_filter(spf)
    return spf


def format_safe_publication_filter(spf: SafePublicationFilter) -> str:
    lines = [
        f"Safe-Publication Filter — {spf.spf_id}",
        f"NRR: {spf.nrr_id}  |  Pipeline: {spf.pipeline_version}",
        f"Verdict: {spf.publication_verdict}",
        f"Dual-use clear: {spf.dual_use_clear}",
        f"Sequence privacy clear: {spf.sequence_privacy_clear}",
        f"Informative as negative: {spf.informative_as_negative}",
    ]
    if spf.blocked_reasons:
        lines.append(f"Blocked reasons: {'; '.join(spf.blocked_reasons)}")
    if spf.redactions_applied:
        lines.append(f"Redactions applied: {'; '.join(spf.redactions_applied)}")
    lines.append(f"Limitations: {'; '.join(spf.limitations)}")
    lines.append(f"Created: {spf.created_at}")
    lines.append(f"dry_lab_only: {spf.dry_lab_only}")
    return "\n".join(lines)
