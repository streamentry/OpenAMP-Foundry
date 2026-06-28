"""Tests for serum_stability_score and the new interior protease site features."""
from __future__ import annotations

import pytest

from openamp_foundry.features.physchem import (
    compute_features,
    interior_protease_sites,
    TRYPSIN_SITES,
    CHYMOTRYPSIN_SITES,
)
from openamp_foundry.scoring.stability import serum_stability_score


class TestInteriorProteaseSites:
    def test_empty_sequence_returns_zero(self):
        assert interior_protease_sites("", TRYPSIN_SITES) == 0

    def test_single_residue_returns_zero(self):
        # C-terminal K is excluded — no downstream fragment
        assert interior_protease_sites("K", TRYPSIN_SITES) == 0

    def test_two_residues_only_first_counted(self):
        # "KK": only position 0 (first K) is interior; second K is C-terminal → excluded
        assert interior_protease_sites("KK", TRYPSIN_SITES) == 1

    def test_all_k_n_residues_counts_n_minus_1(self):
        # "KKK" → positions 0,1 are interior (position 2 = C-term excluded)
        assert interior_protease_sites("KKK", TRYPSIN_SITES) == 2

    def test_terminal_only_not_counted(self):
        # "GALAG": only A,L,A in interior; no K/R → 0 trypsin sites
        assert interior_protease_sites("GALAG", TRYPSIN_SITES) == 0

    def test_interior_k_counted(self):
        # "GKALAG": K at position 1 (interior) → 1 site
        assert interior_protease_sites("GKALAG", TRYPSIN_SITES) == 1

    def test_c_terminal_k_not_counted(self):
        # "GALK": K at C-terminus → 0 interior trypsin sites
        assert interior_protease_sites("GALK", TRYPSIN_SITES) == 0

    def test_chymotrypsin_fw_counted(self):
        # "FWYGALAG": F(0) and W(1) are interior, Y(2) is interior → 3 chymo sites; G at end
        assert interior_protease_sites("FWYAAAG", CHYMOTRYPSIN_SITES) == 3

    def test_seed003_trypsin_count(self):
        # RRWRWRMKKLG: R(0) R(1) W(2) R(3) W(4) R(5) M(6) K(7) K(8) L(9) G(10)
        # Interior K/R at positions 0,1,3,5,7,8 = 6 sites; but C-term is G, so all K/R are interior
        # Actually interior = positions 0..9 (excluding G at position 10)
        # K/R at 0,1,3,5,7,8 → all are interior (not at position 10) → 6 sites
        assert interior_protease_sites("RRWRWRMKKLG", TRYPSIN_SITES) == 6


class TestComputeFeaturesNewKeys:
    def test_trypsin_site_density_present(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert "trypsin_site_density" in f

    def test_chymotrypsin_site_density_present(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert "chymotrypsin_site_density" in f

    def test_interior_trypsin_sites_present(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert "interior_trypsin_sites" in f

    def test_interior_chymotrypsin_sites_present(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert "interior_chymotrypsin_sites" in f

    def test_trypsin_density_is_float(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(f["trypsin_site_density"], float)

    def test_chymotrypsin_density_is_float(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(f["chymotrypsin_site_density"], float)

    def test_chymotrypsin_density_consistent_with_count(self):
        # FWYGALAG: F(0) W(1) Y(2) G A L A G → 3 interior chymo sites (G is C-term, excluded)
        # chymotrypsin_site_density = 3/8 = 0.375
        f = compute_features("FWYAALAG")
        expected_density = round(f["interior_chymotrypsin_sites"] / f["length"], 4)
        assert f["chymotrypsin_site_density"] == pytest.approx(expected_density, abs=1e-4)

    def test_trypsin_density_in_range(self):
        for seq in ["KKKK", "LLLL", "KWKLFKKIGAVLKVL", "GALAG"]:
            d = compute_features(seq)["trypsin_site_density"]
            assert 0.0 <= d <= 1.0, f"density out of range for {seq}: {d}"

    def test_all_hydrophobic_no_trypsin_sites(self):
        # LLLLLL has no K or R
        f = compute_features("LLLLLL")
        assert f["interior_trypsin_sites"] == 0
        assert f["trypsin_site_density"] == pytest.approx(0.0, abs=1e-4)

    def test_high_kyr_density_high_trypsin_density(self):
        # KRKRKR: 6 residues, K/R at 0,1,2,3,4,5; C-term is R (pos 5 excluded)
        # Interior K/R: positions 0,1,2,3,4 → 5 sites; density = 5/6 ≈ 0.833
        f = compute_features("KRKRKR")
        assert f["trypsin_site_density"] > 0.7

    def test_empty_sequence(self):
        f = compute_features("")
        assert f["trypsin_site_density"] == 0.0
        assert f["interior_trypsin_sites"] == 0
        assert f["interior_chymotrypsin_sites"] == 0

    def test_seed003_representative(self):
        # RRWQWRMKKLG: trypsin sites at R(0),R(1),R(5),K(7),K(8) = 5 interior; C-term G excluded
        # Wait: RRWQWRMKKLG = R R W Q W R M K K L G (11 chars)
        # K/R at positions 0,1,5,7,8; G at pos 10 = C-term; all K/R are interior → 5 trypsin sites
        f = compute_features("RRWQWRMKKLG")
        assert f["interior_trypsin_sites"] == 5
        assert f["trypsin_site_density"] == pytest.approx(5 / 11, abs=1e-4)


class TestSerumStabilityScore:
    def test_uses_chymotrypsin_site_density_key(self):
        # If chymotrypsin_site_density is present (from compute_features), score uses it
        # rather than re-deriving from raw count. This confirms symmetric schema.
        f = compute_features("FWYAAAG")  # 2 interior chymo sites (W,Y), no trypsin
        assert "chymotrypsin_site_density" in f
        score_from_features = serum_stability_score(f)
        # A peptide with F/W/Y interior sites should score below 1.0
        assert score_from_features < 1.0

    def test_returns_float(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(serum_stability_score(f), float)

    def test_range_zero_to_one(self):
        for seq in ["KKKKKKKK", "LLLLLLLL", "KWKLFKKIGAVLKVL", "ALPFIGRVLSGIL"]:
            f = compute_features(seq)
            score = serum_stability_score(f)
            assert 0.0 <= score <= 1.0, f"score out of range for {seq}: {score}"

    def test_no_cleavage_sites_returns_one(self):
        # LLLLLLLL: no K, R, F, W, Y
        f = compute_features("LLLLLLLL")
        assert serum_stability_score(f) == pytest.approx(1.0, abs=1e-4)

    def test_all_k_returns_low(self):
        # KKKKKKKK: very high trypsin density → low stability
        f = compute_features("KKKKKKKK")
        score = serum_stability_score(f)
        assert score < 0.40, f"all-K stability should be low, got {score}"

    def test_seed003_low_stability(self):
        # RRWQWRMKKLG: 5/11 = 0.455 trypsin density → score < 0.5
        f = compute_features("RRWQWRMKKLG")
        score = serum_stability_score(f)
        assert score < 0.40, f"SEED-003 representative should have low serum stability: {score}"

    def test_seed004_higher_stability(self):
        # ALPFIGRVLSGIL: only 1 interior R at position 6 out of 13 → low trypsin density
        f = compute_features("ALPFIGRVLSGIL")
        seed003 = compute_features("RRWQWRMKKLG")
        assert serum_stability_score(f) > serum_stability_score(seed003), (
            "SEED-004 (low K/R) should be more serum-stable than SEED-003 (high K/R)"
        )

    def test_empty_features_returns_one(self):
        # Empty sequence → length=0 → no cleavage sites → stable
        f = compute_features("")
        assert serum_stability_score(f) == pytest.approx(1.0, abs=1e-4)

    def test_rounding_to_4_decimal_places(self):
        f = compute_features("KWKLFKKIGAVLKVL")
        score = serum_stability_score(f)
        assert score == round(score, 4)

    def test_stability_decreases_with_more_kr_sites(self):
        # Adding K/R residues to a stable backbone should lower stability
        stable = compute_features("LLLLLLL")
        unstable = compute_features("KLRKLRL")
        assert serum_stability_score(stable) > serum_stability_score(unstable)
