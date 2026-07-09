"""Tests for benchmark card module."""
from pathlib import Path

import pytest

from openamp_foundry.benchmarks.benchmark_card import (
    BenchmarkCard,
    make_benchmark_card,
    validate_benchmark_card,
    benchmark_card_summary,
)


def _valid_card() -> BenchmarkCard:
    return make_benchmark_card(
        benchmark_id="bench-auroc-001",
        benchmark_name="AMP vs Decoy AUROC",
        metric="AUROC",
        metric_value=0.82,
        baseline_name="random",
        baseline_value=0.50,
        dataset="APD3",
        dataset_size=500,
    )


class TestMakeBenchmarkCard:
    def test_returns_benchmark_card(self):
        card = make_benchmark_card(
            benchmark_id="bench-001",
            benchmark_name="Test Benchmark",
            metric="AUROC",
            metric_value=0.75,
            baseline_name="random",
            baseline_value=0.50,
            dataset="TestSet",
            dataset_size=100,
        )
        assert isinstance(card, BenchmarkCard)

    def test_delta_computed_correctly(self):
        card = make_benchmark_card(
            benchmark_id="bench-002",
            benchmark_name="Delta Test",
            metric="AUROC",
            metric_value=0.85,
            baseline_name="random",
            baseline_value=0.50,
            dataset="TestSet",
            dataset_size=100,
        )
        assert card.delta == 0.35

    def test_beats_baseline_true_when_delta_positive(self):
        card = make_benchmark_card(
            benchmark_id="bench-003",
            benchmark_name="Beats Test",
            metric="AUROC",
            metric_value=0.90,
            baseline_name="random",
            baseline_value=0.50,
            dataset="TestSet",
            dataset_size=100,
        )
        assert card.beats_baseline is True

    def test_beats_baseline_false_when_delta_non_positive(self):
        card = make_benchmark_card(
            benchmark_id="bench-004",
            benchmark_name="Not Beats",
            metric="AUROC",
            metric_value=0.40,
            baseline_name="random",
            baseline_value=0.50,
            dataset="TestSet",
            dataset_size=100,
        )
        assert card.beats_baseline is False

    def test_dry_lab_only_always_true(self):
        card = _valid_card()
        assert card.dry_lab_only is True

        card2 = make_benchmark_card(
            benchmark_id="bench-005",
            benchmark_name="Another",
            metric="AUPRC",
            metric_value=0.70,
            baseline_name="random",
            baseline_value=0.50,
            dataset="TestSet",
            dataset_size=50,
        )
        assert card2.dry_lab_only is True


class TestValidateBenchmarkCard:
    def test_valid_card_returns_empty_list(self):
        card = _valid_card()
        errors = validate_benchmark_card(card)
        assert errors == []

    def test_catches_empty_benchmark_id(self):
        card = _valid_card()
        card.benchmark_id = ""
        errors = validate_benchmark_card(card)
        assert any("benchmark_id" in e for e in errors)

    def test_catches_empty_metric(self):
        card = _valid_card()
        card.metric = ""
        errors = validate_benchmark_card(card)
        assert any("metric" in e for e in errors)

    def test_catches_dataset_size_less_than_one(self):
        card = _valid_card()
        card.dataset_size = 0
        errors = validate_benchmark_card(card)
        assert any("dataset_size" in e for e in errors)

    def test_catches_wrong_delta(self):
        card = _valid_card()
        card.delta = 999.0
        errors = validate_benchmark_card(card)
        assert any("delta" in e for e in errors)

    def test_catches_wrong_beats_baseline(self):
        card = _valid_card()
        card.beats_baseline = False
        errors = validate_benchmark_card(card)
        assert any("beats_baseline" in e for e in errors)

    def test_catches_dry_lab_only_false(self):
        card = _valid_card()
        card.dry_lab_only = False
        errors = validate_benchmark_card(card)
        assert any("dry_lab_only" in e for e in errors)

    def test_catches_empty_dataset(self):
        card = _valid_card()
        card.dataset = ""
        errors = validate_benchmark_card(card)
        assert any("dataset" in e for e in errors)

    def test_catches_empty_baseline_name(self):
        card = _valid_card()
        card.baseline_name = ""
        errors = validate_benchmark_card(card)
        assert any("baseline_name" in e for e in errors)

    def test_catches_empty_benchmark_name(self):
        card = _valid_card()
        card.benchmark_name = ""
        errors = validate_benchmark_card(card)
        assert any("benchmark_name" in e for e in errors)


class TestBenchmarkCardSummary:
    def test_total_correct(self):
        c1 = _valid_card()
        c2 = _valid_card()
        c2.benchmark_id = "bench-002"
        c2.metric_value = 0.40
        c2.delta = -0.10
        c2.beats_baseline = False
        summary = benchmark_card_summary([c1, c2])
        assert summary["total"] == 2

    def test_beats_baseline_count_correct(self):
        c1 = _valid_card()
        c2 = _valid_card()
        c2.benchmark_id = "bench-002"
        c2.metric_value = 0.40
        c2.delta = -0.10
        c2.beats_baseline = False
        c3 = _valid_card()
        c3.benchmark_id = "bench-003"
        summary = benchmark_card_summary([c1, c2, c3])
        assert summary["beats_baseline_count"] == 2
        assert summary["fails_baseline_count"] == 1

    def test_dry_lab_only_true(self):
        card = _valid_card()
        summary = benchmark_card_summary([card])
        assert summary["dry_lab_only"] is True


class TestSchemaFileExists:
    def test_schema_file_exists(self):
        schema_path = Path("schemas/benchmark_card.schema.json")
        assert schema_path.exists(), (
            f"Schema file not found at {schema_path}"
        )
