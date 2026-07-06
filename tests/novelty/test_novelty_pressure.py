"""Novelty pressure tests — Phase 2 requirement.

AGENTS.md: "Novelty pressure — Top candidates are not merely copies of known AMP motifs."

These tests verify that:
1. Near-duplicate copies of known AMPs receive low novelty scores.
2. Genuinely novel AMP-like sequences receive high novelty scores.
3. The pipeline's min_novelty filter excludes near-duplicates from selection.
4. Top selected candidates are not merely rehashing known AMP sequences.
5. The nearest_reference metadata is populated for near-duplicate candidates.

All scores are computational proxies. No biological activity is implied.
"""
from __future__ import annotations

from pathlib import Path

from openamp_foundry.data.loaders import load_candidates_csv
from openamp_foundry.pipeline import run_ranking_pipeline, score_candidates
from openamp_foundry.scoring.novelty import normalized_similarity, novelty_score


REFS_CSV = "examples/known_reference/demo_known_amps.csv"
POOL_CSV = "examples/benchmark/novelty_pressure_pool.csv"

# NOV-DUP-* are near-duplicates of the reference AMPs
# NOV-NEW-* are genuinely novel AMP-like sequences
# NOV-NEG-* are non-AMP negatives
DUP_IDS = {"NOV-DUP-001", "NOV-DUP-002", "NOV-DUP-003"}
NOVEL_IDS = {"NOV-NEW-001", "NOV-NEW-002", "NOV-NEW-003"}


class TestNoveltyScoringMechanism:
    def test_exact_reference_copy_has_zero_novelty(self):
        """Sequence identical to a reference should receive novelty = 0.0."""
        refs = load_candidates_csv(REFS_CSV)
        # REF-000001 = KWKLFKKIGAVLKVL
        score, nearest = novelty_score("KWKLFKKIGAVLKVL", refs)
        assert score == 0.0, f"Exact reference copy should have novelty=0.0, got {score}"
        assert nearest is not None
        assert nearest["similarity"] == 1.0

    def test_near_duplicate_has_low_novelty(self):
        """Sequence differing by 1 AA from reference should have low novelty."""
        refs = load_candidates_csv(REFS_CSV)
        # KWKLFKKIGAVLKFL = KWKLFKKIGAVLKVL with L→F at position 14 (1/15 edit)
        score, nearest = novelty_score("KWKLFKKIGAVLKFL", refs)
        assert score < 0.20, (
            f"Near-duplicate (1 substitution) should have novelty < 0.20, got {score}. "
            f"Similarity to nearest ref: {nearest['similarity'] if nearest else 'N/A'}"
        )
        assert nearest is not None, "Nearest reference should be populated for near-dups"

    def test_novel_sequence_has_high_novelty(self):
        """Genuinely novel AMP-like sequence should have high novelty."""
        refs = load_candidates_csv(REFS_CSV)
        # RRLKKVLGAVLKVLK — cationic + hydrophobic, but NOT similar to known refs
        score, nearest = novelty_score("RRLKKVLGAVLKVLK", refs)
        assert score >= 0.20, (
            f"Novel sequence should have novelty >= 0.20, got {score}. "
            "This sequence should be structurally distinct from known references."
        )

    def test_novelty_decreases_with_similarity(self):
        """More similar to references → lower novelty."""
        refs = load_candidates_csv(REFS_CSV)
        # Reference exact = min novelty
        exact_score, _ = novelty_score("KWKLFKKIGAVLKVL", refs)
        # 1-substitution near-dup
        near_dup_score, _ = novelty_score("KWKLFKKIGAVLKFL", refs)
        # Novel sequence
        novel_score, _ = novelty_score("RRLKKVLGAVLKVLK", refs)
        assert exact_score < near_dup_score < novel_score, (
            f"Novelty should increase with decreasing similarity to references: "
            f"exact={exact_score}, near_dup={near_dup_score}, novel={novel_score}"
        )

    def test_nearest_reference_field_populated_for_near_dups(self):
        """Pipeline should populate nearest_reference for near-duplicate candidates."""
        scored, _ = score_candidates(POOL_CSV, REFS_CSV)
        dup_candidates = [s for s in scored if s.candidate.candidate_id in DUP_IDS]
        for item in dup_candidates:
            assert item.nearest_reference is not None, (
                f"{item.candidate.candidate_id}: nearest_reference should not be None "
                "for near-duplicate candidates"
            )
            assert "similarity" in item.nearest_reference
            assert "candidate_id" in item.nearest_reference

    def test_near_dup_novelty_score_below_min_novelty_threshold(self):
        """Near-duplicates of references should fall below the pipeline min_novelty=0.20."""
        scored, _ = score_candidates(POOL_CSV, REFS_CSV)
        # NOV-DUP-001 is identical to REF-000001 → novelty = 0.0
        dup001 = next(s for s in scored if s.candidate.candidate_id == "NOV-DUP-001")
        assert dup001.scores["novelty"] < 0.20, (
            f"NOV-DUP-001 (exact reference copy) should have novelty < 0.20, "
            f"got {dup001.scores['novelty']}"
        )


class TestNoveltyScoringInPipeline:
    def test_dup_ids_have_lower_novelty_than_novel_ids(self):
        """Near-duplicate candidates score lower on novelty than genuinely novel ones."""
        scored, _ = score_candidates(POOL_CSV, REFS_CSV)

        dup_novelties = [
            s.scores["novelty"]
            for s in scored
            if s.candidate.candidate_id in DUP_IDS
        ]
        novel_novelties = [
            s.scores["novelty"]
            for s in scored
            if s.candidate.candidate_id in NOVEL_IDS
        ]

        avg_dup = sum(dup_novelties) / len(dup_novelties)
        avg_novel = sum(novel_novelties) / len(novel_novelties)

        assert avg_novel > avg_dup, (
            f"Average novelty of genuine novel AMPs ({avg_novel:.3f}) should exceed "
            f"average novelty of near-duplicates ({avg_dup:.3f})"
        )

    def test_selected_candidates_pass_novelty_threshold(self, tmp_path):
        """All pipeline-selected candidates should meet the min_novelty=0.20 threshold."""
        out = tmp_path / "ranked.jsonl"
        run_ranking_pipeline(
            candidate_path=POOL_CSV,
            reference_path=REFS_CSV,
            out_path=out,
        )
        import json
        rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
        selected = [r for r in rows if r["selected"]]
        for row in selected:
            assert row["scores"]["novelty"] >= 0.20, (
                f"{row['candidate_id']}: selected candidate has novelty "
                f"{row['scores']['novelty']:.4f} < 0.20 minimum"
            )

    def test_exact_reference_copies_not_selected(self, tmp_path):
        """Exact copies of reference AMPs should not appear in the selected batch."""
        out = tmp_path / "ranked.jsonl"
        run_ranking_pipeline(
            candidate_path=POOL_CSV,
            reference_path=REFS_CSV,
            out_path=out,
        )
        import json
        rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
        selected_ids = {r["candidate_id"] for r in rows if r["selected"]}
        assert "NOV-DUP-001" not in selected_ids, (
            "NOV-DUP-001 (exact copy of KWKLFKKIGAVLKVL) should not be in selected batch"
        )

    def test_novel_amp_candidates_preferentially_selected(self, tmp_path):
        """Novel AMP-like candidates should be preferentially selected over near-duplicates."""
        out = tmp_path / "ranked.jsonl"
        run_ranking_pipeline(
            candidate_path=POOL_CSV,
            reference_path=REFS_CSV,
            out_path=out,
        )
        import json
        rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
        selected_ids = {r["candidate_id"] for r in rows if r["selected"]}

        novel_selected = len(NOVEL_IDS & selected_ids)
        dup_selected = len(DUP_IDS & selected_ids)
        assert novel_selected >= dup_selected, (
            f"Novel AMP candidates selected ({novel_selected}) should be ≥ "
            f"near-duplicate candidates selected ({dup_selected}). "
            "Novelty pressure should favor genuinely novel sequences."
        )

    def test_top_ranked_candidates_not_all_near_dups(self):
        """Top-scored candidates by ensemble should not be dominated by reference copies."""
        scored, _ = score_candidates(POOL_CSV, REFS_CSV)
        from openamp_foundry.selection.pareto import rank_candidates
        ranked = rank_candidates(scored)

        top5_ids = {s.candidate.candidate_id for s in ranked[:5]}
        dups_in_top5 = len(DUP_IDS & top5_ids)
        # Even if near-dups have high activity, novelty penalty should limit their presence
        assert dups_in_top5 < len(DUP_IDS), (
            f"All {len(DUP_IDS)} near-duplicate candidates are in the top-5. "
            "Novelty weighting should reduce ranking of reference copies."
        )

    def test_data_integrity_pool_has_expected_ids(self):
        """Verify the novelty pressure pool file has expected structure."""
        assert Path(POOL_CSV).exists(), "Novelty pressure pool CSV not found"
        pool = load_candidates_csv(POOL_CSV)
        ids = {c.candidate_id for c in pool}
        assert DUP_IDS.issubset(ids), f"Missing DUP IDs: {DUP_IDS - ids}"
        assert NOVEL_IDS.issubset(ids), f"Missing NOVEL IDs: {NOVEL_IDS - ids}"

    def test_normalized_similarity_between_dups_and_refs_above_threshold(self):
        """Verify near-dups are above 70% similarity to references (confirming they ARE near-dups)."""
        refs = load_candidates_csv(REFS_CSV)
        ref_seqs = [r.sequence for r in refs]
        # NOV-DUP-001 is KWKLFKKIGAVLKVL = identical to REF-000001
        # NOV-DUP-002 is KWKLFKKIGAVLKFL = 1 edit from REF-000001
        for dup_seq in ["KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKFL", "KWKLFKRIGAVLKVL"]:
            max_sim = max(normalized_similarity(dup_seq, rseq) for rseq in ref_seqs)
            assert max_sim >= 0.70, (
                f"Sequence {dup_seq!r} should have ≥70% similarity to at least one reference "
                f"(got max_sim={max_sim:.4f})"
            )
