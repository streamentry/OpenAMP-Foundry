"""Tests for the adapter declaration validator."""
from __future__ import annotations

import pytest

from openamp_foundry.adapters.adapter_validator import (
    AdapterDeclaration,
    AdapterValidationResult,
    validate_adapter_declaration,
    validate_adapter_dict,
    VALID_ADAPTER_MODES,
    VALID_OUTPUT_STATUSES,
    VALID_RANKING_EFFECTS,
    VALID_RELEASE_STATUSES,
    REQUIRED_OUTPUT_CONTRACT_FIELDS,
)


def make_valid_decl(**overrides) -> AdapterDeclaration:
    defaults = dict(
        adapter_id="test-adapter",
        adapter_version="1.0.0",
        mode="info",
        output_status="ok",
        score_fields={"activity": 0.72},
        uncertainty=0.15,
        warnings=[],
        failure_reason=None,
        release_status="internal",
        ranking_effect="none",
        has_baseline_comparison=False,
        makes_network_calls=False,
        network_call_documented=False,
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return AdapterDeclaration(**defaults)


class TestValidateAdapterDeclaration:
    def test_valid_minimal_declaration_passes(self):
        result = validate_adapter_declaration(make_valid_decl())
        assert result.passed is True
        assert result.errors == []

    def test_empty_adapter_id_fails(self):
        result = validate_adapter_declaration(make_valid_decl(adapter_id=""))
        assert result.passed is False
        assert any("adapter_id" in e for e in result.errors)

    def test_empty_adapter_version_fails(self):
        result = validate_adapter_declaration(make_valid_decl(adapter_version=""))
        assert result.passed is False
        assert any("adapter_version" in e for e in result.errors)

    def test_invalid_mode_fails(self):
        result = validate_adapter_declaration(make_valid_decl(mode="bogus"))
        assert result.passed is False
        assert any("mode" in e for e in result.errors)

    def test_invalid_output_status_fails(self):
        result = validate_adapter_declaration(make_valid_decl(output_status="bogus"))
        assert result.passed is False
        assert any("output_status" in e for e in result.errors)

    def test_invalid_ranking_effect_fails(self):
        result = validate_adapter_declaration(make_valid_decl(ranking_effect="bogus"))
        assert result.passed is False
        assert any("ranking_effect" in e for e in result.errors)

    def test_invalid_release_status_fails(self):
        result = validate_adapter_declaration(make_valid_decl(release_status="bogus"))
        assert result.passed is False
        assert any("release_status" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_adapter_declaration(make_valid_decl(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)

    def test_ranking_effect_active_without_baseline_fails(self):
        result = validate_adapter_declaration(
            make_valid_decl(ranking_effect="active", has_baseline_comparison=False)
        )
        assert result.passed is False
        assert any("baseline_comparison" in e for e in result.errors)

    def test_network_calls_without_documentation_fails(self):
        result = validate_adapter_declaration(
            make_valid_decl(makes_network_calls=True, network_call_documented=False)
        )
        assert result.passed is False
        assert any("network_call_documented" in e for e in result.errors)

    def test_deprecated_with_active_ranking_effect_fails(self):
        result = validate_adapter_declaration(
            make_valid_decl(mode="deprecated", ranking_effect="active")
        )
        assert result.passed is False
        assert any("deprecated" in e for e in result.errors)

    def test_uncertainty_outside_range_fails(self):
        result = validate_adapter_declaration(make_valid_decl(uncertainty=1.5))
        assert result.passed is False
        assert any("uncertainty" in e for e in result.errors)

    def test_uncertainty_none_passes(self):
        result = validate_adapter_declaration(make_valid_decl(uncertainty=None))
        assert result.passed is True

    def test_gated_mode_with_ranking_effect_none_warns(self):
        result = validate_adapter_declaration(
            make_valid_decl(mode="gated", ranking_effect="none")
        )
        assert result.passed is True
        assert any("unusual" in w for w in result.warnings_list)

    @pytest.mark.parametrize("mode", sorted(VALID_ADAPTER_MODES))
    def test_all_valid_modes_pass(self, mode):
        result = validate_adapter_declaration(make_valid_decl(mode=mode))
        assert result.passed is True

    @pytest.mark.parametrize("status", sorted(VALID_OUTPUT_STATUSES))
    def test_all_valid_output_statuses_pass(self, status):
        result = validate_adapter_declaration(make_valid_decl(output_status=status))
        assert result.passed is True

    def test_result_dry_lab_only_is_true(self):
        result = validate_adapter_declaration(make_valid_decl())
        assert result.dry_lab_only is True


class TestValidateAdapterDict:
    def test_valid_dict_passes(self):
        d = {
            "adapter_id": "example-adapter",
            "adapter_version": "1.0.0",
            "mode": "info",
            "output_status": "ok",
            "score_fields": {"activity": 0.72},
            "uncertainty": 0.15,
            "warnings": [],
            "failure_reason": None,
            "release_status": "internal",
            "ranking_effect": "none",
            "has_baseline_comparison": False,
            "makes_network_calls": False,
            "network_call_documented": False,
            "dry_lab_only": True,
        }
        result = validate_adapter_dict(d)
        assert result.passed is True

    def test_dict_missing_required_fields_fails(self):
        d = {"adapter_id": "test"}
        result = validate_adapter_dict(d)
        assert result.passed is False
        assert any("Missing required fields" in e for e in result.errors)

    def test_result_dry_lab_only_is_true(self):
        d = {
            "adapter_id": "example-adapter",
            "adapter_version": "1.0.0",
            "mode": "info",
            "output_status": "ok",
            "score_fields": {"activity": 0.72},
            "uncertainty": 0.15,
            "warnings": [],
            "failure_reason": None,
            "release_status": "internal",
            "ranking_effect": "none",
        }
        result = validate_adapter_dict(d)
        assert result.dry_lab_only is True


class TestConstants:
    def test_valid_adapter_modes_count(self):
        assert len(VALID_ADAPTER_MODES) == 4

    def test_valid_output_statuses_count(self):
        assert len(VALID_OUTPUT_STATUSES) == 4

    def test_valid_ranking_effects(self):
        assert "none" in VALID_RANKING_EFFECTS
        assert "proposed" in VALID_RANKING_EFFECTS
        assert "active" in VALID_RANKING_EFFECTS

    def test_valid_release_statuses_count(self):
        assert len(VALID_RELEASE_STATUSES) == 5

    def test_required_output_contract_fields_count(self):
        assert len(REQUIRED_OUTPUT_CONTRACT_FIELDS) == 10
