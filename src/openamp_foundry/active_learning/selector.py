"""Batch-2 candidate selector: uncertainty, diversity, safety gating.

Picks the next N candidates for lab testing after an initial batch has been
assayed and the recalibration pipeline has run. This is a **selection triage**
module, not a scorer or predictor. All scores are pipeline-produced.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)

_SELECTOR_VERSION = "0.1.0"


@dataclass(frozen=True)
class BatchSelection:
    """Result of batch-2 selection."""

    version: str
    n_requested: int
    n_remaining: int
    n_after_safety_gate: int
    selected: tuple[dict, ...]
    probes_in_top_n: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "n_requested": self.n_requested,
            "n_remaining": self.n_remaining,
            "n_after_safety_gate": self.n_after_safety_gate,
            "selected": list(self.selected),
            "probes_in_top_n": self.probes_in_top_n,
            "notes": list(self.notes),
        }


def _load_candidates(csv_path: Path) -> list[dict]:
    """Load candidates from a panel CSV."""
    rows: list[dict] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed: dict[str, float | int | str] = {}
            for k, v in row.items():
                k = k.strip()
                if v is None:
                    parsed[k] = None
                else:
                    v = v.strip()
                # Try numeric conversion
                try:
                    parsed[k] = float(v)
                except (ValueError, TypeError):
                    try:
                        parsed[k] = int(v)
                    except (ValueError, TypeError):
                        parsed[k] = v
            rows.append(parsed)
    return rows


def _safe_float(val: object, default: float = 0.0) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    return default


def _compute_uncertainty(row: dict) -> float:
    """Compute an uncertainty score in [0, 1] for a candidate.

    Uses the pipeline's built-in ``disagreement`` field (when available)
    and complements it with the distance of the ``ensemble`` score from 0.5
    (the most uncertain region for a binary classifier).

    A value of 1.0 means maximum uncertainty; 0.0 means complete certainty.
    """
    disagreement = _safe_float(row.get("disagreement"), default=0.0)

    ensemble = _safe_float(row.get("ensemble"), default=0.5)
    ensemble_distance = 1.0 - 2.0 * abs(ensemble - 0.5)
    ensemble_distance = max(0.0, min(1.0, ensemble_distance))

    return max(disagreement, ensemble_distance)


def _compute_diversity_vs_batch(
    sequence: str,
    batch_1_sequences: list[str],
) -> float:
    """Compute diversity score for a candidate relative to a set of sequences.

    Uses ``normalized_similarity`` from the novelty module. A score of 1.0
    means the candidate is completely novel relative to batch 1 (maximally
    diverse); 0.0 means it is identical to at least one batch-1 candidate.
    """
    if not batch_1_sequences or not sequence:
        return 1.0
    from openamp_foundry.scoring.novelty import normalized_similarity

    max_sim = max(
        normalized_similarity(sequence, other)
        for other in batch_1_sequences
    )
    return 1.0 - max_sim


def _passes_safety_gate(
    row: dict,
    safety_threshold: float = 0.5,
    selectivity_threshold: float = 0.5,
) -> tuple[bool, str]:
    """Check whether a candidate passes the safety gate.

    Returns (passes, reason).
    """
    reasons: list[str] = []

    safety = _safe_float(row.get("safety"), default=1.0)
    if safety < safety_threshold:
        reasons.append(
            f"safety={safety:.3f} < {safety_threshold:.3f}"
        )

    selectivity = _safe_float(row.get("rich_selectivity"))
    if not selectivity:
        selectivity = _safe_float(row.get("selectivity_proxy"), default=1.0)
    if selectivity < selectivity_threshold:
        reasons.append(
            f"selectivity={selectivity:.3f} < {selectivity_threshold:.3f}"
        )

    if reasons:
        return False, "; ".join(reasons)
    return True, "passes gate"


def select_batch_2(
    candidates_csv: str | Path,
    batch_1_ids: list[str],
    *,
    n: int = 10,
    safety_threshold: float = 0.5,
    selectivity_threshold: float = 0.5,
    ensemble_weight: float = 0.40,
    uncertainty_weight: float = 0.30,
    diversity_weight: float = 0.30,
    min_uncertainty_probes: int = 1,
) -> BatchSelection:
    """Select the next batch of candidates for lab testing.

    Args:
        candidates_csv: Path to the full candidate pool CSV (same format as
            the pilot panel CSV with columns: candidate_id, sequence,
            ensemble, activity, disagreement, safety, novelty, etc.).
        batch_1_ids: List of candidate IDs already tested in batch 1.
        n: Desired batch-2 size.
        safety_threshold: Minimum ``safety`` score (0-1) for a candidate to
            be eligible. Candidates below this are blocked.
        selectivity_threshold: Minimum ``rich_selectivity`` (or
            ``selectivity_proxy`` as fallback) score.
        ensemble_weight: Weight for the ensemble score in the combined rank.
        uncertainty_weight: Weight for the uncertainty score.
        diversity_weight: Weight for the diversity vs batch-1 score.
        min_uncertainty_probes: At least this many high-uncertainty
            candidates must appear in the final selection (to actively probe
            model blind spots).

    Returns:
        ``BatchSelection`` with the selected candidates (enriched with
        uncertainty, diversity, and selection reason metadata).
    """
    csv_path = Path(candidates_csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"Candidates CSV not found: {csv_path}")

    all_candidates = _load_candidates(csv_path)

    batch_1_set = set(batch_1_ids)
    batch_1_rows = [c for c in all_candidates if c.get("candidate_id") in batch_1_set]
    batch_1_sequences = [str(c.get("sequence", "")) for c in batch_1_rows]

    remaining = [
        c for c in all_candidates
        if c.get("candidate_id") not in batch_1_set
    ]

    if not remaining:
        return BatchSelection(
            version=_SELECTOR_VERSION,
            n_requested=n,
            n_remaining=0,
            n_after_safety_gate=0,
            selected=(),
            probes_in_top_n=0,
            notes=("No remaining candidates to select from.",),
        )

    # Compute scores and gate
    scored: list[tuple[float, dict, float, float, float, str]] = []
    n_gated_out = 0
    for row in remaining:
        passes, reason = _passes_safety_gate(
            row,
            safety_threshold=safety_threshold,
            selectivity_threshold=selectivity_threshold,
        )
        if not passes:
            n_gated_out += 1
            _log.debug(
                "Candidate %s gated out: %s",
                row.get("candidate_id", "?"), reason,
            )
            continue

        ensemble_score = _safe_float(row.get("ensemble"), default=0.0)
        uncertainty = _compute_uncertainty(row)
        diversity = _compute_diversity_vs_batch(
            str(row.get("sequence", "")),
            batch_1_sequences,
        )

        combined = (
            ensemble_weight * ensemble_score
            + uncertainty_weight * uncertainty
            + diversity_weight * diversity
        )

        scored.append((combined, row, ensemble_score, uncertainty, diversity, reason))

    if not scored:
        return BatchSelection(
            version=_SELECTOR_VERSION,
            n_requested=n,
            n_remaining=len(remaining),
            n_after_safety_gate=0,
            selected=(),
            probes_in_top_n=0,
            notes=(f"All {len(remaining)} remaining candidates failed the safety gate.",),
        )

    # Sort by combined score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Build selection with uncertainty probe guarantee
    selected_list: list[dict] = []
    notes: list[str] = []

    all_uncertainty_ranked = sorted(
        [s for s in scored if s[3] >= 0.6],
        key=lambda x: x[3], reverse=True,
    )

    probes_placed = 0
    taken_ids: set[str] = set()

    # Phase 1: place high-uncertainty probes if needed
    for _, row, _, _, _, _reason in all_uncertainty_ranked:
        if probes_placed >= min_uncertainty_probes:
            break
        cid = str(row.get("candidate_id", ""))
        if cid not in taken_ids:
            taken_ids.add(cid)
            row_meta = dict(row)
            row_meta["selection_reason"] = "high_uncertainty_probe"
            selected_list.append(row_meta)
            probes_placed += 1

    # Phase 2: fill remaining slots from top-ranked pool (skip taken)
    for _, row, ens, unc, div, _reason in scored:
        if len(selected_list) >= n:
            break
        cid = str(row.get("candidate_id", ""))
        if cid in taken_ids:
            continue
        taken_ids.add(cid)
        row_meta = dict(row)
        row_meta["selection_reason"] = (
            f"combined={ens * ensemble_weight + unc * uncertainty_weight + div * diversity_weight:.4f}; "
            f"ensemble={ens:.3f}, uncertainty={unc:.3f}, diversity={div:.3f}"
        )
        selected_list.append(row_meta)

    if probes_placed < min_uncertainty_probes:
        notes.append(
            f"Only {probes_placed}/{min_uncertainty_probes} high-uncertainty probes "
            f"found in eligible pool; fewer probes placed than requested."
        )

    if len(selected_list) < n:
        notes.append(
            f"Requested {n} but only {len(selected_list)} candidates "
            f"available after safety gating and deduplication."
        )

    n_after_gate = len(scored)

    return BatchSelection(
        version=_SELECTOR_VERSION,
        n_requested=n,
        n_remaining=len(remaining),
        n_after_safety_gate=n_after_gate,
        selected=tuple(selected_list),
        probes_in_top_n=probes_placed,
        notes=tuple(notes),
    )
