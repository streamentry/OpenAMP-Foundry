"""Tests for failure mode similarity report schema (Phase F F8).

5 test classes, 63 tests total.
"""

import pytest

from openamp_foundry.evidence.failure_mode_similarity_report import (
    FAILURE_MODE_SIMILARITY_REPORT_ID_PREFIX,
    FRACTION_TOLERANCE,
    HIGH_SIMILARITY_THRESHOLD,
    MIN_REJECTED_CANDIDATES_FOR_BENCHMARK,
    PATTERN_REPEATED_THRESHOLD,
    VALID_BENCHMARK_STATUSES,
    VALID_FAILURE_MODE_CATEGORIES,
    VALID_SIMILARITY_ASSESSMENT_STATUSES,
    FailureModeSimilarityReport,
    format_failure_mode_similarity_report,
    validate_failure_mode_similarity_report,
)


def _valid_report(**kwargs) -> FailureModeSimilarityReport:
    defaults = dict(
        report_id="FMS-001",
        batch_id="BATCH-001",
        n_rejected_candidates=20,
        n_with_known_failure_mode=8,
        fraction_matching_known_failure_mode=0.40,
        top_failure_mode_category="hemolysis_risk",
        top_failure_mode_fraction=0.30,
        similarity_assessment_status="moderate_similarity",
        pattern_repeated_flag=False,
        benchmark_status="complete",
        dry_lab_only=True,
        calibration_action_recommended=False,
        notes="Routine similarity benchmark",
        created_at="2026-01-01",
    )
    defaults.update(kwargs)
    return FailureModeSimilarityReport(**defaults)


# ---------------------------------------------------------------------------
# Class 1: Constants (10 tests)
# ---------------------------------------------------------------------------

class TestFailureModeSimilarityReportConstants:
    def test_prefix_value(self):
        assert FAILURE_MODE_SIMILARITY_REPORT_ID_PREFIX == "FMS-"

    def test_high_similarity_threshold_in_range(self):
        assert 0.0 < HIGH_SIMILARITY_THRESHOLD < 1.0

    def test_pattern_repeated_threshold_above_high_similarity(self):
        assert PATTERN_REPEATED_THRESHOLD >= HIGH_SIMILARITY_THRESHOLD

    def test_min_rejected_candidates_positive(self):
        assert MIN_REJECTED_CANDIDATES_FOR_BENCHMARK > 0

    def test_fraction_tolerance_small(self):
        assert FRACTION_TOLERANCE < 0.1

    def test_valid_failure_mode_categories_nonempty(self):
        assert len(VALID_FAILURE_MODE_CATEGORIES) >= 8

    def test_valid_similarity_statuses_nonempty(self):
        assert len(VALID_SIMILARITY_ASSESSMENT_STATUSES) >= 4

    def test_valid_benchmark_statuses_nonempty(self):
        assert len(VALID_BENCHMARK_STATUSES) >= 3

    def test_hemolysis_risk_in_failure_categories(self):
        assert "hemolysis_risk" in VALID_FAILURE_MODE_CATEGORIES

    def test_insufficient_data_in_similarity_statuses(self):
        assert "insufficient_data" in VALID_SIMILARITY_ASSESSMENT_STATUSES


# ---------------------------------------------------------------------------
# Class 2: Validation happy and sad paths (20 tests)
# ---------------------------------------------------------------------------

class TestValidateFailureModeSimilarityReport:
    def test_valid_report_has_no_errors(self):
        r = _valid_report()
        assert validate_failure_mode_similarity_report(r) == []

    def test_bad_prefix_rejected(self):
        r = _valid_report(report_id="BAD-001")
        errs = validate_failure_mode_similarity_report(r)
        assert any("report_id" in e for e in errs)

    def test_invalid_failure_mode_category_rejected(self):
        r = _valid_report(top_failure_mode_category="unknown_mode")
        errs = validate_failure_mode_similarity_report(r)
        assert any("top_failure_mode_category" in e for e in errs)

    def test_invalid_similarity_status_rejected(self):
        r = _valid_report(similarity_assessment_status="great")
        errs = validate_failure_mode_similarity_report(r)
        assert any("similarity_assessment_status" in e for e in errs)

    def test_invalid_benchmark_status_rejected(self):
        r = _valid_report(benchmark_status="published")
        errs = validate_failure_mode_similarity_report(r)
        assert any("benchmark_status" in e for e in errs)

    def test_fraction_above_one_rejected(self):
        r = _valid_report(fraction_matching_known_failure_mode=1.1,
                          n_with_known_failure_mode=22)
        errs = validate_failure_mode_similarity_report(r)
        assert any("fraction_matching_known_failure_mode" in e for e in errs)

    def test_fraction_below_zero_rejected(self):
        r = _valid_report(fraction_matching_known_failure_mode=-0.1,
                          n_with_known_failure_mode=0)
        errs = validate_failure_mode_similarity_report(r)
        assert any("fraction_matching_known_failure_mode" in e for e in errs)

    def test_fraction_inconsistency_rejected(self):
        r = _valid_report(
            n_rejected_candidates=20,
            n_with_known_failure_mode=8,
            fraction_matching_known_failure_mode=0.99,
        )
        errs = validate_failure_mode_similarity_report(r)
        assert any("fraction_matching_known_failure_mode" in e for e in errs)

    def test_insufficient_candidates_requires_status(self):
        r = _valid_report(
            n_rejected_candidates=2,
            n_with_known_failure_mode=1,
            fraction_matching_known_failure_mode=0.5,
            similarity_assessment_status="low_similarity",
        )
        errs = validate_failure_mode_similarity_report(r)
        assert any("insufficient_data" in e for e in errs)

    def test_insufficient_candidates_with_correct_status_ok(self):
        r = _valid_report(
            n_rejected_candidates=2,
            n_with_known_failure_mode=1,
            fraction_matching_known_failure_mode=0.5,
            similarity_assessment_status="insufficient_data",
        )
        errs = validate_failure_mode_similarity_report(r)
        assert not any("insufficient_data" in e for e in errs)

    def test_dry_lab_only_false_rejected(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_failure_mode_similarity_report(r)
        assert any("dry_lab_only" in e for e in errs)

    def test_pattern_repeated_flag_must_be_true_at_high_fraction(self):
        high_fraction = PATTERN_REPEATED_THRESHOLD + 0.05
        n_total = 20
        n_matching = round(high_fraction * n_total)
        actual_fraction = n_matching / n_total
        r = _valid_report(
            n_rejected_candidates=n_total,
            n_with_known_failure_mode=n_matching,
            fraction_matching_known_failure_mode=round(actual_fraction, 4),
            similarity_assessment_status="pattern_repeated",
            pattern_repeated_flag=False,
        )
        errs = validate_failure_mode_similarity_report(r)
        assert any("pattern_repeated_flag" in e for e in errs)

    def test_pattern_repeated_flag_true_at_high_fraction_passes(self):
        high_fraction = PATTERN_REPEATED_THRESHOLD + 0.05
        n_total = 20
        n_matching = round(high_fraction * n_total)
        actual_fraction = n_matching / n_total
        r = _valid_report(
            n_rejected_candidates=n_total,
            n_with_known_failure_mode=n_matching,
            fraction_matching_known_failure_mode=round(actual_fraction, 4),
            similarity_assessment_status="pattern_repeated",
            pattern_repeated_flag=True,
        )
        errs = validate_failure_mode_similarity_report(r)
        assert not any("pattern_repeated_flag" in e for e in errs)

    def test_blank_batch_id_rejected(self):
        r = _valid_report(batch_id="   ")
        errs = validate_failure_mode_similarity_report(r)
        assert any("batch_id" in e for e in errs)

    def test_blank_created_at_rejected(self):
        r = _valid_report(created_at="")
        errs = validate_failure_mode_similarity_report(r)
        assert any("created_at" in e for e in errs)

    def test_n_with_failure_mode_exceeds_rejected_rejected(self):
        r = _valid_report(n_rejected_candidates=10, n_with_known_failure_mode=15,
                          fraction_matching_known_failure_mode=0.40)
        errs = validate_failure_mode_similarity_report(r)
        assert any("exceed" in e for e in errs)

    def test_all_failure_mode_categories_valid(self):
        for cat in VALID_FAILURE_MODE_CATEGORIES:
            r = _valid_report(top_failure_mode_category=cat)
            errs = validate_failure_mode_similarity_report(r)
            assert not any("top_failure_mode_category" in e for e in errs), cat

    def test_all_similarity_statuses_valid_with_sufficient_data(self):
        for status in VALID_SIMILARITY_ASSESSMENT_STATUSES:
            if status == "insufficient_data":
                continue
            r = _valid_report(similarity_assessment_status=status)
            errs = validate_failure_mode_similarity_report(r)
            assert not any("similarity_assessment_status" in e for e in errs), status

    def test_all_benchmark_statuses_valid(self):
        for bs in VALID_BENCHMARK_STATUSES:
            r = _valid_report(benchmark_status=bs)
            errs = validate_failure_mode_similarity_report(r)
            assert not any("benchmark_status" in e for e in errs), bs

    def test_top_failure_mode_fraction_above_one_rejected(self):
        r = _valid_report(top_failure_mode_fraction=1.1)
        errs = validate_failure_mode_similarity_report(r)
        assert any("top_failure_mode_fraction" in e for e in errs)


# ---------------------------------------------------------------------------
# Class 3: Edge cases (13 tests)
# ---------------------------------------------------------------------------

class TestFailureModeSimilarityReportEdgeCases:
    def test_zero_rejected_candidates_ok_with_zero_matching(self):
        r = _valid_report(
            n_rejected_candidates=0,
            n_with_known_failure_mode=0,
            fraction_matching_known_failure_mode=0.0,
            similarity_assessment_status="insufficient_data",
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_exactly_min_candidates_ok(self):
        n = MIN_REJECTED_CANDIDATES_FOR_BENCHMARK
        r = _valid_report(
            n_rejected_candidates=n,
            n_with_known_failure_mode=1,
            fraction_matching_known_failure_mode=round(1 / n, 4),
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_one_below_min_requires_insufficient_data(self):
        n = MIN_REJECTED_CANDIDATES_FOR_BENCHMARK - 1
        r = _valid_report(
            n_rejected_candidates=n,
            n_with_known_failure_mode=0,
            fraction_matching_known_failure_mode=0.0,
            similarity_assessment_status="low_similarity",
        )
        errs = validate_failure_mode_similarity_report(r)
        assert any("insufficient_data" in e for e in errs)

    def test_all_candidates_have_failure_mode(self):
        r = _valid_report(
            n_rejected_candidates=10,
            n_with_known_failure_mode=10,
            fraction_matching_known_failure_mode=1.0,
            similarity_assessment_status="pattern_repeated",
            pattern_repeated_flag=True,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_no_candidates_have_failure_mode(self):
        r = _valid_report(
            n_rejected_candidates=10,
            n_with_known_failure_mode=0,
            fraction_matching_known_failure_mode=0.0,
            similarity_assessment_status="low_similarity",
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_calibration_action_recommended_true_ok(self):
        r = _valid_report(calibration_action_recommended=True)
        assert validate_failure_mode_similarity_report(r) == []

    def test_calibration_action_recommended_false_ok(self):
        r = _valid_report(calibration_action_recommended=False)
        assert validate_failure_mode_similarity_report(r) == []

    def test_empty_notes_ok(self):
        r = _valid_report(notes="")
        assert validate_failure_mode_similarity_report(r) == []

    def test_prefix_case_sensitive(self):
        r = _valid_report(report_id="fms-001")
        errs = validate_failure_mode_similarity_report(r)
        assert any("report_id" in e for e in errs)

    def test_fraction_consistency_with_tolerance(self):
        r = _valid_report(
            n_rejected_candidates=7,
            n_with_known_failure_mode=3,
            fraction_matching_known_failure_mode=0.4286,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_high_similarity_status_ok_without_pattern_repeat(self):
        r = _valid_report(
            similarity_assessment_status="high_similarity",
            pattern_repeated_flag=False,
            fraction_matching_known_failure_mode=0.70,
            n_with_known_failure_mode=14,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_pattern_repeated_status_with_flag_true_ok(self):
        r = _valid_report(
            n_rejected_candidates=10,
            n_with_known_failure_mode=9,
            fraction_matching_known_failure_mode=0.9,
            similarity_assessment_status="pattern_repeated",
            pattern_repeated_flag=True,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_top_failure_mode_fraction_zero_ok(self):
        r = _valid_report(top_failure_mode_fraction=0.0)
        assert validate_failure_mode_similarity_report(r) == []


# ---------------------------------------------------------------------------
# Class 4: Format output (10 tests)
# ---------------------------------------------------------------------------

class TestFormatFailureModeSimilarityReport:
    def test_format_contains_report_id(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "FMS-001" in out

    def test_format_contains_batch_id(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "BATCH-001" in out

    def test_format_contains_rejected_count(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "20" in out

    def test_format_contains_failure_mode_category(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "hemolysis_risk" in out

    def test_format_contains_similarity_status(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "moderate_similarity" in out

    def test_format_pattern_repeated_warning_when_flag_true(self):
        r = _valid_report(
            n_rejected_candidates=10,
            n_with_known_failure_mode=9,
            fraction_matching_known_failure_mode=0.9,
            similarity_assessment_status="pattern_repeated",
            pattern_repeated_flag=True,
        )
        out = format_failure_mode_similarity_report(r)
        assert "WARNING" in out or "pattern" in out.lower()

    def test_format_calibration_action_note_when_true(self):
        r = _valid_report(calibration_action_recommended=True)
        out = format_failure_mode_similarity_report(r)
        assert "calibration" in out.lower() or "ACTION" in out

    def test_format_contains_dry_lab_only(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "True" in out

    def test_format_includes_fraction_percentage(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert "%" in out

    def test_format_is_string(self):
        r = _valid_report()
        out = format_failure_mode_similarity_report(r)
        assert isinstance(out, str)
        assert len(out) > 50


# ---------------------------------------------------------------------------
# Class 5: Dry-lab enforcement (10 tests)
# ---------------------------------------------------------------------------

class TestFailureModeSimilarityReportDryLabEnforcement:
    def test_dry_lab_only_true_required(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_failure_mode_similarity_report(r)
        assert len(errs) >= 1

    def test_dry_lab_only_true_passes(self):
        r = _valid_report(dry_lab_only=True)
        assert validate_failure_mode_similarity_report(r) == []

    def test_error_message_mentions_dry_lab(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_failure_mode_similarity_report(r)
        assert any("dry_lab" in e for e in errs)

    def test_fms_prefix_is_mandatory(self):
        r = _valid_report(report_id="FMR-001")
        errs = validate_failure_mode_similarity_report(r)
        assert any("FMS-" in e for e in errs)

    def test_n_with_failure_mode_counts_consistency(self):
        r = _valid_report(
            n_rejected_candidates=10,
            n_with_known_failure_mode=5,
            fraction_matching_known_failure_mode=0.5,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_large_batch_ok(self):
        r = _valid_report(
            n_rejected_candidates=500,
            n_with_known_failure_mode=100,
            fraction_matching_known_failure_mode=0.2,
        )
        assert validate_failure_mode_similarity_report(r) == []

    def test_dual_use_concern_category_ok(self):
        r = _valid_report(top_failure_mode_category="dual_use_concern")
        assert validate_failure_mode_similarity_report(r) == []

    def test_charge_shortcut_category_ok(self):
        r = _valid_report(top_failure_mode_category="charge_shortcut")
        assert validate_failure_mode_similarity_report(r) == []

    def test_notes_with_toy_candidate_ok(self):
        r = _valid_report(notes="Tested on TOY-001 through TOY-050; all dry-lab only.")
        assert validate_failure_mode_similarity_report(r) == []

    def test_format_shows_dry_lab_true(self):
        r = _valid_report(dry_lab_only=True)
        out = format_failure_mode_similarity_report(r)
        assert "True" in out
