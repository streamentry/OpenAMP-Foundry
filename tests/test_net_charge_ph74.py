"""Tests for net_charge_at_ph74() and its integration into compute_features()."""
from __future__ import annotations

import pytest

from openamp_foundry.features.physchem import compute_features, net_charge_at_ph74


class TestNetChargeAtPH74:
    def test_empty_sequence_returns_zero(self):
        assert net_charge_at_ph74("") == 0.0

    def test_single_arg_fully_protonated(self):
        result = net_charge_at_ph74("R")
        assert result == 1.0

    def test_single_lys_fully_protonated(self):
        result = net_charge_at_ph74("K")
        assert result == 1.0

    def test_single_asp_fully_deprotonated(self):
        result = net_charge_at_ph74("D")
        assert result == -1.0

    def test_single_glu_fully_deprotonated(self):
        result = net_charge_at_ph74("E")
        assert result == -1.0

    def test_his_partial_protonation(self):
        # His at pH 7.4, pKa 6.5 → 1 / (1 + 10^(7.4-6.5)) = 1 / (1 + 7.943) ≈ 0.1117
        result = net_charge_at_ph74("H")
        expected = 1.0 / (1.0 + 10.0 ** (7.4 - 6.5))
        assert abs(result - round(expected, 4)) < 1e-6

    def test_his_less_than_one(self):
        result = net_charge_at_ph74("H")
        assert 0.0 < result < 1.0

    def test_his_near_0p11(self):
        result = net_charge_at_ph74("H")
        assert 0.10 < result < 0.12

    def test_neutral_residue_contributes_zero(self):
        # Neutral AAs (A, G, V, L, I, P, F, W, M, S, T, C, N, Q, Y) add nothing
        assert net_charge_at_ph74("AGVLIPFWMSTCNQY") == 0.0

    def test_balanced_charge_krde(self):
        # 1R + 1K + 1D + 1E = +2 - 2 = 0
        result = net_charge_at_ph74("RKDE")
        assert result == 0.0

    def test_his_vs_proxy_difference(self):
        # proxy treats H as +1; pH74 treats H as ~+0.11
        # so pH74 charge < proxy charge for His-containing sequences
        seq = "HHHH"
        proxy = sum(1 for aa in seq if aa in "KRH") - sum(1 for aa in seq if aa in "DE")
        ph74 = net_charge_at_ph74(seq)
        assert ph74 < proxy

    def test_multiple_his_additive(self):
        # 2× His → 2 × 0.1117 ≈ 0.2234
        single = net_charge_at_ph74("H")
        double = net_charge_at_ph74("HH")
        assert abs(double - 2 * single) < 1e-4

    def test_known_amp_ll37_fragment(self):
        # KRIVQRIKDFLR — 2K + 2R (no His, no D/E) → +4.0
        result = net_charge_at_ph74("KRIVQRIKDFLR")
        assert result == 4.0

    def test_returns_float_rounded_to_4dp(self):
        result = net_charge_at_ph74("HKRD")
        assert isinstance(result, float)
        assert result == round(result, 4)

    def test_nonstandard_aa_ignored(self):
        # X is unknown; should not raise and should not contribute charge
        try:
            result = net_charge_at_ph74("XKXRX")
            assert result == 2.0  # only K and R counted
        except KeyError:
            pytest.fail("net_charge_at_ph74 raised KeyError on unknown AA 'X'")


class TestComputeFeaturesNetCharge:
    def test_net_charge_ph74_key_present(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "net_charge_ph74" in features

    def test_charge_density_ph74_key_present(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "charge_density_ph74" in features

    def test_net_charge_ph74_is_float(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(features["net_charge_ph74"], float)

    def test_charge_density_ph74_is_float(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(features["charge_density_ph74"], float)

    def test_charge_density_ph74_within_bounds(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        # 15-residue sequence, 3K+1R = 4, no H/D/E → charge_density = 4/15 ≈ 0.267
        assert 0.0 < features["charge_density_ph74"] < 1.0

    def test_his_sequence_ph74_less_than_proxy(self):
        # Sequence with His: pH74 charge < proxy charge
        seq = "HKFLHAVL"  # 1H + 1K (proxy: +2; ph74: 1.0 + 0.1117 = 1.1117)
        features = compute_features(seq)
        assert features["net_charge_ph74"] < features["net_charge_proxy"]

    def test_no_his_ph74_equals_proxy(self):
        # Without His, net_charge_ph74 == net_charge_proxy for K/R/D/E only
        seq = "RKRKDE"  # 2R + 2K + 1D + 1E = +2
        features = compute_features(seq)
        assert features["net_charge_ph74"] == float(features["net_charge_proxy"])

    def test_empty_sequence_no_crash(self):
        features = compute_features("")
        assert features["net_charge_ph74"] == 0.0
        assert features["charge_density_ph74"] == 0.0

    def test_charge_density_ph74_ratio(self):
        # charge_density_ph74 = net_charge_ph74 / length
        seq = "KKRR"  # 4 cationic, no His
        features = compute_features(seq)
        expected = round(features["net_charge_ph74"] / 4, 4)
        assert features["charge_density_ph74"] == expected
