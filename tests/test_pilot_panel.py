"""Tests for pilot panel selection and report formatting."""
from __future__ import annotations

import csv

import pytest

from openamp_foundry.selection.pilot import _pilot_priority, _seed_from_source, select_pilot_panel
from openamp_foundry.reports.pilot_panel import write_pilot_csv, write_pilot_markdown


def _make(
    cid: str,
    seq: str = "KWKLFKKIGAVLKVL",
    seed: str = "SEED-001",
    ensemble: float = 0.70,
    activity: float = 0.72,
    boman: float = 0.65,
    disagreement: float | None = None,
    safety: float = 0.90,
    synthesis: float = 0.80,
    novelty: float = 0.20,
) -> dict:
    if disagreement is None:
        disagreement = round(abs(activity - boman), 4)
    return {
        "candidate_id": cid,
        "sequence": seq,
        "source": f"template_mutation_from_{seed}",
        "selected": True,
        "scores": {
            "ensemble": ensemble,
            "activity": activity,
            "boman_activity": boman,
            "disagreement": disagreement,
            "safety": safety,
            "synthesis": synthesis,
            "novelty": novelty,
        },
        "features": {"length": len(seq)},
        "nearest_reference": None,
        "selection_reason": [],
        "known_failure_modes": [],
    }


FIVE_SEEDS = [
    _make("C1", seed="SEED-001", ensemble=0.80, disagreement=0.05),
    _make("C2", seed="SEED-002", ensemble=0.75, disagreement=0.10),
    _make("C3", seed="SEED-003", ensemble=0.70, disagreement=0.15),
    _make("C4", seed="SEED-004", ensemble=0.68, disagreement=0.20),
    _make("C5", seed="SEED-005", ensemble=0.65, disagreement=0.25),
]

EXTRA_SEED1 = [
    _make("C6", seed="SEED-001", ensemble=0.60, disagreement=0.05),
    _make("C7", seed="SEED-001", ensemble=0.55, disagreement=0.08),
]


class TestSeedFromSource:
    def test_standard_prefix(self):
        assert _seed_from_source("template_mutation_from_SEED-003") == "SEED-003"

    def test_no_prefix_returns_source_as_is(self):
        assert _seed_from_source("SEED-001") == "SEED-001"

    def test_empty_string(self):
        assert _seed_from_source("") == ""


class TestPilotPriority:
    def test_higher_ensemble_higher_priority(self):
        p1 = _pilot_priority({"ensemble": 0.80, "disagreement": 0.10})
        p2 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10})
        assert p1 > p2

    def test_lower_disagreement_higher_priority(self):
        p1 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.05})
        p2 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.30})
        assert p1 > p2

    def test_missing_disagreement_defaults_to_0_5(self):
        # stability defaults to 0.5 when absent; disagreement defaults to 0.5
        p = _pilot_priority({"ensemble": 0.70})
        assert p == pytest.approx(0.70 - 0.3 * 0.5 + 0.05 * 0.5, abs=1e-6)

    def test_higher_stability_higher_priority(self):
        p1 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "serum_stability": 1.0})
        p2 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "serum_stability": 0.0})
        assert p1 > p2

    def test_higher_novelty_higher_priority(self):
        p1 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "novelty": 0.467})
        p2 = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "novelty": 0.10})
        assert p1 > p2

    def test_missing_novelty_defaults_to_0(self):
        p_absent = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10})
        p_zero = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "novelty": 0.0})
        assert p_absent == pytest.approx(p_zero, abs=1e-9)

    def test_novelty_formula_contribution(self):
        # novelty bonus = 0.05 * 0.40 = 0.02; stability absent → 0.5
        p = _pilot_priority({"ensemble": 0.70, "disagreement": 0.10, "novelty": 0.40})
        expected = 0.70 - 0.3 * 0.10 + 0.05 * 0.5 + 0.05 * 0.40
        assert p == pytest.approx(expected, abs=1e-6)


class TestSelectPilotPanel:
    def test_empty_input_returns_empty(self):
        assert select_pilot_panel([]) == []

    def test_panel_size_capped_at_n(self):
        big = [_make(f"C{i}", seed=f"SEED-{i:03d}") for i in range(50)]
        panel = select_pilot_panel(big, n=20)
        assert len(panel) == 20

    def test_panel_size_when_fewer_candidates_than_n(self):
        panel = select_pilot_panel(FIVE_SEEDS, n=20)
        assert len(panel) == 5

    def test_each_seed_represented_at_most_once_in_first_pass(self):
        candidates = FIVE_SEEDS + EXTRA_SEED1
        panel = select_pilot_panel(candidates, n=5)
        seeds = [c["seed"] for c in panel]
        # Each of SEED-001..005 appears once in a 5-slot panel
        assert len(set(seeds)) == 5

    def test_extra_slots_filled_from_remainder(self):
        candidates = FIVE_SEEDS + EXTRA_SEED1
        panel = select_pilot_panel(candidates, n=7)
        assert len(panel) == 7
        # SEED-001 should appear twice (C1 and one of C6/C7)
        seed_counts = {}
        for c in panel:
            seed_counts[c["seed"]] = seed_counts.get(c["seed"], 0) + 1
        assert seed_counts["SEED-001"] == 3  # C1, C6, C7 all in when n=7

    def test_panel_sorted_by_priority_descending(self):
        candidates = FIVE_SEEDS + EXTRA_SEED1
        panel = select_pilot_panel(candidates, n=7)
        priorities = [c["pilot_priority"] for c in panel]
        assert priorities == sorted(priorities, reverse=True)

    def test_pilot_rank_assigned(self):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        ranks = [c["pilot_rank"] for c in panel]
        assert ranks == list(range(1, 6))

    def test_seed_field_added(self):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        for c in panel:
            assert "seed" in c
            assert c["seed"].startswith("SEED-")

    def test_best_per_seed_selected_first(self):
        # C1 (ensemble=0.80) should beat C6 (0.60) for SEED-001 slot
        candidates = EXTRA_SEED1 + FIVE_SEEDS  # order shouldn't matter
        panel = select_pilot_panel(candidates, n=5)
        seed1_entries = [c for c in panel if c["seed"] == "SEED-001"]
        assert len(seed1_entries) == 1
        assert seed1_entries[0]["candidate_id"] == "C1"

    def test_high_disagreement_penalised(self):
        low_disagree = _make("LOW", seed="SEED-X", ensemble=0.72, disagreement=0.02)
        high_disagree = _make("HIGH", seed="SEED-Y", ensemble=0.75, disagreement=0.50)
        panel = select_pilot_panel([low_disagree, high_disagree], n=2)
        assert panel[0]["candidate_id"] == "LOW"

    def test_n_equals_1(self):
        panel = select_pilot_panel(FIVE_SEEDS, n=1)
        assert len(panel) == 1
        assert panel[0]["pilot_rank"] == 1

    def test_max_per_seed_caps_dominant_family(self):
        # 10 SEED-001 + 3 from each of SEED-002..005 → 22 total, n=10, max=2
        # Phase 1: 5 seats (1/seed). Phase 2: 5 more, each seed has ≥2 → cap binds exactly.
        # No Phase-3 spillover needed, so cap is effective.
        many_seed1 = [_make(f"A{i}", seed="SEED-001", ensemble=0.90 - i * 0.01) for i in range(10)]
        others = [_make(f"B{s}{i}", seed=f"SEED-00{s}", ensemble=0.72 - i * 0.01)
                  for s in range(2, 6) for i in range(3)]
        panel = select_pilot_panel(many_seed1 + others, n=10, max_per_seed=2)
        seed_counts = {}
        for c in panel:
            seed_counts[c["seed"]] = seed_counts.get(c["seed"], 0) + 1
        assert seed_counts.get("SEED-001", 0) <= 2, "SEED-001 should be capped at 2"

    def test_max_per_seed_none_is_uncapped(self):
        # Without cap, the dominant family fills all remaining slots
        many_seed1 = [_make(f"A{i}", seed="SEED-001", ensemble=0.90 - i * 0.01) for i in range(10)]
        others = [_make(f"B{i}", seed=f"SEED-00{i}", ensemble=0.60) for i in range(2, 6)]
        candidates = many_seed1 + others
        panel = select_pilot_panel(candidates, n=8, max_per_seed=None)
        seed_counts = {}
        for c in panel:
            seed_counts[c["seed"]] = seed_counts.get(c["seed"], 0) + 1
        # SEED-001 fills all slots after seed guarantee (1 from each seed = 5, 3 remaining → SEED-001)
        assert seed_counts.get("SEED-001", 0) > 2

    def test_max_per_seed_preserves_total_n(self):
        many_seed1 = [_make(f"A{i}", seed="SEED-001", ensemble=0.90 - i * 0.01) for i in range(10)]
        others = [_make(f"B{s}{i}", seed=f"SEED-00{s}", ensemble=0.72 - i * 0.01)
                  for s in range(2, 6) for i in range(3)]
        panel = select_pilot_panel(many_seed1 + others, n=10, max_per_seed=2)
        assert len(panel) == 10

    def test_max_per_seed_all_seeds_represented(self):
        many_seed1 = [_make(f"A{i}", seed="SEED-001", ensemble=0.90 - i * 0.01) for i in range(10)]
        others = [_make(f"B{s}{i}", seed=f"SEED-00{s}", ensemble=0.72 - i * 0.01)
                  for s in range(2, 6) for i in range(3)]
        panel = select_pilot_panel(many_seed1 + others, n=10, max_per_seed=2)
        seeds_in_panel = {c["seed"] for c in panel}
        assert "SEED-001" in seeds_in_panel
        assert "SEED-002" in seeds_in_panel
        assert "SEED-003" in seeds_in_panel
        assert "SEED-004" in seeds_in_panel
        assert "SEED-005" in seeds_in_panel


class TestSelectPilotPanelDiversity:
    """Tests for the similarity_threshold parameter added to select_pilot_panel."""

    # Two sequences from DIFFERENT seeds that differ by 1 AA (V→I at position 14).
    # Levenshtein distance = 1, max_len = 15 → similarity = 1 - 1/15 ≈ 0.933.
    # With threshold=0.75 the lower-priority one should be filtered out.
    _HIGH_SEQ = "KWKLFKKIGAVLKVL"  # SEED-001-like
    _NEAR_DUP = "KWKLFKKIGAVLKIL"  # SEED-002-like; 1 substitution

    def _near_dup_pair(self, ensemble_high: float = 0.80, ensemble_low: float = 0.70) -> list[dict]:
        """Two candidates from different seeds with very similar sequences."""
        return [
            _make("HIGH", seq=self._HIGH_SEQ, seed="SEED-001", ensemble=ensemble_high, disagreement=0.05),
            _make("LOW",  seq=self._NEAR_DUP, seed="SEED-002", ensemble=ensemble_low,  disagreement=0.05),
        ]

    def test_no_threshold_includes_both_near_duplicates(self):
        pair = self._near_dup_pair()
        panel = select_pilot_panel(pair, n=2, similarity_threshold=None)
        ids = {c["candidate_id"] for c in panel}
        assert ids == {"HIGH", "LOW"}

    def test_strict_threshold_excludes_near_duplicate(self):
        pair = self._near_dup_pair()
        # threshold=0.75: similarity 0.933 > 0.75 → LOW excluded
        panel = select_pilot_panel(pair, n=2, similarity_threshold=0.75)
        ids = {c["candidate_id"] for c in panel}
        assert "HIGH" in ids
        assert "LOW" not in ids

    def test_high_threshold_includes_both(self):
        pair = self._near_dup_pair()
        # threshold=0.95: similarity 0.933 <= 0.95 → both included
        panel = select_pilot_panel(pair, n=2, similarity_threshold=0.95)
        ids = {c["candidate_id"] for c in panel}
        assert ids == {"HIGH", "LOW"}

    def test_higher_priority_candidate_retained(self):
        """When a near-dup pair shares a threshold, the higher-priority member is kept."""
        # HIGH (ensemble=0.80) should win over LOW (ensemble=0.70)
        pair = self._near_dup_pair(ensemble_high=0.80, ensemble_low=0.70)
        panel = select_pilot_panel(pair, n=2, similarity_threshold=0.75)
        assert len(panel) >= 1
        # The retained candidate must be the higher-priority one
        assert panel[0]["candidate_id"] == "HIGH"

    def test_fully_diverse_panel_not_affected(self):
        """Sequences from completely different families all pass even with strict threshold."""
        diverse = [
            _make("S1", seq="KWKLFKKIGAVLKVL", seed="SEED-001", ensemble=0.80),
            _make("S2", seq="GIGKFLHSAKKFGKAFVGEIMNS", seed="SEED-002", ensemble=0.75),
            _make("S3", seq="RRWQWRMKKLG",     seed="SEED-003", ensemble=0.70),
            _make("S4", seq="FLPLIGRVLSGIL",   seed="SEED-004", ensemble=0.68),
        ]
        panel = select_pilot_panel(diverse, n=4, similarity_threshold=0.75)
        assert len(panel) == 4

    def test_threshold_none_unchanged_from_no_arg(self):
        """Explicitly passing None is identical to not passing threshold at all."""
        candidates = FIVE_SEEDS + EXTRA_SEED1
        panel_default = select_pilot_panel(candidates, n=7)
        panel_none = select_pilot_panel(candidates, n=7, similarity_threshold=None)
        ids_default = [c["candidate_id"] for c in panel_default]
        ids_none = [c["candidate_id"] for c in panel_none]
        assert ids_default == ids_none

    def test_panel_rank_still_assigned_with_threshold(self):
        pair = self._near_dup_pair()
        panel = select_pilot_panel(pair, n=2, similarity_threshold=0.75)
        assert all("pilot_rank" in c for c in panel)
        ranks = [c["pilot_rank"] for c in panel]
        assert ranks == list(range(1, len(panel) + 1))

    def test_diversity_filter_respects_max_per_seed(self):
        """Diversity filter + max_per_seed both apply simultaneously."""
        # 3 SEED-001 variants + 1 near-dup from SEED-002 (similar to SEED-001's best)
        seed1_variants = [
            _make("A1", seq=self._HIGH_SEQ, seed="SEED-001", ensemble=0.85),
            _make("A2", seq="KWKLFKKIGAVLKVK", seed="SEED-001", ensemble=0.78),
        ]
        near_dup = _make("B1", seq=self._NEAR_DUP, seed="SEED-002", ensemble=0.77)
        seed3 = _make("C1", seq="GIGKFLHSAKKFGKAFVGEIMNS", seed="SEED-003", ensemble=0.70)
        candidates = seed1_variants + [near_dup, seed3]
        panel = select_pilot_panel(candidates, n=4, max_per_seed=1, similarity_threshold=0.75)
        # max_per_seed=1 ensures only 1 per seed; diversity also filters near-dup
        seed_counts = {}
        for c in panel:
            seed_counts[c["seed"]] = seed_counts.get(c["seed"], 0) + 1
        for seed, count in seed_counts.items():
            assert count <= 1, f"{seed} appeared {count} times despite max_per_seed=1"


class TestWritePilotCsv:
    def test_creates_file(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.csv"
        write_pilot_csv(panel, out)
        assert out.exists()

    def test_correct_columns(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.csv"
        write_pilot_csv(panel, out)
        with open(out, newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
        expected = {"pilot_rank", "candidate_id", "sequence", "length", "seed",
                    "ensemble", "activity", "boman_activity", "disagreement",
                    "safety", "synthesis", "novelty", "serum_stability", "pilot_priority"}
        assert set(fields) == expected

    def test_row_count_matches_panel(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.csv"
        write_pilot_csv(panel, out)
        with open(out, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 5

    def test_length_column_is_sequence_length(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.csv"
        write_pilot_csv(panel, out)
        with open(out, newline="") as f:
            for row in csv.DictReader(f):
                assert int(row["length"]) == len(row["sequence"])


class TestWritePilotMarkdown:
    def test_creates_file(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out)
        assert out.exists()

    def test_contains_disclaimer(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out)
        content = out.read_text()
        assert "Disclaimer" in content
        assert "demonstrated" in content

    def test_contains_all_candidate_ids(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out)
        content = out.read_text()
        for c in panel:
            assert c["candidate_id"] in content

    def test_contains_next_steps(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out)
        content = out.read_text()
        assert "Next steps" in content
        assert "MIC" in content

    def test_contains_reproducibility_block(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out)
        content = out.read_text()
        assert "make pilot" in content

    def test_generated_at_included_when_provided(self, tmp_path):
        panel = select_pilot_panel(FIVE_SEEDS, n=5)
        out = tmp_path / "pilot.md"
        write_pilot_markdown(panel, out, generated_at="2026-06-27T00:00:00Z")
        assert "2026-06-27" in out.read_text()
