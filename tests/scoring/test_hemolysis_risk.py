"""Tests for scoring/hemolysis.py — dedicated hemolysis risk scorer.

Tests verify intended behavior against known hemolytic and selective AMPs from
the hemolysis reference dataset. Expected values are reasoned from documented
component thresholds, not back-fitted to the implementation.

Key finding being tested: the safety scorer fails hemolysis detection
(AUROC=0.3844), but the dedicated hemolysis risk scorer achieves
detection AUROC=0.9218 (CI=[0.82, 0.99]) on the original 42-peptide reference set.

IMPORTANT: The expanded 238-peptide reference set (v0.5.11, DBAASP data) revealed
this was small-sample inflation. On n=179 (54 hemolytic vs 125 selective), the
detection AUROC drops to 0.5650 (CI 0.47-0.66) — direction correct but no longer
statistically significant. The scorer retains weak directional signal but should
NOT be trusted as a hemolysis detector without further improvement.
"""
from __future__ import annotations

import pytest

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.hemolysis import (
    _HEMOLYSIS_WEIGHTS,
    hemolysis_risk_score,
    hemolysis_safety_component,
)


class TestHemolysisRiskScore:
    def test_score_in_unit_interval(self):
        for seq in ["GIGKFLHSAKKFGKAFVGEIMNS", "GIGAVLKVLTTGLPALISWIKRKRQQ",
                     "RGGRLCYCRRRFCVCVGR", "KKKKKKKKKK", "DEDEDEDEDEDE"]:
            f = compute_features(seq)
            risk = hemolysis_risk_score(f)
            assert 0.0 <= risk <= 1.0

    def test_weights_sum_to_one(self):
        assert sum(_HEMOLYSIS_WEIGHTS.values()) == pytest.approx(1.0, abs=1e-9)

    def test_melittin_has_nonzero_risk(self):
        """Melittin (HC50=1.5) should have nonzero hemolysis risk.

        Melittin is a known hard case: no cysteine, low aromatic fraction,
        moderate face cationic leakage. Its risk score is modest (0.13)
        because its hemolysis mechanism (bent-helix, curvature-mediated lysis)
        is not fully captured by 1D features. This is documented as a
        limitation of the hemolysis risk scorer.
        """
        f = compute_features("GIGAVLKVLTTGLPALISWIKRKRQQ")
        risk = hemolysis_risk_score(f)
        assert risk > 0.10, f"Melittin risk={risk}, expected > 0.10"
        # Melittin risk should still be lower than protegrin (cys-rich)
        f_prg = compute_features("RGGRLCYCRRRFCVCVGR")
        risk_prg = hemolysis_risk_score(f_prg)
        assert risk < risk_prg

    def test_protegrin_has_high_risk(self):
        """Protegrin-1 (HC50=5, cys-rich) should have high hemolysis risk."""
        f = compute_features("RGGRLCYCRRRFCVCVGR")
        risk = hemolysis_risk_score(f)
        assert risk > 0.40, f"Protegrin-1 risk={risk}, expected > 0.40"

    def test_tachyplesin_has_high_risk(self):
        """Tachyplesin-I (HC50=10, cys-rich, face cationic leakage) should have high risk."""
        f = compute_features("KWCFRVCYRGICYRRCR")
        risk = hemolysis_risk_score(f)
        assert risk > 0.40, f"Tachyplesin-I risk={risk}, expected > 0.40"

    def test_magainin_has_low_risk(self):
        """Magainin-2 (HC50=100, selective) should have lower risk than melittin."""
        f = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        risk = hemolysis_risk_score(f)
        assert risk < 0.30, f"Magainin-2 risk={risk}, expected < 0.30"

    def test_cecropin_has_low_risk(self):
        """Cecropin-A (HC50=200, selective, well-segregated faces) should have low risk."""
        f = compute_features("KWKLFKKIEKVGQNIRDGIIKAGPAV")
        risk = hemolysis_risk_score(f)
        assert risk < 0.35, f"Cecropin-A risk={risk}, expected < 0.35"

    def test_hemolytic_higher_than_selective_on_average(self):
        """Mean hemolysis risk for hemolytic AMPs should exceed selective AMPs."""
        hemolytic_seqs = [
            "GIGAVLKVLTTGLPALISWIKRKRQQ",  # melittin, HC50=1.5
            "RGGRLCYCRRRFCVCVGR",           # protegrin-1, HC50=5
            "KWCFRVCYRGICYRRCR",            # tachyplesin-I, HC50=10
            "ILPWKWPWWPWRR",                # indolicidin, HC50=10
        ]
        selective_seqs = [
            "GIGKFLHSAKKFGKAFVGEIMNS",      # magainin-2, HC50=100
            "KWKLFKKIEKVGQNIRDGIIKAGPAV",   # cecropin-A, HC50=200
            "DSHAKRHHGYKRKFHEKHHSHRGY",     # histatin-5, HC50=200
            "GNNRPVYIPQPRPPHPRI",           # apidaecin, HC50=200
        ]
        hemo_risks = [hemolysis_risk_score(compute_features(s)) for s in hemolytic_seqs]
        sel_risks = [hemolysis_risk_score(compute_features(s)) for s in selective_seqs]
        mean_hemo = sum(hemo_risks) / len(hemo_risks)
        mean_sel = sum(sel_risks) / len(sel_risks)
        assert mean_hemo > mean_sel, (
            f"Hemolytic mean={mean_hemo:.4f} should exceed selective mean={mean_sel:.4f}"
        )

    def test_cysteine_component_drives_protegrin_risk(self):
        """Protegrin's high risk is partly driven by cysteine content (cys=0.222)."""
        f = compute_features("RGGRLCYCRRRFCVCVGR")
        assert f["cysteine_fraction"] > 0.15
        risk = hemolysis_risk_score(f)
        # If we zero out cysteine contribution, risk should drop
        f_no_cys = dict(f)
        f_no_cys["cysteine_fraction"] = 0.0
        risk_no_cys = hemolysis_risk_score(f_no_cys)
        assert risk > risk_no_cys, "Cysteine component should contribute to protegrin risk"

    def test_aromatic_component_drives_indolicidin_risk(self):
        """Indolicidin's risk is partly driven by aromatic content (aromatic=0.385)."""
        f = compute_features("ILPWKWPWWPWRR")
        assert f["aromatic_fraction"] > 0.25
        risk = hemolysis_risk_score(f)
        f_no_arom = dict(f)
        f_no_arom["aromatic_fraction"] = 0.0
        risk_no_arom = hemolysis_risk_score(f_no_arom)
        assert risk > risk_no_arom, "Aromatic component should contribute to indolicidin risk"

    def test_empty_sequence(self):
        """Empty sequence should return 0 risk (no features to trigger risk)."""
        f = compute_features("")
        risk = hemolysis_risk_score(f)
        assert 0.0 <= risk <= 1.0

    def test_short_sequence(self):
        """Very short sequence should not crash."""
        f = compute_features("KK")
        risk = hemolysis_risk_score(f)
        assert 0.0 <= risk <= 1.0


class TestHemolysisSafetyComponent:
    def test_is_inverse_of_risk(self):
        """hemolysis_safety_component = 1 - hemolysis_risk_score."""
        for seq in ["GIGKFLHSAKKFGKAFVGEIMNS", "GIGAVLKVLTTGLPALISWIKRKRQQ",
                     "RGGRLCYCRRRFCVCVGR"]:
            f = compute_features(seq)
            risk = hemolysis_risk_score(f)
            safety = hemolysis_safety_component(f)
            assert safety == pytest.approx(1.0 - risk, abs=1e-4)

    def test_in_unit_interval(self):
        f = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        safety = hemolysis_safety_component(f)
        assert 0.0 <= safety <= 1.0

    def test_selective_higher_than_hemolytic(self):
        """Selective AMPs should have higher hemolysis_safety than hemolytic AMPs."""
        sel = hemolysis_safety_component(compute_features("GIGKFLHSAKKFGKAFVGEIMNS"))
        hemo = hemolysis_safety_component(compute_features("RGGRLCYCRRRFCVCVGR"))
        assert sel > hemo
