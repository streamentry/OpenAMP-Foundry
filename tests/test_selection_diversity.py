"""Tests for selection/diversity.py — greedy_diverse_select."""
from __future__ import annotations

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.selection.diversity import greedy_diverse_select
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


def _make(cid: str, seq: str, ensemble: float = 0.80) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=PeptideCandidate(candidate_id=cid, sequence=seq, source="test"),
        features=compute_features(seq),
        scores={"ensemble": ensemble},
    )


# Clearly distinct sequences
_DISTINCT = [
    _make("AMP1", "KWKLFKKIGAVLKVL", 0.90),
    _make("AMP2", "DEDEDEDEDEDEDEDE", 0.80),
    _make("AMP3", "GGGGGGGGGGGGGGGG", 0.70),
]

# Three nearly identical sequences, one clearly distinct
_NEAR_DUPLICATES = [
    _make("A", "KWKLFKKIGAVLKVL", 0.90),
    _make("B", "KWKLFKKIGAVLKVK", 0.85),  # 1 substitution → very similar to A
    _make("C", "KWKLFKKIGAVLKVV", 0.80),  # 1 substitution → very similar to A
    _make("D", "DEDEDEDEDEDEDEDE", 0.70),  # completely different
]


class TestGreedyDiverseSelect:
    def test_returns_up_to_top_n(self):
        # _DISTINCT has pairwise similarities well below 0.85, so top_n=2 returns exactly 2
        result = greedy_diverse_select(_DISTINCT, top_n=2, max_pairwise_similarity=0.85)
        assert len(result) == 2

    def test_distinct_sequences_all_selected(self):
        result = greedy_diverse_select(_DISTINCT, top_n=3, max_pairwise_similarity=0.85)
        assert len(result) == 3

    def test_near_duplicates_excluded(self):
        result = greedy_diverse_select(_NEAR_DUPLICATES, top_n=4, max_pairwise_similarity=0.85)
        ids = {c.candidate.candidate_id for c in result}
        # B and C are near-duplicates of A (>0.85 similar) — at most one of A/B/C should survive
        amp_like = ids & {"A", "B", "C"}
        assert len(amp_like) <= 1

    def test_empty_input_returns_empty(self):
        assert greedy_diverse_select([], top_n=5) == []

    def test_top_n_zero_returns_empty(self):
        assert greedy_diverse_select(_DISTINCT, top_n=0) == []

    def test_first_in_list_wins_when_duplicates(self):
        result = greedy_diverse_select(_NEAR_DUPLICATES, top_n=4, max_pairwise_similarity=0.85)
        ids = {c.candidate.candidate_id for c in result}
        # A is first and highest ensemble — it should always be selected
        assert "A" in ids

    def test_distinct_survivor_included_despite_duplicates(self):
        result = greedy_diverse_select(_NEAR_DUPLICATES, top_n=4, max_pairwise_similarity=0.85)
        ids = {c.candidate.candidate_id for c in result}
        # D is completely different — should always be selected
        assert "D" in ids

    def test_threshold_one_accepts_all(self):
        # max_pairwise_similarity=1.0 → condition is sim <= 1.0, always True (sim is in [0,1])
        # so ALL candidates are accepted, including exact duplicates
        result = greedy_diverse_select(_NEAR_DUPLICATES, top_n=4, max_pairwise_similarity=1.0)
        assert len(result) == 4

    def test_low_threshold_rejects_most(self):
        # With a very low threshold, sequences with any non-zero similarity are excluded.
        # AMP1 (len 15, has G) and AMP3 (all-G, len 16) share similarity > 0 due to the
        # one G in AMP1, so AMP3 is excluded after AMP1 is added.
        result = greedy_diverse_select(_DISTINCT, top_n=3, max_pairwise_similarity=0.0)
        assert len(result) < len(_DISTINCT)

    def test_input_order_determines_priority(self):
        low_first = [
            _make("LOW", "KWKLFKKIGAVLKVL", 0.50),
            _make("HIGH", "KWKLFKKIGAVLKVK", 0.99),  # near-dup of LOW
        ]
        result = greedy_diverse_select(low_first, top_n=1, max_pairwise_similarity=0.85)
        assert result[0].candidate.candidate_id == "LOW"
