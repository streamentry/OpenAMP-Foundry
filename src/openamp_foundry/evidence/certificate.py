from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from openamp_foundry import __version__
from openamp_foundry.types import ScoredCandidate
from openamp_foundry.utils.hashing import stable_json_hash


def _infer_proof_ladder_level(scored: ScoredCandidate) -> str:
    """Infer highest proof-ladder level supported by this candidate's evidence.

    Pipeline outputs are multi_signal_candidate_evidence (Level 4) by default:
    they have feature extraction, multiple independent scorers, novelty checking,
    and diversity selection. Lower levels apply only if key signals are missing.
    """
    scores = scored.scores
    has_multi_signal = (
        scores.get("activity", 0) > 0
        and scores.get("safety", 0) > 0
        and scores.get("novelty", 0) > 0
    )
    if not has_multi_signal:
        return "baseline_triaged"
    return "multi_signal_candidate_evidence"


def build_certificate(
    scored: ScoredCandidate,
    config: dict[str, Any],
    references_checked: list[str],
) -> dict[str, Any]:
    return {
        "candidate_id": scored.candidate.candidate_id,
        "sequence": scored.candidate.sequence,
        "source": scored.candidate.source,
        "features": scored.features,
        "scores": scored.scores,
        "nearest_reference": scored.nearest_reference,
        "references_checked": references_checked,
        "selection_reason": scored.selection_reason,
        "known_failure_modes": scored.known_failure_modes,
        "recommended_next_steps": [
            "Independent domain expert review before any assay decision.",
            "If reviewed positively, consider standard non-dangerous MIC and safety assays through qualified professionals or CROs.",
            "Do not claim antimicrobial activity without experimental validation.",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": __version__,
        "config_hash": stable_json_hash(config),
        "proof_ladder_level": _infer_proof_ladder_level(scored),
    }
