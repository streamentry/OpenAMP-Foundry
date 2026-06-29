"""Tests for scoring/macrel_local.py — calibrated local Macrel margin scorer.

These tests verify the calibration logic against the gold-standard AMP panel used to
derive the thresholds. They are skipped automatically if the Macrel ONNX models are
not installed in the environment, so the suite stays green on minimal installs.
"""
from __future__ import annotations

import pytest

from openamp_foundry.scoring import macrel_local as ml

pytestmark = pytest.mark.skipif(not ml.available(), reason="Macrel ONNX models not available")


KNOWN_AMPS = {
    "magainin2": "GIGKFLHSAKKFGKAFVGEIMNS",
    "LL37": "LLGDFFRKSKEKIGKEFKRIVQRIKDFLRNLVPRTES",
    "cecropinA": "KWKLFKKIEKVGQNIRDGIIKAGPAVAVVGQATQIAK",
    "pexiganan": "GIGKFLKKAKKFGKAFVKILKK",
}
NON_AMPS = {
    "polyA": "AAAAAAAAAAAA",
    "insulinB": "FVNQHLCGSHLVEALYLVCGERGFFYTPKT",
    "albumin_frag": "DAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQCPFEDHVKLVNEVTEFAK",
}


class TestCalibration:
    def test_known_amps_pass_amp_gate(self):
        for name, seq in KNOWN_AMPS.items():
            r = ml.score_one(seq)
            assert r is not None
            assert r.passes_amp_gate, f"{name} margin={r.amp_margin} below gate"

    def test_non_amps_fail_amp_gate(self):
        for name, seq in NON_AMPS.items():
            r = ml.score_one(seq)
            assert r is not None
            assert not r.passes_amp_gate, f"{name} margin={r.amp_margin} should fail gate"

    def test_amp_like_score_ordering(self):
        # A gold-standard AMP must score more AMP-like than a homopolymer.
        amp = ml.score_one(KNOWN_AMPS["magainin2"])
        non = ml.score_one(NON_AMPS["polyA"])
        assert amp.amp_like_score > non.amp_like_score

    def test_melittin_more_hemolytic_than_magainin(self):
        # Melittin is the canonical hemolytic AMP; magainin is selective.
        melittin = ml.score_one("GIGAVLKVLTTGLPALISWIKRKRQQ")
        magainin = ml.score_one(KNOWN_AMPS["magainin2"])
        assert melittin.hemo_margin > magainin.hemo_margin
        assert magainin.nonhemo_score > melittin.nonhemo_score

    def test_scores_in_unit_interval(self):
        r = ml.score_one(KNOWN_AMPS["magainin2"])
        assert 0.0 <= r.amp_like_score <= 1.0
        assert 0.0 <= r.nonhemo_score <= 1.0

    def test_batch_matches_single(self):
        seqs = list(KNOWN_AMPS.values())
        batch = ml.score_batch(seqs)
        assert batch is not None and len(batch) == len(seqs)
        for seq, b in zip(seqs, batch):
            s = ml.score_one(seq)
            assert b.amp_margin == s.amp_margin
