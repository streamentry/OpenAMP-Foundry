"""Tests for simulation baseline registry (Phase H H3)."""

from __future__ import annotations

from openamp_foundry.simulation.baseline_registry import (
    BASELINE_DECLARATIONS,
    BaselineDeclaration,
    VALID_BASELINE_TYPES,
    check_baseline_requirement,
    get_baseline_declaration,
    list_baseline_declarations,
    validate_baseline_declarations,
)


class TestBaselineDeclarations:
    def test_has_at_least_4_entries(self):
        assert len(BASELINE_DECLARATIONS) >= 4

    def test_all_entries_pass_validation(self):
        errors = validate_baseline_declarations()
        assert errors == [], f"Validation errors: {errors}"

    def test_get_baseline_declaration_known_id(self):
        entry = get_baseline_declaration("membrane_proxy")
        assert entry is not None
        assert entry.module_id == "membrane_proxy"
        assert entry.baseline_description == "charge density (net charge at pH 7.4)"

    def test_get_baseline_declaration_unknown_id(self):
        entry = get_baseline_declaration("nonexistent_module")
        assert entry is None

    def test_list_baseline_declarations_returns_all(self):
        entries = list_baseline_declarations()
        assert len(entries) == len(BASELINE_DECLARATIONS)

    def test_each_entry_has_non_empty_module_id(self):
        for entry in BASELINE_DECLARATIONS:
            assert entry.module_id, f"Empty module_id in {entry}"

    def test_each_entry_has_non_empty_baseline_description(self):
        for entry in BASELINE_DECLARATIONS:
            assert entry.baseline_description, f"Empty baseline_description in {entry.module_id}"

    def test_baseline_type_in_valid_set(self):
        for entry in BASELINE_DECLARATIONS:
            assert entry.baseline_type in VALID_BASELINE_TYPES, (
                f"Invalid baseline_type '{entry.baseline_type}' in {entry.module_id}"
            )


class TestCheckBaselineRequirement:
    def test_baseline_beaten_no_cap(self):
        result = check_baseline_requirement("membrane_proxy", 2, baseline_beaten=True)
        assert result["capped"] is False
        assert result["effective_evidence_level"] == 2
        assert result["claimed_evidence_level"] == 2
        assert result["baseline_beaten"] is True

    def test_baseline_not_beaten_claimed_above_ceiling_capped(self):
        result = check_baseline_requirement("membrane_proxy", 5, baseline_beaten=False)
        assert result["capped"] is True
        assert result["effective_evidence_level"] == 1
        assert result["claimed_evidence_level"] == 5

    def test_baseline_not_beaten_claimed_at_or_below_ceiling_no_cap(self):
        result = check_baseline_requirement("membrane_proxy", 1, baseline_beaten=False)
        assert result["capped"] is False
        assert result["effective_evidence_level"] == 1
        assert result["claimed_evidence_level"] == 1

    def test_dry_lab_only_always_true(self):
        result = check_baseline_requirement("membrane_proxy", 2, baseline_beaten=False)
        assert result["dry_lab_only"] is True

    def test_unknown_module_id_returns_no_cap(self):
        result = check_baseline_requirement("unknown_module", 3, baseline_beaten=False)
        assert result["capped"] is False
        assert result["effective_evidence_level"] == 3
        assert "No baseline declaration found" in result["message"]


class TestValidateBaselineDeclarations:
    def test_returns_empty_for_valid_registry(self):
        errors = validate_baseline_declarations()
        assert errors == []

    def test_detects_duplicate_module_id(self, monkeypatch):
        dup = BaselineDeclaration(
            module_id="membrane_proxy",
            module_name="Dup",
            baseline_description="test",
            baseline_type="constant",
            evidence_level_ceiling=1,
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.baseline_registry.BASELINE_DECLARATIONS",
            BASELINE_DECLARATIONS + [dup],
        )
        errors = validate_baseline_declarations()
        dup_errors = [e for e in errors if "Duplicate" in e and "membrane_proxy" in e]
        assert len(dup_errors) >= 1

    def test_detects_invalid_baseline_type(self, monkeypatch):
        bad = BaselineDeclaration(
            module_id="test_bad_type",
            module_name="Bad",
            baseline_description="test",
            baseline_type="invalid_type",
            evidence_level_ceiling=1,
        )
        monkeypatch.setattr(
            "openamp_foundry.simulation.baseline_registry.BASELINE_DECLARATIONS",
            [bad],
        )
        errors = validate_baseline_declarations()
        type_errors = [e for e in errors if "invalid_type" in e]
        assert len(type_errors) >= 1
