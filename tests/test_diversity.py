"""Tests for src/openamp_foundry/analysis/diversity.py"""
from openamp_foundry.analysis.diversity import (
    cluster_panel,
    diversity_stats,
    family_structural_warnings,
    levenshtein_similarity,
    pairwise_similarity_matrix,
    recommend_minimal_diverse_panel,
)


# ---------------------------------------------------------------------------
# levenshtein_similarity
# ---------------------------------------------------------------------------

class TestLevenshteinSimilarity:
    def test_identical_sequences(self):
        assert levenshtein_similarity("ACDEF", "ACDEF") == 1.0

    def test_completely_different(self):
        # Every character substituted
        sim = levenshtein_similarity("AAAAA", "BBBBB")
        assert sim == 0.0

    def test_empty_both(self):
        assert levenshtein_similarity("", "") == 1.0

    def test_single_substitution(self):
        # 1 edit in 5 → similarity = 1 - 1/5 = 0.8
        sim = levenshtein_similarity("ACDEF", "ACGEF")
        assert abs(sim - 0.8) < 1e-9

    def test_one_insertion(self):
        # "ABC" → "ABCD": 1 insertion, max_len = 4 → sim = 1 - 1/4 = 0.75
        sim = levenshtein_similarity("ABC", "ABCD")
        assert abs(sim - 0.75) < 1e-9

    def test_symmetric(self):
        a, b = "KRLFKKIG", "KRLFKKIGSALKFL"
        assert levenshtein_similarity(a, b) == levenshtein_similarity(b, a)

    def test_case_insensitive(self):
        assert levenshtein_similarity("acdef", "ACDEF") == 1.0

    def test_known_seed005_variants_high_similarity(self):
        # Two SEED-005 variants — should be > 0.6
        v1 = "KRLFKKIGSALKFL"
        v2 = "KRLFKKVGSALRFL"
        assert levenshtein_similarity(v1, v2) > 0.6

    def test_different_families_low_similarity(self):
        seed005 = "KRLFKKIGSALKFL"
        seed003 = "RRWQWRMKKLG"
        assert levenshtein_similarity(seed005, seed003) < 0.5


# ---------------------------------------------------------------------------
# pairwise_similarity_matrix
# ---------------------------------------------------------------------------

class TestPairwiseSimilarityMatrix:
    def test_diagonal_is_one(self):
        seqs = ["ACDEF", "KLMNO", "PQRST"]
        mat = pairwise_similarity_matrix(seqs)
        for i in range(len(seqs)):
            assert mat[i][i] == 1.0

    def test_symmetric(self):
        seqs = ["ACDEF", "KLMNO", "PQRST"]
        mat = pairwise_similarity_matrix(seqs)
        n = len(seqs)
        for i in range(n):
            for j in range(n):
                assert abs(mat[i][j] - mat[j][i]) < 1e-9

    def test_shape(self):
        seqs = ["ABC", "DEF", "GHI", "JKL"]
        mat = pairwise_similarity_matrix(seqs)
        assert len(mat) == 4
        assert all(len(row) == 4 for row in mat)

    def test_single_sequence(self):
        mat = pairwise_similarity_matrix(["ACDEF"])
        assert mat == [[1.0]]

    def test_values_in_range(self):
        seqs = ["KRLFKKIGSALKFL", "KRLFKKVGSALRFL", "RRWQWRMKKLG"]
        mat = pairwise_similarity_matrix(seqs)
        for row in mat:
            for v in row:
                assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# cluster_panel
# ---------------------------------------------------------------------------

class TestClusterPanel:
    def _make_candidates(self, id_seq_pairs):
        return [{"candidate_id": cid, "sequence": seq} for cid, seq in id_seq_pairs]

    def test_identical_sequences_same_cluster(self):
        candidates = self._make_candidates([
            ("A", "KRLFKKIGSALKFL"),
            ("B", "KRLFKKIGSALKFL"),
        ])
        clustered = cluster_panel(candidates, similarity_threshold=0.6)
        assert clustered[0]["cluster_id"] == clustered[1]["cluster_id"]

    def test_different_families_different_clusters(self):
        candidates = self._make_candidates([
            ("seed005", "KRLFKKIGSALKFL"),
            ("seed003", "RRWQWRMKKLG"),
        ])
        clustered = cluster_panel(candidates, similarity_threshold=0.6)
        assert clustered[0]["cluster_id"] != clustered[1]["cluster_id"]

    def test_preserves_original_fields(self):
        candidates = [{"candidate_id": "X", "sequence": "ACDEF", "ensemble": 0.85}]
        clustered = cluster_panel(candidates)
        assert clustered[0]["ensemble"] == 0.85
        assert "cluster_id" in clustered[0]

    def test_cluster_id_added(self):
        candidates = self._make_candidates([("A", "ACDEF"), ("B", "KLMNO")])
        clustered = cluster_panel(candidates)
        assert all("cluster_id" in c for c in clustered)

    def test_threshold_zero_all_same_cluster(self):
        # threshold=0 → everything clusters together
        candidates = self._make_candidates([
            ("A", "AAAA"), ("B", "BBBB"), ("C", "CCCC"),
        ])
        clustered = cluster_panel(candidates, similarity_threshold=0.0)
        ids = {c["cluster_id"] for c in clustered}
        assert len(ids) == 1

    def test_threshold_one_all_different(self):
        # threshold=1.0 → only identical sequences cluster
        candidates = self._make_candidates([
            ("A", "AAAA"), ("B", "BBBB"), ("C", "CCCC"),
        ])
        clustered = cluster_panel(candidates, similarity_threshold=1.0)
        ids = {c["cluster_id"] for c in clustered}
        assert len(ids) == 3

    def test_seed005_family_clusters_together(self):
        candidates = self._make_candidates([
            ("V068", "KRLMKKIGSAIKFL"),
            ("V009", "KRFFKKIGSALKFA"),
            ("V063", "KRLFRKIGSALKFV"),
        ])
        clustered = cluster_panel(candidates, similarity_threshold=0.6)
        ids = {c["cluster_id"] for c in clustered}
        # All similar → should share cluster
        assert len(ids) == 1


# ---------------------------------------------------------------------------
# recommend_minimal_diverse_panel
# ---------------------------------------------------------------------------

class TestRecommendMinimalDiversePanel:
    def test_one_per_cluster(self):
        clustered = [
            {"candidate_id": "A", "cluster_id": 0},
            {"candidate_id": "B", "cluster_id": 0},
            {"candidate_id": "C", "cluster_id": 1},
        ]
        minimal = recommend_minimal_diverse_panel(clustered, n_per_cluster=1)
        assert len(minimal) == 2
        assert minimal[0]["candidate_id"] == "A"
        assert minimal[1]["candidate_id"] == "C"

    def test_two_per_cluster(self):
        clustered = [
            {"candidate_id": "A", "cluster_id": 0},
            {"candidate_id": "B", "cluster_id": 0},
            {"candidate_id": "C", "cluster_id": 0},
            {"candidate_id": "D", "cluster_id": 1},
        ]
        minimal = recommend_minimal_diverse_panel(clustered, n_per_cluster=2)
        ids = [c["candidate_id"] for c in minimal]
        assert ids == ["A", "B", "D"]

    def test_all_unique_clusters(self):
        clustered = [
            {"candidate_id": str(i), "cluster_id": i} for i in range(5)
        ]
        minimal = recommend_minimal_diverse_panel(clustered)
        assert len(minimal) == 5

    def test_preserves_fields(self):
        clustered = [{"candidate_id": "A", "cluster_id": 0, "ensemble": 0.9}]
        minimal = recommend_minimal_diverse_panel(clustered)
        assert minimal[0]["ensemble"] == 0.9


# ---------------------------------------------------------------------------
# diversity_stats
# ---------------------------------------------------------------------------

class TestDiversityStats:
    def test_all_unique(self):
        clustered = [{"sequence": seq, "cluster_id": i}
                     for i, seq in enumerate(["ACDEF", "KLMNO", "PQRST"])]
        stats = diversity_stats(clustered)
        assert stats["n_clusters"] == 3
        assert stats["n_redundant"] == 0
        assert stats["n_singletons"] == 3

    def test_all_same_cluster(self):
        clustered = [{"sequence": "ACDEF", "cluster_id": 0} for _ in range(3)]
        stats = diversity_stats(clustered)
        assert stats["n_clusters"] == 1
        assert stats["n_redundant"] == 3
        assert stats["largest_cluster_size"] == 3

    def test_diversity_score_range(self):
        clustered = [
            {"sequence": "AAAA", "cluster_id": 0},
            {"sequence": "BBBB", "cluster_id": 1},
        ]
        stats = diversity_stats(clustered)
        assert 0.0 <= stats["diversity_score"] <= 1.0

    def test_single_candidate(self):
        clustered = [{"sequence": "ACDEF", "cluster_id": 0}]
        stats = diversity_stats(clustered)
        assert stats["n_candidates"] == 1
        assert stats["mean_pairwise_similarity"] == 1.0


# ---------------------------------------------------------------------------
# family_structural_warnings
# ---------------------------------------------------------------------------

class TestFamilyStructuralWarnings:
    def _make_member(self, seed, trypsin_sites, mu_h, cid="X"):
        return {
            "candidate_id": cid,
            "seed": seed,
            "trypsin_sites": trypsin_sites,
            "mu_h": mu_h,
        }

    def test_trypsin_warning_fires_for_large_family(self):
        members = [
            self._make_member("SEED-005", [0, 1, 4, 5, 11], 0.70, f"V{i}")
            for i in range(3)
        ]
        warnings = family_structural_warnings(members, min_family_size=3)
        types = [w["warning_type"] for w in warnings]
        assert "TRYPSIN_STABILITY" in types

    def test_no_warning_for_small_family(self):
        members = [
            self._make_member("SEED-005", [0, 1, 4], 0.70, f"V{i}")
            for i in range(2)
        ]
        warnings = family_structural_warnings(members, min_family_size=3)
        assert len(warnings) == 0

    def test_hemolytic_warning_fires_when_all_high_mu_h(self):
        members = [
            self._make_member("SEED-005", [], 0.75, f"V{i}")
            for i in range(3)
        ]
        warnings = family_structural_warnings(members, min_family_size=3)
        types = [w["warning_type"] for w in warnings]
        assert "HEMOLYTIC_FAMILY_RISK" in types

    def test_no_hemolytic_warning_when_one_low_mu_h(self):
        members = [
            self._make_member("SEED-005", [], 0.75, "V0"),
            self._make_member("SEED-005", [], 0.80, "V1"),
            self._make_member("SEED-005", [], 0.40, "V2"),  # low μH
        ]
        warnings = family_structural_warnings(members, min_family_size=3)
        types = [w["warning_type"] for w in warnings]
        assert "HEMOLYTIC_FAMILY_RISK" not in types

    def test_warning_contains_family_name(self):
        members = [
            self._make_member("SEED-005", [0, 1, 4, 5, 11], 0.80, f"V{i}")
            for i in range(3)
        ]
        warnings = family_structural_warnings(members, min_family_size=3)
        for w in warnings:
            assert "SEED-005" in w["message"]
