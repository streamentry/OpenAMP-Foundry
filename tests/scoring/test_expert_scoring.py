"""Tests for scoring/expert.py — helix hinge, k-mer prior art, expert composite.

Expected values are reasoned from the documented thresholds, not back-fitted to the
implementation, so the tests verify intended behaviour rather than self-consistency.
"""
from __future__ import annotations

import pytest

from openamp_foundry.scoring.expert import (
    EXPERT_WEIGHTS,
    build_kmer_index,
    expert_score,
    helix_hinge_analysis,
    kmer_prior_art,
)


class TestHelixHinge:
    def test_short_sequence_no_hinge(self):
        r = helix_hinge_analysis("KRLW")
        assert r["hinge_score"] == 0.0
        assert r["has_central_hinge"] is False

    def test_single_central_proline_is_ideal_hinge(self):
        # 12-mer; central third = indices [4, 8). Proline at index 5 (position 6).
        seq = "KLRAIPLKRLWV"
        r = helix_hinge_analysis(seq)
        assert r["central_breakers"] == 1
        assert r["has_central_hinge"] is True
        assert r["hinge_score"] == 1.00

    def test_no_central_breaker_is_neutral(self):
        # All-helix-favouring residues, no G/P anywhere.
        seq = "KLRAILLKRLWV"
        r = helix_hinge_analysis(seq)
        assert r["central_breakers"] == 0
        assert r["hinge_score"] == 0.30

    def test_terminal_proline_is_not_a_central_hinge(self):
        # Proline at the N-terminus only — outside the central third.
        seq = "PKLRAILLKRLW"
        r = helix_hinge_analysis(seq)
        assert r["central_breakers"] == 0
        assert r["has_central_hinge"] is False

    def test_consecutive_breakers_destroy_helix(self):
        # PP run in the centre → helix shredded, low score.
        seq = "KLRAIPPKRLWV"
        r = helix_hinge_analysis(seq)
        assert r["breaker_run"] >= 2
        assert r["hinge_score"] == 0.10

    def test_two_central_breakers_overflexible(self):
        # 15-mer, central third [5,10): G at 6 and P at 9 → two isolated breakers.
        seq = "KLRAIGLLPKRLWVA"
        r = helix_hinge_analysis(seq)
        assert r["central_breakers"] == 2
        assert r["breaker_run"] == 1
        assert r["hinge_score"] == 0.60


class TestKmerPriorArt:
    def test_build_index_collects_all_kmers(self):
        idx = build_kmer_index(["ABCDE", "CDEFG"], k=3)
        assert "ABC" in idx
        assert "BCD" in idx
        assert "EFG" in idx
        assert "XYZ" not in idx

    def test_fully_novel_motifs(self):
        idx = build_kmer_index(["KKKKKKKKKK"], k=5)
        r = kmer_prior_art("WYWYWYWYWY", idx, k=5)
        assert r["n_known"] == 0
        assert r["motif_novelty_score"] == 1.0

    def test_fully_known_motifs(self):
        known = "KLWKLWKLWK"
        idx = build_kmer_index([known], k=5)
        r = kmer_prior_art(known, idx, k=5)
        assert r["n_known"] == r["n_kmers"]
        assert r["motif_novelty_score"] == 0.0
        assert r["max_run_known"] == r["n_kmers"]

    def test_partial_overlap_run_detected(self):
        # Candidate shares its first 6 chars (two 5-mers in a run) with a known seq.
        idx = build_kmer_index(["ABCDEF"], k=5)
        r = kmer_prior_art("ABCDEFqqqq".upper(), idx, k=5)
        assert r["n_known"] == 2          # ABCDE, BCDEF
        assert r["max_run_known"] == 2

    def test_empty_when_shorter_than_k(self):
        idx = build_kmer_index(["ABCDE"], k=5)
        r = kmer_prior_art("ABC", idx, k=5)
        assert r["n_kmers"] == 0
        assert r["motif_novelty_score"] == 1.0


class TestExpertComposite:
    def test_weights_sum_to_one(self):
        assert sum(EXPERT_WEIGHTS.values()) == pytest.approx(1.0, abs=1e-9)

    def test_composite_in_unit_interval(self):
        s = expert_score("KWKLFKKIGAVLKVL")
        assert 0.0 <= s.composite <= 1.0
        # All weighted components must be present in the breakdown.
        for name in EXPERT_WEIGHTS:
            assert name in s.components

    def test_motif_novelty_defaults_high_without_index(self):
        s = expert_score("KWKLFKKIGAVLKVL")
        assert s.components["motif_novelty"] == 1.0

    def test_known_peptide_scores_lower_motif_novelty(self):
        seq = "KWKLFKKIGAVLKVL"
        idx = build_kmer_index([seq], k=5)
        s = expert_score(seq, kmer_index=idx)
        # Every k-mer is in the index → motif novelty collapses to 0.
        assert s.components["motif_novelty"] == 0.0
        assert any("MOTIF_PRIOR_ART" in f for f in s.flags)

    def test_anionic_peptide_has_low_activity_consensus(self):
        # Net-negative peptide: cationic-AMP activity mechanism does not apply.
        s = expert_score("DEDEDEDEDEDE")
        assert s.components["activity_consensus"] <= 0.5

    def test_hemolytic_helix_penalised_vs_hinged(self):
        # A rigid hydrophobic amphipathic helix vs a hinged, more selective analogue.
        rigid = expert_score("FLFLFLKKFLFLFLKK")
        hinged = expert_score("FLFLFKKPLKFLKKAS")
        # The hinged candidate should not be dominated on the hinge axis.
        assert hinged.components["hinge_selectivity"] >= rigid.components["hinge_selectivity"]
