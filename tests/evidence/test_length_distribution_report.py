"""Tests for length_distribution_report module (C5)."""
import pytest

from openamp_foundry.evidence.length_distribution_report import (
    AMP_LENGTH_MAX,
    AMP_LENGTH_MIN,
    SHORTCUT_FRACTION_THRESHOLD,
    SHORTCUT_RATIO_THRESHOLD,
    LengthDistributionReport,
    _in_range_fraction,
    _mean,
    _median,
    compute_length_report,
    format_length_report,
)


# --- Constants ---

class TestConstants:
    def test_amp_length_min_is_10(self):
        assert AMP_LENGTH_MIN == 10

    def test_amp_length_max_is_40(self):
        assert AMP_LENGTH_MAX == 40

    def test_shortcut_ratio_threshold(self):
        assert SHORTCUT_RATIO_THRESHOLD == pytest.approx(1.5)

    def test_shortcut_fraction_threshold(self):
        assert SHORTCUT_FRACTION_THRESHOLD == pytest.approx(0.60)


# --- _mean ---

class TestMean:
    def test_empty(self):
        assert _mean([]) == pytest.approx(0.0)

    def test_single(self):
        assert _mean([5.0]) == pytest.approx(5.0)

    def test_multiple(self):
        assert _mean([10.0, 20.0, 30.0]) == pytest.approx(20.0)

    def test_all_same(self):
        assert _mean([15.0, 15.0, 15.0]) == pytest.approx(15.0)


# --- _median ---

class TestMedian:
    def test_empty(self):
        assert _median([]) == pytest.approx(0.0)

    def test_single(self):
        assert _median([25.0]) == pytest.approx(25.0)

    def test_odd(self):
        assert _median([10.0, 20.0, 30.0]) == pytest.approx(20.0)

    def test_even(self):
        assert _median([10.0, 20.0, 30.0, 40.0]) == pytest.approx(25.0)

    def test_unsorted(self):
        assert _median([30.0, 10.0, 20.0]) == pytest.approx(20.0)


# --- _in_range_fraction ---

class TestInRangeFraction:
    def test_empty(self):
        assert _in_range_fraction([], 10, 40) == pytest.approx(0.0)

    def test_all_in_range(self):
        assert _in_range_fraction([10, 20, 30, 40], 10, 40) == pytest.approx(1.0)

    def test_none_in_range(self):
        assert _in_range_fraction([5, 50, 100], 10, 40) == pytest.approx(0.0)

    def test_half_in_range(self):
        assert _in_range_fraction([10, 50], 10, 40) == pytest.approx(0.5)

    def test_boundary_min_included(self):
        assert _in_range_fraction([10], 10, 40) == pytest.approx(1.0)

    def test_boundary_max_included(self):
        assert _in_range_fraction([40], 10, 40) == pytest.approx(1.0)

    def test_just_below_min_excluded(self):
        assert _in_range_fraction([9], 10, 40) == pytest.approx(0.0)

    def test_just_above_max_excluded(self):
        assert _in_range_fraction([41], 10, 40) == pytest.approx(0.0)


# --- compute_length_report ---

class TestComputeLengthReport:
    def _amp_seq(self, length: int) -> str:
        return "A" * length

    def test_no_shortcut_balanced(self):
        # Equal fraction of pos and neg in range → no shortcut
        seqs = ["A" * 20, "A" * 20, "A" * 20, "A" * 20]
        labels = [1, 1, 0, 0]
        report = compute_length_report(seqs, labels)
        assert report.length_shortcut_likely is False

    def test_shortcut_detected(self):
        # Positives all in range, negatives all out of range
        seqs = ["A" * 15, "A" * 25, "A" * 5, "A" * 60]
        labels = [1, 1, 0, 0]
        report = compute_length_report(seqs, labels)
        assert report.positive_in_amp_range_fraction == pytest.approx(1.0)
        assert report.negative_in_amp_range_fraction == pytest.approx(0.0)
        assert report.length_shortcut_likely is True

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            compute_length_report(["AA", "KK"], [1])

    def test_empty_sequences(self):
        report = compute_length_report([], [])
        assert report.n_positives == 0
        assert report.n_negatives == 0
        assert report.length_shortcut_likely is False

    def test_all_positives(self):
        seqs = ["A" * 20, "A" * 25]
        labels = [1, 1]
        report = compute_length_report(seqs, labels)
        assert report.n_negatives == 0
        assert report.n_positives == 2

    def test_all_negatives(self):
        seqs = ["A" * 20, "A" * 25]
        labels = [0, 0]
        report = compute_length_report(seqs, labels)
        assert report.n_positives == 0
        assert report.n_negatives == 2

    def test_positive_mean_length(self):
        seqs = ["A" * 10, "A" * 20, "K" * 5]
        labels = [1, 1, 0]
        report = compute_length_report(seqs, labels)
        assert report.positive_mean_length == pytest.approx(15.0)

    def test_negative_mean_length(self):
        seqs = ["A" * 5, "K" * 5]
        labels = [0, 0]
        report = compute_length_report(seqs, labels)
        assert report.negative_mean_length == pytest.approx(5.0)

    def test_positive_median_length(self):
        seqs = ["A" * 10, "A" * 20, "A" * 30]
        labels = [1, 1, 1]
        report = compute_length_report(seqs, labels)
        assert report.positive_median_length == pytest.approx(20.0)

    def test_length_ratio_correct(self):
        # pos all in range (frac=1.0), neg half in range (frac=0.5) → ratio=2.0
        seqs = ["A" * 20, "A" * 5, "A" * 25]
        labels = [1, 0, 0]
        report = compute_length_report(seqs, labels)
        assert report.positive_in_amp_range_fraction == pytest.approx(1.0)
        assert report.negative_in_amp_range_fraction == pytest.approx(0.5)
        assert report.length_ratio == pytest.approx(2.0)

    def test_no_neg_in_range_gives_inf_ratio(self):
        seqs = ["A" * 20, "A" * 5]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        assert report.length_ratio == float("inf")

    def test_no_pos_in_range_no_shortcut(self):
        seqs = ["A" * 5, "A" * 20]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        assert report.positive_in_amp_range_fraction == pytest.approx(0.0)
        assert report.length_shortcut_likely is False

    def test_positive_lengths_list(self):
        seqs = ["AA", "AAAA", "K"]
        labels = [1, 1, 0]
        report = compute_length_report(seqs, labels)
        assert sorted(report.positive_lengths) == [2, 4]

    def test_negative_lengths_list(self):
        seqs = ["K", "KKK"]
        labels = [0, 0]
        report = compute_length_report(seqs, labels)
        assert sorted(report.negative_lengths) == [1, 3]

    def test_custom_amp_range(self):
        seqs = ["A" * 5, "A" * 50]
        labels = [1, 0]
        report = compute_length_report(seqs, labels, amp_length_min=1, amp_length_max=10)
        assert report.positive_in_amp_range_fraction == pytest.approx(1.0)
        assert report.negative_in_amp_range_fraction == pytest.approx(0.0)

    def test_thresholds_stored_in_report(self):
        report = compute_length_report([], [], ratio_threshold=2.0, fraction_threshold=0.7)
        assert report.ratio_threshold == pytest.approx(2.0)
        assert report.fraction_threshold == pytest.approx(0.7)

    def test_amp_range_stored_in_report(self):
        report = compute_length_report([], [], amp_length_min=5, amp_length_max=50)
        assert report.amp_length_min == 5
        assert report.amp_length_max == 50

    def test_returns_dataclass(self):
        report = compute_length_report([], [])
        assert isinstance(report, LengthDistributionReport)

    def test_shortcut_explanation_contains_fractions(self):
        seqs = ["A" * 20, "A" * 5]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        assert "%" in report.shortcut_explanation

    def test_no_shortcut_explanation_format(self):
        seqs = ["A" * 20, "A" * 20]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        assert "No length shortcut detected" in report.shortcut_explanation

    def test_fraction_threshold_required_for_shortcut(self):
        # High ratio but low positive fraction → no shortcut
        # pos: 1 seq in range out of 10 → 0.10 (below 0.60 threshold)
        pos_seqs = ["A" * 20] + ["A" * 5] * 9   # 1 in range, 9 out
        neg_seqs = []
        seqs = pos_seqs + neg_seqs
        labels = [1] * 10
        report = compute_length_report(seqs, labels)
        assert report.positive_in_amp_range_fraction == pytest.approx(0.1)
        assert report.length_shortcut_likely is False

    def test_shortcut_detection_with_perfect_separation(self):
        pos_seqs = ["A" * 20, "A" * 25, "A" * 15]
        neg_seqs = ["A" * 5, "A" * 60, "A" * 80]
        seqs = pos_seqs + neg_seqs
        labels = [1, 1, 1, 0, 0, 0]
        report = compute_length_report(seqs, labels)
        assert report.positive_in_amp_range_fraction == pytest.approx(1.0)
        assert report.negative_in_amp_range_fraction == pytest.approx(0.0)
        assert report.length_shortcut_likely is True

    def test_zero_everything_is_safe(self):
        report = compute_length_report([], [])
        assert report.length_ratio == pytest.approx(1.0)
        assert report.length_shortcut_likely is False


# --- format_length_report ---

class TestFormatLengthReport:
    def _basic_report(self) -> LengthDistributionReport:
        seqs = ["A" * 20, "A" * 25, "A" * 5, "A" * 60]
        labels = [1, 1, 0, 0]
        return compute_length_report(seqs, labels)

    def test_returns_string(self):
        assert isinstance(format_length_report(self._basic_report()), str)

    def test_contains_header(self):
        assert "LENGTH DISTRIBUTION REPORT" in format_length_report(self._basic_report())

    def test_contains_positive_count(self):
        assert "2 positives" in format_length_report(self._basic_report())

    def test_contains_negative_count(self):
        assert "2 negatives" in format_length_report(self._basic_report())

    def test_contains_amp_range(self):
        text = format_length_report(self._basic_report())
        assert "10" in text and "40" in text

    def test_contains_mean(self):
        assert "Mean:" in format_length_report(self._basic_report())

    def test_contains_median(self):
        assert "Median:" in format_length_report(self._basic_report())

    def test_shortcut_yes_in_text(self):
        seqs = ["A" * 20, "A" * 5]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        text = format_length_report(report)
        assert "YES" in text

    def test_shortcut_no_in_text(self):
        seqs = ["A" * 20, "A" * 20]
        labels = [1, 0]
        report = compute_length_report(seqs, labels)
        text = format_length_report(report)
        assert "no" in text.lower()

    def test_contains_notice(self):
        assert "NOTICE" in format_length_report(self._basic_report())

    def test_contains_shortcut_explanation(self):
        report = self._basic_report()
        text = format_length_report(report)
        assert report.shortcut_explanation in text

    def test_empty_report_does_not_crash(self):
        report = compute_length_report([], [])
        text = format_length_report(report)
        assert isinstance(text, str) and len(text) > 0

    def test_positive_section_present(self):
        assert "POSITIVE" in format_length_report(self._basic_report())

    def test_negative_section_present(self):
        assert "NEGATIVE" in format_length_report(self._basic_report())

    def test_ratio_in_output(self):
        assert "ratio" in format_length_report(self._basic_report()).lower()
