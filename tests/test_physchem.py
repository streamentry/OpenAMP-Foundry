"""Tests for features/physchem.py — all feature computation functions."""
from __future__ import annotations

from openamp_foundry.features.physchem import (
    AROMATIC,
    HYDROPHOBIC,
    NEGATIVE,
    POSITIVE,
    compute_features,
    fraction,
    longest_repeat_run,
    net_charge_proxy,
)


class TestNetChargeProxy:
    def test_positive_residues(self):
        assert net_charge_proxy("KKK") == 3

    def test_negative_residues(self):
        assert net_charge_proxy("DDE") == -3  # D(-1) + D(-1) + E(-1)

    def test_mixed_charge(self):
        assert net_charge_proxy("KKD") == 1
        assert net_charge_proxy("DEK") == -1

    def test_neutral_sequence(self):
        assert net_charge_proxy("AAAA") == 0

    def test_empty_sequence(self):
        assert net_charge_proxy("") == 0

    def test_r_counts_positive(self):
        assert net_charge_proxy("RRR") == 3

    def test_h_counts_positive(self):
        assert net_charge_proxy("HHH") == 3

    def test_all_positive_aa(self):
        assert net_charge_proxy("KRH") == 3

    def test_d_and_e_both_negative(self):
        assert net_charge_proxy("DE") == -2

    def test_balanced_long_sequence(self):
        assert net_charge_proxy("KKKKDDDD") == 0


class TestFraction:
    def test_all_hydrophobic(self):
        # AILMFWVY are HYDROPHOBIC
        assert fraction("AAAA", HYDROPHOBIC) == 1.0

    def test_none_hydrophobic(self):
        assert fraction("KKKK", HYDROPHOBIC) == 0.0

    def test_half_hydrophobic(self):
        assert abs(fraction("KAKAKAKA", HYDROPHOBIC) - 0.5) < 1e-9

    def test_empty_returns_zero(self):
        assert fraction("", HYDROPHOBIC) == 0.0

    def test_aromatic_fraction(self):
        # FWY are AROMATIC
        seq = "FWYK"
        expected = 3 / 4
        assert abs(fraction(seq, AROMATIC) - expected) < 1e-9

    def test_single_residue_present(self):
        assert fraction("K", POSITIVE) == 1.0

    def test_single_residue_absent(self):
        assert fraction("K", NEGATIVE) == 0.0


class TestLongestRepeatRun:
    def test_no_repeats(self):
        assert longest_repeat_run("KWKLF") == 1

    def test_single_pair(self):
        assert longest_repeat_run("KWKKF") == 2

    def test_triple_run(self):
        assert longest_repeat_run("KWKKKF") == 3

    def test_whole_sequence_same(self):
        assert longest_repeat_run("AAAAAAA") == 7

    def test_empty_sequence(self):
        assert longest_repeat_run("") == 0

    def test_single_residue(self):
        assert longest_repeat_run("K") == 1

    def test_multiple_runs_returns_longest(self):
        # "AAA" and "BB" — longest is 3
        assert longest_repeat_run("KWKAAABBL") == 3

    def test_run_at_end(self):
        assert longest_repeat_run("KWLLLLL") == 5

    def test_run_at_start(self):
        assert longest_repeat_run("KKKKLF") == 4


class TestComputeFeatures:
    def test_all_required_keys_present(self):
        feat = compute_features("KWKLFKKIGAVLKVL")
        required = {
            "length", "net_charge_proxy", "charge_density",
            "hydrophobic_fraction", "aromatic_fraction", "cysteine_fraction",
            "glycine_fraction", "proline_fraction", "longest_repeat_run",
            "hydrophobic_moment", "boman_index", "gravy", "residue_counts",
        }
        assert required <= set(feat.keys())

    def test_length_correct(self):
        assert compute_features("KWKLFKKIGAVLKVL")["length"] == 15
        assert compute_features("AAAAA")["length"] == 5

    def test_empty_sequence(self):
        feat = compute_features("")
        assert feat["length"] == 0
        assert feat["net_charge_proxy"] == 0
        assert feat["charge_density"] == 0.0
        assert feat["hydrophobic_moment"] == 0.0

    def test_charge_density_proportional_to_charge(self):
        # KKK: charge=3, length=3 → density=1.0
        feat = compute_features("KKK")
        assert abs(feat["charge_density"] - 1.0) < 1e-9

    def test_hydrophobic_fraction_correct(self):
        # AAAK: A is hydrophobic (in AILMFWVY set? Let me check)
        # HYDROPHOBIC = set("AILMFWVY") — A is IN this set
        feat = compute_features("AAAK")
        assert abs(feat["hydrophobic_fraction"] - 0.75) < 1e-9

    def test_aromatic_fraction_correct(self):
        # FWY are aromatic
        feat = compute_features("FKWKY")
        assert abs(feat["aromatic_fraction"] - 0.60) < 1e-9

    def test_cysteine_fraction_correct(self):
        feat = compute_features("KCCK")
        assert abs(feat["cysteine_fraction"] - 0.5) < 1e-9

    def test_glycine_fraction_correct(self):
        feat = compute_features("KGGG")
        assert abs(feat["glycine_fraction"] - 0.75) < 1e-9

    def test_proline_fraction_correct(self):
        feat = compute_features("KPPP")
        assert abs(feat["proline_fraction"] - 0.75) < 1e-9

    def test_longest_repeat_run_correct(self):
        feat = compute_features("KWKAAAF")
        assert feat["longest_repeat_run"] == 3

    def test_residue_counts_match(self):
        feat = compute_features("KKWKK")
        counts = feat["residue_counts"]
        assert counts["K"] == 4
        assert counts["W"] == 1

    def test_hydrophobic_moment_nonnegative(self):
        feat = compute_features("KWKLFKKIGAVLKVL")
        assert feat["hydrophobic_moment"] >= 0.0

    def test_all_features_numeric(self):
        feat = compute_features("KWKLFKKIGAVLKVL")
        for key, val in feat.items():
            if key != "residue_counts":
                assert isinstance(val, (int, float)), f"{key}={val!r} is not numeric"

    def test_positive_amp_has_positive_charge_density(self):
        # Typical AMPs are cationic
        feat = compute_features("KWKLFKKIGAVLKVL")
        assert feat["charge_density"] > 0

    def test_all_canonical_aa_no_crash(self):
        seq = "ACDEFGHIKLMNPQRSTVWY"
        feat = compute_features(seq)
        assert feat["length"] == 20
