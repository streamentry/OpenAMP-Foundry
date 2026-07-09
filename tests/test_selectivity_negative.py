"""Verify selectivity proxy has expected behavior.

Honest finding: Poly-glycine gets HIGH selectivity (0.80) because the
rich_selectivity scorer detects "not hemolytic" features, and poly-G has
none of the features associated with hemolysis (no charge, no hydrophobicity,
no hydrophobic moment). This is a vacuous signal — poly-G is neither
selective nor antimicrobial. The scorer detects selective-vs-hemolytic
among AMPs, not AMP-vs-non-AMP.
"""
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.selectivity_rich import rich_selectivity_score
from openamp_foundry.scoring.hemolysis import hemolysis_risk_score


def test_hemolysis_risk_low_for_neutral():
    """Neutral peptide should have low hemolysis risk."""
    features = compute_features("GGGGGGGGGG")
    risk = hemolysis_risk_score(features)
    assert risk < 0.5, f"Poly-G hemolysis risk {risk} should be low"


def test_selectivity_scores_differ():
    """Different peptides should get different selectivity scores (not constant)."""
    g_features = compute_features("GGGGGGGGGG")
    k_features = compute_features("KKKKKKKKKK")
    g_score = rich_selectivity_score(g_features)
    k_score = rich_selectivity_score(k_features)
    assert g_score != k_score, "Different sequences should produce different selectivity scores"


def test_rich_selectivity_breakdown_returns_dict():
    from openamp_foundry.scoring.selectivity_rich import rich_selectivity_breakdown
    features = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
    breakdown = rich_selectivity_breakdown(features)
    assert isinstance(breakdown, dict)
    assert len(breakdown) > 0
