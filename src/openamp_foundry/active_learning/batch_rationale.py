"""Batch-2 rationale report: explains why each candidate was selected.

Decomposes the batch-2 selection into exploit, explore, and diversity roles
so that reviewers can understand the selection logic at the per-candidate
level. Every role explanation is based on the same ``select_batch_2``
weights and scores — no additional modelling.

Role definitions:

- **exploit**: candidate selected primarily for high ensemble score
  (ensemble_weight contribution dominates).
- **explore**: candidate selected primarily for high uncertainty
  (uncertainty_weight contribution dominates).
- **diversity**: candidate selected primarily for structural novelty
  vs batch-1 (diversity_weight contribution dominates).
- **combined**: balanced contributions from all three weights —
  the production selector default.
- **safety_gated**: candidate was blocked by the safety or
  selectivity gate.

This report is informational and requires qualified human review
before influencing selection decisions.
"""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_VERSION = "0.1.0"

# Default selector weights
_DEFAULT_ENSEMBLE_WEIGHT = 0.40
_DEFAULT_UNCERTAINTY_WEIGHT = 0.30
_DEFAULT_DIVERSITY_WEIGHT = 0.30


def _classify_role(
    ensemble_contrib: float,
    uncertainty_contrib: float,
    diversity_contrib: float,
) -> str:
    """Classify a candidate's selection role based on which weight
    contribution dominates.

    Returns one of 'exploit', 'explore', 'diversity', or 'combined'.
    """
    contributions = [
        ("exploit", ensemble_contrib),
        ("explore", uncertainty_contrib),
        ("diversity", diversity_contrib),
    ]
    contributions.sort(key=lambda x: x[1], reverse=True)
    top_role, top_val = contributions[0]
    second_val = contributions[1][1]

    if top_val > second_val + 0.05:
        return top_role
    return "combined"


@dataclass(frozen=True)
class PerCandidateRationale:
    """Rationale for a single candidate's selection."""

    candidate_id: str
    role: str
    ensemble_score: float
    uncertainty_score: float
    diversity_score: float
    ensemble_contribution: float
    uncertainty_contribution: float
    diversity_contribution: float
    combined_score: float
    passed_safety_gate: bool
    safety_gate_reason: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "role": self.role,
            "ensemble_score": self.ensemble_score,
            "uncertainty_score": self.uncertainty_score,
            "diversity_score": self.diversity_score,
            "ensemble_contribution": self.ensemble_contribution,
            "uncertainty_contribution": self.uncertainty_contribution,
            "diversity_contribution": self.diversity_contribution,
            "combined_score": self.combined_score,
            "passed_safety_gate": self.passed_safety_gate,
            "safety_gate_reason": self.safety_gate_reason,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class BatchRationaleReport:
    """Report explaining the batch-2 selection rationale."""

    version: str
    pool_size: int
    n_requested: int
    n_selected: int
    n_after_safety_gate: int
    n_gated_out: int
    ensemble_weight: float
    uncertainty_weight: float
    diversity_weight: float
    candidates: tuple[PerCandidateRationale, ...]
    role_summary: dict[str, int]
    role_descriptions: dict[str, str]
    selected_ids: tuple[str, ...]
    probes_in_top_n: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "pool_size": self.pool_size,
            "n_requested": self.n_requested,
            "n_selected": self.n_selected,
            "n_after_safety_gate": self.n_after_safety_gate,
            "n_gated_out": self.n_gated_out,
            "ensemble_weight": self.ensemble_weight,
            "uncertainty_weight": self.uncertainty_weight,
            "diversity_weight": self.diversity_weight,
            "candidates": [c.to_dict() for c in self.candidates],
            "role_summary": self.role_summary,
            "role_descriptions": self.role_descriptions,
            "selected_ids": list(self.selected_ids),
            "probes_in_top_n": self.probes_in_top_n,
            "notes": list(self.notes),
        }


def _generate_pool(
    *,
    n_total: int = 50,
    n_active: int = 10,
    rng_seed: int = 42,
) -> list[dict]:
    """Generate a synthetic candidate pool for the rationale report.

    Active candidates get higher ensemble scores and lower disagreement
    to create a realistic mix of exploit/explore/diversity candidates.
    """
    rng = random.Random(rng_seed)
    pool: list[dict] = []
    for i in range(n_total):
        is_active = i < n_active
        cid = f"RATIONAL-CAND-{i:04d}"
        if is_active:
            ensemble = rng.uniform(0.75, 0.95)
            disagreement = rng.uniform(0.05, 0.20)
        else:
            ensemble = rng.uniform(0.30, 0.55)
            disagreement = rng.uniform(0.20, 0.50)
        pool.append({
            "pilot_rank": str(i + 1),
            "candidate_id": cid,
            "sequence": f"PEPTIDE{i:04d}AKLF",
            "length": 12,
            "seed": "RATIONAL-SEED",
            "ensemble": round(ensemble, 4),
            "activity": round(ensemble, 4),
            "boman_activity": "0.50",
            "disagreement": round(disagreement, 4),
            "safety": "0.90",
            "synthesis": "0.85",
            "novelty": "0.70",
            "serum_stability": "0.65",
            "selectivity_proxy": "0.60",
            "rich_selectivity": "0.75",
            "pilot_priority": "0.75",
            "amphipathic_score": "1.5",
            "charge_ph74": "4.0",
            "label": 1 if is_active else 0,
        })
    return pool


def _write_pool(pool: list[dict], path: Path) -> Path:
    fieldnames = list(pool[0].keys()) if pool else []
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in pool:
            writer.writerow(row)
    return path


def build_batch_rationale_report(
    *,
    n_total: int = 50,
    n_active: int = 10,
    batch_size: int = 10,
    safety_threshold: float = 0.5,
    selectivity_threshold: float = 0.5,
    ensemble_weight: float = _DEFAULT_ENSEMBLE_WEIGHT,
    uncertainty_weight: float = _DEFAULT_UNCERTAINTY_WEIGHT,
    diversity_weight: float = _DEFAULT_DIVERSITY_WEIGHT,
    min_uncertainty_probes: int = 1,
    rng_seed: int = 42,
) -> BatchRationaleReport:
    """Build a batch-2 rationale report from a synthetic pool.

    Generates a synthetic candidate pool with known active/inactive labels,
    runs ``select_batch_2`` with the specified weights, and produces a
    per-candidate rationale report classifying each selected candidate
    into exploit / explore / diversity / combined roles.

    All data is synthetic. The report is a code-path integrity check,
    not biological evidence.

    Returns:
        ``BatchRationaleReport`` with per-candidate rationales and
        role summary.
    """
    from openamp_foundry.active_learning.selector import (
        _compute_diversity_vs_batch,
        _compute_uncertainty,
        _passes_safety_gate,
        _safe_float,
        select_batch_2,
    )

    import tempfile

    rng = random.Random(rng_seed)
    pool = _generate_pool(
        n_total=n_total,
        n_active=n_active,
        rng_seed=rng_seed,
    )

    all_ids = [str(c["candidate_id"]) for c in pool]
    batch_1_ids = rng.sample(all_ids, max(1, n_total // 5))
    batch_1_rows = [c for c in pool if str(c.get("candidate_id", "")) in batch_1_ids]
    batch_1_sequences = [str(c.get("sequence", "")) for c in batch_1_rows]

    pool_csv = Path(tempfile.mktemp(suffix=".csv"))
    try:
        _write_pool(pool, pool_csv)

        selection = select_batch_2(
            candidates_csv=pool_csv,
            batch_1_ids=batch_1_ids,
            n=batch_size,
            safety_threshold=safety_threshold,
            selectivity_threshold=selectivity_threshold,
            ensemble_weight=ensemble_weight,
            uncertainty_weight=uncertainty_weight,
            diversity_weight=diversity_weight,
            min_uncertainty_probes=min_uncertainty_probes,
        )
    finally:
        pool_csv.unlink(missing_ok=True)

    # Count gated-out candidates
    n_gated_out = selection.n_remaining - selection.n_after_safety_gate

    # Build per-candidate rationales
    candidates_list: list[PerCandidateRationale] = []
    for sel in selection.selected:
        cid = str(sel.get("candidate_id", "?"))
        ens = _safe_float(sel.get("ensemble"), default=0.0)
        unc = _compute_uncertainty(sel)
        div = _compute_diversity_vs_batch(
            str(sel.get("sequence", "")),
            batch_1_sequences,
        )

        ens_contrib = ensemble_weight * ens
        unc_contrib = uncertainty_weight * unc
        div_contrib = diversity_weight * div
        combined = ens_contrib + unc_contrib + div_contrib

        passes, reason = _passes_safety_gate(
            sel,
            safety_threshold=safety_threshold,
            selectivity_threshold=selectivity_threshold,
        )

        role = _classify_role(ens_contrib, unc_contrib, div_contrib)

        if role == "exploit":
            explanation = (
                f"Candidate {cid} selected primarily for high ensemble score "
                f"(ensemble contribution {ens_contrib:.3f} dominates). "
                f"Exploitation targets known high-scoring regions."
            )
        elif role == "explore":
            explanation = (
                f"Candidate {cid} selected primarily for high uncertainty "
                f"(uncertainty contribution {unc_contrib:.3f} dominates). "
                f"Exploration probes model blind spots."
            )
        elif role == "diversity":
            explanation = (
                f"Candidate {cid} selected primarily for structural novelty "
                f"vs batch-1 (diversity contribution {div_contrib:.3f} dominates). "
                f"Diversity expands sequence space coverage."
            )
        else:
            explanation = (
                f"Candidate {cid} selected with balanced contributions "
                f"(ensemble {ens_contrib:.3f}, uncertainty {unc_contrib:.3f}, "
                f"diversity {div_contrib:.3f}). Combined production tradeoff."
            )

        candidates_list.append(PerCandidateRationale(
            candidate_id=cid,
            role=role,
            ensemble_score=round(ens, 4),
            uncertainty_score=round(unc, 4),
            diversity_score=round(div, 4),
            ensemble_contribution=round(ens_contrib, 4),
            uncertainty_contribution=round(unc_contrib, 4),
            diversity_contribution=round(div_contrib, 4),
            combined_score=round(combined, 4),
            passed_safety_gate=passes,
            safety_gate_reason=reason,
            explanation=explanation,
        ))

    # Build role summary
    role_summary: dict[str, int] = {}
    for c in candidates_list:
        role_summary[c.role] = role_summary.get(c.role, 0) + 1

    role_descriptions = {
        "exploit": (
            "Candidates selected primarily for high ensemble score — exploitation "
            "targets known high-scoring regions of sequence space."
        ),
        "explore": (
            "Candidates selected primarily for high uncertainty — exploration probes "
            "model blind spots where the ensemble is most uncertain."
        ),
        "diversity": (
            "Candidates selected primarily for structural novelty vs batch-1 — "
            "diversity expands sequence space coverage."
        ),
        "combined": (
            "Candidates selected with balanced contributions from all three weights — "
            "production tradeoff between exploitation, exploration, and diversity."
        ),
    }

    selected_ids = tuple(
        str(c.get("candidate_id", "")) for c in selection.selected
    )

    notes: list[str] = []
    notes.append(
        f"Pool: {len(pool)} total candidates across {n_active} active "
        f"(label=1) and {len(pool) - n_active} inactive (label=0)."
    )
    notes.append(
        f"Batch-2 requested: {batch_size}, selected: {len(candidates_list)}, "
        f"gated-out: {n_gated_out}."
    )
    notes.append(
        "Role classification is based on which weight contribution dominates "
        "(threshold: > 0.05 above second-place contribution)."
    )
    if selection.notes:
        notes.extend(selection.notes)

    return BatchRationaleReport(
        version=_VERSION,
        pool_size=len(pool),
        n_requested=batch_size,
        n_selected=len(candidates_list),
        n_after_safety_gate=selection.n_after_safety_gate,
        n_gated_out=n_gated_out,
        ensemble_weight=ensemble_weight,
        uncertainty_weight=uncertainty_weight,
        diversity_weight=diversity_weight,
        candidates=tuple(candidates_list),
        role_summary=role_summary,
        role_descriptions=role_descriptions,
        selected_ids=selected_ids,
        probes_in_top_n=selection.probes_in_top_n,
        notes=tuple(notes),
    )


def write_rationale_json(
    report: BatchRationaleReport,
    path: Path,
) -> Path:
    """Write the rationale report to a JSON file."""
    import json
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return path


def write_rationale_markdown(
    report: BatchRationaleReport,
    path: Path,
) -> Path:
    """Write a human-readable Markdown rationale report."""
    lines: list[str] = []
    lines.append("# Batch-2 Selection Rationale Report")
    lines.append("")
    lines.append(f"> **Version:** {report.version}")
    lines.append(f"> **Generated:** auto")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        f"Generated rationale report for batch-2 selection from a synthetic pool of "
        f"**{report.pool_size}** candidates."
    )
    lines.append(
        f"Requested: **{report.n_requested}**, Selected: **{report.n_selected}**, "
        f"Gated out: **{report.n_gated_out}**."
    )
    lines.append("")

    # Weight configuration
    lines.append("## Selection Weights")
    lines.append("")
    lines.append("| Role | Weight | Description |")
    lines.append("|------|:-----:|-------------|")
    wmap = [
        ("Exploitation (ensemble)", report.ensemble_weight,
         "Rewards high ensemble score"),
        ("Exploration (uncertainty)", report.uncertainty_weight,
         "Rewards high model uncertainty"),
        ("Diversity (diversity)", report.diversity_weight,
         "Rewards structural novelty vs batch-1"),
    ]
    for label, weight, desc in wmap:
        lines.append(f"| {label} | {weight} | {desc} |")
    lines.append("")

    # Role summary
    lines.append("## Selection Breakdown by Role")
    lines.append("")
    lines.append("| Role | Count | Description |")
    lines.append("|------|:-----:|-------------|")
    for role in ("exploit", "explore", "diversity", "combined"):
        count = report.role_summary.get(role, 0)
        desc = report.role_descriptions.get(role, "")
        lines.append(f"| {role} | {count} | {desc} |")
    lines.append("")

    # Per-candidate rationales
    lines.append("## Per-Candidate Rationale")
    lines.append("")
    lines.append(
        "| Candidate ID | Role | Ensemble | Uncertainty | Diversity | "
        "Combined | Explanation |"
    )
    lines.append(
        "|:-------------|:----:|:--------:|:-----------:|:---------:|:--------:|:------------|"
    )
    for c in report.candidates:
        lines.append(
            f"| {c.candidate_id} | {c.role} | {c.ensemble_score} | "
            f"{c.uncertainty_score} | {c.diversity_score} | "
            f"{c.combined_score} | {c.explanation} |"
        )
    lines.append("")

    # Role contribution detail
    lines.append("## Contribution Detail")
    lines.append("")
    lines.append(
        "| Candidate ID | Role | Ensemble×W | Uncert×W | Diversity×W | "
        "Classification basis |"
    )
    lines.append(
        "|:-------------|:----:|:----------:|:---------:|:------------:|:---------------------|"
    )
    for c in report.candidates:
        basis = (
            f"ensemble dominates" if c.role == "exploit"
            else f"uncertainty dominates" if c.role == "explore"
            else f"diversity dominates" if c.role == "diversity"
            else f"balanced contributions"
        )
        lines.append(
            f"| {c.candidate_id} | {c.role} | {c.ensemble_contribution} | "
            f"{c.uncertainty_contribution} | {c.diversity_contribution} | {basis} |"
        )
    lines.append("")

    # Safety gate info
    if report.n_gated_out > 0:
        lines.append("## Safety Gate")
        lines.append("")
        lines.append(
            f"**{report.n_gated_out}** candidates were gated out by safety/"
            f"selectivity thresholds (safety >= {0.5}, "
            f"selectivity >= {0.5})."
        )
        lines.append(
            "Gated-out candidates are not available for selection."
        )
        lines.append("")

    # Caveat
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- This report uses **synthetic data** with known labels. "
        "Results reflect code-path integrity, not biological performance."
    )
    lines.append(
        "- Role classification threshold: a role is assigned when its "
        "weighted contribution exceeds the second-best by > 0.05. "
        "Candidates near the boundary are classified as 'combined'."
    )
    lines.append(
        "- The production selector optimises for multiple objectives "
        "(activity, safety, diversity) that a single-role label does not capture."
    )
    lines.append(
        "- This report is informational and requires qualified human review "
        "before influencing selection decisions."
    )

    path.write_text("\n".join(lines) + "\n")
    return path
