"""Verify hemolysis risk scorer has expected behavior on controls."""
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.hemolysis import hemolysis_risk_score


def test_known_hemolytic_peptide_scores_higher_than_neutral():
    """Melittin (known hemolytic) should get higher hemolysis risk than poly-G."""
    features_mel = compute_features("GIGAVLKVLTTGLPALISWIKRKRQQ")
    features_polyg = compute_features("GGGGGGGGGG")
    risk_mel = hemolysis_risk_score(features_mel)
    risk_polyg = hemolysis_risk_score(features_polyg)
    assert risk_mel > risk_polyg, (
        f"Melittin hemolysis risk {risk_mel} should exceed poly-G {risk_polyg}"
    )


def test_hemolysis_risk_in_range():
    features = compute_features("GIGAVLKVLTTGLPALISWIKRKRQQ")
    risk = hemolysis_risk_score(features)
    assert 0 <= risk <= 1, f"Hemolysis risk {risk} should be in [0, 1]"
