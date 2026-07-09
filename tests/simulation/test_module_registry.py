"""Tests for the simulation module registry."""

import pytest
from openamp_foundry.simulation.module_registry import (
    SIMULATION_MODULE_REGISTRY,
    SimulationModuleEntry,
    SimulationModuleStatus,
    VALID_STATUSES,
    get_module_entry,
    get_active_modules,
    list_module_entries,
    registry_summary,
    validate_registry,
)
from openamp_foundry.evidence.synthetic_result_policy import PROOF_LADDER_LEVELS


class TestRegistryContents:
    def test_has_at_least_four_entries(self):
        assert len(SIMULATION_MODULE_REGISTRY) >= 4

    def test_all_entries_pass_validation(self):
        errors = validate_registry()
        assert errors == []

    def test_all_entries_have_required_fields(self):
        for entry in SIMULATION_MODULE_REGISTRY:
            assert entry.module_id, "module_id must be non-empty"
            assert entry.name, "name must be non-empty"
            assert entry.description, "description must be non-empty"
            assert entry.baseline_comparison, "baseline_comparison must be non-empty"

    def test_all_evidence_levels_in_range(self):
        for entry in SIMULATION_MODULE_REGISTRY:
            assert 1 <= entry.evidence_level <= 6, (
                f"evidence_level {entry.evidence_level} must be 1..6"
            )

    def test_all_statuses_valid(self):
        for entry in SIMULATION_MODULE_REGISTRY:
            assert entry.status in VALID_STATUSES, (
                f"unknown status '{entry.status}' for {entry.module_id}"
            )


class TestGetModuleEntry:
    def test_known_id_returns_entry(self):
        entry = get_module_entry("membrane_proxy")
        assert entry is not None
        assert entry.module_id == "membrane_proxy"
        assert entry.name == "Membrane Proxy"

    def test_unknown_id_returns_none(self):
        assert get_module_entry("nonexistent_module") is None

    def test_empty_string_returns_none(self):
        assert get_module_entry("") is None


class TestListModuleEntries:
    def test_no_filter_returns_all(self):
        all_entries = list_module_entries()
        assert len(all_entries) == len(SIMULATION_MODULE_REGISTRY)

    def test_status_filter_active(self):
        active = list_module_entries(status="active")
        assert all(e.status == "active" for e in active)

    def test_status_filter_deprecated(self):
        deprecated = list_module_entries(status="deprecated")
        assert all(e.status == "deprecated" for e in deprecated)

    def test_min_evidence_level_filter(self):
        high_evidence = list_module_entries(min_evidence_level=2)
        assert all(e.evidence_level >= 2 for e in high_evidence)

    def test_min_evidence_level_1_includes_all(self):
        all_entries = list_module_entries(min_evidence_level=1)
        assert len(all_entries) == len(SIMULATION_MODULE_REGISTRY)


class TestGetActiveModules:
    def test_returns_only_active(self):
        active = get_active_modules()
        assert all(e.status == "active" for e in active)

    def test_returns_list(self):
        assert isinstance(get_active_modules(), list)


class TestRegistrySummary:
    def test_has_required_keys(self):
        summary = registry_summary()
        assert "total" in summary
        assert "by_status" in summary
        assert "by_evidence_level" in summary
        assert "active_module_ids" in summary

    def test_total_matches_registry_length(self):
        summary = registry_summary()
        assert summary["total"] == len(SIMULATION_MODULE_REGISTRY)

    def test_by_status_sum_matches_total(self):
        summary = registry_summary()
        assert sum(summary["by_status"].values()) == summary["total"]

    def test_by_evidence_level_sum_matches_total(self):
        summary = registry_summary()
        assert sum(summary["by_evidence_level"].values()) == summary["total"]

    def test_active_module_ids_are_all_active(self):
        summary = registry_summary()
        for mid in summary["active_module_ids"]:
            entry = get_module_entry(mid)
            assert entry is not None
            assert entry.status == "active"


class TestValidateRegistry:
    def test_default_registry_has_no_errors(self):
        errors = validate_registry()
        assert errors == []

    def test_detects_empty_module_id(self, monkeypatch):
        bad_entry = SimulationModuleEntry(
            module_id="",
            name="Bad Module",
            description="test",
            status="active",
            evidence_level=1,
            baseline_comparison="charge density",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [bad_entry],
        )
        errors = validate_registry()
        assert any("module_id is empty" in e for e in errors)

    def test_detects_empty_name(self, monkeypatch):
        bad_entry = SimulationModuleEntry(
            module_id="bad_mod",
            name="",
            description="test",
            status="active",
            evidence_level=1,
            baseline_comparison="charge density",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [bad_entry],
        )
        errors = validate_registry()
        assert any("name is empty" in e for e in errors)

    def test_detects_empty_baseline(self, monkeypatch):
        bad_entry = SimulationModuleEntry(
            module_id="bad_mod",
            name="Bad Module",
            description="test",
            status="active",
            evidence_level=1,
            baseline_comparison="",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [bad_entry],
        )
        errors = validate_registry()
        assert any("baseline_comparison is empty" in e for e in errors)

    def test_detects_invalid_evidence_level(self, monkeypatch):
        bad_entry = SimulationModuleEntry(
            module_id="bad_mod",
            name="Bad Module",
            description="test",
            status="active",
            evidence_level=0,
            baseline_comparison="charge density",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [bad_entry],
        )
        errors = validate_registry()
        assert any("evidence_level" in e for e in errors)

    def test_detects_invalid_status(self, monkeypatch):
        bad_entry = SimulationModuleEntry(
            module_id="bad_mod",
            name="Bad Module",
            description="test",
            status="super_active",
            evidence_level=1,
            baseline_comparison="charge density",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [bad_entry],
        )
        errors = validate_registry()
        assert any("unknown status" in e for e in errors)

    def test_detects_duplicate_module_ids(self, monkeypatch):
        dup_entry = SimulationModuleEntry(
            module_id="duplicate",
            name="Dup1",
            description="test",
            status="active",
            evidence_level=1,
            baseline_comparison="charge density",
            scope=[],
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.module_registry.SIMULATION_MODULE_REGISTRY",
            [dup_entry, dup_entry],
        )
        errors = validate_registry()
        assert any("Duplicate module_id" in e for e in errors)


class TestProofLadderLevels:
    def test_proof_ladder_levels_are_imported(self):
        assert isinstance(PROOF_LADDER_LEVELS, dict)
        assert set(PROOF_LADDER_LEVELS.keys()) == {1, 2, 3, 4, 5, 6}
