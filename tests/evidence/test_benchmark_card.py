"""Tests for BenchmarkCard schema — Phase C C2.

63 tests across 7 groups.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.benchmark_card import (
    BMC_PREFIX,
    VALID_EVALUATION_METRICS,
    VALID_MEASUREMENT_TARGETS,
    VALID_SPLIT_STRATEGIES,
    BenchmarkCard,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid() -> BenchmarkCard:
    return BenchmarkCard(
        bmc_id="BMC-0001",
        pipeline_version="0.10.32",
        benchmark_name="AMP Activity Prediction Benchmark v1",
        measurement_target="antimicrobial_activity_prediction",
        split_strategy="leakage_aware_split",
        cheap_enemy_baselines=[
            "charge_threshold_gte4",
            "length_10_to_40_heuristic",
        ],
        evaluation_metrics=["precision_at_k", "auc_roc"],
        known_limitations=[
            "Trained on APD3; may overfit to alpha-helical AMPs.",
            "Does not account for post-translational modifications.",
        ],
        deprecated=False,
        created_date="2024-06-01",
        last_updated_date="2024-06-01",
        notes="Validated against DRAMP3 holdout set.",
    )


def _valid_dict() -> dict:
    r = _valid()
    return {
        "bmc_id": r.bmc_id,
        "pipeline_version": r.pipeline_version,
        "benchmark_name": r.benchmark_name,
        "measurement_target": r.measurement_target,
        "split_strategy": r.split_strategy,
        "cheap_enemy_baselines": r.cheap_enemy_baselines,
        "evaluation_metrics": r.evaluation_metrics,
        "known_limitations": r.known_limitations,
        "deprecated": r.deprecated,
        "created_date": r.created_date,
        "last_updated_date": r.last_updated_date,
        "notes": r.notes,
    }


# ---------------------------------------------------------------------------
# Group 1: ValidRecord (8 tests)
# ---------------------------------------------------------------------------

class TestValidRecord:
    def test_valid_record_passes(self):
        assert _valid().validate() == []

    def test_valid_dict_passes(self):
        assert validate_dict(_valid_dict()) == []

    def test_bmc_prefix_constant(self):
        assert BMC_PREFIX == "BMC-"

    def test_valid_split_strategies_non_empty(self):
        assert len(VALID_SPLIT_STRATEGIES) >= 8

    def test_valid_measurement_targets_non_empty(self):
        assert len(VALID_MEASUREMENT_TARGETS) >= 8

    def test_valid_evaluation_metrics_non_empty(self):
        assert len(VALID_EVALUATION_METRICS) >= 8

    def test_deprecated_false_no_notes_needed(self):
        r = _valid()
        r.notes = ""
        result = r.validate()
        # warnings only, no errors
        assert all("WARNING" in msg for msg in result)

    def test_valid_record_with_multiple_metrics(self):
        r = _valid()
        r.evaluation_metrics = ["precision_at_k", "auc_roc", "mcc"]
        assert r.validate() == []


# ---------------------------------------------------------------------------
# Group 2: IDAndVersionRules (8 tests)
# ---------------------------------------------------------------------------

class TestIDAndVersionRules:
    def test_wrong_prefix_fails(self):
        r = _valid()
        r.bmc_id = "WRONG-001"
        assert any("BMC-" in e for e in r.validate())

    def test_empty_bmc_id_fails(self):
        r = _valid()
        r.bmc_id = ""
        assert any("bmc_id" in e for e in r.validate())

    def test_lowercase_prefix_fails(self):
        r = _valid()
        r.bmc_id = "bmc-001"
        assert any("BMC-" in e for e in r.validate())

    def test_empty_pipeline_version_fails(self):
        r = _valid()
        r.pipeline_version = ""
        assert any("pipeline_version" in e for e in r.validate())

    def test_empty_benchmark_name_fails(self):
        r = _valid()
        r.benchmark_name = ""
        assert any("benchmark_name" in e for e in r.validate())

    def test_whitespace_benchmark_name_fails(self):
        r = _valid()
        r.benchmark_name = "   "
        assert any("benchmark_name" in e for e in r.validate())

    def test_bmc_prefix_with_suffix_passes(self):
        r = _valid()
        r.bmc_id = "BMC-9999"
        assert r.validate() == []

    def test_validate_dict_wrong_prefix(self):
        d = _valid_dict()
        d["bmc_id"] = "WRONG-001"
        assert any("BMC-" in e for e in validate_dict(d))


# ---------------------------------------------------------------------------
# Group 3: MeasurementTargetAndSplitRules (10 tests)
# ---------------------------------------------------------------------------

class TestMeasurementTargetAndSplitRules:
    def test_invalid_measurement_target_fails(self):
        r = _valid()
        r.measurement_target = "made_up_target"
        assert any("measurement_target" in e for e in r.validate())

    def test_all_valid_measurement_targets_pass(self):
        for target in VALID_MEASUREMENT_TARGETS:
            r = _valid()
            r.measurement_target = target
            errors = [e for e in r.validate() if "measurement_target" in e]
            assert errors == [], f"Target {target!r} should be valid"

    def test_empty_measurement_target_fails(self):
        r = _valid()
        r.measurement_target = ""
        assert any("measurement_target" in e for e in r.validate())

    def test_invalid_split_strategy_fails(self):
        r = _valid()
        r.split_strategy = "random_split_99"
        assert any("split_strategy" in e for e in r.validate())

    def test_all_valid_split_strategies_pass(self):
        for strategy in VALID_SPLIT_STRATEGIES:
            r = _valid()
            r.split_strategy = strategy
            errors = [e for e in r.validate() if "split_strategy" in e]
            assert errors == [], f"Strategy {strategy!r} should be valid"

    def test_empty_split_strategy_fails(self):
        r = _valid()
        r.split_strategy = ""
        assert any("split_strategy" in e for e in r.validate())

    def test_leakage_aware_split_passes(self):
        r = _valid()
        r.split_strategy = "leakage_aware_split"
        errors = [e for e in r.validate() if "split_strategy" in e]
        assert errors == []

    def test_family_stratified_passes(self):
        r = _valid()
        r.split_strategy = "family_stratified"
        errors = [e for e in r.validate() if "split_strategy" in e]
        assert errors == []

    def test_antimicrobial_activity_prediction_target_passes(self):
        r = _valid()
        r.measurement_target = "antimicrobial_activity_prediction"
        errors = [e for e in r.validate() if "measurement_target" in e]
        assert errors == []

    def test_calibration_accuracy_target_passes(self):
        r = _valid()
        r.measurement_target = "calibration_accuracy"
        errors = [e for e in r.validate() if "measurement_target" in e]
        assert errors == []


# ---------------------------------------------------------------------------
# Group 4: CheapEnemyRules (10 tests)
# ---------------------------------------------------------------------------

class TestCheapEnemyRules:
    def test_empty_cheap_enemies_fails(self):
        r = _valid()
        r.cheap_enemy_baselines = []
        assert any("cheap_enemy_baselines" in e for e in r.validate())

    def test_one_cheap_enemy_passes_with_warning(self):
        r = _valid()
        r.cheap_enemy_baselines = ["charge_threshold_gte4"]
        result = r.validate()
        assert all("WARNING" in msg for msg in result)

    def test_one_cheap_enemy_warning_mentions_two(self):
        r = _valid()
        r.cheap_enemy_baselines = ["charge_threshold_gte4"]
        result = r.validate()
        assert any("WARNING" in msg and "cheap_enemy" in msg for msg in result)

    def test_two_cheap_enemies_no_warning(self):
        r = _valid()
        r.cheap_enemy_baselines = ["charge_threshold", "length_heuristic"]
        result = r.validate()
        assert not any("cheap_enemy" in msg for msg in result)

    def test_empty_string_enemy_fails(self):
        r = _valid()
        r.cheap_enemy_baselines = [""]
        assert any("cheap_enemy_baselines" in e for e in r.validate())

    def test_whitespace_enemy_fails(self):
        r = _valid()
        r.cheap_enemy_baselines = ["   "]
        assert any("cheap_enemy_baselines" in e for e in r.validate())

    def test_multiple_cheap_enemies_pass(self):
        r = _valid()
        r.cheap_enemy_baselines = ["enemy1", "enemy2", "enemy3"]
        errors = [e for e in r.validate() if "cheap_enemy" in e and "WARNING" not in e]
        assert errors == []

    def test_cheap_enemy_names_are_descriptive(self):
        r = _valid()
        for enemy in r.cheap_enemy_baselines:
            assert len(enemy.strip()) > 0

    def test_dict_empty_cheap_enemies_fails(self):
        d = _valid_dict()
        d["cheap_enemy_baselines"] = []
        assert any("cheap_enemy" in e for e in validate_dict(d))

    def test_non_string_enemy_fails(self):
        r = _valid()
        r.cheap_enemy_baselines = [123]  # type: ignore
        errors = r.validate()
        # 123 is not a string with strip(), should error
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# Group 5: EvalMetricsAndLimitations (10 tests)
# ---------------------------------------------------------------------------

class TestEvalMetricsAndLimitations:
    def test_empty_evaluation_metrics_fails(self):
        r = _valid()
        r.evaluation_metrics = []
        assert any("evaluation_metrics" in e for e in r.validate())

    def test_invalid_metric_fails(self):
        r = _valid()
        r.evaluation_metrics = ["made_up_metric"]
        assert any("evaluation_metrics" in e for e in r.validate())

    def test_all_valid_metrics_pass(self):
        for metric in VALID_EVALUATION_METRICS:
            r = _valid()
            r.evaluation_metrics = [metric]
            errors = [e for e in r.validate() if "evaluation_metrics" in e and "WARNING" not in e]
            assert errors == [], f"Metric {metric!r} should be valid"

    def test_empty_known_limitations_fails(self):
        r = _valid()
        r.known_limitations = []
        assert any("known_limitations" in e for e in r.validate())

    def test_one_known_limitation_warning(self):
        r = _valid()
        r.known_limitations = ["Only tested on alpha-helical AMPs."]
        result = r.validate()
        # May have warning about only one limitation
        assert all("WARNING" in msg for msg in result) or result == []

    def test_two_known_limitations_no_warning(self):
        r = _valid()
        r.known_limitations = [
            "Only tested on alpha-helical AMPs.",
            "No temporal split applied.",
        ]
        result = r.validate()
        assert not any("known_limitations" in msg for msg in result)

    def test_empty_limitation_string_fails(self):
        r = _valid()
        r.known_limitations = [""]
        assert any("known_limitations" in e for e in r.validate())

    def test_precision_at_k_metric_passes(self):
        r = _valid()
        r.evaluation_metrics = ["precision_at_k"]
        errors = [e for e in r.validate() if "evaluation_metrics" in e and "WARNING" not in e]
        assert errors == []

    def test_auc_roc_metric_passes(self):
        r = _valid()
        r.evaluation_metrics = ["auc_roc"]
        errors = [e for e in r.validate() if "evaluation_metrics" in e and "WARNING" not in e]
        assert errors == []

    def test_calibration_error_metric_passes(self):
        r = _valid()
        r.evaluation_metrics = ["calibration_error"]
        errors = [e for e in r.validate() if "evaluation_metrics" in e and "WARNING" not in e]
        assert errors == []


# ---------------------------------------------------------------------------
# Group 6: DeprecatedAndDates (9 tests)
# ---------------------------------------------------------------------------

class TestDeprecatedAndDates:
    def test_deprecated_true_requires_notes(self):
        r = _valid()
        r.deprecated = True
        r.notes = ""
        assert any("deprecated" in e for e in r.validate())

    def test_deprecated_true_with_notes_passes(self):
        r = _valid()
        r.deprecated = True
        r.notes = "Superseded by BMC-0002 which uses leakage-aware split."
        assert r.validate() == []

    def test_deprecated_false_empty_notes_only_warning(self):
        r = _valid()
        r.deprecated = False
        r.notes = ""
        result = r.validate()
        assert all("WARNING" in msg for msg in result)

    def test_invalid_created_date_fails(self):
        r = _valid()
        r.created_date = "June 2024"
        assert any("created_date" in e for e in r.validate())

    def test_valid_created_date_passes(self):
        r = _valid()
        r.created_date = "2024-01-15"
        assert r.validate() == []

    def test_invalid_last_updated_date_fails(self):
        r = _valid()
        r.last_updated_date = "not-a-date"
        assert any("last_updated_date" in e for e in r.validate())

    def test_notes_exceeds_limit_fails(self):
        r = _valid()
        r.notes = "x" * 501
        assert any("notes" in e for e in r.validate())

    def test_notes_exactly_at_limit_passes(self):
        r = _valid()
        r.notes = "x" * 500
        errors = [e for e in r.validate() if "notes" in e and "WARNING" not in e]
        assert errors == []

    def test_datetime_format_date_passes(self):
        r = _valid()
        r.created_date = "2024-06-01T12:00:00Z"
        assert r.validate() == []


# ---------------------------------------------------------------------------
# Group 7: ValidateDictEdgeCases (8 tests)
# ---------------------------------------------------------------------------

class TestValidateDictEdgeCases:
    def test_empty_dict_fails(self):
        assert len(validate_dict({})) > 0

    def test_valid_dict_passes(self):
        assert validate_dict(_valid_dict()) == []

    def test_missing_bmc_id_fails(self):
        d = _valid_dict()
        del d["bmc_id"]
        assert any("bmc_id" in e for e in validate_dict(d))

    def test_missing_cheap_enemies_fails(self):
        d = _valid_dict()
        del d["cheap_enemy_baselines"]
        assert any("cheap_enemy" in e for e in validate_dict(d))

    def test_missing_known_limitations_fails(self):
        d = _valid_dict()
        del d["known_limitations"]
        assert any("known_limitations" in e for e in validate_dict(d))

    def test_missing_deprecated_defaults_false(self):
        d = _valid_dict()
        del d["deprecated"]
        # deprecated defaults False → no error for notes
        result = validate_dict(d)
        assert all("WARNING" in msg for msg in result) or result == []

    def test_construction_error_returns_error_list(self):
        result = validate_dict({"bmc_id": None})
        assert len(result) > 0

    def test_dict_with_extra_fields_passes(self):
        d = _valid_dict()
        d["extra_field"] = "extra_value"
        assert validate_dict(d) == []
