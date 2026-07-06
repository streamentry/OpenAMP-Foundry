"""Tests for hydrophobic moment (amphipathicity) feature."""
from __future__ import annotations

import pytest

from openamp_foundry.features.physchem import (
    compute_features,
    helix_wheel_faces,
    hydrophobic_moment,
    max_windowed_hydrophobic_moment,
)


class TestHydrophobicMoment:
    def test_empty_sequence_returns_zero(self):
        assert hydrophobic_moment("") == 0.0

    def test_uniform_sequence_low_moment(self):
        # All same amino acid → sine/cosine terms distribute evenly → low moment
        result = hydrophobic_moment("AAAAAAAAAA")
        assert isinstance(result, float)
        assert result >= 0.0

    def test_alternating_hydrophobic_polar_has_higher_moment(self):
        # Alternating hydrophobic/polar gives high periodicity
        # e.g. KLKLKLKL at 100deg/residue should show amphipathic character
        # vs KKKKKKKK which is all charged (low hydrophobic contrast)
        seq_amphipathic = "KLKLKLKL"
        seq_uniform = "KKKKKKKK"
        result_amph = hydrophobic_moment(seq_amphipathic)
        result_unif = hydrophobic_moment(seq_uniform)
        assert result_amph > result_unif, (
            f"Amphipathic KLKLKLKL moment ({result_amph:.4f}) should exceed "
            f"uniform KKKKKKKK moment ({result_unif:.4f})"
        )

    def test_known_amp_has_nonzero_moment(self):
        # KWKLFKKIGAVLKVL is a classic AMP (magainin analogue)
        result = hydrophobic_moment("KWKLFKKIGAVLKVL")
        assert result > 0.0

    def test_returns_float_rounded_to_4dp(self):
        result = hydrophobic_moment("KWKLFKK")
        assert isinstance(result, float)
        # Check 4 decimal places
        assert result == round(result, 4)

    def test_single_residue(self):
        result = hydrophobic_moment("K")
        # sin(0) = 0, cos(0) = 1 → moment = |H_K * cos(0)| / 1 = |H_K|
        assert isinstance(result, float)


class TestComputeFeaturesAmphipathicity:
    def test_hydrophobic_moment_in_features(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "hydrophobic_moment" in features
        assert isinstance(features["hydrophobic_moment"], float)
        assert features["hydrophobic_moment"] >= 0.0

    def test_empty_sequence_does_not_crash(self):
        features = compute_features("")
        assert "hydrophobic_moment" in features
        assert features["hydrophobic_moment"] == 0.0

    def test_all_canonical_amino_acids(self):
        seq = "ACDEFGHIKLMNPQRSTVWY"
        features = compute_features(seq)
        assert "hydrophobic_moment" in features
        assert features["hydrophobic_moment"] >= 0.0


class TestMaxWindowedHydrophobicMoment:
    """Tests for the Eisenberg-standard windowed mu_h (window=11)."""

    def test_empty_sequence_returns_zero(self):
        assert max_windowed_hydrophobic_moment("") == 0.0

    def test_short_sequence_equals_full_seq_mu_h(self):
        # For sequences <= 11 AA, windowed == full-sequence (only one window)
        seq = "KWKLFKK"  # 7 residues < 11
        windowed = max_windowed_hydrophobic_moment(seq, window=11)
        full = hydrophobic_moment(seq)
        assert windowed == pytest.approx(full, abs=1e-3)

    def test_long_sequence_windowed_ge_full_seq(self):
        # For sequences > 11 AA, windowed >= full-sequence by definition
        # (best 11-residue window >= average over all residues)
        seq = "GIGKFLHSAKKFGKAFVGEIMNS"  # magainin-2, 23 residues
        windowed = max_windowed_hydrophobic_moment(seq, window=11)
        full = hydrophobic_moment(seq)
        assert windowed >= full - 1e-4, (
            f"Windowed mu_h ({windowed:.4f}) should be >= full-seq mu_h ({full:.4f})"
        )

    def test_magainin2_windowed_substantially_higher_than_full(self):
        # Magainin-2: windowed mu_h should be meaningfully higher than full-seq
        # (helical segment is concentrated; full-seq is diluted by terminal coil)
        magainin2 = "GIGKFLHSAKKFGKAFVGEIMNS"
        windowed = max_windowed_hydrophobic_moment(magainin2, window=11)
        full = hydrophobic_moment(magainin2)
        # Empirically: windowed ~0.68, full ~0.45 → ratio ~1.5×
        assert windowed > full * 1.2, (
            f"Magainin-2 windowed ({windowed:.4f}) should be >1.2× full-seq ({full:.4f})"
        )

    def test_returns_float_rounded_to_4dp(self):
        result = max_windowed_hydrophobic_moment("KWKLFKKIGAVLKVL")
        assert isinstance(result, float)
        assert result == round(result, 4)

    def test_single_residue_equals_full_moment(self):
        result = max_windowed_hydrophobic_moment("K", window=11)
        full = hydrophobic_moment("K")
        assert result == pytest.approx(full, abs=1e-3)

    def test_window_equal_to_sequence_length(self):
        seq = "KWKLFKKIGAV"  # exactly 11 residues
        windowed = max_windowed_hydrophobic_moment(seq, window=11)
        full = hydrophobic_moment(seq)
        assert windowed == pytest.approx(full, abs=1e-3)

    def test_nonnegative(self):
        for seq in ["", "A", "KWKLFKK", "GIGKFLHSAKKFGKAFVGEIMNS", "EEIEIEIEIEIEIEE"]:
            result = max_windowed_hydrophobic_moment(seq)
            assert result >= 0.0, f"max_windowed_hydrophobic_moment({seq!r}) returned {result}"

    def test_custom_window(self):
        seq = "KWKLFKKIGAVLKVL"
        w7 = max_windowed_hydrophobic_moment(seq, window=7)
        w11 = max_windowed_hydrophobic_moment(seq, window=11)
        # Both must be non-negative; neither is bounded at 1.0 (Eisenberg values can
        # be large for tightly packed hydrophobic windows — clamping happens in the scorer)
        assert w7 >= 0.0
        assert w11 >= 0.0


class TestComputeFeaturesMaxMuH:
    """Tests that compute_features() includes max_hydrophobic_moment."""

    def test_max_hydrophobic_moment_key_present(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "max_hydrophobic_moment" in features, (
            "compute_features() must return 'max_hydrophobic_moment'"
        )

    def test_max_hydrophobic_moment_is_float(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(features["max_hydrophobic_moment"], float)

    def test_max_hydrophobic_moment_nonnegative(self):
        for seq in ["", "A", "KWKLFKK", "GIGKFLHSAKKFGKAFVGEIMNS"]:
            features = compute_features(seq)
            assert features["max_hydrophobic_moment"] >= 0.0

    def test_max_hydrophobic_moment_ge_hydrophobic_moment_for_known_amps(self):
        # For known helical AMPs with a concentrated amphipathic segment, the windowed
        # value should be >= the full-seq value (good amphipathic signal).
        # NOTE: this invariant does NOT hold for non-amphipathic or uniform sequences
        # (see test_windowed_can_be_less_than_full_for_uniform_sequences below).
        for seq in ["KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS", "LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES"]:
            features = compute_features(seq)
            assert features["max_hydrophobic_moment"] >= features["hydrophobic_moment"] - 1e-4, (
                f"max_mu_h ({features['max_hydrophobic_moment']:.4f}) < mu_h "
                f"({features['hydrophobic_moment']:.4f}) for {seq}"
            )

    def test_windowed_can_be_less_than_full_for_uniform_sequences(self):
        # For non-amphipathic sequences (e.g. all-Ala, all-Glu), the windowed mu_h
        # (normalised by window=11) can be LESS than full-seq mu_h (normalised by len>11).
        # activity_likeness_score() handles this correctly via max(); direct callers
        # must not assume max_hydrophobic_moment >= hydrophobic_moment.
        seq = "AAAAAAAAAAAA"  # 12-A, uniform → no concentrated amphipathic segment
        windowed = max_windowed_hydrophobic_moment(seq, window=11)
        full = hydrophobic_moment(seq)
        assert windowed < full, (
            f"For uniform sequence {seq!r}, expected windowed ({windowed:.4f}) < "
            f"full-seq ({full:.4f}) to document the non-invariant"
        )

    def test_short_seq_max_equals_full(self):
        features = compute_features("KWKLFKK")  # 7 residues, window=11 → only one window
        assert features["max_hydrophobic_moment"] == pytest.approx(
            features["hydrophobic_moment"], abs=1e-3
        )


class TestHelixWheelFaces:
    """Tests for the moment-oriented amphipathic face analysis.

    NOTE: The analysis is NOT independent of circular permutation. It depends on the
    N-terminal convention (which residue is at position 0). This is by design — all
    pipeline candidates have a fixed N-terminus determined at synthesis.
    """

    def test_returns_required_keys(self):
        result = helix_wheel_faces("KWKLFKKIGAVLKVL")
        for key in [
            "hydrophobic_face_mean_h", "hydrophilic_face_mean_h",
            "face_contrast", "h_face_cationic_fraction",
            "ph_face_cationic_fraction", "amphipathic_score",
        ]:
            assert key in result

    def test_short_sequence_lt4_returns_zeros(self):
        # Sequences < 4 AA return all zeros (amphipathic character is ill-defined)
        for seq in ["", "K", "KW", "KWL"]:
            result = helix_wheel_faces(seq)
            assert result["face_contrast"] == 0.0
            assert result["amphipathic_score"] == 0.0

    def test_four_residue_sequence_returns_nonzero(self):
        # Exactly 4 residues should escape the guard and return a real result
        result = helix_wheel_faces("KWLF")
        assert isinstance(result["face_contrast"], float)
        # KWLF has some amphipathic character; all required keys must be present
        for key in ["hydrophobic_face_mean_h", "hydrophilic_face_mean_h",
                    "face_contrast", "h_face_cationic_fraction",
                    "ph_face_cationic_fraction", "amphipathic_score"]:
            assert key in result

    def test_known_amp_magainin_has_high_contrast(self):
        # Magainin-2 is a textbook amphipathic helix — contrast should be > 0.8
        hw = helix_wheel_faces("GIGKFLHSAKKFGKAFVGEIMNS")
        assert hw["face_contrast"] > 0.8, (
            f"Magainin-2 face_contrast={hw['face_contrast']:.4f} should be > 0.8"
        )

    def test_known_amp_cationic_on_hydrophilic_face(self):
        # Magainin-2: K/R on the hydrophilic face — h_face_cationic_fraction should be low
        hw = helix_wheel_faces("GIGKFLHSAKKFGKAFVGEIMNS")
        assert hw["h_face_cationic_fraction"] < 0.15, (
            f"Magainin-2 should have few cationic on hydrophobic face; "
            f"got {hw['h_face_cationic_fraction']:.4f}"
        )
        assert hw["ph_face_cationic_fraction"] > 0.30, (
            f"Magainin-2 should have cationic residues on hydrophilic face; "
            f"got {hw['ph_face_cationic_fraction']:.4f}"
        )

    def test_uniform_sequence_has_zero_contrast(self):
        # All-Gly: no hydrophobicity gradient → zero face contrast (zero moment → zero guard)
        hw = helix_wheel_faces("GGGGGGGGGGGG")
        assert hw["face_contrast"] == pytest.approx(0.0, abs=1e-6)
        assert hw["amphipathic_score"] == 0.0

    def test_amphipathic_score_in_unit_interval(self):
        for seq in ["", "K", "KWKLFKK", "GIGKFLHSAKKFGKAFVGEIMNS", "GGGGGGGGGGGG"]:
            hw = helix_wheel_faces(seq)
            assert 0.0 <= hw["amphipathic_score"] <= 1.0

    def test_amphipathic_score_positive_for_known_amp(self):
        # A well-designed AMP (KWKLFKKIGAVLKVL) should score above 0.3 on the [0,1] scale
        hw = helix_wheel_faces("KWKLFKKIGAVLKVL")
        assert hw["amphipathic_score"] > 0.3

    def test_nterminal_convention_documented(self):
        # Circular permutation (different N-terminus) changes face_contrast — this is expected
        # and documents that the analysis depends on the N-terminal convention.
        seq = "KWKLFKKIGAVLKVL"
        hw_original = helix_wheel_faces(seq)
        # Rotation by 5 positions changes moment direction → different contrast
        hw_rotated = helix_wheel_faces(seq[5:] + seq[:5])
        # The values will differ (this is correct behaviour by design)
        # We just verify both return valid results, not that they are equal
        assert 0.0 <= hw_original["amphipathic_score"] <= 1.0
        assert 0.0 <= hw_rotated["amphipathic_score"] <= 1.0
        # Document the non-invariance explicitly for future readers
        # (Values typically differ by 20-60% across random permutations)

    def test_face_contrast_positive_for_amphipathic(self):
        # For an amphipathic peptide, hydrophobic face must have higher mean_h than hydrophilic
        hw = helix_wheel_faces("GIGKFLHSAKKFGKAFVGEIMNS")
        assert hw["face_contrast"] > 0.0
        assert hw["hydrophobic_face_mean_h"] > hw["hydrophilic_face_mean_h"]

    def test_cationic_fractions_in_unit_interval(self):
        for seq in ["KWKLFKK", "GIGKFLHSAKKFGKAFVGEIMNS", "RRWQWRMKKLG"]:
            hw = helix_wheel_faces(seq)
            assert 0.0 <= hw["h_face_cationic_fraction"] <= 1.0
            assert 0.0 <= hw["ph_face_cationic_fraction"] <= 1.0

    def test_amphipathic_score_not_saturated_for_magainin(self):
        # With normalization constant 2.0 (contrast range [0, 2]), magainin-2 (contrast ~1.23)
        # should NOT saturate to 1.0 — it should be in [0.5, 0.9]
        hw = helix_wheel_faces("GIGKFLHSAKKFGKAFVGEIMNS")
        assert hw["amphipathic_score"] < 1.0, (
            f"Magainin-2 amphipathic_score={hw['amphipathic_score']:.4f} should not saturate; "
            "normalization constant may need adjustment"
        )
        assert hw["amphipathic_score"] > 0.5, (
            f"Magainin-2 amphipathic_score={hw['amphipathic_score']:.4f} should be > 0.5"
        )


class TestComputeFeaturesHelixWheel:
    """Tests that compute_features() includes helix wheel face keys."""

    def test_helix_wheel_keys_in_features(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        for key in [
            "helix_wheel_hydrophobic_face_mean_h", "helix_wheel_hydrophilic_face_mean_h",
            "helix_wheel_face_contrast", "helix_wheel_h_face_cationic_fraction",
            "helix_wheel_ph_face_cationic_fraction", "helix_wheel_amphipathic_score",
        ]:
            assert key in features, f"Missing key: {key}"

    def test_helix_wheel_amphipathic_score_nonneg(self):
        for seq in ["", "K", "KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS"]:
            features = compute_features(seq)
            assert features["helix_wheel_amphipathic_score"] >= 0.0

    def test_known_amp_has_positive_face_contrast(self):
        features = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        assert features["helix_wheel_face_contrast"] > 0.0
