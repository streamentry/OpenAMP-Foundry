from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_NOVELTY_EVIDENCE_TYPES = frozenset({
    "blast_search_no_hits",          # BLAST against known AMP databases returned no hits
    "hmm_profile_no_match",          # HMM profile search found no match to known families
    "structural_divergence",         # structural prediction differs from known AMP classes
    "charge_length_outside_known",   # charge/length distribution outside all known families
    "expert_assessment",             # domain expert assessed family as novel
    "insufficient_evidence",         # not enough evidence to claim novelty
})

VALID_CLUSTERING_METHODS = frozenset({
    "sequence_identity",     # pairwise sequence identity threshold
    "edit_distance",         # Levenshtein distance threshold
    "kmer_similarity",       # k-mer profile similarity
    "embedding_distance",    # learned embedding distance (e.g. ESM-2)
    "manual_grouping",       # manually assigned by researcher
})

VALID_NOVELTY_VERDICTS = frozenset({
    "novel_family",           # sufficient evidence of novelty
    "variant_of_known",       # candidates are variants of a known AMP family
    "insufficient_evidence",  # not enough data to assess novelty
    "disputed",               # novelty contested by multiple evidence sources
})

MIN_FAMILY_SIZE = 2
MAX_SIMILARITY_THRESHOLD = 1.0
MIN_SIMILARITY_THRESHOLD = 0.0


@dataclass
class CandidateFamilyClustering:
    cfc_id: str
    family_name: str
    candidate_ids: List[str]
    clustering_method: str
    similarity_threshold: float
    novelty_evidence_types: List[str]
    novelty_verdict: str
    n_candidates: int
    n_toy_excluded: int
    known_family_hits: List[str]
    dry_lab_only: bool
    limitations: str
    notes: str = ""
    min_pairwise_similarity: Optional[float] = None
    max_pairwise_similarity: Optional[float] = None


@dataclass
class CFCValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_candidate_family_clustering(cfc: CandidateFamilyClustering) -> CFCValidationResult:
    violations = []

    if not cfc.cfc_id.startswith("CFC-"):
        violations.append("cfc_id must start with 'CFC-'")

    if not cfc.family_name or len(cfc.family_name.strip()) < 3:
        violations.append("family_name must be at least 3 characters")

    if not cfc.candidate_ids:
        violations.append("candidate_ids must not be empty")

    for cid in cfc.candidate_ids:
        if cid.startswith("TOY-"):
            violations.append(f"TOY- candidate_id '{cid}' is not allowed in real CFC- records")

    if cfc.clustering_method not in VALID_CLUSTERING_METHODS:
        violations.append(
            f"clustering_method '{cfc.clustering_method}' must be one of {sorted(VALID_CLUSTERING_METHODS)}"
        )

    if not (MIN_SIMILARITY_THRESHOLD <= cfc.similarity_threshold <= MAX_SIMILARITY_THRESHOLD):
        violations.append(
            f"similarity_threshold {cfc.similarity_threshold} must be in [0.0, 1.0]"
        )

    for net in cfc.novelty_evidence_types:
        if net not in VALID_NOVELTY_EVIDENCE_TYPES:
            violations.append(
                f"novelty_evidence_type '{net}' must be one of {sorted(VALID_NOVELTY_EVIDENCE_TYPES)}"
            )

    if not cfc.novelty_evidence_types:
        violations.append("at least one novelty_evidence_type is required")

    if cfc.novelty_verdict not in VALID_NOVELTY_VERDICTS:
        violations.append(
            f"novelty_verdict '{cfc.novelty_verdict}' must be one of {sorted(VALID_NOVELTY_VERDICTS)}"
        )

    if cfc.n_candidates < MIN_FAMILY_SIZE:
        violations.append(f"n_candidates must be >= {MIN_FAMILY_SIZE} (minimum family size)")

    if cfc.n_candidates != len(cfc.candidate_ids):
        violations.append(
            f"n_candidates ({cfc.n_candidates}) must equal len(candidate_ids) ({len(cfc.candidate_ids)})"
        )

    if cfc.n_toy_excluded < 0:
        violations.append("n_toy_excluded must be >= 0")

    # novel_family requires at least one hard evidence type (not insufficient_evidence or expert_assessment alone)
    if cfc.novelty_verdict == "novel_family":
        hard_evidence = {"blast_search_no_hits", "hmm_profile_no_match", "structural_divergence", "charge_length_outside_known"}
        if not any(net in hard_evidence for net in cfc.novelty_evidence_types):
            violations.append(
                "novelty_verdict='novel_family' requires at least one hard evidence type "
                "(blast_search_no_hits, hmm_profile_no_match, structural_divergence, or charge_length_outside_known)"
            )

    # variant_of_known requires known_family_hits
    if cfc.novelty_verdict == "variant_of_known" and not cfc.known_family_hits:
        violations.append(
            "novelty_verdict='variant_of_known' requires at least one entry in known_family_hits"
        )

    if not cfc.dry_lab_only:
        violations.append("dry_lab_only must be True for CFC- records (clustering is a computational result)")

    if not cfc.limitations or len(cfc.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    # pairwise similarity consistency
    if cfc.min_pairwise_similarity is not None and cfc.max_pairwise_similarity is not None:
        if cfc.min_pairwise_similarity > cfc.max_pairwise_similarity:
            violations.append(
                f"min_pairwise_similarity ({cfc.min_pairwise_similarity}) cannot exceed max_pairwise_similarity ({cfc.max_pairwise_similarity})"
            )

    return CFCValidationResult(valid=len(violations) == 0, violations=violations)


def build_candidate_family_clustering(
    cfc_id: str,
    family_name: str,
    candidate_ids: List[str],
    clustering_method: str,
    similarity_threshold: float,
    novelty_evidence_types: List[str],
    novelty_verdict: str,
    n_toy_excluded: int,
    known_family_hits: List[str],
    limitations: str,
    notes: str = "",
    min_pairwise_similarity: Optional[float] = None,
    max_pairwise_similarity: Optional[float] = None,
) -> CandidateFamilyClustering:
    cfc = CandidateFamilyClustering(
        cfc_id=cfc_id,
        family_name=family_name,
        candidate_ids=candidate_ids,
        clustering_method=clustering_method,
        similarity_threshold=similarity_threshold,
        novelty_evidence_types=novelty_evidence_types,
        novelty_verdict=novelty_verdict,
        n_candidates=len(candidate_ids),
        n_toy_excluded=n_toy_excluded,
        known_family_hits=known_family_hits,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
        min_pairwise_similarity=min_pairwise_similarity,
        max_pairwise_similarity=max_pairwise_similarity,
    )
    result = validate_candidate_family_clustering(cfc)
    if not result.valid:
        raise ValueError(f"Invalid CFC: {result.violations}")
    return cfc


def format_candidate_family_clustering(cfc: CandidateFamilyClustering) -> str:
    lines = [
        f"Candidate Family Clustering — {cfc.cfc_id}",
        f"Family: {cfc.family_name}",
        f"Novelty Verdict: {cfc.novelty_verdict}",
        f"Clustering Method: {cfc.clustering_method}  |  Similarity Threshold: {cfc.similarity_threshold:.3f}",
        f"Candidates: {cfc.n_candidates} ({', '.join(cfc.candidate_ids[:3])}{'...' if len(cfc.candidate_ids) > 3 else ''})",
        f"TOY Excluded: {cfc.n_toy_excluded}",
        f"Novelty Evidence: {', '.join(cfc.novelty_evidence_types)}",
    ]
    if cfc.known_family_hits:
        lines.append(f"Known Family Hits: {', '.join(cfc.known_family_hits)}")
    if cfc.min_pairwise_similarity is not None and cfc.max_pairwise_similarity is not None:
        lines.append(f"Pairwise Similarity Range: [{cfc.min_pairwise_similarity:.3f}, {cfc.max_pairwise_similarity:.3f}]")
    lines.append(f"Limitations: {cfc.limitations}")
    if cfc.notes:
        lines.append(f"Notes: {cfc.notes}")
    lines.append("dry_lab_only: True (computational clustering result)")
    return "\n".join(lines)
