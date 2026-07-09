"""Tests for calibration decision review checklist."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from openamp_foundry.calibration.decision_checklist import (
    CHECKLIST_ITEMS,
    CalibrationDecisionChecklist,
    build_checklist,
    write_checklist_json,
    write_checklist_markdown,
)


class TestChecklistItems:
    def test_at_least_10_items(self):
        assert len(CHECKLIST_ITEMS) >= 10

    def test_required_items_have_required_true(self):
        for item in CHECKLIST_ITEMS:
            if item["id"] in ("G9-01", "G9-02", "G9-03", "G9-04", "G9-05",
                              "G9-06", "G9-07", "G9-08", "G9-09", "G9-10"):
                assert item["required"] is True, f"Item {item['id']} should be required"

    def test_all_items_have_required_fields(self):
        for item in CHECKLIST_ITEMS:
            assert "id" in item
            assert "category" in item
            assert "question" in item
            assert "rationale" in item
            assert "required" in item


class TestBuildChecklist:
    ALL_PASS = {
        "G9-01": True, "G9-02": True, "G9-03": True, "G9-04": True,
        "G9-05": True, "G9-06": True, "G9-07": True, "G9-08": True,
        "G9-09": True, "G9-10": True, "G9-11": True,
    }

    def test_all_required_pass_overall_pass_true(self):
        checklist = build_checklist("CHK-001", "2026-07-09", "test-reviewer", self.ALL_PASS)
        assert checklist.overall_pass is True
        assert checklist.missing_required == []

    def test_missing_required_item_overall_pass_false(self):
        responses = dict(self.ALL_PASS)
        responses["G9-08"] = False
        checklist = build_checklist("CHK-002", "2026-07-09", "test-reviewer", responses)
        assert checklist.overall_pass is False
        assert "G9-08" in checklist.missing_required

    def test_missing_required_list_correct(self):
        responses = {
            "G9-01": True, "G9-03": True, "G9-05": True, "G9-07": True,
            "G9-09": True,
        }
        checklist = build_checklist("CHK-003", "2026-07-09", "test-reviewer", responses)
        assert checklist.overall_pass is False
        for rid in ("G9-02", "G9-04", "G9-06", "G9-08", "G9-10", "G9-11"):
            assert rid in checklist.missing_required

    def test_unknown_response_id_raises(self):
        responses = {"G9-01": True, "UNKNOWN-ID": True}
        with pytest.raises(ValueError, match="Unknown checklist item id"):
            build_checklist("CHK-004", "2026-07-09", "test-reviewer", responses)

    def test_dry_lab_only_always_true(self):
        checklist = build_checklist("CHK-005", "2026-07-09", "test-reviewer", self.ALL_PASS)
        assert checklist.dry_lab_only is True

    def test_notes_stored_correctly(self):
        notes = {"G9-01": "Cohort size was 45 — adequate.", "G9-08": "Reviewed by Dr. Smith on 2026-07-09."}
        checklist = build_checklist("CHK-006", "2026-07-09", "test-reviewer", self.ALL_PASS, notes=notes)
        assert checklist.notes == notes
        assert checklist.notes["G9-01"] == "Cohort size was 45 — adequate."

    def test_checklist_id_stored_correctly(self):
        responses = {"G9-01": True}
        checklist = build_checklist("CHK-CUSTOM", "2026-07-09", "test-reviewer", responses)
        assert checklist.checklist_id == "CHK-CUSTOM"

    def test_reviewer_stored_correctly(self):
        responses = {"G9-01": True}
        checklist = build_checklist("CHK-007", "2026-07-09", "dr-jones", responses)
        assert checklist.reviewer == "dr-jones"

    def test_date_stored_correctly(self):
        responses = {"G9-01": True}
        checklist = build_checklist("CHK-008", "2026-07-09", "reviewer", responses)
        assert checklist.date == "2026-07-09"


class TestWriters:
    def test_write_checklist_json(self, tmp_path: Path):
        from openamp_foundry.calibration.decision_checklist import build_checklist
        responses = dict(TestBuildChecklist.ALL_PASS)
        checklist = build_checklist("CHK-JSON", "2026-07-09", "test-reviewer", responses)
        out = tmp_path / "checklist.json"
        write_checklist_json(checklist, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["checklist_id"] == "CHK-JSON"
        assert data["overall_pass"] is True
        assert data["dry_lab_only"] is True

    def test_write_checklist_markdown(self, tmp_path: Path):
        responses = {
            "G9-01": True, "G9-02": True, "G9-03": False, "G9-04": True,
            "G9-05": True, "G9-06": True, "G9-07": True, "G9-08": True,
            "G9-09": True, "G9-10": True,
        }
        checklist = build_checklist("CHK-MD", "2026-07-09", "test-reviewer", responses)
        out = tmp_path / "checklist.md"
        write_checklist_markdown(checklist, out)
        assert out.exists()
        content = out.read_text()
        assert "# Calibration Decision Review Checklist" in content
        assert "CHK-MD" in content
        assert "G9-03" in content
        assert "❌" in content
        assert "✅" in content
