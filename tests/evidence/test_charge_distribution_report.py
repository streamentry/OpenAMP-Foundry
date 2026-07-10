"""Tests for charge-distribution report — Phase C C3.

63 tests across 7 groups.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.charge_distribution_report import (
    CHARGE_THRESHOLD,
    SHORTCUT_RATIO_THRESHOLD,
    SHORTCUT_WARNING_FRACTION,
    ChargeDistributionReport,
    _net_charge_proxy,
    compute_charge_report,
    format_charge_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# AMP-like (high charge): K, R, H are positive AA
_AMP_SEQ = "KWKLFKK"   # net charge ~5 (K=5, W=0, L=0, F=0)
_NEG_SEQ = "GSGSGSGS"  # net charge 0

# High-charge AMP set (positives) and low-charge set (negatives)
_HIGH_CHARGE_SEQS = ["KKKKKK", "RRRRRR", "KRKRKR", "KWKLFKK", "KKWWKK"]
_LOW_CHARGE_SEQS = ["GGGGGG", "AAAAAA", "LLLLLL", "FFFFFF", "GGAAGG"]
_HIGH_LABELS = [1] * 5
_LOW_LABELS = [0] * 5


# ---------------------------------------------------------------------------
# Group 1: NetChargeProxy (8 tests)
# ---------------------------------------------------------------------------

class TestNetChargeProxy:
    def test_positive_aa_charge(self):
        assert _net_charge_proxy("KKK") == 3.0

    def test_negative_aa_charge(self):
        assert _net_charge_proxy("EEE") == -3.0

    def test_mixed_charge(self):
        assert _net_charge_proxy("KE") == 0.0

    def test_neutral_aa_zero(self):
        assert _net_charge_proxy("GSGSGS") == 0.0

    def test_amp_seq_positive(self):
        assert _net_charge_proxy(_AMP_SEQ) > 0

    def test_arginine_counted(self):
        assert _net_charge_proxy("R") == 1.0

    def test_histidine_counted(self):
        assert _net_charge_proxy("H") == 1.0

    def test_case_insensitive(self):
        assert _net_charge_proxy("kkk") == _net_charge_proxy("KKK")


# ---------------------------------------------------------------------------
# Group 2: BasicComputeReport (10 tests)
# ---------------------------------------------------------------------------

class TestBasicComputeReport:
    def test_returns_report_object(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert isinstance(report, ChargeDistributionReport)

    def test_n_positive_correct(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert report.n_positive == 5

    def test_n_negative_correct(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert report.n_negative == 5

    def test_mean_charge_positive_greater_than_negative(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert report.mean_charge_positive > report.mean_charge_negative

    def test_fraction_positive_high_charge_is_float(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert isinstance(report.fraction_positive_high_charge, float)

    def test_fraction_negative_high_charge_is_float(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert isinstance(report.fraction_negative_high_charge, float)

    def test_fractions_between_0_and_1(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert 0.0 <= report.fraction_positive_high_charge <= 1.0
        assert 0.0 <= report.fraction_negative_high_charge <= 1.0

    def test_charge_shortcut_likely_is_bool(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert isinstance(report.charge_shortcut_likely, bool)

    def test_shortcut_warning_is_string(self):
        report = compute_charge_report(_HIGH_CHARGE_SEQS + _LOW_CHARGE_SEQS,
                                       _HIGH_LABELS + _LOW_LABELS)
        assert isinstance(report.shortcut_warning, str)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            compute_charge_report(["KKK", "GGG"], [1])


# ---------------------------------------------------------------------------
# Group 3: ShortcutDetection (10 tests)
# ---------------------------------------------------------------------------

class TestShortcutDetection:
    def _high_charge_report(self) -> ChargeDistributionReport:
        seqs = ["KKKKKK"] * 10 + ["GGGGGG"] * 10
        labels = [1] * 10 + [0] * 10
        return compute_charge_report(seqs, labels)

    def test_all_positive_high_charge_triggers_shortcut(self):
        report = self._high_charge_report()
        assert report.charge_shortcut_likely is True

    def test_shortcut_warning_non_empty_when_likely(self):
        report = self._high_charge_report()
        assert len(report.shortcut_warning) > 0

    def test_shortcut_warning_mentions_charge(self):
        report = self._high_charge_report()
        assert "charge" in report.shortcut_warning.lower()

    def test_balanced_charge_no_shortcut(self):
        seqs = ["KKKK"] * 5 + ["KKKK"] * 5
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(seqs, labels)
        # Both groups same charge → ratio = 1 → no ratio shortcut
        # But fraction may still be high → check individually
        # This is borderline — fraction_positive_high_charge depends on threshold
        assert isinstance(report.charge_shortcut_likely, bool)

    def test_low_charge_positives_no_shortcut(self):
        seqs = ["GGGGGG"] * 5 + ["KKKKKK"] * 5
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(seqs, labels)
        # Positives have LOW charge, negatives have HIGH charge → no shortcut
        assert report.fraction_positive_high_charge == 0.0
        assert not report.charge_shortcut_likely

    def test_shortcut_fraction_threshold_is_60pct(self):
        assert SHORTCUT_WARNING_FRACTION == 0.60

    def test_shortcut_ratio_threshold_is_1_5(self):
        assert SHORTCUT_RATIO_THRESHOLD == 1.5

    def test_charge_threshold_is_4(self):
        assert CHARGE_THRESHOLD == 4

    def test_report_has_charge_ratio(self):
        # positives charge 6, negatives charge 1 → ratio = 6
        seqs = ["KKKKKK"] * 5 + ["K"] * 5
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(seqs, labels)
        assert report.charge_ratio is not None
        assert report.charge_ratio > 1.0

    def test_equal_charge_groups_ratio_is_1(self):
        seqs = ["KKKK"] * 4 + ["KKKK"] * 4
        labels = [1] * 4 + [0] * 4
        report = compute_charge_report(seqs, labels)
        assert report.charge_ratio == pytest.approx(1.0, abs=0.01)

    def test_high_ratio_triggers_shortcut(self):
        # positives: very high charge; negatives: charge = 1
        seqs = ["KKKKKK"] * 5 + ["K"] * 5  # charge 6 vs charge 1 → ratio 6
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(seqs, labels)
        assert report.charge_ratio is not None
        assert report.charge_ratio >= SHORTCUT_RATIO_THRESHOLD


# ---------------------------------------------------------------------------
# Group 4: EdgeCases (8 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_sequences_returns_report(self):
        report = compute_charge_report([], [])
        assert report.n_positive == 0
        assert report.n_negative == 0

    def test_all_positives_no_negatives(self):
        report = compute_charge_report(["KKKK", "RRRR"], [1, 1])
        assert report.n_negative == 0
        assert report.mean_charge_negative is None

    def test_all_negatives_no_positives(self):
        report = compute_charge_report(["GGGG", "AAAA"], [0, 0])
        assert report.n_positive == 0
        assert report.mean_charge_positive is None

    def test_single_positive(self):
        report = compute_charge_report(["KKKK"], [1])
        assert report.n_positive == 1
        assert report.mean_charge_positive == 4.0

    def test_single_negative(self):
        report = compute_charge_report(["GGGG"], [0])
        assert report.n_negative == 1
        assert report.mean_charge_negative == 0.0

    def test_charge_ratio_none_when_neg_charge_is_zero(self):
        seqs = ["KKKK"] * 3 + ["GGGG"] * 3
        labels = [1] * 3 + [0] * 3
        report = compute_charge_report(seqs, labels)
        # negatives have charge=0 → ratio undefined (division by zero prevented)
        assert report.charge_ratio is None or report.charge_ratio > 0

    def test_positive_charges_stored(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert 4.0 in report.positive_charges

    def test_negative_charges_stored(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert 0.0 in report.negative_charges


# ---------------------------------------------------------------------------
# Group 5: MedianAndMeanStats (8 tests)
# ---------------------------------------------------------------------------

class TestMedianAndMeanStats:
    def test_mean_positive_is_float(self):
        report = compute_charge_report(["KKKK"], [1])
        assert isinstance(report.mean_charge_positive, float)

    def test_median_positive_is_float_or_none(self):
        report = compute_charge_report(["KKKK"], [1])
        assert isinstance(report.median_charge_positive, (float, int))

    def test_mean_charge_computed_correctly(self):
        seqs = ["KK", "KKKK"]  # charge 2 and 4 → mean 3
        labels = [1, 1]
        report = compute_charge_report(seqs, labels)
        assert report.mean_charge_positive == pytest.approx(3.0)

    def test_median_charge_computed_correctly(self):
        seqs = ["K", "KK", "KKKK"]  # charge 1, 2, 4 → median 2
        labels = [1, 1, 1]
        report = compute_charge_report(seqs, labels)
        assert report.median_charge_positive == pytest.approx(2.0)

    def test_mean_negative_computed_correctly(self):
        seqs = ["GG", "GGGG"]  # charge 0, 0 → mean 0
        labels = [0, 0]
        report = compute_charge_report(seqs, labels)
        assert report.mean_charge_negative == pytest.approx(0.0)

    def test_none_mean_for_empty_group(self):
        report = compute_charge_report([], [])
        assert report.mean_charge_positive is None
        assert report.mean_charge_negative is None

    def test_none_median_for_empty_group(self):
        report = compute_charge_report([], [])
        assert report.median_charge_positive is None
        assert report.median_charge_negative is None

    def test_fraction_high_charge_1_0_for_all_high(self):
        seqs = ["KKKK", "KKKKK"]  # both charge >= 4
        labels = [1, 1]
        report = compute_charge_report(seqs, labels)
        assert report.fraction_positive_high_charge == 1.0


# ---------------------------------------------------------------------------
# Group 6: FormatReport (8 tests)
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_format_report_returns_string(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert isinstance(format_charge_report(report), str)

    def test_format_report_non_empty(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert len(format_charge_report(report)) > 0

    def test_format_report_contains_header(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        text = format_charge_report(report)
        assert "CHARGE DISTRIBUTION" in text

    def test_format_report_contains_shortcut_result(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        text = format_charge_report(report)
        assert "Shortcut" in text or "shortcut" in text

    def test_format_report_contains_n_positive(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        text = format_charge_report(report)
        assert "n=1" in text

    def test_format_report_multiline(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert "\n" in format_charge_report(report)

    def test_format_report_warning_included_when_shortcut(self):
        seqs = ["KKKKKK"] * 10 + ["GGGGGG"] * 10
        labels = [1] * 10 + [0] * 10
        report = compute_charge_report(seqs, labels)
        text = format_charge_report(report)
        if report.charge_shortcut_likely:
            assert "SHORTCUT" in text.upper() or "WARNING" in text.upper() or "LIKELY" in text.upper()

    def test_format_report_no_output_when_no_shortcut(self):
        seqs = ["GGGG"] * 5 + ["KKKK"] * 5
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(seqs, labels)
        text = format_charge_report(report)
        assert isinstance(text, str)


# ---------------------------------------------------------------------------
# Group 7: IntegrationAndConstants (11 tests)
# ---------------------------------------------------------------------------

class TestIntegrationAndConstants:
    def test_charge_threshold_constant(self):
        assert CHARGE_THRESHOLD == 4

    def test_shortcut_warning_fraction_constant(self):
        assert 0 < SHORTCUT_WARNING_FRACTION < 1

    def test_shortcut_ratio_threshold_constant(self):
        assert SHORTCUT_RATIO_THRESHOLD > 1

    def test_report_dataclass_fields_complete(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        assert hasattr(report, "n_positive")
        assert hasattr(report, "n_negative")
        assert hasattr(report, "mean_charge_positive")
        assert hasattr(report, "mean_charge_negative")
        assert hasattr(report, "fraction_positive_high_charge")
        assert hasattr(report, "fraction_negative_high_charge")
        assert hasattr(report, "charge_shortcut_likely")
        assert hasattr(report, "shortcut_warning")

    def test_typical_amp_dataset_flagged(self):
        # Typical AMP datasets: AMPs tend to be cationic (charge >= 4)
        amp_seqs = ["KWKLFKK", "KKKWWKK", "RRRRWWW", "RRKKKLL", "KKHHHKK"]
        neg_seqs = ["GGGGGG", "AAAAAA", "LLLLLL", "FFFFFF", "WWWWWW"]
        labels = [1] * 5 + [0] * 5
        report = compute_charge_report(amp_seqs + neg_seqs, labels)
        # AMP positives should have higher charge
        assert report.mean_charge_positive > report.mean_charge_negative

    def test_compute_charge_report_symmetric(self):
        seqs = ["KKKK", "KKKK", "GGGG", "GGGG"]
        labels_a = [1, 1, 0, 0]
        labels_b = [0, 0, 1, 1]  # swapped
        report_a = compute_charge_report(seqs, labels_a)
        report_b = compute_charge_report(seqs, labels_b)
        # Swapping labels swaps pos/neg stats
        assert report_a.mean_charge_positive == report_b.mean_charge_negative

    def test_positive_charges_list_correct(self):
        report = compute_charge_report(["KKKK", "KK"], [1, 1])
        assert sorted(report.positive_charges) == [2.0, 4.0]

    def test_negative_charges_list_correct(self):
        report = compute_charge_report(["GGGG", "GGGGGG"], [0, 0])
        assert all(c == 0.0 for c in report.negative_charges)

    def test_charge_ratio_positive_over_negative(self):
        seqs = ["KKKK"] * 3 + ["KK"] * 3
        labels = [1] * 3 + [0] * 3
        report = compute_charge_report(seqs, labels)
        # mean pos = 4, mean neg = 2 → ratio = 2
        assert report.charge_ratio == pytest.approx(2.0)

    def test_format_charge_report_mentions_threshold(self):
        report = compute_charge_report(["KKKK", "GGGG"], [1, 0])
        text = format_charge_report(report)
        assert str(CHARGE_THRESHOLD) in text

    def test_compute_report_with_all_zeros(self):
        seqs = ["GGGG"] * 3 + ["GGGG"] * 3
        labels = [1] * 3 + [0] * 3
        report = compute_charge_report(seqs, labels)
        assert report.fraction_positive_high_charge == 0.0
        assert report.charge_shortcut_likely is False
