from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from openamp_foundry import __version__
from openamp_foundry.types import ScoredCandidate
from openamp_foundry.utils.hashing import stable_json_hash

# Cheap-baseline thresholds for AMP selection heuristics.
# These define what a simple rule-based filter would pass —
# a candidate passing all three is explainable without ML.
_BASELINE_MIN_CHARGE = 4
_BASELINE_LENGTH_MIN = 10
_BASELINE_LENGTH_MAX = 40
_BASELINE_MIN_HYDROPHOBIC_FRACTION = 0.30


def _infer_proof_ladder_level(scored: ScoredCandidate) -> str:
    scores = scored.scores
    has_multi_signal = (
        scores.get("activity", 0) > 0
        and scores.get("safety", 0) > 0
        and scores.get("novelty", 0) > 0
    )
    if not has_multi_signal:
        return "baseline_triaged"
    return "multi_signal_candidate_evidence"


def _build_baseline_caveat(scored: ScoredCandidate) -> str:
    features = scored.features
    charge = float(features.get("net_charge_proxy", 0))
    length = int(features.get("length", 0))
    hydro = float(features.get("hydrophobic_fraction", 0.0))

    charge_passes = charge >= _BASELINE_MIN_CHARGE
    length_passes = _BASELINE_LENGTH_MIN <= length <= _BASELINE_LENGTH_MAX
    hydro_passes = hydro >= _BASELINE_MIN_HYDROPHOBIC_FRACTION

    flags_yes = sum([charge_passes, length_passes, hydro_passes])

    charge_flag = "YES" if charge_passes else "NO"
    length_flag = "YES" if length_passes else "NO"
    hydro_flag = "YES" if hydro_passes else "NO"

    if flags_yes == 3:
        residual_note = (
            "All three baseline flags pass — a simple conjunction rule "
            "(charge\u22654 AND length 10-40 AND hydrophobicity\u22650.30) would select "
            "this candidate without ML scoring. Residual ML signal must exceed "
            "this baseline to justify pipeline use."
        )
    elif flags_yes == 2:
        residual_note = (
            "Two of three baseline flags pass — candidate partially explainable "
            "by heuristic rules. Verify ML residual is non-trivial."
        )
    elif flags_yes == 1:
        residual_note = (
            "One of three baseline flags passes — candidate unlikely to be "
            "selected by simple heuristics alone."
        )
    else:
        residual_note = (
            "No baseline flags pass — candidate cannot be explained by the "
            "standard cheap heuristics; ML signal is dominant."
        )

    return (
        f"Cheapest-explanation check: "
        f"charge={charge:.1f} (\u2265{_BASELINE_MIN_CHARGE} passes: {charge_flag}), "
        f"length={length} ({_BASELINE_LENGTH_MIN}-{_BASELINE_LENGTH_MAX} aa range: {length_flag}), "
        f"hydrophobic_fraction={hydro:.2f} (\u2265{_BASELINE_MIN_HYDROPHOBIC_FRACTION:.2f} passes: {hydro_flag}). "
        f"{residual_note}"
    )


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
        "baseline_caveat": _build_baseline_caveat(scored),
    }
