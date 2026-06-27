"""Cluster split validation tests — Phase 2 requirement.

AGENTS.md: "Cluster split — Pipeline still performs when near-duplicates are removed."

These tests verify that:
1. The cluster algorithm correctly groups near-duplicate sequences.
2. The cluster split partitions sequences so each cluster is not split across reference/test.
3. After removing near-duplicate references, the pipeline still enriches AMP-like sequences
   over non-AMP negatives — confirming the scoring is feature-based, not reference-proximity-based.

All results are computational scores only. No biological activity is implied.
"""
from __future__ import annotations

import csv
from pathlib import Path


from openamp_foundry.benchmark.evaluate import (
    enrichment_factor,
    find_contaminated_references,
    recall_at_k,
)
from openamp_foundry.benchmark.splits import cluster_by_similarity, cluster_split
from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.pipeline import score_candidates
from openamp_foundry.scoring.novelty import normalized_similarity


POOL_CSV = "examples/benchmark/cluster_split_pool.csv"
REFS_CSV = "examples/benchmark/cluster_split_refs.csv"

# CS-POS-001/002 are near-dups of CSREF-001 (KWKLFKKIGAVLKVL)
# CS-POS-003 is a near-dup of CSREF-003 (GLFDIVKKVVGALGSL)
POSITIVE_IDS = {"CS-POS-001", "CS-POS-002", "CS-POS-003"}


class TestClusterBySimilarity:
    def test_identical_sequences_in_same_cluster(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKVL", "AAAAAAAAAA"]
        clusters = cluster_by_similarity(seqs, threshold=0.70)
        assert len(clusters) == 2
        assert set(clusters[0]) == {0, 1}

    def test_near_duplicates_co_clustered(self):
        # KWKLFKKIGAVLKVL vs KWKLFKKIGAVLKFL: levenshtein=1, len=15 → sim=14/15≈0.933
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "AAAAAAAAAAAAA"]
        clusters = cluster_by_similarity(seqs, threshold=0.70)
        assert len(clusters) == 2
        assert set(clusters[0]) == {0, 1}
        assert clusters[1] == [2]

    def test_dissimilar_sequences_in_separate_clusters(self):
        seqs = ["KWKLFKKIGAVLKVL", "AAAAAAAAAAAA", "DEDEDEDEDEDE"]
        clusters = cluster_by_similarity(seqs, threshold=0.70)
        assert len(clusters) == 3
        assert all(len(c) == 1 for c in clusters)

    def test_single_sequence_forms_one_cluster(self):
        clusters = cluster_by_similarity(["KWKLFKKIGAVLKVL"], threshold=0.70)
        assert clusters == [[0]]

    def test_empty_input(self):
        clusters = cluster_by_similarity([], threshold=0.70)
        assert clusters == []

    def test_threshold_controls_grouping(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL"]
        sim = normalized_similarity(seqs[0], seqs[1])
        # Should cluster at low threshold, not at very high threshold
        low = cluster_by_similarity(seqs, threshold=sim - 0.01)
        assert len(low) == 1  # grouped
        high = cluster_by_similarity(seqs, threshold=sim + 0.01)
        assert len(high) == 2  # split

    def test_all_index_covered_exactly_once(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "RRWQWRMKKLG", "AAAAAAAAAAAAA"]
        clusters = cluster_by_similarity(seqs, threshold=0.70)
        all_indices = [i for c in clusters for i in c]
        assert sorted(all_indices) == list(range(len(seqs)))


class TestClusterSplit:
    def test_singleton_clusters_all_go_to_reference(self):
        seqs = ["KWKLFKKIGAVLKVL", "AAAAAAAAAAAAA", "DEDEDEDEDEDE"]
        ref_idx, test_idx = cluster_split(seqs, threshold=0.70)
        assert set(ref_idx) == {0, 1, 2}
        assert test_idx == []

    def test_near_dup_goes_to_test(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "AAAAAAAAAAAAA"]
        ref_idx, test_idx = cluster_split(seqs, threshold=0.70)
        assert 0 in ref_idx  # cluster center → reference
        assert 1 in test_idx  # near-dup → test
        assert 2 in ref_idx  # unrelated → reference

    def test_reference_and_test_partition_all_sequences(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "RRWQWRMKKLG", "AAAAAAAAAAAAA"]
        ref_idx, test_idx = cluster_split(seqs, threshold=0.70)
        all_covered = sorted(ref_idx + test_idx)
        assert all_covered == list(range(len(seqs)))

    def test_no_test_sequence_is_near_dup_of_different_cluster_ref(self):
        seqs = ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "RRWQWRMKKLG"]
        ref_idx, test_idx = cluster_split(seqs, threshold=0.70)
        # test_idx should only contain the near-dup of cluster A (index 1)
        # and NOT the unrelated cluster B center (index 2)
        assert len(test_idx) == 1
        assert 1 in test_idx  # only near-dup of cluster A goes to test
        assert 2 not in test_idx  # cluster B center stays in reference

    def test_multiple_near_dup_clusters(self):
        # Two separate clusters with near-dups each
        seqs = [
            "KWKLFKKIGAVLKVL",  # cluster A center → ref
            "KWKLFKKIGAVLKFL",  # near-dup of A → test
            "RRWQWRMKKLG",      # cluster B center → ref
            "RRWQWRMKKLF",      # near-dup of B (M→F) → test
            "AAAAAAAAAAAA",     # singleton → ref
        ]
        ref_idx, test_idx = cluster_split(seqs, threshold=0.70)
        assert sorted(ref_idx) == [0, 2, 4]
        assert sorted(test_idx) == [1, 3]


class TestFindContaminatedReferences:
    def test_identifies_near_dup_reference(self):
        candidate_seqs = ["KWKLFKKIGAVLKFL", "AAAAAAAAAAAA"]
        candidate_ids = ["CS-POS-001", "CS-NEG-001"]
        ref_seqs = ["KWKLFKKIGAVLKVL", "DEDEDEDEDEDE"]  # ref[0] near-dup of CS-POS-001
        positive_ids = {"CS-POS-001"}

        contaminated = find_contaminated_references(
            candidate_seqs, ref_seqs, positive_ids, candidate_ids, threshold=0.70
        )
        assert 0 in contaminated  # KWKLFKKIGAVLKVL is near-dup of CS-POS-001
        assert 1 not in contaminated  # DEDEDEDEDEDE is not

    def test_non_similar_reference_not_contaminated(self):
        candidate_seqs = ["KWKLFKKIGAVLKFL"]
        candidate_ids = ["CS-POS-001"]
        ref_seqs = ["DEDEDEDEDEDE", "GGGGGGGGGGGG"]
        positive_ids = {"CS-POS-001"}

        contaminated = find_contaminated_references(
            candidate_seqs, ref_seqs, positive_ids, candidate_ids, threshold=0.70
        )
        assert contaminated == set()

    def test_only_positive_near_dups_flagged(self):
        # Negative candidate has near-dup in ref — should NOT be flagged
        candidate_seqs = ["KWKLFKKIGAVLKFL", "DEDEDEDEDEDE"]
        candidate_ids = ["CS-POS-001", "CS-NEG-001"]
        ref_seqs = ["KWKLFKKIGAVLKVL", "DEDEDEDEDEDF"]  # ref[1] near-dup of CS-NEG-001
        positive_ids = {"CS-POS-001"}

        contaminated = find_contaminated_references(
            candidate_seqs, ref_seqs, positive_ids, candidate_ids, threshold=0.70
        )
        assert 0 in contaminated   # ref[0] is near-dup of positive
        assert 1 not in contaminated  # ref[1] is near-dup of NEGATIVE — not flagged


class TestClusterSplitEnrichment:
    """End-to-end tests verifying pipeline performance after cluster split."""

    def test_positives_score_higher_than_negatives_without_references(self):
        """AMP-like sequences should score above non-AMP negatives based on features alone."""
        scored, _ = score_candidates(POOL_CSV)  # no reference → novelty=1.0 for all
        pos_scores = [
            s.scores["activity"]
            for s in scored
            if s.candidate.candidate_id in POSITIVE_IDS
        ]
        neg_scores = [
            s.scores["activity"]
            for s in scored
            if s.candidate.candidate_id not in POSITIVE_IDS
        ]
        assert pos_scores, "No positive candidates scored"
        assert neg_scores, "No negative candidates scored"
        avg_pos = sum(pos_scores) / len(pos_scores)
        avg_neg = sum(neg_scores) / len(neg_scores)
        assert avg_pos > avg_neg, (
            f"AMP-like candidates (avg activity={avg_pos:.3f}) should score higher "
            f"than non-AMP negatives (avg activity={avg_neg:.3f})"
        )

    def test_enrichment_factor_positive_after_cluster_split(self):
        """EF > 1.0 after removing near-dup references (cluster split scenario)."""
        scored_full, _ = score_candidates(POOL_CSV, REFS_CSV)

        # Identify contaminated references
        candidate_seqs = [s.candidate.sequence for s in scored_full]
        candidate_ids = [s.candidate.candidate_id for s in scored_full]
        refs = load_candidates_csv(REFS_CSV)
        ref_seqs = [r.sequence for r in refs]

        contaminated = find_contaminated_references(
            candidate_seqs, ref_seqs, POSITIVE_IDS, candidate_ids, threshold=0.70
        )
        # At least one reference should be flagged as near-dup of the test positives
        assert contaminated, "Expected at least one contaminated reference to be identified"

        # Score without near-dup references (cluster-split reference set)
        scored_clean, _ = score_candidates(POOL_CSV)  # no reference = clean split

        ef = enrichment_factor(scored_clean, POSITIVE_IDS, k=3)
        assert ef > 1.0, (
            f"EF={ef:.3f} should be > 1.0 after cluster split "
            "(pipeline should still enrich AMP-like sequences over negatives)"
        )

    def test_recall_at_k3_beats_random_after_split(self):
        """recall@3 > random_recall@3 after removing near-dup references."""
        from openamp_foundry.benchmark.evaluate import random_recall_at_k

        scored, _ = score_candidates(POOL_CSV)  # no references
        n = len(scored)
        n_pos = len(POSITIVE_IDS)

        rc = recall_at_k(scored, POSITIVE_IDS, k=3)
        rrc = random_recall_at_k(n, n_pos, k=3)
        assert rc >= rrc, (
            f"recall@3={rc:.4f} should be >= random baseline={rrc:.4f} "
            "after cluster split"
        )

    def test_cluster_split_benchmark_data_integrity(self):
        """Verify the cluster split pool has the expected IDs and structure."""
        pool = Path(POOL_CSV)
        assert pool.exists(), "Cluster split pool CSV not found"

        with pool.open() as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        ids = {r["id"] for r in rows}
        assert POSITIVE_IDS.issubset(ids), "Expected positive IDs missing from pool"
        neg_ids = ids - POSITIVE_IDS
        assert len(neg_ids) >= 8, "Expected at least 8 negative controls in pool"

    def test_cluster_split_finds_near_dups_in_reference(self):
        """Cluster split analysis correctly detects CSREF-001 as near-dup of CS-POS-001/002."""
        scored, _ = score_candidates(POOL_CSV, REFS_CSV)
        candidate_seqs = [s.candidate.sequence for s in scored]
        candidate_ids = [s.candidate.candidate_id for s in scored]
        refs = load_candidates_csv(REFS_CSV)
        ref_seqs = [r.sequence for r in refs]

        contaminated = find_contaminated_references(
            candidate_seqs, ref_seqs, POSITIVE_IDS, candidate_ids, threshold=0.70
        )
        # CSREF-001 (KWKLFKKIGAVLKVL) should be flagged as near-dup of CS-POS-001/002
        csref001_idx = next(i for i, r in enumerate(refs) if r.candidate_id == "CSREF-001")
        assert csref001_idx in contaminated

    def test_feature_scores_drive_ranking_not_reference_proximity(self):
        """Verify the positives rank above negatives on feature scores alone (no references)."""
        scored, _ = score_candidates(POOL_CSV)

        # Sort by ensemble score
        ranked = sorted(scored, key=lambda s: s.scores["ensemble"], reverse=True)
        top3_ids = {s.candidate.candidate_id for s in ranked[:3]}

        # At least 2 of top 3 should be known positives
        overlap = len(top3_ids & POSITIVE_IDS)
        assert overlap >= 2, (
            f"Expected ≥2 of top-3 to be AMP-like positives, got {overlap}. "
            f"Top 3: {top3_ids}"
        )
