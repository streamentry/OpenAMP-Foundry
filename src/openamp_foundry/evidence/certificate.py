from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from openamp_foundry import __version__
from openamp_foundry.types import ScoredCandidate
from openamp_foundry.utils.hashing import stable_json_hash


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
    }
