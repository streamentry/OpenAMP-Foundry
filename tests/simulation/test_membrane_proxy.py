"""Tests for the membrane interaction proxy."""

import pytest

from openamp_foundry.simulation.interfaces import SimulationResult
from openamp_foundry.simulation.membrane import (
    BomanBaseline,
    MembraneProxy,
    _mean_scale,
    _normalize_negative,
    _normalize_positive,
    _selectivity_ratio,
    _uncertainty,
)

_MAGAININ = "GIGKFLHSAKKFGKAFVGEIMNS"
_MELITTIN = "GIGAVLKVLTTGLPALISWIKRKRQQ"


def test_mean_scale_full_match():
    score = _mean_scale("AAAA", {"A": 1.0, "C": 2.0})
    assert score == 1.0


def test_mean_scale_empty():
    assert _mean_scale("", {"A": 1.0}) == 0.0


def test_mean_scale_partial_match():
    score = _mean_scale("AXA", {"A": 2.0, "X": 1.0})
    assert score == pytest.approx(1.6667, rel=1e-3)


def test_normalize_negative_at_lo():
    assert _normalize_negative(-2.0) == 1.0


def test_normalize_negative_at_hi():
    assert _normalize_negative(1.0) == 0.0


def test_normalize_negative_mid():
    val = _normalize_negative(-0.5)
    assert 0.4 < val < 0.6


def test_normalize_positive_at_lo():
    assert _normalize_positive(0.0) == 1.0


def test_normalize_positive_at_hi():
    assert _normalize_positive(1.5) == 0.0


def test_selectivity_ratio_bacterial_higher():
    r = _selectivity_ratio(0.9, 0.3)
    assert r > 1.0


def test_selectivity_ratio_mammalian_higher():
    r = _selectivity_ratio(0.3, 0.9)
    assert r < 1.0


def test_selectivity_ratio_clamps_at_2():
    r = _selectivity_ratio(0.9, 0.01)
    assert r == 2.0


def test_selectivity_ratio_zero_mammalian():
    assert _selectivity_ratio(0.5, 0.0) == 2.0


def test_uncertainty_short_sequence():
    u = _uncertainty("KK", 0.8, 0.3)
    assert u > 0.5


def test_uncertainty_long_sequence():
    u = _uncertainty("KKLFKKILKYLKKLFKKILKYL", 0.8, 0.3)
    assert u < 0.5


def test_membrane_proxy_returns_simulation_result():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert isinstance(result, SimulationResult)


def test_membrane_proxy_has_all_expected_scores():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    for key in ["bacterial_binding", "mammalian_binding", "selectivity_ratio",
                "raw_interfacial_mean", "raw_octanol_mean", "hydrophobic_moment"]:
        assert key in result.scores, f"Missing score: {key}"


def test_membrane_proxy_bacterial_binding_in_range():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert 0.0 <= result.scores["bacterial_binding"] <= 1.0


def test_membrane_proxy_mammalian_binding_in_range():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert 0.0 <= result.scores["mammalian_binding"] <= 1.0


def test_membrane_proxy_selectivity_ratio_in_range():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert 0.0 <= result.scores["selectivity_ratio"] <= 2.0


def test_membrane_proxy_uncertainty_in_range():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert 0.0 <= result.uncertainty <= 1.0


def test_membrane_proxy_scope():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert "bacterial_membrane_binding" in result.scope
    assert "mammalian_membrane_binding" in result.scope
    assert "selectivity_ratio" in result.scope


def test_membrane_proxy_has_baseline():
    proxy = MembraneProxy()
    baseline = proxy.get_baseline()
    score = baseline.evaluate(_MAGAININ)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_membrane_proxy_uncertainty_label():
    proxy = MembraneProxy()
    result = proxy.simulate(_MAGAININ)
    assert "Uncertainty > 0.5 = experimental" in result.notes[3]


def test_boman_baseline():
    baseline = BomanBaseline()
    score = baseline.evaluate(_MAGAININ)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert score >= 0.0  # clamped


def test_magainin_more_selective_than_melittin():
    """Known biological fact: magainin is more selective (bacterial vs mammalian)
    than melittin (which is broadly hemolytic). The selectivity ratio should
    reflect this."""
    proxy = MembraneProxy()
    mag = proxy.simulate(_MAGAININ)
    mel = proxy.simulate(_MELITTIN)
    assert mag.scores["selectivity_ratio"] > mel.scores["selectivity_ratio"]


def test_membrane_proxy_version():
    proxy = MembraneProxy(version="test_v")
    result = proxy.simulate(_MAGAININ)
    assert result.version == "test_v"


def test_membrane_proxy_scores_different_for_different_sequences():
    proxy = MembraneProxy()
    mag = proxy.simulate(_MAGAININ)
    mel = proxy.simulate(_MELITTIN)
    assert mag.scores["bacterial_binding"] != mel.scores["bacterial_binding"]


def test_empty_sequence():
    proxy = MembraneProxy()
    result = proxy.simulate("")
    assert 0.0 <= result.scores["bacterial_binding"] <= 1.0
    assert result.uncertainty > 0.5
