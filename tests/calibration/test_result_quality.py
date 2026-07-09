"""Tests for result-quality flag propagation into calibration engine."""
from __future__ import annotations

import pytest
from openamp_foundry.calibration.result_quality import (
    QUALITY_FLAGS,
    EXCLUDED_FLAGS,
    ResultQualityReport,
    assess_result_quality,
    filter_results_for_calibration,
)


class TestAssessResultQuality:
    def test_high_quality_no_flags(self):
        report = assess_result_quality("AMP001", [])
        assert report.quality_level == "high"
        assert report.can_drive_update is True
        assert report.propagation_action == "include"
        assert report.explanation != ""

    def test_contamination_excluded(self):
        report = assess_result_quality("AMP002", ["contamination"])
        assert report.quality_level == "excluded"
        assert report.can_drive_update is False
        assert report.propagation_action == "exclude"
        assert report.explanation != ""

    def test_assay_interference_excluded(self):
        report = assess_result_quality("AMP003", ["assay_interference"])
        assert report.quality_level == "excluded"
        assert report.can_drive_update is False
        assert report.propagation_action == "exclude"
        assert report.explanation != ""

    def test_two_minor_flags_excluded_low(self):
        report = assess_result_quality("AMP004", ["replicate_disagreement", "borderline_threshold"])
        assert report.quality_level == "low"
        assert report.can_drive_update is False
        assert report.propagation_action == "exclude"
        assert report.explanation != ""

    def test_one_minor_flag_acceptable(self):
        report = assess_result_quality("AMP005", ["protocol_deviation"])
        assert report.quality_level == "acceptable"
        assert report.can_drive_update is True
        assert report.propagation_action == "include_with_caution"
        assert report.explanation != ""

    def test_can_drive_update_true_high(self):
        report = assess_result_quality("AMP006", [])
        assert report.can_drive_update is True

    def test_can_drive_update_true_acceptable(self):
        report = assess_result_quality("AMP007", ["ambiguous_activity"])
        assert report.can_drive_update is True

    def test_can_drive_update_false_excluded(self):
        report = assess_result_quality("AMP008", ["contamination"])
        assert report.can_drive_update is False

    def test_can_drive_update_false_low(self):
        report = assess_result_quality("AMP009", ["low_sample_quality", "protocol_deviation"])
        assert report.can_drive_update is False

    def test_dry_lab_only_always_true(self):
        for flags in ([], ["contamination"], ["protocol_deviation"],
                      ["replicate_disagreement", "borderline_threshold"]):
            report = assess_result_quality("AMP010", flags)
            assert report.dry_lab_only is True

    def test_unknown_flag_raises(self):
        with pytest.raises(ValueError, match="Unknown quality flags"):
            assess_result_quality("AMP011", ["nonexistent_flag"])

    def test_explanation_non_empty(self):
        report = assess_result_quality("AMP012", [])
        assert len(report.explanation) > 0

    def test_explanation_mentions_candidate_id(self):
        report = assess_result_quality("AMP013", ["contamination"])
        assert "AMP013" in report.explanation

    def test_to_dict_includes_all_fields(self):
        report = assess_result_quality("AMP014", ["missing_negative_control"])
        d = report.to_dict()
        assert d["candidate_id"] == "AMP014"
        assert d["quality_level"] == "acceptable"
        assert d["can_drive_update"] is True
        assert d["propagation_action"] == "include_with_caution"
        assert d["dry_lab_only"] is True
        assert "explanation" in d
        assert d["flags"] == ["missing_negative_control"]

    def test_contamination_with_other_flags_still_excluded(self):
        report = assess_result_quality("AMP015", ["contamination", "protocol_deviation"])
        assert report.quality_level == "excluded"
        assert report.can_drive_update is False

    def test_assay_interference_with_other_flags_still_excluded(self):
        report = assess_result_quality("AMP016", ["assay_interference", "ambiguous_activity"])
        assert report.quality_level == "excluded"
        assert report.can_drive_update is False


class TestFilterResultsForCalibration:
    def test_empty_results(self):
        result = filter_results_for_calibration([])
        assert result["summary"]["total"] == 0
        assert result["can_drive_update_count"] == 0
        assert result["dry_lab_only"] is True

    def test_summary_counts(self):
        results = [
            {"candidate_id": "A", "flags": []},
            {"candidate_id": "B", "flags": ["contamination"]},
            {"candidate_id": "C", "flags": ["protocol_deviation"]},
            {"candidate_id": "D", "flags": ["low_sample_quality", "replicate_disagreement"]},
        ]
        result = filter_results_for_calibration(results)
        assert result["summary"]["total"] == 4
        assert result["summary"]["included"] == 1
        assert result["summary"]["included_with_caution"] == 1
        assert result["summary"]["excluded"] == 2
        assert result["can_drive_update_count"] == 2

    def test_included_has_correct_action(self):
        results = [
            {"candidate_id": "X", "flags": []},
        ]
        result = filter_results_for_calibration(results)
        assert len(result["included"]) == 1
        assert result["included"][0]["candidate_id"] == "X"
        assert result["included"][0]["propagation_action"] == "include"

    def test_included_with_caution_has_correct_action(self):
        results = [
            {"candidate_id": "Y", "flags": ["ambiguous_activity"]},
        ]
        result = filter_results_for_calibration(results)
        assert len(result["included_with_caution"]) == 1
        assert result["included_with_caution"][0]["candidate_id"] == "Y"
        assert result["included_with_caution"][0]["propagation_action"] == "include_with_caution"

    def test_excluded_has_correct_action(self):
        results = [
            {"candidate_id": "Z", "flags": ["contamination"]},
        ]
        result = filter_results_for_calibration(results)
        assert len(result["excluded"]) == 1
        assert result["excluded"][0]["candidate_id"] == "Z"
        assert result["excluded"][0]["propagation_action"] == "exclude"

    def test_can_drive_update_count_matches(self):
        results = [
            {"candidate_id": "A", "flags": []},
            {"candidate_id": "B", "flags": ["protocol_deviation"]},
            {"candidate_id": "C", "flags": ["contamination"]},
            {"candidate_id": "D", "flags": ["low_sample_quality", "replicate_disagreement"]},
        ]
        result = filter_results_for_calibration(results)
        assert result["can_drive_update_count"] == 2

    def test_missing_flags_defaults_to_empty(self):
        results = [
            {"candidate_id": "M", "flags": None},
        ]
        result = filter_results_for_calibration(results)
        assert result["summary"]["included"] == 1


class TestExcludedFlags:
    def test_excluded_flags_set(self):
        assert "contamination" in EXCLUDED_FLAGS
        assert "assay_interference" in EXCLUDED_FLAGS

    def test_excluded_flags_size(self):
        assert len(EXCLUDED_FLAGS) == 2


class TestQualityFlags:
    def test_all_flags_have_descriptions(self):
        for flag, desc in QUALITY_FLAGS.items():
            assert isinstance(flag, str)
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_known_flags_count(self):
        assert len(QUALITY_FLAGS) == 8
