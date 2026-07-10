"""Tests for similarity_neighbor_report module (C4)."""
import pytest
from openamp_foundry.evidence.similarity_neighbor_report import (
    SimilarityNeighborReport,
    SIMILARITY_SHORTCUT_THRESHOLD,
    SHORTCUT_FRACTION_THRESHOLD,
    _sequence_similarity,
    _nearest_neighbor_similarity,
    _mean,
    _median,
    _high_similarity_fraction,
    compute_similarity_report,
    format_similarity_report,
)


# --- _sequence_similarity ---

class TestSequenceSimilarity:
    def test_identical_sequences(self):
        assert _sequence_similarity("AAKK", "AAKK") == 1.0

    def test_no_overlap(self):
        assert _sequence_similarity("AAAA", "KKKK") == 0.0

    def test_half_overlap(self):
        result = _sequence_similarity("AAKK", "AALL")
        assert result == pytest.approx(0.5)

    def test_empty_query(self):
        assert _sequence_similarity("", "AAKK") == 0.0

    def test_empty_reference(self):
        assert _sequence_similarity("AAKK", "") == 0.0

    def test_both_empty(self):
        assert _sequence_similarity("", "") == 0.0

    def test_different_lengths_shorter_query(self):
        # "AA" vs "AAKK": 2 matches, max_len=4 -> 0.5
        result = _sequence_similarity("AA", "AAKK")
        assert result == pytest.approx(0.5)

    def test_different_lengths_longer_query(self):
        result = _sequence_similarity("AAKK", "AA")
        assert result == pytest.approx(0.5)

    def test_single_char_match(self):
        assert _sequence_similarity("A", "A") == pytest.approx(1.0)

    def test_single_char_no_match(self):
        assert _sequence_similarity("A", "K") == pytest.approx(0.0)

    def test_partial_overlap_long(self):
        # AAAAAAKKKK vs AAAAAALLLL: 6 matches, max_len=10 -> 0.6
        result = _sequence_similarity("AAAAAAKKKK", "AAAAAALLLL")
        assert result == pytest.approx(0.6)


# --- _nearest_neighbor_similarity ---

class TestNearestNeighborSimilarity:
    def test_no_references(self):
        assert _nearest_neighbor_similarity("AAKK", []) == 0.0

    def test_single_identical_reference(self):
        assert _nearest_neighbor_similarity("AAKK", ["AAKK"]) == pytest.approx(1.0)

    def test_picks_best_reference(self):
        # "AAKK" vs ["LLLL", "AAKK", "KKLL"] -> max is 1.0
        assert _nearest_neighbor_similarity("AAKK", ["LLLL", "AAKK", "KKLL"]) == pytest.approx(1.0)

    def test_all_zero_references(self):
        assert _nearest_neighbor_similarity("AAAA", ["KKKK", "LLLL"]) == pytest.approx(0.0)

    def test_partial_match(self):
        result = _nearest_neighbor_similarity("AAKK", ["AALL"])
        assert result == pytest.approx(0.5)

    def test_multiple_references_partial(self):
        result = _nearest_neighbor_similarity("AAKK", ["AALL", "AAKL"])
        # AAKL has 3 matches out of 4 -> 0.75; AALL has 2/4 -> 0.5
        assert result == pytest.approx(0.75)


# --- _mean ---

class TestMean:
    def test_empty(self):
        assert _mean([]) == pytest.approx(0.0)

    def test_single(self):
        assert _mean([0.5]) == pytest.approx(0.5)

    def test_multiple(self):
        assert _mean([0.0, 0.5, 1.0]) == pytest.approx(0.5)

    def test_all_same(self):
        assert _mean([0.3, 0.3, 0.3]) == pytest.approx(0.3)


# --- _median ---

class TestMedian:
    def test_empty(self):
        assert _median([]) == pytest.approx(0.0)

    def test_single(self):
        assert _median([0.7]) == pytest.approx(0.7)

    def test_odd_count(self):
        assert _median([0.1, 0.5, 0.9]) == pytest.approx(0.5)

    def test_even_count(self):
        assert _median([0.2, 0.4, 0.6, 0.8]) == pytest.approx(0.5)

    def test_unsorted_input(self):
        assert _median([0.9, 0.1, 0.5]) == pytest.approx(0.5)


# --- _high_similarity_fraction ---

class TestHighSimilarityFraction:
    def test_empty(self):
        assert _high_similarity_fraction([], 0.8) == pytest.approx(0.0)

    def test_none_above_threshold(self):
        assert _high_similarity_fraction([0.1, 0.2, 0.3], 0.8) == pytest.approx(0.0)

    def test_all_above_threshold(self):
        assert _high_similarity_fraction([0.9, 0.95, 1.0], 0.8) == pytest.approx(1.0)

    def test_half_above_threshold(self):
        assert _high_similarity_fraction([0.5, 0.9, 0.3, 0.85], 0.8) == pytest.approx(0.5)

    def test_exactly_at_threshold_counts(self):
        assert _high_similarity_fraction([0.8], 0.8) == pytest.approx(1.0)

    def test_just_below_threshold_does_not_count(self):
        assert _high_similarity_fraction([0.799], 0.8) == pytest.approx(0.0)


# --- compute_similarity_report ---

class TestComputeSimilarityReport:
    def test_basic_no_shortcut(self):
        sequences = ["AAAA", "KKKK", "LLLL", "FFFF"]
        labels = [1, 1, 0, 0]
        references = ["MMMM", "GGGG"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.n_positives == 2
        assert report.n_negatives == 2
        assert report.n_references == 2
        assert report.novelty_shortcut_likely is False

    def test_shortcut_detected(self):
        # Positives are nearly identical to references
        sequences = ["AAKK", "AAKL", "LLLL", "MMMM"]
        labels = [1, 1, 0, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references, similarity_threshold=0.5)
        # AAKK->AAKK = 1.0, AAKL->AAKK = 0.75; both >= 0.5 -> fraction=1.0 >= 0.5 threshold
        assert report.novelty_shortcut_likely is True
        assert report.positive_high_similarity_fraction == pytest.approx(1.0)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            compute_similarity_report(["AAKK", "LLLL"], [1], [])

    def test_empty_sequences(self):
        report = compute_similarity_report([], [], ["AAKK"])
        assert report.n_positives == 0
        assert report.n_negatives == 0
        assert report.novelty_shortcut_likely is False

    def test_no_references(self):
        sequences = ["AAKK", "LLLL"]
        labels = [1, 0]
        report = compute_similarity_report(sequences, labels, [])
        assert report.n_references == 0
        assert report.positive_mean_nn == pytest.approx(0.0)
        assert report.negative_mean_nn == pytest.approx(0.0)
        assert report.novelty_shortcut_likely is False

    def test_all_positives(self):
        sequences = ["AAKK", "RRLL"]
        labels = [1, 1]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.n_negatives == 0
        assert report.n_positives == 2
        assert report.negative_mean_nn == pytest.approx(0.0)

    def test_all_negatives(self):
        sequences = ["AAKK", "RRLL"]
        labels = [0, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.n_positives == 0
        assert report.n_negatives == 2
        assert report.positive_mean_nn == pytest.approx(0.0)

    def test_positive_mean_nn_correct(self):
        # AAKK->AAKK=1.0, KKKK->AAKK: 1 match of 4 -> 0.25
        sequences = ["AAKK", "KKKK", "LLLL"]
        labels = [1, 1, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.positive_mean_nn == pytest.approx(0.625)  # (1.0 + 0.25) / 2

    def test_negative_mean_nn_correct(self):
        sequences = ["LLLL", "MMMM"]
        labels = [0, 0]
        references = ["LLLL"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.negative_mean_nn == pytest.approx(0.5)  # (1.0 + 0.0) / 2

    def test_positive_median_nn_correct(self):
        sequences = ["AAKK", "AAAA", "KKKK"]
        labels = [1, 1, 1]
        references = ["AAKK"]
        # AAKK->AAKK=1.0, AAAA->AAKK=0.5, KKKK->AAKK=0.25
        report = compute_similarity_report(sequences, labels, references)
        assert report.positive_median_nn == pytest.approx(0.5)

    def test_shortcut_explanation_contains_fraction(self):
        sequences = ["AAKK", "AAKL", "LLLL", "MMMM"]
        labels = [1, 1, 0, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references, similarity_threshold=0.5)
        assert "100.0%" in report.shortcut_explanation or "100%" in report.shortcut_explanation

    def test_no_shortcut_explanation_format(self):
        sequences = ["AAAA", "KKKK", "LLLL"]
        labels = [1, 0, 0]
        references = ["MMMM"]
        report = compute_similarity_report(sequences, labels, references)
        assert "No novelty shortcut detected" in report.shortcut_explanation

    def test_custom_thresholds_respected(self):
        sequences = ["AAKK", "LLLL"]
        labels = [1, 0]
        references = ["AAKK"]
        # threshold=0.0 means everything is high-similarity
        report = compute_similarity_report(sequences, labels, references, similarity_threshold=0.0, shortcut_fraction_threshold=0.5)
        assert report.positive_high_similarity_fraction == pytest.approx(1.0)
        assert report.novelty_shortcut_likely is True

    def test_threshold_stored_in_report(self):
        sequences = ["AAKK"]
        labels = [1]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references, similarity_threshold=0.9)
        assert report.similarity_threshold_used == pytest.approx(0.9)

    def test_shortcut_fraction_threshold_stored(self):
        sequences = ["AAKK"]
        labels = [1]
        references = []
        report = compute_similarity_report(sequences, labels, references, shortcut_fraction_threshold=0.3)
        assert report.shortcut_fraction_threshold == pytest.approx(0.3)

    def test_report_is_dataclass(self):
        report = compute_similarity_report([], [], [])
        assert isinstance(report, SimilarityNeighborReport)

    def test_positive_nn_similarities_list(self):
        sequences = ["AAKK", "LLLL"]
        labels = [1, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert len(report.positive_nn_similarities) == 1
        assert report.positive_nn_similarities[0] == pytest.approx(1.0)

    def test_negative_nn_similarities_list(self):
        sequences = ["AAKK", "LLLL"]
        labels = [1, 0]
        references = ["AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert len(report.negative_nn_similarities) == 1
        # LLLL vs AAKK: 0 matches / 4 -> 0.0
        assert report.negative_nn_similarities[0] == pytest.approx(0.0)

    def test_multiple_references_uses_best(self):
        sequences = ["AAKK"]
        labels = [1]
        references = ["AAAA", "AAKK"]
        report = compute_similarity_report(sequences, labels, references)
        assert report.positive_nn_similarities[0] == pytest.approx(1.0)

    def test_symmetric_sequences(self):
        sequences = ["KKAAKK", "AAKKAA"]
        labels = [1, 0]
        references = ["KKAAKK"]
        report = compute_similarity_report(sequences, labels, references)
        # First seq exact match -> 1.0; second: AAKKAA vs KKAAKK = 2 matches / 6 -> 0.333
        assert report.positive_nn_similarities[0] == pytest.approx(1.0)
        assert report.negative_nn_similarities[0] == pytest.approx(2 / 6)

    def test_large_reference_set(self):
        references = [f"{'A' * i}{'K' * (20 - i)}" for i in range(21)]
        sequences = ["AAAAAAAAAAKKKKKKKKKKK"[:20], "KKKKKKKKKK"]
        labels = [1, 0]
        report = compute_similarity_report(sequences, labels, references)
        assert report.n_references == 21

    def test_default_threshold_constants(self):
        assert SIMILARITY_SHORTCUT_THRESHOLD == 0.80
        assert SHORTCUT_FRACTION_THRESHOLD == 0.50


# --- format_similarity_report ---

class TestFormatSimilarityReport:
    def _basic_report(self) -> SimilarityNeighborReport:
        return compute_similarity_report(
            ["AAKK", "RRLL", "LLLL", "MMMM"],
            [1, 1, 0, 0],
            ["AAKK"],
        )

    def test_returns_string(self):
        report = self._basic_report()
        assert isinstance(format_similarity_report(report), str)

    def test_contains_header(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "SIMILARITY-NEIGHBOR DISTRIBUTION REPORT" in text

    def test_contains_positive_count(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "2 positives" in text

    def test_contains_negative_count(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "2 negatives" in text

    def test_contains_reference_count(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "1 sequence" in text

    def test_contains_threshold(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "80%" in text

    def test_contains_mean_positive(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "Mean:" in text

    def test_contains_median(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "Median:" in text

    def test_novelty_shortcut_no_in_text(self):
        report = compute_similarity_report(["MMMM"], [1], ["AAKK"])
        text = format_similarity_report(report)
        assert "no" in text.lower()

    def test_novelty_shortcut_yes_in_text(self):
        report = compute_similarity_report(["AAKK"], [1], ["AAKK"], similarity_threshold=0.5, shortcut_fraction_threshold=0.5)
        text = format_similarity_report(report)
        assert "YES" in text

    def test_contains_notice(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "NOTICE" in text

    def test_contains_shortcut_explanation(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert report.shortcut_explanation in text

    def test_empty_report_does_not_crash(self):
        report = compute_similarity_report([], [], [])
        text = format_similarity_report(report)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_fraction_displayed_as_percent(self):
        report = compute_similarity_report(
            ["AAKK", "AAKL", "LLLL", "MMMM"],
            [1, 1, 0, 0],
            ["AAKK"],
            similarity_threshold=0.5,
        )
        text = format_similarity_report(report)
        assert "%" in text

    def test_positive_section_header_present(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "POSITIVE" in text

    def test_negative_section_header_present(self):
        report = self._basic_report()
        text = format_similarity_report(report)
        assert "NEGATIVE" in text
