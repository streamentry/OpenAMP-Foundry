"""FIA- feature importance audit schema.

Documents which features drove selections and whether charge/length alone
explains the result. An anti-cheap-explanation gate: rejects candidate panels
where a single cheap feature (charge, length, hydrophobicity) recovers the
same top-k ordering as the full pipeline. Required before any novelty or
multi-feature claim.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_FIA_VERDICTS: frozenset[str] = frozenset({
    "multi_feature_signal",
    "charge_dominated",
    "length_dominated",
    "hydrophobicity_dominated",
    "insufficient_data",
})

VALID_FEATURE_IMPORTANCE_LEVELS: frozenset[str] = frozenset({
    "high",
    "moderate",
    "low",
    "negligible",
})

VALID_AUDIT_FEATURES: frozenset[str] = frozenset({
    "charge",
    "length",
    "hydrophobicity",
    "amphipathicity",
    "helicity",
    "sequence_motif",
    "secondary_structure",
    "physicochemical_composite",
})

DOMINATION_THRESHOLD: float = 0.80
MIN_FEATURES_FOR_AUDIT: int = 2


@dataclass
class FeatureImportanceEntry:
    feature_name: str
    importance_score: float
    importance_level: str


@dataclass
class FeatureImportanceAudit:
    fia_id: str
    pipeline_version: str
    feature_entries: list[FeatureImportanceEntry]
    top_feature: str
    top_feature_importance_score: float
    charge_importance_score: float
    length_importance_score: float
    charge_explains_fraction: float
    fia_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_feature_importance_audit(fia: FeatureImportanceAudit) -> None:
    if not fia.fia_id.startswith("FIA-"):
        raise ValueError(f"fia_id must start with 'FIA-': {fia.fia_id!r}")
    if not fia.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for entry in fia.feature_entries:
        if entry.feature_name not in VALID_AUDIT_FEATURES:
            raise ValueError(
                f"feature_name {entry.feature_name!r} not in VALID_AUDIT_FEATURES"
            )
        if not (0.0 <= entry.importance_score <= 1.0):
            raise ValueError(
                f"importance_score must be in [0, 1] for {entry.feature_name!r}: "
                f"{entry.importance_score}"
            )
        if entry.importance_level not in VALID_FEATURE_IMPORTANCE_LEVELS:
            raise ValueError(
                f"importance_level {entry.importance_level!r} not in "
                f"VALID_FEATURE_IMPORTANCE_LEVELS"
            )
    if not (0.0 <= fia.charge_explains_fraction <= 1.0):
        raise ValueError(
            f"charge_explains_fraction must be in [0, 1]: {fia.charge_explains_fraction}"
        )
    if fia.fia_verdict not in VALID_FIA_VERDICTS:
        raise ValueError(
            f"fia_verdict {fia.fia_verdict!r} not in VALID_FIA_VERDICTS"
        )
    if not fia.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not fia.limitations:
        raise ValueError("limitations must be non-empty")
    if not fia.created_at:
        raise ValueError("created_at must be non-empty")


def _assign_importance_level(score: float) -> str:
    if score >= 0.50:
        return "high"
    if score >= 0.20:
        return "moderate"
    if score >= 0.05:
        return "low"
    return "negligible"


def _compute_verdict(
    n_features: int,
    charge_explains_fraction: float,
    top_feature: str,
) -> str:
    if n_features < MIN_FEATURES_FOR_AUDIT:
        return "insufficient_data"
    if charge_explains_fraction >= DOMINATION_THRESHOLD:
        return "charge_dominated"
    if top_feature == "length":
        return "length_dominated"
    if top_feature == "hydrophobicity":
        return "hydrophobicity_dominated"
    return "multi_feature_signal"


def build_feature_importance_audit(
    *,
    fia_id: str,
    pipeline_version: str,
    feature_importance_dicts: list[dict],
    charge_explains_fraction: float,
    limitations: list[str],
    created_at: str,
) -> FeatureImportanceAudit:
    """Build a FeatureImportanceAudit.

    feature_importance_dicts: list of dicts with keys:
        feature_name, importance_score
        importance_level is auto-assigned from score.

    charge_explains_fraction: fraction [0,1] of top-k ordering explained
        by charge-only ranking (pre-computed externally).
    """
    entries = [
        FeatureImportanceEntry(
            feature_name=d["feature_name"],
            importance_score=float(d["importance_score"]),
            importance_level=_assign_importance_level(float(d["importance_score"])),
        )
        for d in feature_importance_dicts
    ]
    if entries:
        top_entry = max(entries, key=lambda e: e.importance_score)
        top_feature = top_entry.feature_name
        top_score = top_entry.importance_score
    else:
        top_feature = ""
        top_score = 0.0

    charge_entry = next(
        (e for e in entries if e.feature_name == "charge"), None
    )
    charge_score = charge_entry.importance_score if charge_entry else 0.0
    length_entry = next(
        (e for e in entries if e.feature_name == "length"), None
    )
    length_score = length_entry.importance_score if length_entry else 0.0

    verdict = _compute_verdict(len(entries), charge_explains_fraction, top_feature)
    fia = FeatureImportanceAudit(
        fia_id=fia_id,
        pipeline_version=pipeline_version,
        feature_entries=entries,
        top_feature=top_feature,
        top_feature_importance_score=top_score,
        charge_importance_score=charge_score,
        length_importance_score=length_score,
        charge_explains_fraction=float(charge_explains_fraction),
        fia_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_feature_importance_audit(fia)
    return fia


def format_feature_importance_audit(fia: FeatureImportanceAudit) -> str:
    lines = [
        f"Feature Importance Audit — {fia.fia_id}",
        f"Pipeline: {fia.pipeline_version}",
        f"Verdict: {fia.fia_verdict}",
        f"Top feature: {fia.top_feature} (score={fia.top_feature_importance_score:.3f})",
        f"Charge importance: {fia.charge_importance_score:.3f}  "
        f"Length importance: {fia.length_importance_score:.3f}",
        f"Charge explains fraction: {fia.charge_explains_fraction:.1%}",
    ]
    if fia.feature_entries:
        lines.append("Feature scores:")
        for entry in fia.feature_entries:
            lines.append(
                f"  {entry.feature_name}: {entry.importance_score:.3f} "
                f"({entry.importance_level})"
            )
    lines.append(f"Created: {fia.created_at}")
    lines.append(f"Limitations: {'; '.join(fia.limitations)}")
    lines.append(f"dry_lab_only: {fia.dry_lab_only}")
    return "\n".join(lines)
