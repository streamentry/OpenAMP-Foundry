"""Tests for the active-learning strategy comparison report.

All data is synthetic. Tests verify code-path integrity, structure, and
honest comparison mechanics — not biological sampling efficiency.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ── Helpers ───────────────────────────────────────────────────────────


def _check_report_shape(report: dict) -> None:
    """Assert all required top-level fields exist."""
    required = [
        "version", "pool_size", "n_active_total", "n_hidden_actives",
        "batch_size", "max_rounds", "results", "ranked_by_recall",
        "best_strategy", "production_strategy",
        "production_outperforms_random", "notes",
    ]
    for field in required:
        assert field in report, f"Missing field: {field}"


def _check_result_shape(result: dict) -> None:
    """Assert all required per-strategy result fields exist."""
    required = [
        "strategy_name", "rounds_to_first_recovery", "final_recall",
        "n_hidden_recovered", "n_hidden_actives", "total_rounds_run", "notes",
    ]
    for field in required:
        assert field in result, f"Missing result field: {field}"


# ── Tests ─────────────────────────────────────────────────────────────


class TestStrategyComparisonReport:
    """Tests for the strategy comparison report generation."""

    def test_report_has_all_strategies(self):
        """Report contains results for all 5 strategies."""
        from openamp_foundry.active_learning.strategy_comparison import (
            STRATEGY_WEIGHTS,
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        d = report.to_dict()
        strategy_names = {r["strategy_name"] for r in d["results"]}
        expected = set(STRATEGY_WEIGHTS.keys())
        assert strategy_names == expected, (
            f"Missing strategies: {expected - strategy_names}"
        )

    def test_report_required_fields(self):
        """Report has all required top-level fields."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        _check_report_shape(report.to_dict())

    def test_per_strategy_required_fields(self):
        """Each strategy result has all required fields."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        for r in report.to_dict()["results"]:
            _check_result_shape(r)

    def test_recall_in_valid_range(self):
        """Final recall is between 0 and 1 for all strategies."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        for r in report.to_dict()["results"]:
            assert 0.0 <= r["final_recall"] <= 1.0, (
                f"Recall {r['final_recall']} out of range for {r['strategy_name']}"
            )

    def test_ranked_by_recall_matches_results(self):
        """Ranked strategy list matches sorted results by recall descending."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        d = report.to_dict()
        results = {r["strategy_name"]: r["final_recall"] for r in d["results"]}
        ranked = d["ranked_by_recall"]
        assert len(ranked) == len(results)
        for i in range(len(ranked) - 1):
            assert results[ranked[i]] >= results[ranked[i + 1]], (
                f"Ranking order wrong: {ranked[i]} ({results[ranked[i]]}) "
                f"should be >= {ranked[i + 1]} ({results[ranked[i + 1]]})"
            )

    def test_production_strategy_is_combined(self):
        """The production strategy is 'combined'."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        assert report.production_strategy == "combined"

    def test_best_strategy_not_null(self):
        """Best strategy is identified."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        assert report.best_strategy is not None
        assert report.best_strategy in [r.strategy_name for r in report.results]

    def test_exploitation_recovers_actives_fast(self):
        """Exploitation should recover hidden actives quickly because they
        have higher ensemble scores."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=50, n_active=10, n_hidden_actives=3,
            batch_size=5, max_rounds=5,
        )
        exploitation = next(
            r for r in report.results if r.strategy_name == "exploitation"
        )
        assert exploitation.final_recall > 0.0, (
            f"Exploitation failed to recover any actives: {exploitation.notes}"
        )

    def test_random_baseline_has_notes(self):
        """Random strategy result includes averaging note."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        random_result = next(
            r for r in report.results if r.strategy_name == "random"
        )
        assert len(random_result.notes) > 0

    def test_production_vs_comparison_fields(self):
        """Production vs other strategy comparison fields are present."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        d = report.to_dict()
        for field in [
            "production_vs_exploitation",
            "production_vs_exploration",
            "production_vs_diversity",
        ]:
            assert field in d, f"Missing comparison field: {field}"
            assert d[field] in ("better", "worse", "similar", None), (
                f"Unexpected value for {field}: {d[field]}"
            )

    def test_notes_are_present(self):
        """Report has human-readable notes."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        assert len(report.notes) > 0
        assert any("Pool" in n for n in report.notes)

    def test_write_json(self, tmp_path):
        """Writing to JSON produces valid file with expected fields."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
            write_comparison_json,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        out = tmp_path / "report.json"
        write_comparison_json(report, out)
        assert out.exists()
        data = json.loads(out.read_text())
        _check_report_shape(data)

    def test_write_markdown(self, tmp_path):
        """Writing to Markdown produces expected sections."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
            write_comparison_markdown,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        out = tmp_path / "report.md"
        write_comparison_markdown(report, out)
        assert out.exists()
        content = out.read_text()
        assert "# Active-Learning Strategy Comparison Report" in content
        assert "## Overview" in content
        assert "## Strategies" in content
        assert "## Per-Strategy Recovery Results" in content
        assert "## Ranking by Recall" in content
        assert "## Production Selector Comparison" in content
        assert "## Caveats" in content

    def test_cli_exits_zero(self):
        """CLI bench strategy-compare exits 0 and produces valid output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli", "bench",
                "strategy-compare",
                "--n-total", "20",
                "--n-active", "4",
                "--n-hidden", "2",
                "--batch-size", "3",
                "--max-rounds", "3",
                "--rng-seed", "42",
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr[:500]}"
        data = json.loads(result.stdout)
        assert "version" in data
        assert "results" in data
        assert "ranked_by_recall" in data
        assert len(data["results"]) == 5

    def test_cli_writes_json_and_md(self, tmp_path):
        """CLI with --out-json and --out-md writes both files."""
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli", "bench",
                "strategy-compare",
                "--n-total", "20",
                "--n-active", "4",
                "--n-hidden", "2",
                "--batch-size", "3",
                "--max-rounds", "3",
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr[:500]}"
        assert out_json.exists()
        assert out_md.exists()
        data = json.loads(out_json.read_text())
        _check_report_shape(data)
        md_content = out_md.read_text()
        assert "# Active-Learning Strategy Comparison Report" in md_content

    def test_random_has_expected_ranges(self):
        """Random baseline recall should be within expected bounds
        on a small pool with several hidden actives."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=20, n_active=5, n_hidden_actives=3,
            batch_size=5, max_rounds=3,
        )
        random_result = next(
            r for r in report.results if r.strategy_name == "random"
        )
        assert 0.0 <= random_result.final_recall <= 1.0
        # With 3 hidden out of 20, batch size 5, 3 rounds, expectation is
        # non-trivial recovery probability
        assert random_result.n_hidden_recovered >= 0

    def test_schema_conformance(self, tmp_path):
        """JSON output validates against JSON Schema."""
        import jsonschema

        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "active_learning_strategy_comparison.schema.json"
        )
        schema = json.loads(schema_path.read_text())

        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
            write_comparison_json,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        out = tmp_path / "report.json"
        write_comparison_json(report, out)
        data = json.loads(out.read_text())

        jsonschema.validate(instance=data, schema=schema)

    def test_production_outperforms_random_type(self):
        """production_outperforms_random is bool or None."""
        from openamp_foundry.active_learning.strategy_comparison import (
            run_strategy_comparison,
        )

        report = run_strategy_comparison(
            n_total=30, n_active=5, n_hidden_actives=2,
            batch_size=3, max_rounds=3,
        )
        val = report.production_outperforms_random
        assert val is True or val is False or val is None
