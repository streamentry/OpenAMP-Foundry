"""Tests for family_stratified_report module (C7)."""
import pytest

from openamp_foundry.evidence.family_stratified_report import (
    FAMILY_INFLATION_DOMINANCE_THRESHOLD,
    FAMILY_INFLATION_FRACTION_THRESHOLD,
    FamilyStratifiedReport,
    _family_counts_in_top_k,
    _family_fractions,
    _precision_at_k,
    compute_family_stratified_report,
    format_family_stratified_report,
)


# --- Constants ---

class TestConstants:
    def test_dominance_threshold(self):
        assert FAMILY_INFLATION_DOMINANCE_THRESHOLD == pytest.approx(0.60)

    def test_fraction_threshold(self):
        assert FAMILY_INFLATION_FRACTION_THRESHOLD == pytest.approx(0.50)


# --- _precision_at_k ---

class TestPrecisionAtK:
    def test_all_positive(self):
        assert _precision_at_k([1, 1, 1], 3) == pytest.approx(1.0)

    def test_all_negative(self):
        assert _precision_at_k([0, 0, 0], 3) == pytest.approx(0.0)

    def test_half_positive(self):
        assert _precision_at_k([1, 0, 1, 0], 4) == pytest.approx(0.5)

    def test_k_larger_than_list(self):
        assert _precision_at_k([1, 0], 10) == pytest.approx(0.5)

    def test_k_zero(self):
        assert _precision_at_k([1, 1, 1], 0) == pytest.approx(0.0)

    def test_empty_labels(self):
        assert _precision_at_k([], 3) == pytest.approx(0.0)

    def test_top_k_only(self):
        # Only top-2 evaluated, rest ignored
        assert _precision_at_k([1, 1, 0, 0], 2) == pytest.approx(1.0)

    def test_single_positive(self):
        assert _precision_at_k([1], 1) == pytest.approx(1.0)


# --- _family_counts_in_top_k ---

class TestFamilyCountsInTopK:
    def test_single_family(self):
        result = _family_counts_in_top_k(["defensin", "defensin", "defensin"], 3)
        assert result == {"defensin": 3}

    def test_two_families(self):
        result = _family_counts_in_top_k(["defensin", "cathelicidin", "defensin"], 3)
        assert result["defensin"] == 2
        assert result["cathelicidin"] == 1

    def test_k_limits_count(self):
        result = _family_counts_in_top_k(["A", "A", "B", "B"], 2)
        assert result == {"A": 2}

    def test_empty_families(self):
        result = _family_counts_in_top_k([], 5)
        assert result == {}

    def test_k_larger_than_list(self):
        result = _family_counts_in_top_k(["A", "B"], 10)
        assert result == {"A": 1, "B": 1}


# --- _family_fractions ---

class TestFamilyFractions:
    def test_single_family_all(self):
        result = _family_fractions({"defensin": 3}, 3)
        assert result == {"defensin": pytest.approx(1.0)}

    def test_two_families_equal(self):
        result = _family_fractions({"A": 2, "B": 2}, 4)
        assert result["A"] == pytest.approx(0.5)
        assert result["B"] == pytest.approx(0.5)

    def test_empty_counts(self):
        result = _family_fractions({}, 5)
        assert result == {}

    def test_k_zero(self):
        result = _family_fractions({"A": 1}, 0)
        assert result == {}


# --- compute_family_stratified_report ---

class TestComputeFamilyStratifiedReport:
    def test_basic_no_inflation(self):
        seqs = ["A", "B", "C", "D", "E", "F"]
        labels = [1, 1, 1, 0, 0, 0]
        families = ["alpha", "beta", "gamma", "alpha", "beta", "gamma"]
        report = compute_family_stratified_report(seqs, labels, families, k=3)
        assert report.family_inflation_likely is False
        assert report.k == 3

    def test_inflation_single_family_dominates(self):
        seqs = ["A"] * 5 + ["B"] * 5
        labels = [1] * 10
        families = ["defensin"] * 8 + ["cathelicidin"] * 2
        report = compute_family_stratified_report(seqs, labels, families, k=5)
        # Top-5 all defensin → fraction=1.0 ≥ 0.60 threshold
        assert report.family_inflation_likely is True
        assert report.dominant_family == "defensin"

    def test_length_mismatch_sequences_labels(self):
        with pytest.raises(ValueError, match="same length"):
            compute_family_stratified_report(["A", "B"], [1], ["fam"], k=1)

    def test_length_mismatch_sequences_families(self):
        with pytest.raises(ValueError, match="same length"):
            compute_family_stratified_report(["A", "B"], [1, 0], ["fam"], k=1)

    def test_k_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            compute_family_stratified_report(["A"], [1], ["fam"], k=0)

    def test_k_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            compute_family_stratified_report(["A"], [1], ["fam"], k=-1)

    def test_empty_sequences(self):
        with pytest.raises(ValueError):
            compute_family_stratified_report([], [], [], k=5)

    def test_k_capped_at_n(self):
        seqs = ["A", "B"]
        labels = [1, 0]
        families = ["fam", "fam"]
        report = compute_family_stratified_report(seqs, labels, families, k=100)
        assert report.k == 2

    def test_precision_at_k_correct(self):
        seqs = ["A", "B", "C", "D"]
        labels = [1, 1, 0, 0]
        families = ["alpha", "beta", "alpha", "beta"]
        report = compute_family_stratified_report(seqs, labels, families, k=2)
        assert report.precision_at_k == pytest.approx(1.0)

    def test_n_families_counted(self):
        seqs = ["A", "B", "C"]
        labels = [1, 0, 1]
        families = ["alpha", "beta", "alpha"]
        report = compute_family_stratified_report(seqs, labels, families, k=3)
        assert report.n_families == 2

    def test_top_k_family_counts_correct(self):
        seqs = ["A", "B", "C"]
        labels = [1, 1, 0]
        families = ["defensin", "defensin", "cathelicidin"]
        report = compute_family_stratified_report(seqs, labels, families, k=3)
        assert report.top_k_family_counts["defensin"] == 2
        assert report.top_k_family_counts["cathelicidin"] == 1

    def test_top_k_family_fractions_correct(self):
        seqs = ["A", "B", "C", "D"]
        labels = [1, 1, 0, 0]
        families = ["alpha", "alpha", "alpha", "beta"]
        report = compute_family_stratified_report(seqs, labels, families, k=4)
        assert report.top_k_family_fractions["alpha"] == pytest.approx(0.75)

    def test_dominant_family_is_most_common(self):
        seqs = ["A", "B", "C", "D"]
        labels = [1, 1, 1, 0]
        families = ["alpha", "alpha", "beta", "alpha"]
        report = compute_family_stratified_report(seqs, labels, families, k=4)
        assert report.dominant_family == "alpha"

    def test_returns_dataclass(self):
        seqs = ["A"]
        labels = [1]
        families = ["fam"]
        report = compute_family_stratified_report(seqs, labels, families, k=1)
        assert isinstance(report, FamilyStratifiedReport)

    def test_custom_dominance_threshold(self):
        seqs = ["A", "B", "C"]
        labels = [1, 1, 0]
        families = ["alpha", "alpha", "beta"]
        # With dominance_threshold=0.9, even 2/3 = 0.67 won't trigger
        report = compute_family_stratified_report(seqs, labels, families, k=3, dominance_threshold=0.9)
        assert report.family_inflation_likely is False

    def test_inflation_explanation_contains_family(self):
        seqs = ["A"] * 5
        labels = [1] * 5
        families = ["defensin"] * 5
        report = compute_family_stratified_report(seqs, labels, families, k=5)
        assert "defensin" in report.inflation_explanation

    def test_no_inflation_explanation_format(self):
        seqs = ["A", "B", "C"]
        labels = [1, 0, 1]
        families = ["alpha", "beta", "gamma"]
        report = compute_family_stratified_report(seqs, labels, families, k=3)
        assert "No family inflation detected" in report.inflation_explanation

    def test_family_precision_at_k_computed(self):
        seqs = ["A", "B", "C", "D"]
        labels = [1, 0, 1, 0]
        families = ["alpha", "alpha", "beta", "beta"]
        report = compute_family_stratified_report(seqs, labels, families, k=4)
        assert "alpha" in report.family_precision_at_k
        assert "beta" in report.family_precision_at_k
        assert report.family_precision_at_k["alpha"] == pytest.approx(0.5)

    def test_n_sequences_stored(self):
        seqs = ["A", "B", "C"]
        labels = [1, 0, 1]
        families = ["fam", "fam", "fam"]
        report = compute_family_stratified_report(seqs, labels, families, k=3)
        assert report.n_sequences == 3

    def test_thresholds_stored(self):
        seqs = ["A"]
        labels = [1]
        families = ["fam"]
        report = compute_family_stratified_report(seqs, labels, families, k=1, dominance_threshold=0.7, fraction_threshold=0.4)
        assert report.dominance_threshold == pytest.approx(0.7)
        assert report.fraction_threshold == pytest.approx(0.4)


# --- format_family_stratified_report ---

class TestFormatFamilyStratifiedReport:
    def _basic_report(self) -> FamilyStratifiedReport:
        seqs = ["A", "B", "C", "D", "E", "F"]
        labels = [1, 1, 0, 0, 1, 0]
        families = ["alpha", "beta", "alpha", "beta", "gamma", "gamma"]
        return compute_family_stratified_report(seqs, labels, families, k=4)

    def test_returns_string(self):
        assert isinstance(format_family_stratified_report(self._basic_report()), str)

    def test_contains_header(self):
        assert "FAMILY-STRATIFIED" in format_family_stratified_report(self._basic_report())

    def test_contains_k(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert "k = " in text or f"@{report.k}" in text

    def test_contains_precision(self):
        text = format_family_stratified_report(self._basic_report())
        assert "Precision" in text

    def test_contains_family_names(self):
        text = format_family_stratified_report(self._basic_report())
        assert "alpha" in text or "beta" in text

    def test_inflation_yes_in_text(self):
        seqs = ["A"] * 5
        labels = [1] * 5
        families = ["defensin"] * 5
        report = compute_family_stratified_report(seqs, labels, families, k=5)
        text = format_family_stratified_report(report)
        assert "YES" in text

    def test_inflation_no_in_text(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert "no" in text.lower()

    def test_contains_notice(self):
        assert "NOTICE" in format_family_stratified_report(self._basic_report())

    def test_contains_explanation(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert report.inflation_explanation in text

    def test_contains_dominant_family(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert "Dominant family" in text

    def test_empty_like_report_does_not_crash(self):
        seqs = ["A"]
        labels = [1]
        families = ["fam"]
        report = compute_family_stratified_report(seqs, labels, families, k=1)
        text = format_family_stratified_report(report)
        assert isinstance(text, str) and len(text) > 0

    def test_threshold_in_output(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert "threshold" in text.lower()

    def test_per_family_section_present(self):
        report = self._basic_report()
        text = format_family_stratified_report(report)
        assert "PER-FAMILY" in text
