"""Tests for hidden-active recovery benchmark.

These tests verify that the pipeline recovers known-active AMPs better than
a random ranker when mixed with non-active sequences. This is a key Phase 2
requirement per AGENTS.md.

No biological activity is implied or proven by these results.
The benchmark only tests whether physicochemical features of known AMPs
correlate with higher ensemble scores than simple non-AMP sequences.
"""
from __future__ import annotations

import json


from openamp_foundry.benchmark.evaluate import (
    benchmark_summary,
    enrichment_factor,
    recall_at_k,
)
from openamp_foundry.cli import main
from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.pipeline import score_candidates
from openamp_foundry.selection.pareto import rank_candidates


MIXED_CANDIDATES = "examples/benchmark/mixed_candidates.csv"
ACTIVE_LABELS = "examples/benchmark/active_labels.csv"

POSITIVE_IDS = {
    "BM-POS-001",
    "BM-POS-002",
    "BM-POS-003",
    "BM-POS-004",
    "BM-POS-005",
}


class TestHiddenActiveRecovery:
    def test_all_positives_rank_in_top_half(self):
        scored, _ = score_candidates(MIXED_CANDIDATES)
        ranked = rank_candidates(scored)
        n = len(ranked)
        top_half_ids = {item.candidate.candidate_id for item in ranked[: n // 2]}
        for pid in POSITIVE_IDS:
            assert pid in top_half_ids, f"{pid} not in top half"

    def test_recall_at_5_equals_1(self):
        """All 5 positives should appear in top-5 of 20 candidates."""
        scored, _ = score_candidates(MIXED_CANDIDATES)
        rc = recall_at_k(scored, POSITIVE_IDS, k=5)
        assert rc == 1.0, f"Expected recall@5=1.0, got {rc}"

    def test_enrichment_factor_at_5_exceeds_2(self):
        """Pipeline should achieve at least 2× enrichment vs random at k=5."""
        scored, _ = score_candidates(MIXED_CANDIDATES)
        ef = enrichment_factor(scored, POSITIVE_IDS, k=5)
        assert ef >= 2.0, f"Enrichment factor {ef} below minimum of 2.0"

    def test_pipeline_verdict_outperforms_random(self):
        scored, _ = score_candidates(MIXED_CANDIDATES)
        summary = benchmark_summary(scored, POSITIVE_IDS, ks=[5])
        assert summary["verdict"] == "pipeline outperforms random"

    def test_negatives_score_lower_than_positives_on_average(self):
        scored, _ = score_candidates(MIXED_CANDIDATES)
        pos_scores = [
            s.scores["ensemble"]
            for s in scored
            if s.candidate.candidate_id in POSITIVE_IDS
        ]
        neg_scores = [
            s.scores["ensemble"]
            for s in scored
            if s.candidate.candidate_id not in POSITIVE_IDS
        ]
        assert pos_scores
        assert neg_scores
        assert sum(pos_scores) / len(pos_scores) > sum(neg_scores) / len(neg_scores)

    def test_bench_baseline_cli_shows_enrichment(self, tmp_path, capsys):
        out = str(tmp_path / "bench_report.json")
        ret = main([
            "bench", "baseline",
            "--candidates", MIXED_CANDIDATES,
            "--positives", ACTIVE_LABELS,
            "--k", "5",
            "--out", out,
        ])
        assert ret == 0
        data = json.loads((tmp_path / "bench_report.json").read_text())
        k5_result = next(r for r in data["results"] if r["k"] == 5)
        assert k5_result["enrichment_factor"] >= 2.0
        assert data["verdict"] == "pipeline outperforms random"

    def test_benchmark_summary_disclaimer_present(self):
        scored, _ = score_candidates(MIXED_CANDIDATES)
        summary = benchmark_summary(scored, POSITIVE_IDS, ks=[5])
        assert "disclaimer" in summary
        assert len(summary["disclaimer"]) > 20

    def test_known_active_amps_outrank_all_repeat_sequences(self):
        """Biologically implausible repeat sequences should rank below AMP-like ones."""
        scored, _ = score_candidates(MIXED_CANDIDATES)
        ranked = rank_candidates(scored)
        ranked_ids = [s.candidate.candidate_id for s in ranked]

        # All positives should appear before all-same-AA negatives
        for pos_id in POSITIVE_IDS:
            pos_rank = ranked_ids.index(pos_id)
            for neg_id in ["BM-NEG-001", "BM-NEG-002", "BM-NEG-004"]:
                neg_rank = ranked_ids.index(neg_id)
                assert pos_rank < neg_rank, (
                    f"{pos_id} (rank {pos_rank}) should outrank {neg_id} (rank {neg_rank})"
                )


class TestBenchmarkDataIntegrity:
    def test_benchmark_csvs_exist(self):
        from pathlib import Path
        assert Path(MIXED_CANDIDATES).exists()
        assert Path(ACTIVE_LABELS).exists()

    def test_all_positive_ids_in_mixed_candidates(self):
        mixed = load_candidates_csv(MIXED_CANDIDATES)
        mixed_ids = {c.candidate_id for c in mixed}
        for pid in POSITIVE_IDS:
            assert pid in mixed_ids, f"Positive {pid} missing from mixed candidates"

    def test_mixed_has_both_positives_and_negatives(self):
        mixed = load_candidates_csv(MIXED_CANDIDATES)
        ids = {c.candidate_id for c in mixed}
        positive_overlap = ids & POSITIVE_IDS
        negative_only = ids - POSITIVE_IDS
        assert len(positive_overlap) >= 3
        assert len(negative_only) >= 5

    def test_active_labels_are_subset_of_mixed(self):
        mixed = load_candidates_csv(MIXED_CANDIDATES)
        active = load_candidates_csv(ACTIVE_LABELS)
        mixed_ids = {c.candidate_id for c in mixed}
        for a in active:
            assert a.candidate_id in mixed_ids
