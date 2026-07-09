"""Tests for roadmap-to-issue sync validation."""
import pytest
from openamp_foundry.governance.roadmap_sync import (
    VALID_PHASES,
    VALID_PRIORITY_LEVELS,
    VALID_SYNC_STATUSES,
    RoadmapSyncEntry,
    RoadmapSyncResult,
    validate_roadmap_sync_dict,
    validate_roadmap_sync_entry,
)


def _valid_entry(**kwargs) -> RoadmapSyncEntry:
    defaults = dict(
        item_id="J8",
        phase="J",
        description="Add roadmap-to-issue sync checklist",
        priority="B",
        sync_status="synced",
        issue_number=807,
        pr_number=807,
        completed=False,
        completion_date="",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return RoadmapSyncEntry(**defaults)


class TestValidSyncEntry:
    def test_valid_entry_passes(self):
        result = validate_roadmap_sync_entry(_valid_entry())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_item_id(self):
        result = validate_roadmap_sync_entry(_valid_entry())
        assert result.item_id == "J8"

    def test_result_has_correct_phase(self):
        result = validate_roadmap_sync_entry(_valid_entry())
        assert result.phase == "J"

    def test_all_phases_accepted(self):
        for phase in VALID_PHASES:
            result = validate_roadmap_sync_entry(_valid_entry(phase=phase))
            assert result.passed is True, f"Expected phase {phase} to pass"

    def test_all_priorities_accepted(self):
        for priority in VALID_PRIORITY_LEVELS:
            result = validate_roadmap_sync_entry(_valid_entry(priority=priority))
            assert result.passed is True, f"Expected priority {priority} to pass"

    def test_all_sync_statuses_accepted(self):
        for status in VALID_SYNC_STATUSES:
            result = validate_roadmap_sync_entry(_valid_entry(sync_status=status))
            assert result.passed is True, f"Expected status {status} to pass"

    def test_completed_entry_with_date_passes(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(completed=True, completion_date="2026-07-09")
        )
        assert result.passed is True


class TestInvalidSyncEntry:
    def test_empty_item_id_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(item_id=""))
        assert result.passed is False
        assert any("item_id" in e for e in result.errors)

    def test_invalid_phase_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(phase="Z"))
        assert result.passed is False
        assert any("phase" in e for e in result.errors)

    def test_empty_description_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(description=""))
        assert result.passed is False
        assert any("description" in e for e in result.errors)

    def test_invalid_priority_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(priority="E"))
        assert result.passed is False
        assert any("priority" in e for e in result.errors)

    def test_invalid_sync_status_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(sync_status="unknown"))
        assert result.passed is False
        assert any("sync_status" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_roadmap_sync_entry(_valid_entry(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)

    def test_completed_without_date_fails(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(completed=True, completion_date="")
        )
        assert result.passed is False
        assert any("completion_date" in e for e in result.errors)

    def test_invalid_completion_date_format_fails(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(completed=True, completion_date="09-07-2026")
        )
        assert result.passed is False
        assert any("completion_date" in e for e in result.errors)


class TestSyncWarnings:
    def test_priority_a_missing_issue_warns(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(priority="A", sync_status="missing_issue")
        )
        assert result.passed is True
        assert any("missing_issue" in w for w in result.warnings)

    def test_stale_status_warns(self):
        result = validate_roadmap_sync_entry(_valid_entry(sync_status="stale"))
        assert result.passed is True
        assert any("stale" in w for w in result.warnings)

    def test_orphaned_issue_warns(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(sync_status="orphaned_issue")
        )
        assert result.passed is True
        assert any("orphaned_issue" in w for w in result.warnings)

    def test_no_issue_number_warns(self):
        result = validate_roadmap_sync_entry(
            _valid_entry(issue_number=None, sync_status="missing_issue")
        )
        assert result.passed is True
        assert any("issue_number" in w for w in result.warnings)


class TestValidateRoadmapSyncDict:
    def test_valid_dict_passes(self):
        d = {
            "item_id": "J8",
            "phase": "J",
            "description": "Add roadmap-to-issue sync checklist",
            "priority": "B",
            "sync_status": "synced",
            "issue_number": 807,
        }
        result = validate_roadmap_sync_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_roadmap_sync_dict({"item_id": "J8"})
        assert result.passed is False
        assert any("Missing" in e for e in result.errors)


class TestConstants:
    def test_valid_sync_statuses_has_5(self):
        assert len(VALID_SYNC_STATUSES) == 5

    def test_valid_priority_levels_has_4(self):
        assert len(VALID_PRIORITY_LEVELS) == 4

    def test_valid_phases_has_7(self):
        assert len(VALID_PHASES) == 7

    def test_all_results_dry_lab_only_true(self):
        result = validate_roadmap_sync_entry(_valid_entry())
        assert result.dry_lab_only is True
