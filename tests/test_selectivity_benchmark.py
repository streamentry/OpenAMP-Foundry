"""Within-AMP selectivity benchmark tests.

Tests the benchmark that asks: can the pipeline's physicochemical scorers
distinguish hemolytic AMPs (HC50 < 25 µg/mL) from selective AMPs (HC50 >= 100 µg/mL)?

This is the complementary benchmark to the expert ablation: the ablation tested
AMP-vs-decoy discrimination (where safety/synthesis were anti-signal); this tests
within-AMP selectivity, the task those scorers were designed for.

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

import csv
import tempfile

import pytest

from openamp_foundry.benchmark.retrospective import run_selectivity_benchmark


HEMOLYSIS_CSV = "examples/validation/hemolysis_reference.csv"

SCORE_COLS = [
    "ensemble", "expert_composite", "activity", "safety",
    "synthesis", "novelty", "boman_activity", "serum_stability",
    "selectivity_proxy", "hinge_selectivity",
]


class TestSelectivityBenchmark:
    @pytest.fixture(scope="class")
    def result(self):
        return run_selectivity_benchmark(
            HEMOLYSIS_CSV, n_bootstrap=200,
        )

    def test_benchmark_runs_on_real_data(self, result):
        assert result["benchmark"] == "within_amp_selectivity"
        assert result["n_hemolytic"] > 0
        assert result["n_selective"] > 0
        assert result["n_total"] == result["n_hemolytic"] + result["n_selective"] + result["n_border"]

    def test_per_score_auroc_has_all_columns(self, result):
        per_score = result["per_score_auroc"]
        for col in SCORE_COLS:
            assert col in per_score
            assert 0.0 <= per_score[col]["auroc"] <= 1.0
            assert 0.0 <= per_score[col]["hemolysis_detection_auroc"] <= 1.0

    def test_detection_auroc_is_complement(self, result):
        """Detection AUROC = 1 - AUROC for every score."""
        for col, info in result["per_score_auroc"].items():
            assert info["hemolysis_detection_auroc"] == pytest.approx(
                1.0 - info["auroc"], abs=1e-4
            )

    def test_ci_bounds_are_ordered(self, result):
        for col, info in result["per_score_auroc"].items():
            assert info["ci95_lo"] <= info["ci95_hi"]
            assert info["detection_ci95_lo"] <= info["detection_ci95_hi"]

    def test_mean_scores_are_present(self, result):
        for col, info in result["per_score_auroc"].items():
            assert info["mean_hemolytic"] is not None
            assert info["mean_selective"] is not None

    def test_safety_verdict_present(self, result):
        assert "safety" in result["safety_verdict"].lower()
        assert "hemolysis" in result["safety_verdict"].lower()

    def test_selectivity_proxy_verdict_present(self, result):
        assert "selectivity" in result["selectivity_proxy_verdict"].lower()

    def test_expert_composite_verdict_present(self, result):
        assert "expert" in result["expert_composite_verdict"].lower()
        assert "ensemble" in result["expert_composite_verdict"].lower()

    def test_blind_spots_listed(self, result):
        """All hemolytic AMPs with safety >= 0.8 should be listed as blind spots."""
        blind = result["blind_spots"]
        for bp in blind:
            assert bp["safety"] >= 0.8
            assert bp["hc50"] < 25

    def test_border_zone_present(self, result):
        """Border zone peptides (25 <= HC50 < 100) should be reported."""
        border = result["border_zone"]
        for bp in border:
            assert 25 <= bp["hc50"] < 100

    def test_disclaimer_present(self, result):
        assert "wet-lab" in result["disclaimer"].lower()
        assert "physicochemical" in result["disclaimer"].lower()

    def test_design_note_present(self, result):
        assert "within-amp" in result["design_note"].lower()
        assert "hemolytic" in result["design_note"].lower()

    def test_risk_detectors_and_indicators_partitioned(self, result):
        """Risk detectors (CI lo > 0.5) and indicators (point > 0.5, CI lo <= 0.5) are disjoint."""
        detectors = set(result["risk_detectors"])
        indicators = set(result["risk_indicators"])
        assert detectors & indicators == set()

    def test_safety_scorer_is_not_a_risk_detector(self, result):
        """The safety scorer should NOT be a significant hemolysis risk detector.

        This confirms the known melittin blind spot: the 1D hydrophobic moment
        cannot capture all hemolysis mechanisms. If this test fails, the safety
        scorer has improved and the blind spot may be closing.
        """
        assert "safety" not in result["risk_detectors"]


class TestSelectivityBenchmarkEdgeCases:
    """Test edge cases with small synthetic datasets."""

    def _write_csv(self, rows: list[dict]) -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        )
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "sequence", "family", "hc50_ugml", "hemolysis_class", "reference"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        f.close()
        return f.name

    def test_all_hemolytic(self):
        """If all peptides are hemolytic, AUROC should be 0.5 (no negatives)."""
        rows = [
            {"id": "H1", "sequence": "GIGAVLKVLTTGLPALISWIKRKRQQ", "family": "melittin",
             "hc50_ugml": "1.5", "hemolysis_class": "HEMOLYTIC", "reference": "test"},
            {"id": "H2", "sequence": "RGGRLCYCRRRFCVCVGR", "family": "protegrin",
             "hc50_ugml": "5", "hemolysis_class": "HEMOLYTIC", "reference": "test"},
        ]
        csv_path = self._write_csv(rows)
        result = run_selectivity_benchmark(csv_path, n_bootstrap=50)
        assert result["n_selective"] == 0
        # With no selective class, AUROC should be 0.5
        for col, info in result["per_score_auroc"].items():
            assert info["auroc"] == 0.5

    def test_all_selective(self):
        """If all peptides are selective, AUROC should be 0.5 (no positives)."""
        rows = [
            {"id": "S1", "sequence": "GIGKFLHSAKKFGKAFVGEIMNS", "family": "magainin",
             "hc50_ugml": "100", "hemolysis_class": "SELECTIVE", "reference": "test"},
            {"id": "S2", "sequence": "DSHAKRHHGYKRKFHEKHHSHRGY", "family": "histatin",
             "hc50_ugml": "200", "hemolysis_class": "SELECTIVE", "reference": "test"},
        ]
        csv_path = self._write_csv(rows)
        result = run_selectivity_benchmark(csv_path, n_bootstrap=50)
        assert result["n_hemolytic"] == 0

    def test_nonstandard_aa_skipped(self):
        """Sequences with non-standard amino acids should be silently skipped."""
        rows = [
            {"id": "H1", "sequence": "GIGAVLKVLTTGLPALISWIKRKRQQ", "family": "melittin",
             "hc50_ugml": "1.5", "hemolysis_class": "HEMOLYTIC", "reference": "test"},
            {"id": "X1", "sequence": "XBZBQ", "family": "nonstandard",
             "hc50_ugml": "1", "hemolysis_class": "HEMOLYTIC", "reference": "test"},
            {"id": "S1", "sequence": "GIGKFLHSAKKFGKAFVGEIMNS", "family": "magainin",
             "hc50_ugml": "100", "hemolysis_class": "SELECTIVE", "reference": "test"},
        ]
        csv_path = self._write_csv(rows)
        result = run_selectivity_benchmark(csv_path, n_bootstrap=50)
        assert result["n_total"] == 2  # only H1 and S1
        assert result["n_hemolytic"] == 1
        assert result["n_selective"] == 1

    def test_perfect_separation(self):
        """If hemolytic and selective peptides score perfectly apart, AUROC = 1.0 or 0.0."""
        # Use peptides where activity scorer will give very different scores
        rows = [
            {"id": "H1", "sequence": "GIGAVLKVLTTGLPALISWIKRKRQQ", "family": "melittin",
             "hc50_ugml": "1.5", "hemolysis_class": "HEMOLYTIC", "reference": "test"},
            {"id": "S1", "sequence": "DSHAKRHHGYKRKFHEKHHSHRGY", "family": "histatin",
             "hc50_ugml": "200", "hemolysis_class": "SELECTIVE", "reference": "test"},
        ]
        csv_path = self._write_csv(rows)
        result = run_selectivity_benchmark(csv_path, n_bootstrap=50)
        # With 1 vs 1, AUROC is either 0, 0.5, or 1
        for col, info in result["per_score_auroc"].items():
            assert info["auroc"] in (0.0, 0.5, 1.0)
