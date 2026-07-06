"""Tests for expert composite ranking integration.

Verifies that:
1. score_candidates() now computes expert_composite and hemolysis_risk for every candidate.
2. rank_candidates(ranking_mode='expert') produces a different order than ensemble.
3. The expert composite partially corrects the anti-selective bias.
4. The CLI --ranking-mode expert flag works end-to-end.
5. The batch report records which ranking mode was used.

Context: The triage benchmark (v0.5.12) showed the ensemble has an anti-selective
bias (AUROC selective_vs_hemolytic = 0.466, below random). The expert composite
incorporates selectivity, hemolysis risk, and helix-hinge analysis. This test
verifies the integration is correct, not that the expert composite is biologically
validated (it is not).
"""
from __future__ import annotations

import json
from io import StringIO
import sys


from openamp_foundry.pipeline import score_candidates
from openamp_foundry.selection.pareto import rank_candidates


class TestExpertCompositeInPipeline:
    """Verify expert_composite is computed during scoring."""

    def test_expert_composite_present_in_scores(self):
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        for s in scored:
            assert "expert_composite" in s.scores, (
                f"{s.candidate.candidate_id} missing expert_composite score"
            )
            assert 0.0 <= s.scores["expert_composite"] <= 1.0

    def test_hemolysis_risk_present_in_scores(self):
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        for s in scored:
            assert "hemolysis_risk" in s.scores, (
                f"{s.candidate.candidate_id} missing hemolysis_risk score"
            )
            assert 0.0 <= s.scores["hemolysis_risk"] <= 1.0

    def test_expert_composite_differs_from_ensemble(self):
        """Expert composite should not be identical to ensemble (different formula)."""
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        for s in scored:
            assert s.scores["expert_composite"] != s.scores["ensemble"], (
                f"{s.candidate.candidate_id}: expert_composite equals ensemble "
                "-- they should differ (different component weights)"
            )


class TestExpertRankingMode:
    """Verify ranking_mode='expert' produces different ordering than ensemble."""

    def test_expert_ranking_differs_from_ensemble(self):
        """At least one position should differ between ensemble and expert ranking."""
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        ens_ranked = rank_candidates(scored, ranking_mode="ensemble")
        exp_ranked = rank_candidates(scored, ranking_mode="expert")

        ens_ids = [s.candidate.candidate_id for s in ens_ranked]
        exp_ids = [s.candidate.candidate_id for s in exp_ranked]

        # With 10 candidates, at least one position should differ
        assert ens_ids != exp_ids, (
            "Expert ranking produced identical order to ensemble — "
            "the expert composite should change at least some rankings"
        )

    def test_expert_ranking_sorts_by_expert_composite(self):
        """Expert ranking should sort by expert_composite, highest first."""
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        exp_ranked = rank_candidates(scored, ranking_mode="expert")

        for i in range(len(exp_ranked) - 1):
            assert exp_ranked[i].scores["expert_composite"] >= exp_ranked[i + 1].scores["expert_composite"]

    def test_ensemble_ranking_unchanged_by_default(self):
        """Default ranking_mode should still be ensemble."""
        scored, _ = score_candidates("examples/sequences/demo_candidates.csv")
        default_ranked = rank_candidates(scored)
        ens_ranked = rank_candidates(scored, ranking_mode="ensemble")

        default_ids = [s.candidate.candidate_id for s in default_ranked]
        ens_ids = [s.candidate.candidate_id for s in ens_ranked]
        assert default_ids == ens_ids


class TestExpertRankingCLI:
    """CLI integration test for --ranking-mode expert."""

    def test_cli_expert_ranking_produces_valid_output(self, tmp_path):
        from openamp_foundry.cli import main

        out = tmp_path / "ranked.jsonl"
        report = tmp_path / "report.md"
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            rc = main([
                "rank",
                "--candidates", "examples/sequences/demo_candidates.csv",
                "--references", "examples/known_reference/demo_known_amps.csv",
                "--out", str(out),
                "--report", str(report),
                "--ranking-mode", "expert",
            ])
            stdout = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert rc == 0
        assert out.exists()

        cli_payload = json.loads(stdout)
        assert cli_payload["ranking_mode"] == "expert"
        assert cli_payload["ranking_policy"]["mode"] == "expert"
        assert "not a validated safety predictor" in cli_payload["ranking_policy"]["not_a_claim"]

        # Batch report should record the ranking mode
        report_json = tmp_path / "report.json"
        assert report_json.exists()
        data = json.loads(report_json.read_text())
        assert data["ranking_mode"] == "expert"
        assert data["ranking_policy"]["mode"] == "expert"
        assert len(data["ranking_policy"]["evidence_basis"]) >= 2

    def test_cli_ensemble_ranking_default(self, tmp_path):
        """Default ranking (no --ranking-mode) should be ensemble."""
        from openamp_foundry.cli import main

        out = tmp_path / "ranked.jsonl"
        report = tmp_path / "report.md"
        rc = main([
            "rank",
            "--candidates", "examples/sequences/demo_candidates.csv",
            "--references", "examples/known_reference/demo_known_amps.csv",
            "--out", str(out),
            "--report", str(report),
        ])
        assert rc == 0
        report_json = tmp_path / "report.json"
        data = json.loads(report_json.read_text())
        assert data["ranking_mode"] == "ensemble"
        assert data["ranking_policy"]["mode"] == "ensemble"


class TestExpertRankingSelectivity:
    """Verify expert ranking shifts top candidates toward safer profiles."""

    def test_expert_top_5_have_lower_hemolysis_risk_on_average(self):
        """Expert-ranked top-5 should have lower mean hemolysis_risk than ensemble top-5.

        This is the core value proposition: the expert composite incorporates
        hemolysis risk, so top-ranked candidates should be safer on average.
        If this test fails, the expert composite's hemolysis components are
        not effectively influencing the ranking.
        """
        scored, _ = score_candidates("examples/benchmark/mixed_candidates.csv")
        ens_ranked = rank_candidates(scored, ranking_mode="ensemble")
        exp_ranked = rank_candidates(scored, ranking_mode="expert")

        ens_top5_hemo = sum(s.scores["hemolysis_risk"] for s in ens_ranked[:5]) / 5
        exp_top5_hemo = sum(s.scores["hemolysis_risk"] for s in exp_ranked[:5]) / 5

        assert exp_top5_hemo <= ens_top5_hemo, (
            f"Expert top-5 mean hemolysis_risk ({exp_top5_hemo:.4f}) should be <= "
            f"ensemble top-5 ({ens_top5_hemo:.4f}). The expert composite should "
            f"favor safer candidates."
        )
