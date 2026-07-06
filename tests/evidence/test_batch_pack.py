"""Tests for batch_pack.py — Phase 3 batch pack report generator.

Verifies that all four required sub-reports are produced correctly from
a ranked JSONL file:
  1. Diversity clustering
  2. Novelty
  3. Toxicity/hemolysis risk
  4. Synthesis feasibility
"""
from __future__ import annotations

import json

import pytest

from openamp_foundry.reports.batch_pack import (
    diversity_clustering_report,
    generate_batch_pack,
    novelty_report,
    scorer_consensus_report,
    synthesis_feasibility_report,
    toxicity_hemolysis_risk_report,
    write_batch_pack_markdown,
)


def _make_candidate(
    candidate_id: str,
    sequence: str,
    selected: bool = True,
    activity: float = 0.7,
    safety: float = 0.9,
    synthesis: float = 0.8,
    novelty: float = 0.2,
    boman_activity: float = 0.65,
    disagreement: float | None = None,
    nearest_reference: str | None = "SEED-001",
) -> dict:
    features = {
        "length": len(sequence),
        "hydrophobic_fraction": 0.4,
        "charge_density": 0.3,
        "cysteine_fraction": 0.0,
        "proline_fraction": 0.0,
        "longest_repeat_run": 1,
        "net_charge_proxy": 3,
        "aromatic_fraction": 0.1,
        "hydrophobic_moment": 0.3,
    }
    if disagreement is None:
        disagreement = round(abs(activity - boman_activity), 4)
    ensemble = 0.35 * activity + 0.30 * safety + 0.20 * synthesis + 0.15 * novelty
    return {
        "candidate_id": candidate_id,
        "sequence": sequence,
        "source": "test",
        "selected": selected,
        "scores": {
            "activity": activity,
            "safety": safety,
            "synthesis": synthesis,
            "novelty": novelty,
            "ensemble": ensemble,
            "boman_activity": boman_activity,
            "disagreement": disagreement,
        },
        "features": features,
        "nearest_reference": nearest_reference,
        "selection_reason": [],
        "known_failure_modes": [],
    }


SELECTED_CANDIDATES = [
    _make_candidate("CAND-001", "KWKLFKKIGAVLKVL", novelty=0.13),
    _make_candidate("CAND-002", "RRWQWRMKKLG", novelty=0.18),
    _make_candidate("CAND-003", "FLPLIGRVLSGIL", novelty=0.15),
    _make_candidate("CAND-004", "GIGKFLHSAKKFGK", novelty=0.20),
    _make_candidate("CAND-005", "KRLFKKIGSALKFL", novelty=0.09),
]

NOT_SELECTED = [
    _make_candidate("CAND-006", "KKKKKKKKKK", selected=False, safety=0.2),
    _make_candidate("CAND-007", "LLLLLLLLLLL", selected=False, safety=0.3),
]

ALL_ROWS = SELECTED_CANDIDATES + NOT_SELECTED


@pytest.fixture
def ranked_jsonl(tmp_path):
    path = tmp_path / "ranked.jsonl"
    with open(path, "w") as f:
        for row in ALL_ROWS:
            f.write(json.dumps(row) + "\n")
    return path


class TestDiversityClusteringReport:
    def test_report_type_field(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        assert report["report_type"] == "diversity_clustering"

    def test_n_selected_matches_input(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        assert report["n_selected"] == len(SELECTED_CANDIDATES)

    def test_clusters_are_non_empty(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        assert report["n_clusters"] >= 1

    def test_all_members_accounted_for(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        all_members = [m for c in report["clusters"] for m in c["members"]]
        assert len(all_members) == len(SELECTED_CANDIDATES)

    def test_singleton_fraction_between_0_and_1(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        assert 0.0 <= report["singleton_fraction"] <= 1.0

    def test_identical_sequences_cluster_together(self):
        duped = [
            _make_candidate("A", "KWKLFKKIGAVLKVL"),
            _make_candidate("B", "KWKLFKKIGAVLKVL"),
        ]
        report = diversity_clustering_report(duped, threshold=0.80)
        assert report["n_clusters"] == 1
        assert report["clusters"][0]["size"] == 2

    def test_very_different_sequences_are_singletons(self):
        diverse = [
            _make_candidate("A", "KWKLFKKIGAVLKVL"),
            _make_candidate("B", "GGGGGGGGGGGGGGGG"),
        ]
        report = diversity_clustering_report(diverse, threshold=0.80)
        assert report["n_clusters"] == 2
        assert report["n_singleton_clusters"] == 2

    def test_has_disclaimer(self):
        report = diversity_clustering_report(SELECTED_CANDIDATES)
        assert "disclaimer" in report
        assert len(report["disclaimer"]) > 10


class TestNoveltyReport:
    def test_report_type_field(self):
        report = novelty_report(SELECTED_CANDIDATES)
        assert report["report_type"] == "novelty_report"

    def test_n_selected_correct(self):
        report = novelty_report(SELECTED_CANDIDATES)
        assert report["n_selected"] == len(SELECTED_CANDIDATES)

    def test_mean_novelty_in_range(self):
        report = novelty_report(SELECTED_CANDIDATES)
        assert 0.0 <= report["mean_novelty"] <= 1.0

    def test_min_le_mean_le_max(self):
        report = novelty_report(SELECTED_CANDIDATES)
        assert report["min_novelty"] <= report["mean_novelty"] <= report["max_novelty"]

    def test_candidate_count_matches(self):
        report = novelty_report(SELECTED_CANDIDATES)
        assert len(report["candidates"]) == len(SELECTED_CANDIDATES)

    def test_candidates_sorted_by_novelty_descending(self):
        report = novelty_report(SELECTED_CANDIDATES)
        scores = [c["novelty"] for c in report["candidates"]]
        assert scores == sorted(scores, reverse=True)

    def test_low_novelty_counted_correctly(self):
        # CAND-005 has novelty=0.09 which is < 0.10
        report = novelty_report(SELECTED_CANDIDATES)
        assert report["n_low_novelty_lt_0_10"] >= 1


class TestToxicityHemolysisRiskReport:
    def test_report_type_field(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        assert report["report_type"] == "toxicity_hemolysis_risk"

    def test_n_selected_correct(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        assert report["n_selected"] == len(SELECTED_CANDIDATES)

    def test_mean_safety_in_range(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        assert 0.0 <= report["mean_safety_score"] <= 1.0

    def test_candidate_count_matches(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        assert len(report["candidates"]) == len(SELECTED_CANDIDATES)

    def test_candidates_sorted_by_safety_ascending(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        scores = [c["safety_score"] for c in report["candidates"]]
        assert scores == sorted(scores)

    def test_high_hydrophobic_flagged(self):
        risky = [_make_candidate("RISK", "LLLLLLLLLLL")]
        risky[0]["features"]["hydrophobic_fraction"] = 0.90
        report = toxicity_hemolysis_risk_report(risky)
        flags = report["candidates"][0]["risk_flags"]
        assert "high_hydrophobic_fraction" in flags

    def test_balanced_amp_has_no_risk_flags(self):
        balanced = [_make_candidate("BALANCED", "KWKLFKKIGAVLKVL")]
        report = toxicity_hemolysis_risk_report(balanced)
        assert report["candidates"][0]["risk_flags"] == []

    def test_risk_thresholds_present(self):
        report = toxicity_hemolysis_risk_report(SELECTED_CANDIDATES)
        assert "risk_thresholds" in report
        assert "hydrophobic_fraction_high" in report["risk_thresholds"]

    def test_high_charge_density_flagged(self):
        cand = [_make_candidate("HIGH-CHG", "KKKKKKKKK")]
        cand[0]["features"]["charge_density"] = 0.70
        report = toxicity_hemolysis_risk_report(cand)
        assert "high_charge_density" in report["candidates"][0]["risk_flags"]

    def test_high_cysteine_fraction_flagged(self):
        cand = [_make_candidate("HIGH-CYS", "CCCCCKKKK")]
        cand[0]["features"]["cysteine_fraction"] = 0.55
        report = toxicity_hemolysis_risk_report(cand)
        assert "high_cysteine_fraction" in report["candidates"][0]["risk_flags"]

    def test_long_repeat_run_flagged(self):
        cand = [_make_candidate("REPEAT", "KKKKKKRRL")]
        cand[0]["features"]["longest_repeat_run"] = 6
        report = toxicity_hemolysis_risk_report(cand)
        assert "long_repeat_run" in report["candidates"][0]["risk_flags"]

    def test_length_exceeds_35aa_flagged(self):
        long_seq = "KWKLFKKIGAVLKVLKWKLFKKIGAVLKVLKWKLFK"  # 36 AA (> 35 threshold)
        cand = [_make_candidate("LONG", long_seq)]
        report = toxicity_hemolysis_risk_report(cand)
        assert "length_exceeds_35aa" in report["candidates"][0]["risk_flags"]

    def test_n_with_risk_flags_counts_correctly(self):
        clean = _make_candidate("CLEAN", "KWKLFKKIGAVLKVL")
        risky = _make_candidate("RISKY", "LLLLLLLLLLL")
        risky["features"]["hydrophobic_fraction"] = 0.90
        report = toxicity_hemolysis_risk_report([clean, risky])
        assert report["n_with_risk_flags"] == 1


class TestSynthesisFeasibilityReport:
    def test_report_type_field(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        assert report["report_type"] == "synthesis_feasibility"

    def test_n_selected_correct(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        assert report["n_selected"] == len(SELECTED_CANDIDATES)

    def test_mean_synthesis_in_range(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        assert 0.0 <= report["mean_synthesis_score"] <= 1.0

    def test_counts_sum_to_n_selected(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        total = (
            report["n_high_feasibility_ge_0_80"]
            + report["n_mid_feasibility_0_50_to_0_80"]
            + report["n_low_feasibility_lt_0_50"]
        )
        assert total == len(SELECTED_CANDIDATES)

    def test_candidates_sorted_by_synthesis_ascending(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        scores = [c["synthesis_score"] for c in report["candidates"]]
        assert scores == sorted(scores)

    def test_sequence_and_length_present(self):
        report = synthesis_feasibility_report(SELECTED_CANDIDATES)
        for c in report["candidates"]:
            assert "sequence" in c
            assert "length" in c


class TestScorerConsensusReport:
    def test_report_type_field(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        assert report["report_type"] == "scorer_consensus"

    def test_n_selected_correct(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        assert report["n_selected"] == len(SELECTED_CANDIDATES)

    def test_all_candidates_included_when_boman_present(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        assert report["n_scored_with_boman"] == len(SELECTED_CANDIDATES)

    def test_empty_candidates_handled(self):
        report = scorer_consensus_report([])
        assert report["n_selected"] == 0
        assert report["n_scored_with_boman"] == 0

    def test_high_consensus_counted(self):
        # activity=0.7, boman_activity=0.7 → disagreement=0.0 → high_consensus
        candidates = [_make_candidate("C1", "KWKLFKKIGAVLKVL", activity=0.7, boman_activity=0.7)]
        report = scorer_consensus_report(candidates)
        assert report["n_high_consensus_lt_0_20"] == 1
        assert report["n_uncertain_ge_0_30"] == 0

    def test_uncertain_counted(self):
        # activity=0.9, boman_activity=0.4 → disagreement=0.5 → uncertain
        candidates = [_make_candidate("C1", "KWKLFKKIGAVLKVL", activity=0.9, boman_activity=0.4)]
        report = scorer_consensus_report(candidates)
        assert report["n_uncertain_ge_0_30"] == 1
        assert report["n_high_consensus_lt_0_20"] == 0

    def test_consensus_labels_correct(self):
        candidates = [
            _make_candidate("C1", "KWKLFKKIGAVLKVL", activity=0.7, boman_activity=0.7),
            _make_candidate("C2", "RRWQWRMKKLG", activity=0.9, boman_activity=0.4),
        ]
        report = scorer_consensus_report(candidates)
        by_id = {c["candidate_id"]: c["consensus_label"] for c in report["candidates"]}
        assert by_id["C1"] == "high_consensus"
        assert by_id["C2"] == "uncertain"

    def test_sorted_by_disagreement_ascending(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        diffs = [c["disagreement"] for c in report["candidates"]]
        assert diffs == sorted(diffs)

    def test_mean_disagreement_in_range(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        assert 0.0 <= report["mean_disagreement"] <= 1.0

    def test_has_disclaimer(self):
        report = scorer_consensus_report(SELECTED_CANDIDATES)
        assert "disclaimer" in report
        assert "lab" in report["disclaimer"].lower()

    def test_no_boman_scores_gracefully_handled(self):
        # Candidates without boman_activity should be skipped
        candidates = [
            {
                "candidate_id": "NOBOMAN",
                "sequence": "KWKLFKK",
                "scores": {"activity": 0.7, "safety": 0.9, "synthesis": 0.8, "novelty": 0.2, "ensemble": 0.75},
                "features": {},
                "selected": True,
            }
        ]
        report = scorer_consensus_report(candidates)
        assert report["n_scored_with_boman"] == 0


class TestGenerateBatchPack:
    def test_all_required_top_level_keys_present(self, ranked_jsonl):
        pack = generate_batch_pack(ranked_jsonl)
        assert "summary" in pack
        assert "diversity_clustering" in pack
        assert "novelty_report" in pack
        assert "toxicity_hemolysis_risk" in pack
        assert "synthesis_feasibility" in pack
        assert "scorer_consensus" in pack
        assert "disclaimer" in pack

    def test_summary_n_selected_matches_selected_rows(self, ranked_jsonl):
        pack = generate_batch_pack(ranked_jsonl)
        assert pack["summary"]["n_candidates_selected"] == len(SELECTED_CANDIDATES)

    def test_summary_n_scored_matches_total_rows(self, ranked_jsonl):
        pack = generate_batch_pack(ranked_jsonl)
        assert pack["summary"]["n_candidates_scored"] == len(ALL_ROWS)

    def test_non_selected_excluded_from_sub_reports(self, ranked_jsonl):
        pack = generate_batch_pack(ranked_jsonl)
        all_ids_in_novelty = {c["candidate_id"] for c in pack["novelty_report"]["candidates"]}
        assert "CAND-006" not in all_ids_in_novelty
        assert "CAND-007" not in all_ids_in_novelty

    def test_selected_ids_present_in_sub_reports(self, ranked_jsonl):
        pack = generate_batch_pack(ranked_jsonl)
        novelty_ids = {c["candidate_id"] for c in pack["novelty_report"]["candidates"]}
        assert "CAND-001" in novelty_ids
        assert "CAND-002" in novelty_ids


class TestWriteBatchPackMarkdown:
    def test_markdown_file_created(self, ranked_jsonl, tmp_path):
        pack = generate_batch_pack(ranked_jsonl)
        md_path = tmp_path / "batch_pack.md"
        write_batch_pack_markdown(pack, md_path)
        assert md_path.exists()

    def test_markdown_contains_required_sections(self, ranked_jsonl, tmp_path):
        pack = generate_batch_pack(ranked_jsonl)
        md_path = tmp_path / "batch_pack.md"
        write_batch_pack_markdown(pack, md_path)
        content = md_path.read_text()
        assert "Diversity Clustering" in content
        assert "Novelty Report" in content
        assert "Toxicity" in content
        assert "Synthesis Feasibility" in content
        assert "Scorer Consensus" in content

    def test_markdown_contains_disclaimer(self, ranked_jsonl, tmp_path):
        pack = generate_batch_pack(ranked_jsonl)
        md_path = tmp_path / "batch_pack.md"
        write_batch_pack_markdown(pack, md_path)
        content = md_path.read_text()
        assert "heuristic" in content.lower() or "disclaimer" in content.lower()

    def test_markdown_requires_human_review(self, ranked_jsonl, tmp_path):
        pack = generate_batch_pack(ranked_jsonl)
        md_path = tmp_path / "batch_pack.md"
        write_batch_pack_markdown(pack, md_path)
        content = md_path.read_text()
        assert "Human Review" in content or "human expert" in content.lower()

    def test_markdown_truncates_clusters_beyond_20(self, tmp_path):
        _CANONICAL = list("ACDEFGHIKLMNPQRSTVWY")
        rows = []
        for i, aa in enumerate(_CANONICAL):
            rows.append(_make_candidate(f"CAND-{i:03d}", aa * 10, novelty=0.5 + i * 0.001))
        rows.append(_make_candidate("CAND-020", "KWKLFKKIGAVLKVLKWKLFK", novelty=0.6))
        jsonl_path = tmp_path / "big.jsonl"
        with open(jsonl_path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        pack = generate_batch_pack(jsonl_path)
        md_path = tmp_path / "big.md"
        write_batch_pack_markdown(pack, md_path)
        content = md_path.read_text()
        assert "more clusters" in content
