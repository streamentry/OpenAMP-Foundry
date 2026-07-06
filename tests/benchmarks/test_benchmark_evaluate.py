"""Tests for benchmark evaluation: recall@k, enrichment factor, and summary."""
from __future__ import annotations


from openamp_foundry.benchmark.evaluate import (
    benchmark_summary,
    enrichment_factor,
    random_recall_at_k,
    recall_at_k,
)
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


def _make_scored(cid: str, seq: str, ensemble: float) -> ScoredCandidate:
    features = compute_features(seq)
    scores = {
        "activity": ensemble,
        "safety": 0.8,
        "synthesis": 0.9,
        "novelty": 0.5,
        "ensemble": ensemble,
    }
    return ScoredCandidate(
        candidate=PeptideCandidate(candidate_id=cid, sequence=seq, source="test"),
        features=features,
        scores=scores,
    )


ITEMS = [
    _make_scored("C1", "KWKLFKKIGAVLKVL", 0.9),
    _make_scored("C2", "GIGKFLHSAKKFG", 0.7),
    _make_scored("C3", "AAAAAAAA", 0.3),
    _make_scored("C4", "GLFDIVKK", 0.6),
    _make_scored("C5", "DEDEDEDE", 0.1),
]
POSITIVES = {"C1", "C2"}


class TestRecallAtK:
    def test_perfect_recall_when_all_positives_in_top_k(self):
        assert recall_at_k(ITEMS, POSITIVES, k=2) == 1.0

    def test_partial_recall(self):
        assert recall_at_k(ITEMS, POSITIVES, k=1) == 0.5

    def test_zero_recall_when_no_positives_in_top_k(self):
        # Only C5 (worst score) is "positive" here
        assert recall_at_k(ITEMS, {"C5"}, k=1) == 0.0

    def test_full_recall_at_all(self):
        assert recall_at_k(ITEMS, POSITIVES, k=len(ITEMS)) == 1.0

    def test_empty_positives_returns_zero(self):
        assert recall_at_k(ITEMS, set(), k=3) == 0.0


class TestRandomRecallAtK:
    def test_expected_random_recall(self):
        # E[recall@k] = k / n_candidates (hypergeometric expectation)
        # k=2, n_candidates=5 → 2/5 = 0.4
        result = random_recall_at_k(n_candidates=5, n_positives=2, k=2)
        assert abs(result - 0.4) < 0.001, f"Expected 0.4, got {result}"

    def test_expected_random_recall_k_less_than_positives(self):
        # k=1 < n_positives=5, n_candidates=10 → E[recall@1] = 1/10 = 0.1
        result = random_recall_at_k(n_candidates=10, n_positives=5, k=1)
        assert abs(result - 0.1) < 0.001, f"Expected 0.1, got {result}"

    def test_random_recall_real_benchmark_scale(self):
        # 43 AMPs + 44 background = 87 total; k=8 → E[recall@8] = 8/87 ≈ 0.0920
        result = random_recall_at_k(n_candidates=87, n_positives=43, k=8)
        assert abs(result - 8 / 87) < 0.001, f"Expected {8/87:.4f}, got {result}"

    def test_zero_candidates_returns_zero(self):
        assert random_recall_at_k(0, 2, 2) == 0.0

    def test_zero_positives_returns_zero(self):
        assert random_recall_at_k(5, 0, 2) == 0.0

    def test_k_equals_total_returns_one(self):
        result = random_recall_at_k(n_candidates=5, n_positives=2, k=5)
        assert result == 1.0


class TestEnrichmentFactor:
    def test_ef_greater_than_one_for_good_ranker(self):
        # Top-2 by ensemble score are C1 and C2, which are our positives
        ef = enrichment_factor(ITEMS, POSITIVES, k=2)
        assert ef > 1.0

    def test_ef_approximately_one_for_random(self):
        # With k = all items, every ranker has the same recall
        ef = enrichment_factor(ITEMS, POSITIVES, k=len(ITEMS))
        assert abs(ef - 1.0) < 0.01


class TestBenchmarkSummary:
    def test_summary_has_required_keys(self):
        result = benchmark_summary(ITEMS, POSITIVES, ks=[1, 2, 5])
        assert "disclaimer" in result
        assert "n_candidates" in result
        assert "n_positives" in result
        assert "results" in result
        assert "verdict" in result

    def test_summary_contains_disclaimer(self):
        result = benchmark_summary(ITEMS, POSITIVES, ks=[2])
        assert "do not prove biological efficacy" in result["disclaimer"].lower()

    def test_verdict_positive_when_pipeline_outperforms(self):
        # C1 and C2 are top-ranked and are our positives — should outperform random at k=2
        result = benchmark_summary(ITEMS, POSITIVES, ks=[2])
        assert result["verdict"] == "pipeline outperforms random"

    def test_results_per_k(self):
        result = benchmark_summary(ITEMS, POSITIVES, ks=[1, 3])
        assert len(result["results"]) == 2
        assert result["results"][0]["k"] == 1
        assert result["results"][1]["k"] == 3

    def test_auto_ks_when_none_given(self):
        result = benchmark_summary(ITEMS, POSITIVES)
        assert len(result["results"]) > 0

    def test_counts_are_correct(self):
        result = benchmark_summary(ITEMS, POSITIVES, ks=[2])
        assert result["n_candidates"] == 5
        assert result["n_positives"] == 2


class TestEnrichmentFactorEdgeCases:
    def test_enrichment_factor_returns_zero_when_k_is_zero(self):
        # k=0 → random_recall_at_k(n, n_pos, 0) == 0.0 → guard branch returns 0.0
        ef = enrichment_factor(ITEMS, POSITIVES, k=0)
        assert ef == 0.0
