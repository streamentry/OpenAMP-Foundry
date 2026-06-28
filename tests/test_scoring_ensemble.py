"""Tests for scoring/ensemble.py — ensemble_score, selection_reasons, known_failure_modes."""
from __future__ import annotations

from openamp_foundry.scoring.ensemble import (
    ensemble_score,
    known_failure_modes,
    selection_reasons,
)


_WEIGHTS = {"activity": 0.40, "safety": 0.30, "synthesis": 0.20, "novelty": 0.10}


class TestEnsembleScore:
    def test_equal_scores_returns_that_score(self):
        scores = {"activity": 0.80, "safety": 0.80, "synthesis": 0.80, "novelty": 0.80}
        result = ensemble_score(scores, _WEIGHTS)
        assert abs(result - 0.80) < 0.001

    def test_weighted_average_correct(self):
        scores = {"activity": 1.0, "safety": 0.0, "synthesis": 0.0, "novelty": 0.0}
        result = ensemble_score(scores, _WEIGHTS)
        # Only activity contributes: 1.0 * 0.40 / (0.40+0.30+0.20+0.10) = 0.40
        assert abs(result - 0.40) < 0.001

    def test_all_zeros_returns_zero(self):
        scores = {"activity": 0.0, "safety": 0.0, "synthesis": 0.0, "novelty": 0.0}
        assert ensemble_score(scores, _WEIGHTS) == 0.0

    def test_all_ones_returns_one(self):
        scores = {"activity": 1.0, "safety": 1.0, "synthesis": 1.0, "novelty": 1.0}
        assert ensemble_score(scores, _WEIGHTS) == 1.0

    def test_result_clamped_above_one(self):
        scores = {"activity": 2.0, "safety": 2.0, "synthesis": 2.0, "novelty": 2.0}
        assert ensemble_score(scores, _WEIGHTS) == 1.0

    def test_result_clamped_below_zero(self):
        scores = {"activity": -1.0, "safety": -1.0, "synthesis": -1.0, "novelty": -1.0}
        assert ensemble_score(scores, _WEIGHTS) == 0.0

    def test_zero_total_weight_no_crash(self):
        # total_weight falls back to 1.0 when all weights are 0
        scores = {"activity": 0.5}
        result = ensemble_score(scores, {"activity": 0.0})
        assert result == 0.0

    def test_unequal_weights_favour_heavier(self):
        scores = {"activity": 1.0, "safety": 0.0}
        heavy_activity = ensemble_score(scores, {"activity": 0.9, "safety": 0.1})
        heavy_safety = ensemble_score(scores, {"activity": 0.1, "safety": 0.9})
        assert heavy_activity > heavy_safety

    def test_returns_rounded_to_4dp(self):
        scores = {"activity": 1.0 / 3.0, "safety": 0.0}
        result = ensemble_score(scores, {"activity": 1.0, "safety": 0.0})
        assert result == round(result, 4)


class TestSelectionReasons:
    def _scores(
        self,
        activity: float = 0.80,
        safety: float = 0.80,
        synthesis: float = 0.85,
        novelty: float = 0.30,
        boman_activity: float | None = None,
        disagreement: float | None = None,
    ) -> dict:
        s: dict = {
            "activity": activity,
            "safety": safety,
            "synthesis": synthesis,
            "novelty": novelty,
        }
        if boman_activity is not None:
            s["boman_activity"] = boman_activity
        if disagreement is not None:
            s["disagreement"] = disagreement
        return s

    def test_all_thresholds_met(self):
        reasons = selection_reasons(self._scores())
        assert len(reasons) >= 3
        texts = " ".join(reasons).lower()
        assert "activity" in texts
        assert "safety" in texts
        assert "synthesis" in texts

    def test_low_activity_no_activity_reason(self):
        reasons = selection_reasons(self._scores(activity=0.50))
        assert not any("activity-likeness" in r.lower() for r in reasons)

    def test_low_novelty_no_novelty_reason(self):
        reasons = selection_reasons(self._scores(novelty=0.10))
        assert not any("duplicate" in r.lower() for r in reasons)

    def test_boman_agreement_adds_reason(self):
        reasons = selection_reasons(
            self._scores(boman_activity=0.70, disagreement=0.15)
        )
        assert any("boman" in r.lower() for r in reasons)

    def test_boman_high_disagreement_no_boman_reason(self):
        reasons = selection_reasons(
            self._scores(boman_activity=0.70, disagreement=0.35)
        )
        assert not any("boman" in r.lower() for r in reasons)

    def test_no_thresholds_met_returns_fallback(self):
        reasons = selection_reasons(
            self._scores(activity=0.10, safety=0.10, synthesis=0.10, novelty=0.10)
        )
        assert any("only by ensemble rank" in r.lower() for r in reasons)

    def test_returns_list(self):
        assert isinstance(selection_reasons(self._scores()), list)


class TestKnownFailureModes:
    def _scores(
        self,
        activity: float = 0.80,
        safety: float = 0.80,
        synthesis: float = 0.85,
        novelty: float = 0.30,
        disagreement: float | None = None,
    ) -> dict:
        s: dict = {
            "activity": activity,
            "safety": safety,
            "synthesis": synthesis,
            "novelty": novelty,
        }
        if disagreement is not None:
            s["disagreement"] = disagreement
        return s

    def test_always_includes_wet_lab_disclaimer(self):
        failures = known_failure_modes(self._scores())
        assert any("wet-lab" in f.lower() or "assay" in f.lower() for f in failures)

    def test_always_includes_heuristic_disclaimer(self):
        failures = known_failure_modes(self._scores())
        assert any("heuristic" in f.lower() for f in failures)

    def test_low_novelty_flagged(self):
        failures = known_failure_modes(self._scores(novelty=0.10))
        assert any("close to a known reference" in f for f in failures)

    def test_high_novelty_not_flagged(self):
        failures = known_failure_modes(self._scores(novelty=0.50))
        assert not any("close to a known reference" in f for f in failures)

    def test_low_safety_flagged(self):
        failures = known_failure_modes(self._scores(safety=0.60))
        assert any("safety" in f.lower() for f in failures)

    def test_low_synthesis_flagged(self):
        failures = known_failure_modes(self._scores(synthesis=0.70))
        assert any("harder to synthesize" in f for f in failures)

    def test_high_disagreement_flagged(self):
        failures = known_failure_modes(self._scores(disagreement=0.40))
        assert any("disagreement" in f.lower() for f in failures)

    def test_low_disagreement_not_flagged(self):
        failures = known_failure_modes(self._scores(disagreement=0.10))
        assert not any("disagreement" in f.lower() for f in failures)

    def test_returns_non_empty_list(self):
        failures = known_failure_modes(self._scores())
        assert len(failures) >= 2
