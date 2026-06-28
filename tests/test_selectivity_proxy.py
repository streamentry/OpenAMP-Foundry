"""Tests for the selectivity_proxy feature and HIGH_CYTOTOX_RISK flag.

selectivity_proxy [0,1]: heuristic likelihood of selective bacterial killing
without mammalian cytotoxicity. Based on charge (+3 to +7 optimum) and GRAVY
(≤ 0.5 optimum). Values < 0.5 trigger HIGH_CYTOTOX_RISK in presynth_check.

Literature: Dathe & Wieprecht (1999) BBA; Shai (2002) BBA.
"""
from __future__ import annotations

import pytest
from openamp_foundry.features.physchem import compute_features, selectivity_proxy
from openamp_foundry.qc.presynth_check import check_sequence


# ---------------------------------------------------------------------------
# selectivity_proxy() unit tests
# ---------------------------------------------------------------------------

class TestSelectivityProxyChargeEdges:
    """Charge dimension of the selectivity proxy."""

    def test_charge_zero_returns_zero(self):
        # charge=0 → charge_sel = max(0, 0/2) = 0; gravy_sel=1.0 → 0.4
        proxy = selectivity_proxy(0.0, 0.0)
        assert proxy == pytest.approx(0.4, abs=1e-3)

    def test_charge_one_returns_partial(self):
        # charge=1 → charge_sel = 1/2 = 0.5; gravy_sel=1.0 → 0.3+0.4=0.7
        proxy = selectivity_proxy(1.0, 0.0)
        assert proxy == pytest.approx(0.7, abs=1e-3)

    def test_charge_two_at_lower_boundary(self):
        # charge=2 is the lower boundary of the optimal window → charge_sel = 1.0
        proxy = selectivity_proxy(2.0, 0.0)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_charge_five_is_optimal(self):
        proxy = selectivity_proxy(5.0, 0.0)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_charge_seven_at_upper_boundary(self):
        # charge=7 is the last optimal charge → charge_sel = 1.0
        proxy = selectivity_proxy(7.0, 0.0)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_charge_eight_penalized(self):
        # charge=8 → charge_sel = 1 - (1/5) = 0.8; gravy_sel=1.0
        proxy = selectivity_proxy(8.0, 0.0)
        assert proxy == pytest.approx(0.6 * 0.8 + 0.4, abs=1e-3)

    def test_charge_twelve_fully_penalized(self):
        # charge=12 → charge_sel = max(0, 1-(5/5)) = 0; gravy_sel=1.0 → 0.4
        proxy = selectivity_proxy(12.0, 0.0)
        assert proxy == pytest.approx(0.4, abs=1e-3)

    def test_negative_charge_penalized(self):
        # charge=-1 → charge_sel = max(0, -1/2) = 0; gravy_sel=1.0 → 0.4
        proxy = selectivity_proxy(-1.0, 0.0)
        assert proxy == pytest.approx(0.4, abs=1e-3)


class TestSelectivityProxyGravyEdges:
    """GRAVY hydrophobicity dimension of the selectivity proxy."""

    def test_negative_gravy_is_full_score(self):
        # Very hydrophilic peptide: gravy_sel = 1.0; charge=5 (optimal)
        proxy = selectivity_proxy(5.0, -2.0)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_gravy_zero_is_full_score(self):
        proxy = selectivity_proxy(5.0, 0.0)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_gravy_at_threshold_boundary(self):
        # gravy=0.5 → gravy_sel = 1.0 (boundary included in safe zone)
        proxy = selectivity_proxy(5.0, 0.5)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_gravy_above_threshold_penalized(self):
        # gravy=0.75 → gravy_sel = 1 - (0.25/0.5) = 0.5; charge_sel=1.0
        proxy = selectivity_proxy(5.0, 0.75)
        assert proxy == pytest.approx(0.6 + 0.4 * 0.5, abs=1e-3)

    def test_gravy_at_one_zero_score(self):
        # gravy=1.0 → gravy_sel = 0.0; charge_sel=1.0
        proxy = selectivity_proxy(5.0, 1.0)
        assert proxy == pytest.approx(0.6, abs=1e-3)

    def test_gravy_above_one_clamps_to_zero(self):
        # gravy=2.0 → gravy_sel clamped to 0.0
        proxy = selectivity_proxy(5.0, 2.0)
        assert proxy == pytest.approx(0.6, abs=1e-3)


class TestSelectivityProxyCombined:
    """Combined charge+GRAVY cases."""

    def test_magainin_like_is_fully_selective(self):
        # Magainin-2: charge≈3, GRAVY≈0.08 → both in optimal range
        proxy = selectivity_proxy(3.1, 0.08)
        assert proxy == pytest.approx(1.0, abs=1e-3)

    def test_very_hydrophobic_no_charge_is_zero(self):
        # Poly-hydrophobic, no charge: charge=0, GRAVY>1 → both fully penalized
        proxy = selectivity_proxy(0.0, 2.66)
        assert proxy == pytest.approx(0.0, abs=1e-2)

    def test_return_type_is_float(self):
        assert isinstance(selectivity_proxy(5.0, 0.1), float)

    def test_output_clipped_to_unit_interval(self):
        # Cannot exceed 1.0 or go below 0.0 for any input
        for charge in [-5, 0, 5, 15]:
            for gravy in [-3, 0, 0.5, 1, 3]:
                p = selectivity_proxy(float(charge), float(gravy))
                assert 0.0 <= p <= 1.0, f"Out of range: charge={charge}, gravy={gravy}, proxy={p}"


# ---------------------------------------------------------------------------
# compute_features() integration — selectivity_proxy key present
# ---------------------------------------------------------------------------

class TestComputeFeaturesSelectivity:
    """selectivity_proxy is included in compute_features() output."""

    def test_selectivity_proxy_key_present(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert "selectivity_proxy" in f

    def test_selective_amp_proxy_above_0_5(self):
        # Magainin-2 family: charge≈3, GRAVY≈0.08 → highly selective
        f = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        assert f["selectivity_proxy"] >= 0.5

    def test_hydrophobic_peptide_proxy_below_0_5(self):
        # Poly-Leu/Val: zero charge, very high GRAVY → cytotoxic
        f = compute_features("VVVVLLLLVVVVLLLL")
        assert f["selectivity_proxy"] < 0.5

    def test_seed004_temporin_like_flagged(self):
        # SEED-004 (FLPLIGRVLSGIL): charge≈+1, GRAVY≈+1.81 → cytotox risk
        f = compute_features("FLPLIGRVLSGIL")
        assert f["selectivity_proxy"] < 0.5, (
            f"SEED-004 should be flagged (cytotox risk): proxy={f['selectivity_proxy']}"
        )

    def test_seed001_selective_not_flagged(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert f["selectivity_proxy"] >= 0.5

    def test_seed002_magainin_not_flagged(self):
        f = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        assert f["selectivity_proxy"] >= 0.5


# ---------------------------------------------------------------------------
# presynth_check — SynthQC.cytotox_risk and HIGH_CYTOTOX_RISK flag
# ---------------------------------------------------------------------------

class TestPresynthCheckCytotoxFlag:
    """HIGH_CYTOTOX_RISK flag and SynthQC.cytotox_risk field."""

    def _qc(self, seq: str, mu_h: float = 0.0):
        return check_sequence("TEST", seq, mu_h=mu_h)

    def test_selective_amp_no_cytotox_flag(self):
        qc = self._qc("GIGKFLHSAKKFGKAFVGEIMNS")
        assert not qc.cytotox_risk
        assert not any("CYTOTOX" in fl for fl in qc.flags)

    def test_selective_proxy_stored_in_qc(self):
        qc = self._qc("GIGKFLHSAKKFGKAFVGEIMNS")
        assert qc.selectivity_proxy >= 0.5
        # Value matches the standalone selectivity_proxy() function
        from openamp_foundry.features.physchem import selectivity_proxy as sp
        from openamp_foundry.scoring.boman import gravy_score
        expected = sp(qc.charge_ph74, gravy_score("GIGKFLHSAKKFGKAFVGEIMNS"))
        assert qc.selectivity_proxy == pytest.approx(expected, abs=1e-4)

    def test_hydrophobic_sequence_sets_cytotox_risk_true(self):
        # Poly-Leu: zero charge, high GRAVY → cytotox
        qc = self._qc("VVVVLLLLVVLLVV")
        assert qc.cytotox_risk

    def test_high_cytotox_flag_string_in_flags(self):
        qc = self._qc("VVVVLLLLVVLLVV")
        cytotox_flags = [fl for fl in qc.flags if "HIGH_CYTOTOX_RISK" in fl]
        assert len(cytotox_flags) == 1

    def test_cytotox_flag_contains_proxy_value(self):
        qc = self._qc("VVVVLLLLVVLLVV")
        cytotox_flag = next(fl for fl in qc.flags if "HIGH_CYTOTOX_RISK" in fl)
        assert "selectivity_proxy=" in cytotox_flag

    def test_cytotox_flag_is_informational_not_affecting_difficulty(self):
        # HIGH_CYTOTOX_RISK (and other informational flags) must NOT count toward
        # synthesis_difficulty. Verify by checking that difficulty matches the count
        # of synthesis-risk flags only (excluding all informational flags).
        _INFORMATIONAL_PREFIXES = (
            "HIGH_CYTOTOX_RISK",
            "TRP_PHOTOLABILITY",
            "N_ACETYLATION_RECOMMENDED",
            "WAVE2_D_AMINO",
        )
        qc = self._qc("VVVVLLLLVVLLVV")
        synthesis_flags = [
            fl for fl in qc.flags
            if not any(fl.startswith(p) for p in _INFORMATIONAL_PREFIXES)
        ]
        n_synth = len(synthesis_flags)
        if n_synth == 0:
            expected = "LOW"
        elif n_synth <= 2:
            expected = "MODERATE"
        else:
            expected = "HIGH"
        assert qc.synthesis_difficulty == expected

    def test_to_dict_contains_selectivity_fields(self):
        qc = self._qc("KWKLFKKIGAVLKVL")
        d = qc.to_dict()
        assert "selectivity_proxy" in d
        assert "cytotox_risk" in d

    def test_to_dict_cytotox_false_for_selective_amp(self):
        qc = self._qc("KWKLFKKIGAVLKVL")
        d = qc.to_dict()
        assert d["cytotox_risk"] is False
        assert d["selectivity_proxy"] >= 0.5

    def test_seed004_temporin_cytotox_flagged(self):
        # SEED-004: very hydrophobic temporin-like → cytotox risk known in literature
        qc = self._qc("FLPLIGRVLSGIL")
        assert qc.cytotox_risk
        assert any("HIGH_CYTOTOX_RISK" in fl for fl in qc.flags)


# ---------------------------------------------------------------------------
# Order generator — HIGH_CYTOTOX_RISK entry in _HANDLING_MAP
# ---------------------------------------------------------------------------

class TestOrderGeneratorCytotoxHandling:
    """synthesis_order.csv special_handling column includes cytotox note."""

    def test_handling_map_has_cytotox_entry(self):
        from openamp_foundry.qc.order_generator import _HANDLING_MAP
        assert "HIGH_CYTOTOX_RISK" in _HANDLING_MAP

    def test_cytotox_handling_mentions_mammalian_assay(self):
        from openamp_foundry.qc.order_generator import _HANDLING_MAP
        note = _HANDLING_MAP["HIGH_CYTOTOX_RISK"]
        assert "mammalian" in note.lower() or "cytotox" in note.lower()

    def test_cytotox_handling_appears_in_order_row(self):
        from openamp_foundry.qc.order_generator import generate_synthesis_order
        # Use a cytotoxic-profile sequence: low charge, high GRAVY
        candidates = [{"candidate_id": "T1", "sequence": "VVVVLLLLVVLLVV", "pilot_rank": 1}]
        rows, qc_results = generate_synthesis_order(candidates)
        assert qc_results[0].cytotox_risk
        # The handling note should mention cytotox assay
        assert "cytotox" in rows[0]["special_handling"].lower()

    def test_selective_amp_no_cytotox_in_handling(self):
        from openamp_foundry.qc.order_generator import generate_synthesis_order
        candidates = [{"candidate_id": "T2", "sequence": "GIGKFLHSAKKFGKAFVGEIMNS", "pilot_rank": 1}]
        rows, qc_results = generate_synthesis_order(candidates)
        assert not qc_results[0].cytotox_risk
        assert "cytotox" not in rows[0]["special_handling"].lower()
