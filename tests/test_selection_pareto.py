"""Tests for selection/pareto.py — rank_candidates and select_top."""
from __future__ import annotations

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.selection.pareto import rank_candidates, select_top
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


def _make(cid: str, ensemble: float, seq: str = "KWKLFKKIGAVLKVL") -> ScoredCandidate:
    features = compute_features(seq)
    return ScoredCandidate(
        candidate=PeptideCandidate(candidate_id=cid, sequence=seq, source="test"),
        features=features,
        scores={"ensemble": ensemble, "activity": 0.7, "safety": 0.8},
    )


_POOL = [
    _make("A", 0.70),
    _make("B", 0.90),
    _make("C", 0.50),
    _make("D", 0.85),
    _make("E", 0.60),
]


class TestRankCandidates:
    def test_returns_descending_order(self):
        ranked = rank_candidates(list(_POOL))
        scores = [c.scores["ensemble"] for c in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_highest_ensemble_is_first(self):
        ranked = rank_candidates(list(_POOL))
        assert ranked[0].candidate.candidate_id == "B"

    def test_lowest_ensemble_is_last(self):
        ranked = rank_candidates(list(_POOL))
        assert ranked[-1].candidate.candidate_id == "C"

    def test_does_not_mutate_input(self):
        original_order = [c.candidate.candidate_id for c in _POOL]
        rank_candidates(list(_POOL))
        assert [c.candidate.candidate_id for c in _POOL] == original_order

    def test_empty_list_returns_empty(self):
        assert rank_candidates([]) == []

    def test_single_candidate_returned(self):
        single = [_make("X", 0.75)]
        ranked = rank_candidates(single)
        assert len(ranked) == 1
        assert ranked[0].candidate.candidate_id == "X"

    def test_equal_scores_preserves_all(self):
        equal = [_make("P", 0.80), _make("Q", 0.80), _make("R", 0.80)]
        ranked = rank_candidates(equal)
        assert len(ranked) == 3
        assert all(c.scores["ensemble"] == 0.80 for c in ranked)

    def test_missing_ensemble_key_defaults_to_zero(self):
        # rank_candidates uses .get("ensemble", 0.0) — a missing key silently ranks last
        no_ensemble = ScoredCandidate(
            candidate=PeptideCandidate(candidate_id="NO_ENS", sequence="AAAA", source="test"),
            features=compute_features("AAAA"),
            scores={"activity": 0.99},  # no "ensemble" key
        )
        ranked = rank_candidates([no_ensemble, _make("HAS_ENS", 0.5)])
        assert ranked[-1].candidate.candidate_id == "NO_ENS"


class TestSelectTop:
    def test_returns_correct_count(self):
        selected = select_top(_POOL, top_n=3)
        assert len(selected) == 3

    def test_returns_top_ensemble(self):
        selected = select_top(_POOL, top_n=2)
        ids = {c.candidate.candidate_id for c in selected}
        assert ids == {"B", "D"}

    def test_top_1_returns_best(self):
        selected = select_top(_POOL, top_n=1)
        assert selected[0].candidate.candidate_id == "B"

    def test_top_n_larger_than_pool_returns_all(self):
        selected = select_top(_POOL, top_n=100)
        assert len(selected) == len(_POOL)

    def test_top_0_returns_empty(self):
        selected = select_top(_POOL, top_n=0)
        assert selected == []

    def test_empty_pool_returns_empty(self):
        assert select_top([], top_n=5) == []

    def test_result_is_sorted_descending(self):
        selected = select_top(_POOL, top_n=4)
        scores = [c.scores["ensemble"] for c in selected]
        assert scores == sorted(scores, reverse=True)
