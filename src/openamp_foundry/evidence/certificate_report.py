"""Human-readable certificate report generator — Phase B B6.

Converts a certificate dict (from build_certificate()) into a formatted text
report that domain experts can read quickly without parsing JSON.

Usage:
    from openamp_foundry.evidence.certificate import build_certificate
    from openamp_foundry.evidence.certificate_report import build_certificate_report

    cert = build_certificate(scored, config, references)
    report = build_certificate_report(cert)
    print(report)
"""

from __future__ import annotations

from typing import Any

_SEPARATOR = "=" * 72
_SECTION_SEP = "-" * 72


def _fmt_score(val: Any) -> str:
    if isinstance(val, float):
        return f"{val:.3f}"
    return str(val)


def _fmt_list(items: Any, indent: int = 2) -> str:
    prefix = " " * indent
    if not items:
        return f"{prefix}(none)"
    if isinstance(items, list):
        return "\n".join(f"{prefix}• {item}" for item in items)
    return f"{prefix}{items}"


def build_certificate_report(
    cert: dict[str, Any],
    quality_report: dict[str, Any] | None = None,
) -> str:
    """Build a human-readable text report from a certificate dict.

    Args:
        cert: Certificate dict from build_certificate().
        quality_report: Optional output of assess_certificate_quality(cert).
                        If provided, quality tier and readiness are included.

    Returns:
        A multi-line string formatted for domain expert review.
    """
    lines: list[str] = []

    # Header
    lines.append(_SEPARATOR)
    lines.append("OPENAMP FOUNDRY — CANDIDATE EVIDENCE CERTIFICATE")
    lines.append(_SEPARATOR)
    lines.append("")

    # Identity
    lines.append("CANDIDATE")
    lines.append(_SECTION_SEP)
    lines.append(f"  ID:       {cert.get('candidate_id', '(unknown)')}")
    lines.append(f"  Sequence: {cert.get('sequence', '(none)')}")
    lines.append(f"  Source:   {cert.get('source', '(unknown)')}")
    lines.append(f"  Version:  {cert.get('pipeline_version', '(unknown)')}")
    lines.append(f"  Generated:{cert.get('generated_at', '(unknown)')}")
    lines.append("")

    # Proof ladder
    ladder_level = cert.get("proof_ladder_level", "(not set)")
    lines.append("PROOF LADDER")
    lines.append(_SECTION_SEP)
    lines.append(f"  Level: {ladder_level}")
    lines.append("")

    # Scores
    lines.append("SCORES  [dry-lab computational — not biological proof]")
    lines.append(_SECTION_SEP)
    scores = cert.get("scores", {})
    if isinstance(scores, dict):
        for key, val in sorted(scores.items()):
            lines.append(f"  {key:<20} {_fmt_score(val)}")
    else:
        lines.append("  (none)")
    lines.append("")

    # Baseline caveat
    lines.append("CHEAP-EXPLANATION CHECK")
    lines.append(_SECTION_SEP)
    caveat = cert.get("baseline_caveat", "(not computed)")
    for chunk in _wrap(caveat, width=68, indent=2):
        lines.append(chunk)
    lines.append("")

    # Selection reason
    lines.append("SELECTION REASON")
    lines.append(_SECTION_SEP)
    lines.append(_fmt_list(cert.get("selection_reason", [])))
    lines.append("")

    # Known failure modes
    lines.append("KNOWN FAILURE MODES")
    lines.append(_SECTION_SEP)
    lines.append(_fmt_list(cert.get("known_failure_modes", [])))
    lines.append("")

    # Recommended next steps
    lines.append("RECOMMENDED NEXT STEPS")
    lines.append(_SECTION_SEP)
    lines.append(_fmt_list(cert.get("recommended_next_steps", [])))
    lines.append("")

    # References checked
    refs = cert.get("references_checked", [])
    lines.append("REFERENCES CHECKED")
    lines.append(_SECTION_SEP)
    lines.append(_fmt_list(refs) if refs else "  (none)")
    lines.append("")

    # Quality tier (optional)
    if quality_report is not None:
        tier = quality_report.get("quality_tier", "(unknown)")
        is_ready = quality_report.get("is_external_review_ready", False)
        missing = quality_report.get("missing_fields", [])
        violations = quality_report.get("claim_violations", [])
        warnings = quality_report.get("warnings", [])

        lines.append("QUALITY TIER")
        lines.append(_SECTION_SEP)
        lines.append(f"  Tier:                 {tier}")
        lines.append(f"  External-review ready: {'YES' if is_ready else 'NO'}")
        if missing:
            lines.append(f"  Missing fields:       {', '.join(missing)}")
        if violations:
            lines.append(f"  Claim violations:     {len(violations)}")
        if warnings:
            for w in warnings:
                lines.append(f"  Warning: {w}")
        lines.append("")

    # Footer
    lines.append(_SEPARATOR)
    lines.append("NOTICE: This certificate reflects DRY-LAB COMPUTATIONAL OUTPUTS ONLY.")
    lines.append("No biological activity has been confirmed. All scores are predictions.")
    lines.append("Independent domain expert review is required before any assay decision.")
    lines.append(_SEPARATOR)

    return "\n".join(lines)


def _wrap(text: str, width: int = 68, indent: int = 2) -> list[str]:
    """Simple word-wrap that preserves leading indent."""
    prefix = " " * indent
    words = text.split()
    if not words:
        return [prefix]
    lines: list[str] = []
    current = prefix
    for word in words:
        candidate = current + (" " if current.strip() else "") + word
        if len(candidate) <= width:
            current = candidate
        else:
            if current.strip():
                lines.append(current)
            current = prefix + word
    if current.strip():
        lines.append(current)
    return lines if lines else [prefix]
