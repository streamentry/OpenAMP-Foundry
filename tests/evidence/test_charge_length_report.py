"""Tests for charge_length_report module (C6)."""
import pytest

from openamp_foundry.evidence.charge_length_report import (
    COMBINED_CHARGE_THRESHOLD,
    COMBINED_LENGTH_MAX,
    COMBINED_LENGTH_MIN,
    COMBINED_SHORTCUT_FRACTION_THRESHOLD,
    COMBINED_SHORTCUT_RATIO_THRESHOLD,
    ChargeLengthReport,
    _is_charge_length_match,
    _match_fraction,
    _net_charge_proxy,
    compute_charge_length_report,
    format_charge_length_report,
)


# --- Constants ---

class TestConstants:
    def test_charge_threshold_is_4(self):
        assert COMBINED_CHARGE_THRESHOLD == 4

    def test_length_min_is_10(self):
        assert COMBINED_LENGTH_MIN == 10

    def test_length_max_is_40(self):
        assert COMBINED_LENGTH_MAX == 40

    def test_ratio_threshold(self):
        assert COMBINED_SHORTCUT_RATIO_THRESHOLD == pytest.approx(1.5)

    def test_fraction_threshold(self):
        assert COMBINED_SHORTCUT_FRACTION_THRESHOLD == pytest.approx(0.50)


# --- _net_charge_proxy ---

class TestNetChargeProxy:
    def test_all_positive_residues(self):
        assert _net_charge_proxy("KKKK") == pytest.approx(4.0)

    def test_all_negative_residues(self):
        assert _net_charge_proxy("DDDD") == pytest.approx(-4.0)

    def test_neutral(self):
        assert _net_charge_proxy("AAAA") == pytest.approx(0.0)

    def test_mixed(self):
        # 2K + 1R = 3 positive, 1D = 1 negative -> net = 2
        assert _net_charge_proxy("KKRD") == pytest.approx(2.0)

    def test_empty(self):
        assert _net_charge_proxy("") == pytest.approx(0.0)

    def test_lowercase(self):
        assert _net_charge_proxy("kkkk") == pytest.approx(4.0)

    def test_r_counts(self):
        assert _net_charge_proxy("RRRR") == pytest.approx(4.0)

    def test_e_counts_negative(self):
        assert _net_charge_proxy("EEEE") == pytest.approx(-4.0)


# --- _is_charge_length_match ---

class TestIsChargeLengthMatch:
    def test_matching_sequence(self):
        # 15 aa, charge 5 -> match
        assert _is_charge_length_match("KKKKKAAAAAAAAA", 4, 10, 40) is True

    def test_too_short(self):
        assert _is_charge_length_match("KKKK", 4, 10, 40) is False

    def test_too_long(self):
        seq = "K" * 5 + "A" * 40
        assert _is_charge_length_match(seq, 4, 10, 40) is False

    def test_low_charge(self):
        assert _is_charge_length_match("A" * 20, 4, 10, 40) is False

    def test_both_criteria_exactly_at_boundaries(self):
        # length=10, charge=4 exactly
        seq = "KKKK" + "A" * 6  # 10 aa, charge 4
        assert _is_charge_length_match(seq, 4, 10, 40) is True

    def test_length_at_max_boundary(self):
        seq = "KKKKK" + "A" * 35  # 40 aa, charge 5
        assert _is_charge_length_match(seq, 4, 10, 40) is True

    def test_length_just_above_max(self):
        seq = "KKKKK" + "A" * 36  # 41 aa
        assert _is_charge_length_match(seq, 4, 10, 40) is False

    def test_charge_just_below_threshold(self):
        seq = "KKK" + "A" * 17  # 20 aa, charge 3
        assert _is_charge_length_match(seq, 4, 10, 40) is False


# --- _match_fraction ---

class TestMatchFraction:
    def test_empty_sequences(self):
        frac, count = _match_fraction([], 4, 10, 40)
        assert frac == pytest.approx(0.0)
        assert count == 0

    def test_all_match(self):
        seqs = ["KKKK" + "A" * 16, "RRRRR" + "A" * 10]  # both 20aa+, charge>=4
        frac, count = _match_fraction(seqs, 4, 10, 40)
        assert frac == pytest.approx(1.0)
        assert count == 2

    def test_none_match(self):
        seqs = ["AAAA" * 5, "LLLL" * 3]
        frac, count = _match_fraction(seqs, 4, 10, 40)
        assert frac == pytest.approx(0.0)
        assert count == 0

    def test_half_match(self):
        matching = "KKKK" + "A" * 16   # 20aa, charge 4
        non_matching = "A" * 20         # 20aa, charge 0
        frac, count = _match_fraction([matching, non_matching], 4, 10, 40)
        assert frac == pytest.approx(0.5)
        assert count == 1


# --- compute_charge_length_report ---

class TestComputeChargeLengthReport:
    def _amp_match(self) -> str:
        return "KKKK" + "A" * 16  # 20aa, charge 4 - matches both

    def _non_match_low_charge(self) -> str:
        return "A" * 20  # 20aa, charge 0

    def _non_match_too_long(self) -> str:
        return "K" * 5 + "A" * 50  # 55aa, too long

    def test_no_shortcut_balanced(self):
        seqs = [self._amp_match(), self._amp_match(), self._amp_match(), self._amp_match()]
        labels = [1, 1, 0, 0]
        report = compute_charge_length_report(seqs, labels)
        assert report.combined_shortcut_likely is False

    def test_shortcut_detected(self):
        pos = [self._amp_match()] * 3
        neg = [self._non_match_low_charge()] * 3
        report = compute_charge_length_report(pos + neg, [1, 1, 1, 0, 0, 0])
        assert report.positive_combined_match_fraction == pytest.approx(1.0)
        assert report.negative_combined_match_fraction == pytest.approx(0.0)
        assert report.combined_shortcut_likely is True

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            compute_charge_length_report(["AA", "KK"], [1])

    def test_empty_sequences(self):
        report = compute_charge_length_report([], [])
        assert report.n_positives == 0
        assert report.n_negatives == 0
        assert report.combined_shortcut_likely is False

    def test_all_positives(self):
        seqs = [self._amp_match(), self._amp_match()]
        labels = [1, 1]
        report = compute_charge_length_report(seqs, labels)
        assert report.n_negatives == 0

    def test_all_negatives(self):
        seqs = [self._non_match_low_charge(), self._non_match_low_charge()]
        labels = [0, 0]
        report = compute_charge_length_report(seqs, labels)
        assert report.n_positives == 0

    def test_positive_match_count_correct(self):
        seqs = [self._amp_match(), self._non_match_low_charge(), self._non_match_low_charge()]
        labels = [1, 0, 0]
        report = compute_charge_length_report(seqs, labels)
        assert report.positive_match_count == 1

    def test_negative_match_count_correct(self):
        seqs = [self._non_match_low_charge(), self._amp_match(), self._non_match_low_charge()]
        labels = [0, 0, 0]
        report = compute_charge_length_report(seqs, labels)
        assert report.negative_match_count == 1

    def test_ratio_correct(self):
        # pos: all match (frac=1.0), neg: half match (frac=0.5) → ratio=2.0
        pos = [self._amp_match()]
        neg = [self._amp_match(), self._non_match_low_charge()]
        report = compute_charge_length_report(pos + neg, [1, 0, 0])
        assert report.positive_combined_match_fraction == pytest.approx(1.0)
        assert report.negative_combined_match_fraction == pytest.approx(0.5)
        assert report.combined_ratio == pytest.approx(2.0)

    def test_no_neg_match_gives_inf_ratio(self):
        pos = [self._amp_match()]
        neg = [self._non_match_low_charge()]
        report = compute_charge_length_report(pos + neg, [1, 0])
        assert report.combined_ratio == float("inf")

    def test_no_pos_match_no_shortcut(self):
        pos = [self._non_match_low_charge()]
        neg = [self._non_match_low_charge()]
        report = compute_charge_length_report(pos + neg, [1, 0])
        assert report.positive_combined_match_fraction == pytest.approx(0.0)
        assert report.combined_shortcut_likely is False

    def test_custom_thresholds_stored(self):
        report = compute_charge_length_report([], [], charge_threshold=3.0, length_min=5, length_max=50)
        assert report.charge_threshold == pytest.approx(3.0)
        assert report.length_min == 5
        assert report.length_max == 50

    def test_returns_dataclass(self):
        report = compute_charge_length_report([], [])
        assert isinstance(report, ChargeLengthReport)

    def test_explanation_contains_charge_threshold(self):
        pos = [self._amp_match()] * 2
        neg = [self._non_match_low_charge()] * 2
        report = compute_charge_length_report(pos + neg, [1, 1, 0, 0])
        assert "4" in report.shortcut_explanation

    def test_no_shortcut_explanation_format(self):
        seqs = [self._amp_match(), self._amp_match()]
        labels = [1, 0]
        report = compute_charge_length_report(seqs, labels)
        assert "No combined shortcut detected" in report.shortcut_explanation

    def test_shortcut_explanation_has_percent(self):
        pos = [self._amp_match()] * 3
        neg = [self._non_match_low_charge()] * 3
        report = compute_charge_length_report(pos + neg, [1, 1, 1, 0, 0, 0])
        assert "%" in report.shortcut_explanation

    def test_fraction_threshold_required(self):
        # Only 1/10 positives match combined criteria (10%) → below 50% threshold
        pos = [self._amp_match()] + [self._non_match_low_charge()] * 9
        neg = [self._non_match_low_charge()] * 10
        report = compute_charge_length_report(pos + neg, [1] * 10 + [0] * 10)
        assert report.positive_combined_match_fraction == pytest.approx(0.1)
        assert report.combined_shortcut_likely is False

    def test_zero_all_safe(self):
        report = compute_charge_length_report([], [])
        assert report.combined_ratio == pytest.approx(1.0)
        assert report.combined_shortcut_likely is False

    def test_both_criteria_must_hold(self):
        # Long + charged: fails length criterion
        long_charged = "K" * 5 + "A" * 50
        # Short + uncharged: fails charge criterion
        short_uncharged = "A" * 20
        seqs = [long_charged, short_uncharged]
        labels = [1, 0]
        report = compute_charge_length_report(seqs, labels)
        assert report.positive_combined_match_fraction == pytest.approx(0.0)
        assert report.combined_shortcut_likely is False


# --- format_charge_length_report ---

class TestFormatChargeLengthReport:
    def _basic_report(self) -> ChargeLengthReport:
        pos = ["KKKK" + "A" * 16] * 2
        neg = ["A" * 20] * 2
        return compute_charge_length_report(pos + neg, [1, 1, 0, 0])

    def test_returns_string(self):
        assert isinstance(format_charge_length_report(self._basic_report()), str)

    def test_contains_header(self):
        assert "COMBINED CHARGE+LENGTH" in format_charge_length_report(self._basic_report())

    def test_contains_positive_count(self):
        assert "2 positives" in format_charge_length_report(self._basic_report())

    def test_contains_negative_count(self):
        assert "2 negatives" in format_charge_length_report(self._basic_report())

    def test_contains_charge_threshold(self):
        text = format_charge_length_report(self._basic_report())
        assert "4" in text

    def test_contains_length_range(self):
        text = format_charge_length_report(self._basic_report())
        assert "10" in text and "40" in text

    def test_shortcut_yes_in_text(self):
        pos = ["KKKK" + "A" * 16] * 3
        neg = ["A" * 20] * 3
        report = compute_charge_length_report(pos + neg, [1, 1, 1, 0, 0, 0])
        text = format_charge_length_report(report)
        assert "YES" in text

    def test_shortcut_no_in_text(self):
        report = self._basic_report()
        text = format_charge_length_report(report)
        assert "no" in text.lower()

    def test_contains_notice(self):
        assert "NOTICE" in format_charge_length_report(self._basic_report())

    def test_contains_explanation(self):
        report = self._basic_report()
        text = format_charge_length_report(report)
        assert report.shortcut_explanation in text

    def test_empty_report_does_not_crash(self):
        report = compute_charge_length_report([], [])
        text = format_charge_length_report(report)
        assert isinstance(text, str) and len(text) > 0

    def test_positive_section_present(self):
        assert "POSITIVE" in format_charge_length_report(self._basic_report())

    def test_negative_section_present(self):
        assert "NEGATIVE" in format_charge_length_report(self._basic_report())

    def test_ratio_in_output(self):
        assert "ratio" in format_charge_length_report(self._basic_report()).lower()
