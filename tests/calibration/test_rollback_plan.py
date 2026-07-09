"""Tests for recalibration rollback plan."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from openamp_foundry.calibration.rollback_plan import (
    ROLLBACK_TRIGGERS,
    RollbackStep,
    DEFAULT_ROLLBACK_STEPS,
    build_rollback_plan,
    write_rollback_plan_json,
    write_rollback_plan_markdown,
)


class TestRollbackTriggers:
    def test_at_least_5_triggers(self):
        assert len(ROLLBACK_TRIGGERS) >= 5

    def test_all_triggers_have_required_fields(self):
        for trigger in ROLLBACK_TRIGGERS:
            assert "id" in trigger
            assert "name" in trigger
            assert "description" in trigger
            assert "threshold" in trigger
            assert "severity" in trigger


class TestBuildRollbackPlan:
    VALID_TRIGGERS = ["RT-01", "RT-02"]

    def test_valid_triggers_passes(self):
        plan = build_rollback_plan("RBK-001", "v0.5.87", self.VALID_TRIGGERS)
        assert plan.plan_id == "RBK-001"
        assert plan.version == "v0.5.87"

    def test_unknown_trigger_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown rollback trigger id"):
            build_rollback_plan("RBK-002", "v0.5.87", ["RT-99"])

    def test_triggered_by_stored_correctly(self):
        plan = build_rollback_plan("RBK-003", "v0.5.87", ["RT-01", "RT-04"])
        assert "RT-01" in plan.triggered_by
        assert "RT-04" in plan.triggered_by
        assert len(plan.triggered_by) == 2

    def test_steps_include_all_default_steps(self):
        plan = build_rollback_plan("RBK-004", "v0.5.87", self.VALID_TRIGGERS)
        default_actions = {s.action for s in DEFAULT_ROLLBACK_STEPS}
        plan_actions = {s.action for s in plan.steps}
        for action in default_actions:
            assert action in plan_actions

    def test_extra_steps_appended_correctly(self):
        extra = [
            RollbackStep(step_number=0, action="Notify stakeholders", responsible="human-reviewer", detail="Notify affected teams."),
        ]
        plan = build_rollback_plan("RBK-005", "v0.5.87", self.VALID_TRIGGERS, extra_steps=extra)
        assert len(plan.steps) == len(DEFAULT_ROLLBACK_STEPS) + 1
        assert plan.steps[-1].action == "Notify stakeholders"

    def test_dry_lab_only_always_true(self):
        plan = build_rollback_plan("RBK-006", "v0.5.87", self.VALID_TRIGGERS)
        assert plan.dry_lab_only is True

    def test_plan_id_stored_correctly(self):
        plan = build_rollback_plan("RBK-CUSTOM", "v0.5.87", self.VALID_TRIGGERS)
        assert plan.plan_id == "RBK-CUSTOM"

    def test_version_stored_correctly(self):
        plan = build_rollback_plan("RBK-007", "v0.5.88", self.VALID_TRIGGERS)
        assert plan.version == "v0.5.88"

    def test_to_dict_has_required_keys(self):
        plan = build_rollback_plan("RBK-008", "v0.5.87", self.VALID_TRIGGERS)
        d = plan.to_dict()
        for key in ("plan_id", "version", "triggered_by", "steps", "notes", "dry_lab_only"):
            assert key in d
        assert d["dry_lab_only"] is True

    def test_notes_stored_correctly(self):
        plan = build_rollback_plan("RBK-009", "v0.5.87", self.VALID_TRIGGERS, notes="AUROC dropped 0.03.")
        assert plan.notes == "AUROC dropped 0.03."

    def test_default_steps_have_correct_responsible_parties(self):
        expected = {"pipeline", "human-reviewer", "both"}
        for step in DEFAULT_ROLLBACK_STEPS:
            assert step.responsible in expected
            assert step.dry_lab_only is True


class TestWriters:
    def test_write_rollback_plan_json(self, tmp_path: Path):
        plan = build_rollback_plan("RBK-JSON", "v0.5.87", ["RT-01", "RT-04"])
        out = tmp_path / "rollback.json"
        write_rollback_plan_json(plan, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["plan_id"] == "RBK-JSON"
        assert data["dry_lab_only"] is True
        assert len(data["steps"]) == len(DEFAULT_ROLLBACK_STEPS)

    def test_write_rollback_plan_markdown(self, tmp_path: Path):
        plan = build_rollback_plan("RBK-MD", "v0.5.87", ["RT-01", "RT-04"])
        out = tmp_path / "rollback.md"
        write_rollback_plan_markdown(plan, out)
        assert out.exists()
        content = out.read_text()
        assert "# Recalibration Rollback Plan" in content
        assert "RBK-MD" in content
        assert "RT-01" in content
        assert "RT-04" in content
        assert "Caveats" in content
