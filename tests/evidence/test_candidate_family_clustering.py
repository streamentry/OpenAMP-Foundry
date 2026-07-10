import pytest
from src.openamp_foundry.evidence.candidate_family_clustering import (
    VALID_NOVELTY_EVIDENCE_TYPES,
    VALID_CLUSTERING_METHODS,
    VALID_NOVELTY_VERDICTS,
    MIN_FAMILY_SIZE,
    CandidateFamilyClustering,
    CFCValidationResult,
    validate_candidate_family_clustering,
    build_candidate_family_clustering,
    format_candidate_family_clustering,
)


def _valid_cfc(**kwargs):
    defaults = dict(
        cfc_id="CFC-0001",
        family_name="Alpha-Helix Family 1",
        candidate_ids=["AMPF-0001", "AMPF-0002", "AMPF-0003"],
        clustering_method="sequence_identity",
        similarity_threshold=0.70,
        novelty_evidence_types=["blast_search_no_hits"],
        novelty_verdict="novel_family",
        n_candidates=3,
        n_toy_excluded=0,
        known_family_hits=[],
        dry_lab_only=True,
        limitations="Single clustering method; structural clustering not performed.",
        notes="",
        min_pairwise_similarity=0.65,
        max_pairwise_similarity=0.82,
    )
    defaults.update(kwargs)
    return CandidateFamilyClustering(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_novelty_evidence_types_is_frozenset(self):
        assert isinstance(VALID_NOVELTY_EVIDENCE_TYPES, frozenset)

    def test_novelty_evidence_types_count(self):
        assert len(VALID_NOVELTY_EVIDENCE_TYPES) == 6

    def test_blast_search_no_hits_in_evidence_types(self):
        assert "blast_search_no_hits" in VALID_NOVELTY_EVIDENCE_TYPES

    def test_hmm_profile_no_match_in_evidence_types(self):
        assert "hmm_profile_no_match" in VALID_NOVELTY_EVIDENCE_TYPES

    def test_insufficient_evidence_in_evidence_types(self):
        assert "insufficient_evidence" in VALID_NOVELTY_EVIDENCE_TYPES

    def test_clustering_methods_is_frozenset(self):
        assert isinstance(VALID_CLUSTERING_METHODS, frozenset)

    def test_clustering_methods_count(self):
        assert len(VALID_CLUSTERING_METHODS) == 5

    def test_sequence_identity_in_clustering_methods(self):
        assert "sequence_identity" in VALID_CLUSTERING_METHODS

    def test_embedding_distance_in_clustering_methods(self):
        assert "embedding_distance" in VALID_CLUSTERING_METHODS

    def test_novelty_verdicts_is_frozenset(self):
        assert isinstance(VALID_NOVELTY_VERDICTS, frozenset)

    def test_novelty_verdicts_count(self):
        assert len(VALID_NOVELTY_VERDICTS) == 4

    def test_novel_family_in_verdicts(self):
        assert "novel_family" in VALID_NOVELTY_VERDICTS

    def test_variant_of_known_in_verdicts(self):
        assert "variant_of_known" in VALID_NOVELTY_VERDICTS

    def test_min_family_size_is_2(self):
        assert MIN_FAMILY_SIZE == 2


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestCandidateFamilyClusteringDataclass:
    def test_instantiation(self):
        c = _valid_cfc()
        assert c.cfc_id == "CFC-0001"

    def test_dry_lab_only_true(self):
        c = _valid_cfc()
        assert c.dry_lab_only is True

    def test_candidate_ids_list(self):
        c = _valid_cfc()
        assert len(c.candidate_ids) == 3

    def test_notes_default_empty(self):
        c = _valid_cfc(notes="")
        assert c.notes == ""

    def test_optional_pairwise_similarity(self):
        c = _valid_cfc(min_pairwise_similarity=None, max_pairwise_similarity=None)
        assert c.min_pairwise_similarity is None

    def test_known_family_hits_empty(self):
        c = _valid_cfc()
        assert c.known_family_hits == []


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateCandidateFamilyClustering:
    def test_valid_cfc_passes(self):
        c = _valid_cfc()
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_invalid_cfc_id_prefix(self):
        c = _valid_cfc(cfc_id="BAD-0001")
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("cfc_id" in v for v in result.violations)

    def test_short_family_name_blocked(self):
        c = _valid_cfc(family_name="AB")
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_empty_candidate_ids_blocked(self):
        c = _valid_cfc(candidate_ids=[], n_candidates=0)
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_toy_candidate_id_blocked(self):
        c = _valid_cfc(candidate_ids=["TOY-0001", "AMPF-0002", "AMPF-0003"])
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_invalid_clustering_method_blocked(self):
        c = _valid_cfc(clustering_method="magic_clustering")
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_similarity_threshold_above_1_blocked(self):
        c = _valid_cfc(similarity_threshold=1.1)
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_similarity_threshold_negative_blocked(self):
        c = _valid_cfc(similarity_threshold=-0.1)
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_invalid_novelty_evidence_type_blocked(self):
        c = _valid_cfc(novelty_evidence_types=["magic_evidence"])
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_empty_novelty_evidence_types_blocked(self):
        c = _valid_cfc(novelty_evidence_types=[])
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_invalid_novelty_verdict_blocked(self):
        c = _valid_cfc(novelty_verdict="probably_novel")
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_n_candidates_below_min_blocked(self):
        c = _valid_cfc(candidate_ids=["AMPF-0001"], n_candidates=1)
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("n_candidates" in v for v in result.violations)

    def test_n_candidates_mismatch_blocked(self):
        c = _valid_cfc(n_candidates=5)
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("n_candidates" in v for v in result.violations)

    def test_n_toy_excluded_negative_blocked(self):
        c = _valid_cfc(n_toy_excluded=-1)
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_novel_family_requires_hard_evidence(self):
        c = _valid_cfc(novelty_verdict="novel_family", novelty_evidence_types=["expert_assessment"])
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("hard evidence" in v for v in result.violations)

    def test_variant_of_known_requires_known_hits(self):
        c = _valid_cfc(novelty_verdict="variant_of_known", known_family_hits=[])
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("known_family_hits" in v for v in result.violations)

    def test_dry_lab_only_false_blocked(self):
        c = _valid_cfc(dry_lab_only=False)
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_limitations_blocked(self):
        c = _valid_cfc(limitations="")
        result = validate_candidate_family_clustering(c)
        assert not result.valid

    def test_min_pairwise_above_max_blocked(self):
        c = _valid_cfc(min_pairwise_similarity=0.9, max_pairwise_similarity=0.5)
        result = validate_candidate_family_clustering(c)
        assert not result.valid
        assert any("min_pairwise_similarity" in v for v in result.violations)

    def test_variant_of_known_with_hits_valid(self):
        c = _valid_cfc(
            novelty_verdict="variant_of_known",
            novelty_evidence_types=["blast_search_no_hits"],
            known_family_hits=["defensin_family_1"],
        )
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_insufficient_evidence_verdict_valid(self):
        c = _valid_cfc(
            novelty_verdict="insufficient_evidence",
            novelty_evidence_types=["insufficient_evidence"],
        )
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_multiple_novelty_evidence_types_valid(self):
        c = _valid_cfc(novelty_evidence_types=["blast_search_no_hits", "hmm_profile_no_match"])
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_similarity_threshold_boundary_0(self):
        c = _valid_cfc(similarity_threshold=0.0)
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_similarity_threshold_boundary_1(self):
        c = _valid_cfc(similarity_threshold=1.0)
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_no_pairwise_similarity_valid(self):
        c = _valid_cfc(min_pairwise_similarity=None, max_pairwise_similarity=None)
        result = validate_candidate_family_clustering(c)
        assert result.valid

    def test_large_family_valid(self):
        ids = [f"AMPF-{i:04d}" for i in range(1, 21)]
        c = _valid_cfc(candidate_ids=ids, n_candidates=20)
        result = validate_candidate_family_clustering(c)
        assert result.valid


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildCandidateFamilyClustering:
    def test_build_valid(self):
        c = build_candidate_family_clustering(
            cfc_id="CFC-0001",
            family_name="Alpha-Helix Family 1",
            candidate_ids=["AMPF-0001", "AMPF-0002", "AMPF-0003"],
            clustering_method="sequence_identity",
            similarity_threshold=0.70,
            novelty_evidence_types=["blast_search_no_hits"],
            novelty_verdict="novel_family",
            n_toy_excluded=0,
            known_family_hits=[],
            limitations="Single clustering method; structural clustering not performed.",
        )
        assert c.cfc_id == "CFC-0001"
        assert c.dry_lab_only is True
        assert c.n_candidates == 3

    def test_build_sets_n_candidates_from_ids(self):
        c = build_candidate_family_clustering(
            cfc_id="CFC-0002",
            family_name="Beta-Sheet Cluster",
            candidate_ids=["AMPF-0010", "AMPF-0011"],
            clustering_method="kmer_similarity",
            similarity_threshold=0.80,
            novelty_evidence_types=["hmm_profile_no_match"],
            novelty_verdict="novel_family",
            n_toy_excluded=2,
            known_family_hits=[],
            limitations="Limited to gram-positive bacteria; not tested on gram-negative.",
        )
        assert c.n_candidates == 2

    def test_build_enforces_dry_lab_only_true(self):
        c = build_candidate_family_clustering(
            cfc_id="CFC-0003",
            family_name="Test Family XYZ",
            candidate_ids=["AMPF-0020", "AMPF-0021"],
            clustering_method="edit_distance",
            similarity_threshold=0.60,
            novelty_evidence_types=["structural_divergence"],
            novelty_verdict="novel_family",
            n_toy_excluded=0,
            known_family_hits=[],
            limitations="Structural prediction only; not experimentally validated.",
        )
        assert c.dry_lab_only is True

    def test_build_raises_on_toy_id(self):
        with pytest.raises(ValueError):
            build_candidate_family_clustering(
                cfc_id="CFC-0004",
                family_name="Toy Family",
                candidate_ids=["TOY-0001", "TOY-0002"],
                clustering_method="sequence_identity",
                similarity_threshold=0.70,
                novelty_evidence_types=["blast_search_no_hits"],
                novelty_verdict="novel_family",
                n_toy_excluded=0,
                known_family_hits=[],
                limitations="This should fail because TOY- IDs are used.",
            )

    def test_build_raises_on_no_hard_evidence(self):
        with pytest.raises(ValueError):
            build_candidate_family_clustering(
                cfc_id="CFC-0005",
                family_name="Alleged Novel Family",
                candidate_ids=["AMPF-0050", "AMPF-0051"],
                clustering_method="manual_grouping",
                similarity_threshold=0.50,
                novelty_evidence_types=["expert_assessment"],
                novelty_verdict="novel_family",
                n_toy_excluded=0,
                known_family_hits=[],
                limitations="Expert opinion only; no database searches performed.",
            )

    def test_build_variant_of_known(self):
        c = build_candidate_family_clustering(
            cfc_id="CFC-0006",
            family_name="Defensin Variant Cluster",
            candidate_ids=["AMPF-0060", "AMPF-0061", "AMPF-0062"],
            clustering_method="sequence_identity",
            similarity_threshold=0.65,
            novelty_evidence_types=["blast_search_no_hits"],
            novelty_verdict="variant_of_known",
            n_toy_excluded=1,
            known_family_hits=["alpha_defensin_family"],
            limitations="BLAST search only; HMM not performed.",
        )
        assert c.novelty_verdict == "variant_of_known"
        assert "alpha_defensin_family" in c.known_family_hits


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatCandidateFamilyClustering:
    def _build(self, **kwargs):
        defaults = dict(
            cfc_id="CFC-0001",
            family_name="Alpha-Helix Family 1",
            candidate_ids=["AMPF-0001", "AMPF-0002", "AMPF-0003"],
            clustering_method="sequence_identity",
            similarity_threshold=0.70,
            novelty_evidence_types=["blast_search_no_hits"],
            novelty_verdict="novel_family",
            n_toy_excluded=0,
            known_family_hits=[],
            limitations="Single clustering method; structural clustering not performed.",
        )
        defaults.update(kwargs)
        return build_candidate_family_clustering(**defaults)

    def test_format_returns_string(self):
        c = self._build()
        assert isinstance(format_candidate_family_clustering(c), str)

    def test_format_contains_cfc_id(self):
        c = self._build()
        assert "CFC-0001" in format_candidate_family_clustering(c)

    def test_format_contains_family_name(self):
        c = self._build()
        assert "Alpha-Helix Family 1" in format_candidate_family_clustering(c)

    def test_format_contains_novelty_verdict(self):
        c = self._build()
        assert "novel_family" in format_candidate_family_clustering(c)

    def test_format_contains_clustering_method(self):
        c = self._build()
        assert "sequence_identity" in format_candidate_family_clustering(c)

    def test_format_contains_similarity_threshold(self):
        c = self._build()
        assert "0.700" in format_candidate_family_clustering(c)

    def test_format_contains_candidate_count(self):
        c = self._build()
        assert "3" in format_candidate_family_clustering(c)

    def test_format_contains_novelty_evidence(self):
        c = self._build()
        assert "blast_search_no_hits" in format_candidate_family_clustering(c)

    def test_format_contains_dry_lab_only_true(self):
        c = self._build()
        assert "dry_lab_only: True" in format_candidate_family_clustering(c)

    def test_format_contains_limitations(self):
        c = self._build()
        assert "Single clustering method" in format_candidate_family_clustering(c)

    def test_format_contains_pairwise_range(self):
        c = self._build(min_pairwise_similarity=0.65, max_pairwise_similarity=0.82)
        assert "0.650" in format_candidate_family_clustering(c)
        assert "0.820" in format_candidate_family_clustering(c)

    def test_format_contains_known_hits(self):
        c = self._build(
            novelty_verdict="variant_of_known",
            known_family_hits=["defensin_family_1"],
        )
        assert "defensin_family_1" in format_candidate_family_clustering(c)

    def test_format_multiline(self):
        c = self._build()
        lines = format_candidate_family_clustering(c).split("\n")
        assert len(lines) >= 7

    def test_format_truncates_long_candidate_list(self):
        ids = [f"AMPF-{i:04d}" for i in range(1, 11)]
        c = self._build(candidate_ids=ids)
        out = format_candidate_family_clustering(c)
        assert "..." in out
