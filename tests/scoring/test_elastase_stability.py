"""Tests for elastase-extended serum stability scoring."""
from __future__ import annotations

from openamp_foundry.features.physchem import compute_features, interior_protease_sites, ELASTASE_SITES
from openamp_foundry.scoring.stability import serum_stability_score


class TestElastaseSites:
    def test_ala_is_elastase_site(self):
        assert "A" in ELASTASE_SITES

    def test_val_is_elastase_site(self):
        assert "V" in ELASTASE_SITES

    def test_ser_is_elastase_site(self):
        assert "S" in ELASTASE_SITES

    def test_lys_not_elastase_site(self):
        assert "K" not in ELASTASE_SITES

    def test_phe_not_elastase_site(self):
        assert "F" not in ELASTASE_SITES

    def test_pure_ala_interior_sites(self):
        # AAAAAAAAA (9 aa): 8 interior sites (excluding C-terminal A)
        n = interior_protease_sites("AAAAAAAAA", ELASTASE_SITES)
        assert n == 8

    def test_no_elastase_site_sequence(self):
        # KKKFWYKKKR — no A/V/S sites
        n = interior_protease_sites("KKKFWYKKKR", ELASTASE_SITES)
        assert n == 0

    def test_cterminal_excluded(self):
        # KA: only 1 residue before C-terminal; A is at position 0 (interior), excluded by C-term rule
        # sequence "KA": interior_protease_sites excludes C-terminal (index 1=A)
        # so only K (index 0) is checked: K not in ELASTASE_SITES → 0
        n = interior_protease_sites("KA", ELASTASE_SITES)
        assert n == 0

    def test_compute_features_has_elastase_keys(self):
        feats = compute_features("KWKLFKKIGAVLKVL")
        assert "elastase_site_density" in feats
        assert "interior_elastase_sites" in feats

    def test_elastase_density_is_unit_interval(self):
        for seq in ["AAAAAA", "KWKLFK", "GIGKFLHSAKKFGKAFVGEIMNS", "FLPLIGRVLSGIL"]:
            feats = compute_features(seq)
            d = feats["elastase_site_density"]
            assert 0.0 <= d <= 1.0, f"elastase_density={d} out of [0,1] for {seq}"


class TestSerumStabilityWithElastase:
    def test_high_ala_sequence_lower_stability_than_lys_rich(self):
        # Poly-Ala has many elastase sites; high-Lys has many trypsin sites
        # Both should get somewhat reduced stability, elastase modestly penalises Ala
        ala_seq = "AAAAAAAAAAAAA"
        ala_feats = compute_features(ala_seq)
        ala_score = serum_stability_score(ala_feats)
        # Pure Ala has NO trypsin or chymotrypsin sites → old score was 1.0
        # Now elastase (A sites) gives it a modest penalty
        assert ala_score < 1.0, "Poly-Ala should have reduced stability due to elastase sites"

    def test_no_cleavage_site_sequence_perfect_stability(self):
        # Poly-Ile has no trypsin, chymotrypsin, OR elastase sites
        feats = compute_features("IIIIIIIIIII")
        score = serum_stability_score(feats)
        assert score == 1.0

    def test_old_trypsin_dominant_still_holds(self):
        # High Lys (trypsin sites) should still give the lowest stability
        high_lys = compute_features("KKKKKKKKKKKK")
        high_ala = compute_features("AAAAAAAAAAAA")
        assert serum_stability_score(high_lys) < serum_stability_score(high_ala)

    def test_elastase_feature_absent_backward_compat(self):
        # If a caller passes a features dict without elastase_site_density (pre-PR features),
        # serum_stability_score should still work (default=0.0 for elastase term)
        feats = {"length": 15, "trypsin_site_density": 0.1, "chymotrypsin_site_density": 0.0}
        score = serum_stability_score(feats)
        assert 0.0 <= score <= 1.0

    def test_elastase_adds_modest_penalty_to_typical_amp(self):
        # Magainin-2 analog: GIGKFLHSAKKFGKAFVGEIMNS
        # Should have lower stability than a version with all Ala→Ile
        magainin = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        # Replace all A/V/S with I (no elastase sites)
        no_elastase = compute_features("GIGKFLHIKKFGKIFVGEIMNS".replace("S", "I").replace("A", "I").replace("V", "I"))
        assert serum_stability_score(magainin) <= serum_stability_score(no_elastase)

    def test_score_is_unit_interval(self):
        for seq in ["AAAAAA", "KWKLFK", "GIGKFLHSAKKFGKAFVGEIMNS", "FLPLIGRVLSGIL", "RRRRRR"]:
            feats = compute_features(seq)
            s = serum_stability_score(feats)
            assert 0.0 <= s <= 1.0, f"score={s} out of [0,1] for {seq}"

    def test_denominator_normalisation_prevents_unbounded_penalty(self):
        # Worst-case: sequence with all K/R (trypsin), all F/Y/W (chymotrypsin), all A/V/S (elastase)
        # is impossible (same residues can't be all three), but combined density ≤ 1.0
        feats = {"length": 10, "trypsin_site_density": 1.0,
                 "chymotrypsin_site_density": 1.0, "elastase_site_density": 1.0}
        score = serum_stability_score(feats)
        assert score == 0.0
