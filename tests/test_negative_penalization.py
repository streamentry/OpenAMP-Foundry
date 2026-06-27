"""Tests verifying that known problematic sequences are down-ranked.

Per AGENTS.md Phase 2: 'Toxicity penalty — Predicted hemolytic/toxic candidates
are down-ranked.' These tests check that the safety and activity scores penalise
sequences with properties associated with mammalian toxicity risk:
- Extreme hydrophobicity (hemolysis risk)
- All-cysteine (aggregation, disulfide chaos)
- Purely negative charge (anti-AMP, repelled by bacterial membranes)
- Very long repeat runs (low complexity, synthesis issues)

No claims of actual biological toxicity are made. These are heuristic proxy checks.
"""
from __future__ import annotations


from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


def score_seq(seq: str) -> dict:
    f = compute_features(seq)
    return {
        "features": f,
        "activity": activity_likeness_score(f),
        "safety": safety_score(f),
        "synthesis": synthesis_feasibility_score(f, valid_sequence=True),
    }


REFERENCE_AMP = "KWKLFKKIGAVLKVL"  # Magainin analogue, classic AMP


class TestActivityPenalization:
    def test_negative_charge_sequence_has_low_activity(self):
        # Purely negative charge — repelled by bacterial membranes
        result = score_seq("DEDEDEDEDEDE")
        assert result["activity"] < score_seq(REFERENCE_AMP)["activity"]

    def test_low_charge_sequence_has_low_activity(self):
        # No charge → low charge_density → low charge_score
        result = score_seq("AAAAAAAAGGGGGGGG")
        ref = score_seq(REFERENCE_AMP)
        assert result["activity"] < ref["activity"]

    def test_reference_amp_scores_above_low_charge(self):
        ref = score_seq(REFERENCE_AMP)
        bad = score_seq("GGGGGGGGGGGG")
        assert ref["activity"] > bad["activity"]


class TestSafetyPenalization:
    def test_extreme_hydrophobicity_penalizes_safety(self):
        # LLLLLLLLLLLL — very hydrophobic → hemolysis risk proxy
        result = score_seq("LLLLLLLLLLLL")
        assert result["safety"] < 1.0

    def test_high_cysteine_penalizes_safety(self):
        # All cys → risk of aggregation/disulfide chaos
        result = score_seq("CCCCCCCCCCCC")
        assert result["safety"] < 0.9

    def test_very_long_repeat_run_penalizes_safety(self):
        # 8+ same residue in a row triggers safety penalty
        result = score_seq("KKKKKKKKLLLL")
        assert result["safety"] < 1.0

    def test_reference_amp_has_high_safety(self):
        # Known AMP with moderate hydrophobicity should score well
        result = score_seq(REFERENCE_AMP)
        assert result["safety"] >= 0.8

    def test_pure_negative_charge_has_lower_safety_than_amp(self):
        neg = score_seq("DEDEDEDEDEDE")
        ref = score_seq(REFERENCE_AMP)
        # Safety differs because charge_density penalizes extremes
        assert ref["safety"] >= neg["safety"]


class TestSynthesisPenalization:
    def test_very_long_sequence_penalizes_synthesis(self):
        long_seq = "KWKLFKKIGAVLKVL" * 3  # 45 residues
        result = score_seq(long_seq)
        assert result["synthesis"] < 1.0

    def test_high_cysteine_penalizes_synthesis(self):
        result = score_seq("CCCCCCCCCCCC")
        assert result["synthesis"] < 0.9

    def test_short_repeat_penalizes_synthesis(self):
        result = score_seq("KKKKKKKKK")  # long repeat run
        assert result["synthesis"] < 1.0

    def test_reference_amp_fully_feasible(self):
        # 15-residue AMP with no special challenges should be fully feasible
        result = score_seq(REFERENCE_AMP)
        assert result["synthesis"] == 1.0


class TestNegativesVsPositivesSummary:
    """Aggregate check: negatives from demo should average below known AMPs."""

    KNOWN_AMPS = [
        "KWKLFKKIGAVLKVL",
        "GIGKFLHSAKKFGKAFVGEIMNS",
        "GLFDIVKKVVGALGSL",
        "RRWQWRMKKLG",
    ]
    KNOWN_NEGATIVES = [
        "AAAAAAAAAAAA",
        "DEDEDEDEDEDE",
        "GGGGGGGGGGGG",
    ]

    def _avg_activity(self, seqs: list[str]) -> float:
        scores = [score_seq(s)["activity"] for s in seqs]
        return sum(scores) / len(scores)

    def test_amp_average_activity_exceeds_negative_average(self):
        amp_avg = self._avg_activity(self.KNOWN_AMPS)
        neg_avg = self._avg_activity(self.KNOWN_NEGATIVES)
        assert amp_avg > neg_avg, (
            f"AMP avg activity {amp_avg:.4f} should exceed negative avg {neg_avg:.4f}"
        )

    def test_amp_activity_margin_over_negatives(self):
        amp_avg = self._avg_activity(self.KNOWN_AMPS)
        neg_avg = self._avg_activity(self.KNOWN_NEGATIVES)
        margin = amp_avg - neg_avg
        assert margin >= 0.15, f"Activity margin {margin:.4f} below minimum 0.15"
