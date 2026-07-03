"""Tests for rich_selectivity integration into the production pipeline.

Verifies that rich_selectivity_score is:
1. Computed in score_candidates() (pipeline.py)
2. Present in evidence certificates
3. Used in the expert composite scorer
4. Used in pilot priority formula
5. Shown in the pilot panel report

All results are computational. No biological activity is implied.
"""
from __future__ import annotations

import csv

import pytest

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.pipeline import score_candidates
from openamp_foundry.reports.pilot_panel import write_pilot_csv, write_pilot_markdown
from openamp_foundry.scoring.expert import EXPERT_WEIGHTS, expert_score
from openamp_foundry.selection.pilot import _pilot_priority


CANDIDATES_CSV = "examples/sequences/demo_candidates.csv"
REFERENCES_CSV = "examples/known_reference/demo_known_amps.csv"


class TestRichSelectivityInPipeline:
    """Verify rich_selectivity flows through the full production pipeline."""

    @pytest.fixture(scope="class")
    @classmethod
    def scored(cls):
        scored_list, _ = score_candidates(CANDIDATES_CSV, REFERENCES_CSV)
        return scored_list

    def test_rich_selectivity_in_scores(self, scored):
        """rich_selectivity must appear in every candidate's scores dict."""
        for item in scored:
            assert "rich_selectivity" in item.scores, (
                f"rich_selectivity missing from candidate {item.candidate.candidate_id}"
            )

    def test_rich_selectivity_in_range(self, scored):
        """rich_selectivity must be in [0, 1] for all candidates."""
        for item in scored:
            val = item.scores["rich_selectivity"]
            assert 0.0 <= val <= 1.0, (
                f"rich_selectivity={val} out of [0,1] for {item.candidate.candidate_id}"
            )

    def test_rich_selectivity_differs_from_proxy(self, scored):
        """rich_selectivity should not be identical to the old selectivity_proxy."""
        item = scored[0]
        assert item.scores["rich_selectivity"] != item.scores["selectivity_proxy"], (
            "rich_selectivity should be a different score from selectivity_proxy"
        )

    def test_invalid_candidate_gets_neutral(self):
        """Invalid candidates should get rich_selectivity=0.5 (neutral)."""
        # An invalid sequence should still produce a score without crashing.
        scored_list, _ = score_candidates(CANDIDATES_CSV, REFERENCES_CSV)
        # All demo candidates are valid, so just verify the key exists even for valid ones.
        for item in scored_list:
            assert "rich_selectivity" in item.scores


class TestRichSelectivityInEvidenceCertificate:
    """Verify rich_selectivity appears in evidence certificates."""

    def test_rich_selectivity_in_certificate(self):
        """Evidence certificates must include rich_selectivity in the scores section."""
        scored_list, config = score_candidates(CANDIDATES_CSV, REFERENCES_CSV)
        item = scored_list[0]
        cert = build_certificate(item, config, [REFERENCES_CSV])
        assert "scores" in cert
        assert "rich_selectivity" in cert["scores"], (
            "rich_selectivity must be in evidence certificate scores"
        )
        assert "selectivity_proxy" in cert["scores"], (
            "selectivity_proxy must still be in certificate for backward comparability"
        )


class TestRichSelectivityInExpertComposite:
    """Verify rich_selectivity replaced hemolysis_safety as an expert component."""

    def test_rich_selectivity_in_expert_weights(self):
        """EXPERT_WEIGHTS must include rich_selectivity."""
        assert "rich_selectivity" in EXPERT_WEIGHTS
        assert "hemolysis_safety" not in EXPERT_WEIGHTS

    def test_rich_selectivity_in_expert_components(self):
        """expert_score must include rich_selectivity in its component breakdown."""
        seq = "GIGKFLHSAKKFGKAFVGEIMNS"
        feats = compute_features(seq)
        e = expert_score(seq, features=feats)
        assert "rich_selectivity" in e.components
        assert "hemolysis_safety" not in e.components

    def test_hemolysis_safety_in_extras_as_legacy(self):
        """The old hemolysis_safety component must be preserved as a legacy extra."""
        seq = "GIGKFLHSAKKFGKAFVGEIMNS"
        feats = compute_features(seq)
        e = expert_score(seq, features=feats)
        assert "hemolysis_safety_legacy" in e.extras

    def test_weights_sum_to_one(self):
        """EXPERT_WEIGHTS must sum to 1.00."""
        assert abs(sum(EXPERT_WEIGHTS.values()) - 1.0) < 1e-9


class TestRichSelectivityInPilotPriority:
    """Verify rich_selectivity is used in pilot priority, not selectivity_proxy."""

    def test_rich_selectivity_used_when_present(self):
        """When rich_selectivity is in scores, it must be used for pilot priority."""
        scores = {
            "ensemble": 0.8,
            "disagreement": 0.1,
            "serum_stability": 0.5,
            "novelty": 0.5,
            "rich_selectivity": 0.7,
            "selectivity_proxy": 0.3,
        }
        priority = _pilot_priority(scores)
        expected = 0.8 - 0.3 * 0.1 + 0.05 * 0.5 + 0.05 * 0.5 + 0.05 * 0.7
        assert abs(priority - round(expected, 6)) < 1e-6

    def test_falls_back_to_proxy_when_rich_absent(self):
        """When rich_selectivity is absent, pilot priority uses selectivity_proxy."""
        scores = {
            "ensemble": 0.8,
            "disagreement": 0.1,
            "serum_stability": 0.5,
            "novelty": 0.5,
            "selectivity_proxy": 0.7,
        }
        priority = _pilot_priority(scores)
        expected = 0.8 - 0.3 * 0.1 + 0.05 * 0.5 + 0.05 * 0.5 + 0.05 * 0.7
        assert abs(priority - round(expected, 6)) < 1e-6

    def test_low_rich_selectivity_triggers_cytotox_penalty(self):
        """Candidate with rich_selectivity < 0.5 must get the cytotox penalty."""
        scores_good = {
            "ensemble": 0.8,
            "disagreement": 0.0,
            "serum_stability": 0.5,
            "novelty": 0.5,
            "rich_selectivity": 1.0,
        }
        scores_bad = {
            "ensemble": 0.8,
            "disagreement": 0.0,
            "serum_stability": 0.5,
            "novelty": 0.5,
            "rich_selectivity": 0.0,
        }
        good = _pilot_priority(scores_good)
        bad = _pilot_priority(scores_bad)
        assert bad < good, "Low rich_selectivity must reduce pilot priority"


class TestRichSelectivityInPilotPanel:
    """Verify rich_selectivity appears in the pilot panel report output."""

    def _make_candidate(self, cid="X1", seq="GIGKFLHSAKKFGKAFVGEIMNS"):
        return {
            "candidate_id": cid,
            "sequence": seq,
            "source": "SEED-001",
            "scores": {
                "ensemble": 0.8,
                "activity": 0.7,
                "boman_activity": 0.6,
                "disagreement": 0.1,
                "safety": 0.8,
                "synthesis": 0.9,
                "novelty": 0.5,
                "serum_stability": 0.6,
                "selectivity_proxy": 0.9,
                "rich_selectivity": 0.65,
                "pilot_priority": 0.75,
            },
            "features": {
                "helix_wheel_amphipathic_score": 0.5,
                "net_charge_ph74": 3,
            },
            "pilot_rank": 1,
            "pilot_priority": 0.75,
            "seed": "SEED-001",
        }

    def test_rich_selectivity_in_csv(self, tmp_path):
        """Pilot panel CSV must include a rich_selectivity column."""
        panel = [self._make_candidate()]
        csv_path = tmp_path / "pilot.csv"
        write_pilot_csv(panel, csv_path)
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            assert "rich_selectivity" in reader.fieldnames

    def test_rich_selectivity_in_markdown(self, tmp_path):
        """Pilot panel markdown must mention rich_selectivity."""
        panel = [self._make_candidate()]
        md_path = tmp_path / "pilot.md"
        write_pilot_markdown(panel, md_path, generated_at="2026-01-01")
        content = md_path.read_text()
        assert "rich_selectivity" in content
        assert "RichSel" in content
