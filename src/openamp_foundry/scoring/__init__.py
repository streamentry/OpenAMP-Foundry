"""Scoring layer for OpenAMP Foundry.

Transparent, dependency-light scorers used to rank candidate peptides
along activity, safety, synthesis feasibility, novelty, hemolysis
risk, selectivity, and serum stability axes. All scorers accept the
same `features` dict produced by `openamp_foundry.features.physchem`,
which keeps composition-level decisions auditable.
"""

from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.boman import (
    boman_activity_score,
    boman_index,
    gravy_score,
    model_disagreement,
)
from openamp_foundry.scoring.ensemble import (
    ensemble_score,
    known_failure_modes,
    selection_reasons,
)
from openamp_foundry.scoring.expert import (
    EXPERT_WEIGHTS,
    ExpertScore,
    build_kmer_index,
    expert_score,
    helix_hinge_analysis,
    kmer_prior_art,
)
from openamp_foundry.scoring.hemolysis import (
    hemolysis_risk_score,
    hemolysis_safety_component,
)
from openamp_foundry.scoring.macrel_local import (
    MacrelResult,
    available as macrel_available,
    score_batch as macrel_score_batch,
    score_one as macrel_score_one,
)
from openamp_foundry.scoring.novelty import (
    levenshtein,
    normalized_similarity,
    novelty_score,
)
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.selectivity_rich import (
    rich_selectivity_breakdown,
    rich_selectivity_score,
)
from openamp_foundry.scoring.stability import serum_stability_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score

__all__ = [
    # activity
    "activity_likeness_score",
    # boman
    "boman_activity_score",
    "boman_index",
    "gravy_score",
    "model_disagreement",
    # ensemble
    "ensemble_score",
    "known_failure_modes",
    "selection_reasons",
    # expert
    "EXPERT_WEIGHTS",
    "ExpertScore",
    "build_kmer_index",
    "expert_score",
    "helix_hinge_analysis",
    "kmer_prior_art",
    # hemolysis
    "hemolysis_risk_score",
    "hemolysis_safety_component",
    # macrel_local (optional local fallback for external AMP predictor)
    "MacrelResult",
    "macrel_available",
    "macrel_score_batch",
    "macrel_score_one",
    # novelty
    "levenshtein",
    "normalized_similarity",
    "novelty_score",
    # safety
    "safety_score",
    # selectivity_rich
    "rich_selectivity_breakdown",
    "rich_selectivity_score",
    # stability
    "serum_stability_score",
    # synthesis
    "synthesis_feasibility_score",
]
