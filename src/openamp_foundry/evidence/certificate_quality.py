"""Certificate quality-tier validator — Phase B B5.

Computes a quality tier for a certificate dict produced by build_certificate().
Makes external-review readiness a computed, machine-verifiable property rather
than a reviewer judgment call.

Three tiers (ordered ascending):
  draft              — candidate_id, sequence, scores present
  internal_review    — draft + selection_reason, known_failure_modes,
                       proof_ladder_level, baseline_caveat, pipeline_version;
                       zero forbidden-claim violations
  external_review_ready — internal_review + recommended_next_steps,
                          references_checked, config_hash; zero warnings
"""

from __future__ import annotations

import re
from typing import Any

# Fields required for each tier
_DRAFT_REQUIRED = frozenset({"candidate_id", "sequence", "scores"})

_INTERNAL_REQUIRED = frozenset({
    "candidate_id", "sequence", "scores",
    "selection_reason", "known_failure_modes",
    "proof_ladder_level", "baseline_caveat", "pipeline_version",
})

_EXTERNAL_REQUIRED = frozenset({
    "candidate_id", "sequence", "scores",
    "selection_reason", "known_failure_modes",
    "proof_ladder_level", "baseline_caveat", "pipeline_version",
    "recommended_next_steps", "references_checked", "config_hash",
})

# Ordered tiers (ascending quality)
QUALITY_TIERS = ("draft", "internal_review", "external_review_ready")

# Simple forbidden-claim patterns (subset safe to import here without circular dep)
_FORBIDDEN_PHRASES = (
    re.compile(r"\bproven\b", re.IGNORECASE),
    re.compile(r"safe in humans", re.IGNORECASE),
    re.compile(r"clinical(ly)?\b", re.IGNORECASE),
    re.compile(r"\bdrug candidate\b", re.IGNORECASE),
    re.compile(r"\bcure\b", re.IGNORECASE),
    re.compile(r"antibiotic for treatment", re.IGNORECASE),
    re.compile(r"wet.lab evidence confirms", re.IGNORECASE),
)


def _extract_text_fields(cert: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for val in cert.values():
        if isinstance(val, str):
            texts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    texts.append(item)
    return texts


def _find_claim_violations(cert: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    texts = _extract_text_fields(cert)
    for pat in _FORBIDDEN_PHRASES:
        for text in texts:
            if pat.search(text):
                violations.append(
                    f"ForbiddenPattern {pat.pattern!r} found in: {text[:60]!r}"
                )
    return violations


def _missing_fields(cert: dict[str, Any], required: frozenset[str]) -> list[str]:
    missing = []
    for field in sorted(required):
        val = cert.get(field)
        if val is None:
            missing.append(field)
        elif isinstance(val, str) and not val.strip():
            missing.append(field)
        elif isinstance(val, list) and len(val) == 0:
            missing.append(field)
    return missing


def assess_certificate_quality(cert: dict[str, Any]) -> dict[str, Any]:
    """Assess the quality tier of a certificate dict.

    Returns a quality report dict with:
      quality_tier: str           — one of QUALITY_TIERS
      missing_fields: list[str]   — fields absent or empty at the assessed tier
      claim_violations: list[str] — forbidden-claim pattern matches
      warnings: list[str]         — non-blocking issues (e.g. empty optional fields)
      is_external_review_ready: bool

    The tier is the highest tier all requirements are met for.
    If draft requirements are not met, quality_tier is "below_draft".
    """
    claim_violations = _find_claim_violations(cert)
    warnings: list[str] = []

    # Check draft
    draft_missing = _missing_fields(cert, _DRAFT_REQUIRED)
    if draft_missing:
        return {
            "quality_tier": "below_draft",
            "missing_fields": draft_missing,
            "claim_violations": claim_violations,
            "warnings": [f"Missing draft-required field: {f}" for f in draft_missing],
            "is_external_review_ready": False,
        }

    # Check internal_review
    internal_missing = _missing_fields(cert, _INTERNAL_REQUIRED)
    if internal_missing or claim_violations:
        if claim_violations:
            warnings.append(f"{len(claim_violations)} forbidden-claim violation(s) block internal_review tier")
        return {
            "quality_tier": "draft",
            "missing_fields": internal_missing,
            "claim_violations": claim_violations,
            "warnings": warnings + [f"Missing internal-required field: {f}" for f in internal_missing],
            "is_external_review_ready": False,
        }

    # Check external_review_ready
    external_missing = _missing_fields(cert, _EXTERNAL_REQUIRED)
    if external_missing:
        for f in external_missing:
            warnings.append(f"Missing external-required field: {f}")
        return {
            "quality_tier": "internal_review",
            "missing_fields": external_missing,
            "claim_violations": [],
            "warnings": warnings,
            "is_external_review_ready": False,
        }

    # All tiers met
    return {
        "quality_tier": "external_review_ready",
        "missing_fields": [],
        "claim_violations": [],
        "warnings": [],
        "is_external_review_ready": True,
    }
