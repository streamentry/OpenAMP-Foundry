from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_BUNDLE_STATUSES = frozenset({
    "draft",           # not yet reviewed internally
    "internal_review", # under internal review
    "approved",        # approved for preprint submission
    "submitted",       # submitted to preprint server
    "published",       # published on preprint server
})

VALID_PREPRINT_SERVERS = frozenset({
    "bioRxiv",
    "chemRxiv",
    "Research Square",
    "SSRN",
    "Zenodo",
    "OSF Preprints",
    "not_submitted",
})

VALID_CLAIM_STRENGTH_TIERS = frozenset({
    "computational_nomination",   # candidates identified by dry-lab pipeline
    "validated_computational",    # dry-lab validated against multiple benchmarks
    "preliminary_wet_lab",        # one wet-lab confirmation, not replicated
    "replicated_wet_lab",         # replicated in ≥2 independent experiments
})

DRY_LAB_ONLY_DISCLAIMER = (
    "All candidates are dry-lab computational nominations. "
    "Wet-lab results, where present, are preliminary and have not been independently replicated. "
    "No biological proof of efficacy is claimed."
)


@dataclass
class PreprintEvidenceBundle:
    peb_id: str
    run_id: str
    candidate_family_id: str
    srg_id: str
    atr_id: str
    cfc_id: str
    fnr_id: str
    pqg_id: str
    bundle_status: str
    preprint_server: str
    claim_strength_tier: str
    n_candidates_included: int
    n_confirmed_hits: int
    artifact_ids: List[str]
    dry_lab_only_disclaimer: str
    dry_lab_only: bool
    limitations: str
    notes: str = ""
    preprint_doi: Optional[str] = None


@dataclass
class PEBValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_preprint_evidence_bundle(bundle: PreprintEvidenceBundle) -> PEBValidationResult:
    violations = []

    if not bundle.peb_id.startswith("PEB-"):
        violations.append("peb_id must start with 'PEB-'")

    if not bundle.run_id:
        violations.append("run_id is required")

    if not bundle.candidate_family_id:
        violations.append("candidate_family_id is required")

    if bundle.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real PEB- records")

    if not bundle.srg_id.startswith("SRG-"):
        violations.append("srg_id must start with 'SRG-'")

    if not bundle.atr_id.startswith("ATR-"):
        violations.append("atr_id must start with 'ATR-'")

    if not bundle.cfc_id.startswith("CFC-"):
        violations.append("cfc_id must start with 'CFC-'")

    if not bundle.fnr_id.startswith("FNR-"):
        violations.append("fnr_id must start with 'FNR-'")

    if not bundle.pqg_id.startswith("PQG-"):
        violations.append("pqg_id must start with 'PQG-'")

    if bundle.bundle_status not in VALID_BUNDLE_STATUSES:
        violations.append(
            f"bundle_status '{bundle.bundle_status}' must be one of {sorted(VALID_BUNDLE_STATUSES)}"
        )

    if bundle.preprint_server not in VALID_PREPRINT_SERVERS:
        violations.append(
            f"preprint_server '{bundle.preprint_server}' must be one of {sorted(VALID_PREPRINT_SERVERS)}"
        )

    if bundle.claim_strength_tier not in VALID_CLAIM_STRENGTH_TIERS:
        violations.append(
            f"claim_strength_tier '{bundle.claim_strength_tier}' must be one of {sorted(VALID_CLAIM_STRENGTH_TIERS)}"
        )

    if bundle.n_candidates_included < 1:
        violations.append("n_candidates_included must be >= 1")

    if bundle.n_confirmed_hits < 0:
        violations.append("n_confirmed_hits must be >= 0")

    if bundle.n_confirmed_hits > bundle.n_candidates_included:
        violations.append(
            f"n_confirmed_hits ({bundle.n_confirmed_hits}) cannot exceed n_candidates_included ({bundle.n_candidates_included})"
        )

    if not bundle.artifact_ids:
        violations.append("at least one artifact_id is required")

    # submitted/published requires a preprint server (not not_submitted)
    if bundle.bundle_status in ("submitted", "published") and bundle.preprint_server == "not_submitted":
        violations.append(
            f"bundle_status='{bundle.bundle_status}' requires a real preprint_server (not 'not_submitted')"
        )

    # draft status should not have a preprint_doi
    if bundle.bundle_status == "draft" and bundle.preprint_doi is not None:
        violations.append("bundle_status='draft' should not have a preprint_doi")

    # published status requires a preprint_doi
    if bundle.bundle_status == "published" and bundle.preprint_doi is None:
        violations.append("bundle_status='published' requires a preprint_doi")

    # replicated_wet_lab requires n_confirmed_hits >= 2
    if bundle.claim_strength_tier == "replicated_wet_lab" and bundle.n_confirmed_hits < 2:
        violations.append(
            "claim_strength_tier='replicated_wet_lab' requires n_confirmed_hits >= 2"
        )

    # disclaimer must match the canonical text
    if bundle.dry_lab_only_disclaimer != DRY_LAB_ONLY_DISCLAIMER:
        violations.append(
            "dry_lab_only_disclaimer must match the canonical DRY_LAB_ONLY_DISCLAIMER constant"
        )

    if not bundle.dry_lab_only:
        violations.append(
            "dry_lab_only must be True for PEB- records (preprint bundle is a documentation artifact)"
        )

    if not bundle.limitations or len(bundle.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return PEBValidationResult(valid=len(violations) == 0, violations=violations)


def build_preprint_evidence_bundle(
    peb_id: str,
    run_id: str,
    candidate_family_id: str,
    srg_id: str,
    atr_id: str,
    cfc_id: str,
    fnr_id: str,
    pqg_id: str,
    bundle_status: str,
    preprint_server: str,
    claim_strength_tier: str,
    n_candidates_included: int,
    n_confirmed_hits: int,
    artifact_ids: List[str],
    limitations: str,
    notes: str = "",
    preprint_doi: Optional[str] = None,
) -> PreprintEvidenceBundle:
    bundle = PreprintEvidenceBundle(
        peb_id=peb_id,
        run_id=run_id,
        candidate_family_id=candidate_family_id,
        srg_id=srg_id,
        atr_id=atr_id,
        cfc_id=cfc_id,
        fnr_id=fnr_id,
        pqg_id=pqg_id,
        bundle_status=bundle_status,
        preprint_server=preprint_server,
        claim_strength_tier=claim_strength_tier,
        n_candidates_included=n_candidates_included,
        n_confirmed_hits=n_confirmed_hits,
        artifact_ids=artifact_ids,
        dry_lab_only_disclaimer=DRY_LAB_ONLY_DISCLAIMER,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
        preprint_doi=preprint_doi,
    )
    result = validate_preprint_evidence_bundle(bundle)
    if not result.valid:
        raise ValueError(f"Invalid PEB: {result.violations}")
    return bundle


def format_preprint_evidence_bundle(bundle: PreprintEvidenceBundle) -> str:
    lines = [
        f"Preprint Evidence Bundle — {bundle.peb_id}",
        f"Run: {bundle.run_id}  |  Family: {bundle.candidate_family_id}",
        f"Status: {bundle.bundle_status}  |  Server: {bundle.preprint_server}",
        f"Claim Tier: {bundle.claim_strength_tier}",
        f"Candidates: {bundle.n_candidates_included}  |  Confirmed Hits: {bundle.n_confirmed_hits}",
        f"SRG: {bundle.srg_id}  |  ATR: {bundle.atr_id}",
        f"CFC: {bundle.cfc_id}  |  FNR: {bundle.fnr_id}  |  PQG: {bundle.pqg_id}",
        f"Artifacts: {len(bundle.artifact_ids)} included",
    ]
    if bundle.preprint_doi:
        lines.append(f"DOI: {bundle.preprint_doi}")
    lines.append(f"Disclaimer: {bundle.dry_lab_only_disclaimer}")
    lines.append(f"Limitations: {bundle.limitations}")
    if bundle.notes:
        lines.append(f"Notes: {bundle.notes}")
    lines.append("dry_lab_only: True (preprint bundle is a documentation artifact)")
    return "\n".join(lines)
