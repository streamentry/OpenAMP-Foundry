"""Tests for synthetic result policy — anti-overclaim safeguard."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from openamp_foundry.evidence.synthetic_result_policy import (
    PROOF_LADDER_LEVELS,
    SyntheticResultPolicyCheck,
    check_synthetic_result_policy,
    run_policy_batch,
    write_policy_check_json,
    write_policy_check_markdown,
)


class TestSyntheticResultPolicy:
    def test_synthetic_raising_level_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP001",
            current_level=2,
            proposed_level=3,
            evidence_source="synthetic",
        )
        assert result.policy_pass is False
        assert result.violation == "Synthetic evidence cannot raise proof-ladder level"
        assert result.dry_lab_only is True

    def test_synthetic_maintaining_level_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP002",
            current_level=2,
            proposed_level=2,
            evidence_source="synthetic",
        )
        assert result.policy_pass is True
        assert result.violation == ""
        assert result.dry_lab_only is True

    def test_synthetic_lowering_level_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP003",
            current_level=3,
            proposed_level=2,
            evidence_source="synthetic",
        )
        assert result.policy_pass is False
        assert "cannot lower" in result.violation
        assert result.dry_lab_only is True

    def test_lab_raising_level_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP004",
            current_level=2,
            proposed_level=3,
            evidence_source="lab",
        )
        assert result.policy_pass is True
        assert result.violation == ""
        assert result.dry_lab_only is True

    def test_literature_raising_level_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP005",
            current_level=1,
            proposed_level=2,
            evidence_source="literature",
        )
        assert result.policy_pass is True
        assert result.violation == ""

    def test_proposed_level_4_with_synthetic_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP006",
            current_level=3,
            proposed_level=4,
            evidence_source="synthetic",
        )
        assert result.policy_pass is False
        assert "Levels 4+ require wet-lab evidence" in result.violation

    def test_proposed_level_4_with_unknown_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP007",
            current_level=3,
            proposed_level=4,
            evidence_source="unknown",
        )
        assert result.policy_pass is False
        assert "Levels 4+ require wet-lab evidence" in result.violation

    def test_proposed_level_4_with_lab_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP008",
            current_level=3,
            proposed_level=4,
            evidence_source="lab",
        )
        assert result.policy_pass is True
        assert result.violation == ""

    def test_proposed_level_5_with_lab_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP009",
            current_level=4,
            proposed_level=5,
            evidence_source="lab",
        )
        assert result.policy_pass is True
        assert result.violation == ""

    def test_proposed_level_6_with_literature_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP010",
            current_level=5,
            proposed_level=6,
            evidence_source="literature",
        )
        assert result.policy_pass is True
        assert result.violation == ""

    def test_invalid_current_level_raises(self):
        with pytest.raises(ValueError, match="current_level must be 1..6"):
            check_synthetic_result_policy(
                candidate_id="AMP011",
                current_level=0,
                proposed_level=3,
                evidence_source="synthetic",
            )

    def test_invalid_proposed_level_raises(self):
        with pytest.raises(ValueError, match="proposed_level must be 1..6"):
            check_synthetic_result_policy(
                candidate_id="AMP012",
                current_level=2,
                proposed_level=7,
                evidence_source="synthetic",
            )

    def test_unknown_source_treated_as_unknown(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP013",
            current_level=2,
            proposed_level=3,
            evidence_source="invalid_source",
        )
        # invalid source becomes "unknown", and unknown + proposing > 3
        # is a violation, but here proposed=3 so no level-4 violation
        assert result.evidence_source == "unknown"
        assert result.policy_pass is True  # unknown + proposed=3 is fine
        assert result.violation == ""

    def test_unknown_source_proposing_level_4_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP014",
            current_level=3,
            proposed_level=4,
            evidence_source="invalid_source",
        )
        assert result.evidence_source == "unknown"
        assert result.policy_pass is False
        assert "Levels 4+ require wet-lab evidence" in result.violation

    def test_dry_lab_only_always_true(self):
        sources = ["synthetic", "lab", "literature", "unknown"]
        for src in sources:
            result = check_synthetic_result_policy(
                candidate_id="T001", current_level=1, proposed_level=2,
                evidence_source=src,
            )
            assert result.dry_lab_only is True

    def test_run_policy_batch_summary_counts(self):
        proposals = [
            {"candidate_id": "A", "current_level": 2, "proposed_level": 3, "evidence_source": "synthetic"},
            {"candidate_id": "B", "current_level": 2, "proposed_level": 2, "evidence_source": "synthetic"},
            {"candidate_id": "C", "current_level": 2, "proposed_level": 3, "evidence_source": "lab"},
        ]
        result = run_policy_batch(proposals)
        assert result["summary"]["total"] == 3
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 1
        assert result["any_violation"] is True
        assert result["dry_lab_only"] is True

    def test_run_policy_batch_all_pass(self):
        proposals = [
            {"candidate_id": "A", "current_level": 2, "proposed_level": 2, "evidence_source": "lab"},
            {"candidate_id": "B", "current_level": 3, "proposed_level": 4, "evidence_source": "lab"},
        ]
        result = run_policy_batch(proposals)
        assert result["summary"]["total"] == 2
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 0
        assert result["any_violation"] is False

    def test_run_policy_batch_any_violation_flag(self):
        proposals = [
            {"candidate_id": "A", "current_level": 2, "proposed_level": 3, "evidence_source": "synthetic"},
        ]
        result = run_policy_batch(proposals)
        assert result["any_violation"] is True

    def test_to_dict_method(self):
        check = SyntheticResultPolicyCheck(
            candidate_id="T001",
            current_level=2,
            proposed_level=3,
            evidence_source="synthetic",
            policy_pass=False,
            violation="test violation",
            recommendation="test",
        )
        d = check.to_dict()
        assert d["candidate_id"] == "T001"
        assert d["policy_pass"] is False
        assert d["dry_lab_only"] is True

    def test_proof_ladder_levels_dict(self):
        assert PROOF_LADDER_LEVELS[1] == "computational nomination"
        assert PROOF_LADDER_LEVELS[3] == "in-silico ensemble agreement"
        assert PROOF_LADDER_LEVELS[6] == "clinical evidence"
        assert len(PROOF_LADDER_LEVELS) == 6

    def test_write_policy_check_json_single(self):
        check = check_synthetic_result_policy(
            candidate_id="AMP001",
            current_level=2,
            proposed_level=3,
            evidence_source="synthetic",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.json"
            write_policy_check_json(check, path)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["candidate_id"] == "AMP001"
            assert data["policy_pass"] is False

    def test_write_policy_check_json_batch(self):
        proposals = [
            {"candidate_id": "A", "current_level": 2, "proposed_level": 3, "evidence_source": "synthetic"},
        ]
        result = run_policy_batch(proposals)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.json"
            write_policy_check_json(result, path)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["summary"]["total"] == 1

    def test_write_policy_check_markdown_single(self):
        check = check_synthetic_result_policy(
            candidate_id="AMP001",
            current_level=2,
            proposed_level=3,
            evidence_source="synthetic",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "check.md"
            write_policy_check_markdown(check, path)
            assert path.exists()
            content = path.read_text()
            assert "Synthetic Result Policy Check" in content
            assert "AMP001" in content
            assert "FAIL" in content

    def test_write_policy_check_markdown_batch(self):
        proposals = [
            {"candidate_id": "A", "current_level": 2, "proposed_level": 3, "evidence_source": "synthetic"},
            {"candidate_id": "B", "current_level": 2, "proposed_level": 2, "evidence_source": "lab"},
        ]
        result = run_policy_batch(proposals)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.md"
            write_policy_check_markdown(result, path)
            assert path.exists()
            content = path.read_text()
            assert "Batch Report" in content
            assert "A" in content
            assert "B" in content

    def test_recommendation_non_empty_for_violation(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP001",
            current_level=2,
            proposed_level=3,
            evidence_source="synthetic",
        )
        assert result.recommendation != ""

    def test_recommendation_for_pass(self):
        result = check_synthetic_result_policy(
            candidate_id="AMP001",
            current_level=2,
            proposed_level=2,
            evidence_source="synthetic",
        )
        assert result.recommendation != ""
        assert "maintained" in result.recommendation

    def test_run_policy_batch_empty_list(self):
        result = run_policy_batch([])
        assert result["summary"]["total"] == 0
        assert result["summary"]["passed"] == 0
        assert result["summary"]["failed"] == 0
        assert result["any_violation"] is False
