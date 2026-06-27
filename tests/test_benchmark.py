"""Tests for benchmark leakage detection, evaluation, and splits."""
from __future__ import annotations

from openamp_foundry.benchmark.evaluate import top_k_ids
from openamp_foundry.benchmark.leakage import find_near_duplicates
from openamp_foundry.benchmark.splits import deterministic_split
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


def _make_candidate(cid: str, seq: str) -> PeptideCandidate:
    return PeptideCandidate(candidate_id=cid, sequence=seq, source="test")


def _make_scored(cid: str, seq: str, ensemble: float) -> ScoredCandidate:
    features = compute_features(seq)
    scores = {
        "activity": ensemble,
        "safety": 0.8,
        "synthesis": 0.9,
        "novelty": 0.5,
        "ensemble": ensemble,
    }
    return ScoredCandidate(candidate=_make_candidate(cid, seq), features=features, scores=scores)


class TestFindNearDuplicates:
    def test_exact_match_detected(self):
        cands = [_make_candidate("C1", "KWKLFKK")]
        refs = [_make_candidate("R1", "KWKLFKK")]
        hits = find_near_duplicates(cands, refs, threshold=0.90)
        assert len(hits) == 1
        assert hits[0]["candidate_id"] == "C1"
        assert hits[0]["similarity"] == 1.0

    def test_different_sequence_no_hit(self):
        cands = [_make_candidate("C1", "KWKLFKK")]
        refs = [_make_candidate("R1", "GLFDIVKK")]
        hits = find_near_duplicates(cands, refs, threshold=0.90)
        assert hits == []

    def test_threshold_boundary(self):
        # "KWKLFKK" vs "KWKLFKX" — one substitution out of 7 chars = ~86% similarity
        cands = [_make_candidate("C1", "KWKLFKK")]
        refs = [_make_candidate("R1", "KWKLFKA")]
        hits_high = find_near_duplicates(cands, refs, threshold=0.95)
        hits_low = find_near_duplicates(cands, refs, threshold=0.80)
        assert hits_high == []
        assert len(hits_low) == 1

    def test_multiple_candidates_and_refs(self):
        cands = [
            _make_candidate("C1", "KWKLFKK"),
            _make_candidate("C2", "GLFDIVKK"),
        ]
        refs = [
            _make_candidate("R1", "KWKLFKK"),
            _make_candidate("R2", "AAAAAAAAA"),
        ]
        hits = find_near_duplicates(cands, refs, threshold=0.90)
        ids = {h["candidate_id"] for h in hits}
        assert "C1" in ids
        assert "C2" not in ids

    def test_empty_inputs(self):
        assert find_near_duplicates([], [], threshold=0.90) == []
        assert find_near_duplicates([_make_candidate("C1", "KWKLFKK")], [], threshold=0.90) == []


class TestTopKIds:
    def test_returns_top_k_by_ensemble(self):
        items = [
            _make_scored("C1", "KWKLFKKIGAVLKVL", 0.8),
            _make_scored("C2", "GLFDIVKK", 0.6),
            _make_scored("C3", "AAAAAAAA", 0.3),
        ]
        top = top_k_ids(items, k=2)
        assert "C1" in top
        assert "C2" in top
        assert "C3" not in top

    def test_k_larger_than_list(self):
        items = [_make_scored("C1", "KWKLFKK", 0.9)]
        top = top_k_ids(items, k=10)
        assert "C1" in top

    def test_empty_list(self):
        assert top_k_ids([], k=5) == set()


class TestDeterministicSplit:
    def test_split_is_reproducible(self):
        cands = [_make_candidate(f"C{i}", "K" * (8 + i)) for i in range(10)]
        train1, holdout1 = deterministic_split(cands, holdout_mod=5)
        train2, holdout2 = deterministic_split(cands, holdout_mod=5)
        assert [c.candidate_id for c in train1] == [c.candidate_id for c in train2]
        assert [c.candidate_id for c in holdout1] == [c.candidate_id for c in holdout2]

    def test_no_overlap_between_train_and_holdout(self):
        cands = [_make_candidate(f"C{i}", "K" * (8 + i)) for i in range(15)]
        train, holdout = deterministic_split(cands, holdout_mod=5)
        train_ids = {c.candidate_id for c in train}
        holdout_ids = {c.candidate_id for c in holdout}
        assert train_ids.isdisjoint(holdout_ids)

    def test_all_items_covered(self):
        cands = [_make_candidate(f"C{i}", "K" * (8 + i)) for i in range(10)]
        train, holdout = deterministic_split(cands, holdout_mod=3)
        assert len(train) + len(holdout) == 10

    def test_holdout_fraction(self):
        cands = [_make_candidate(f"C{i}", "K" * (8 + i)) for i in range(10)]
        _, holdout = deterministic_split(cands, holdout_mod=5)
        # Every 5th item → 2 holdout from 10
        assert len(holdout) == 2
