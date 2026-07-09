"""Tests for pilot batch safety clearance schema — Phase P P4."""

import pytest
from openamp_foundry.evidence.pilot_batch_safety_clearance import (
    PilotBatchSafetyClearanceEntry,
    validate_pilot_batch_safety_clearance,
    validate_pilot_batch_safety_clearance_dict,
    PSC_PREFIX,
    BSP_PREFIX,
    VALID_RISK_TIERS,
    SAFETY_NOTES_MAX_LENGTH,
    HIGH_RISK_TIER,
    MODERATE_RISK_TIER,
)


def _valid_entry(**kwargs) -> PilotBatchSafetyClearanceEntry:
    defaults = dict(
        psc_id="PSC-001",
        bsp_id="BSP-001",
        pipeline_version="v1.0.0",
        dual_use_risk_checked=True,
        novelty_verified=True,
        toxicity_screened=True,
        hemolysis_screened=True,
        max_safety_risk_tier="low",
        cleared_for_synthesis=True,
        rejection_ids=[],
        safety_notes="All screens passed. Low risk.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PilotBatchSafetyClearanceEntry(**defaults)


class TestValidEntry:
    def test_valid_low_risk_passes(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry())
        assert r.psc_id == "PSC-001"
        assert r.bsp_id == "BSP-001"
        assert r.max_safety_risk_tier == "low"
        assert r.cleared_for_synthesis is True
        assert r.rejection_count == 0
        assert r.dry_lab_only is True

    def test_dry_lab_cleared_warns(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry())
        assert r.passed
        assert any("computational safety" in w or "dry_lab_only=True" in w for w in r.warnings)

    def test_moderate_risk_cleared_warns(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="moderate")
        )
        assert r.passed
        assert any("moderate" in w for w in r.warnings)

    def test_high_risk_not_cleared_passes(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(
                max_safety_risk_tier="high",
                cleared_for_synthesis=False,
            )
        )
        assert r.passed

    def test_rejection_ids_warns(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(rejection_ids=["CAND-001", "CAND-002"])
        )
        assert r.passed
        assert any("rejected" in w for w in r.warnings)
        assert r.rejection_count == 2

    def test_many_rejection_ids_truncated_in_warning(self):
        ids = [f"CAND-{i:03d}" for i in range(10)]
        r = validate_pilot_batch_safety_clearance(_valid_entry(rejection_ids=ids))
        assert r.passed
        assert r.rejection_count == 10
        assert any("..." in w for w in r.warnings)

    def test_empty_notes_passes(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(safety_notes=""))
        assert r.passed

    def test_max_length_notes_passes(self):
        notes = "s" * SAFETY_NOTES_MAX_LENGTH
        r = validate_pilot_batch_safety_clearance(_valid_entry(safety_notes=notes))
        assert r.passed

    def test_wet_lab_clearance_no_warning(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(dry_lab_only=False)
        )
        assert r.passed
        # no dry_lab_only warning when it's a real wet-lab safety assay
        assert not any("computational safety" in w for w in r.warnings)

    def test_not_cleared_passes(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(cleared_for_synthesis=False)
        )
        assert r.passed

    def test_empty_rejection_ids_passes(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(rejection_ids=[]))
        assert r.passed


class TestPscIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(psc_id="001"))
        assert not r.passed
        assert any("psc_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(psc_id="BSP-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(psc_id="psc-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(psc_id="PSC-"))
        assert r.passed


class TestBspIdValidation:
    def test_missing_bsp_prefix_fails(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(bsp_id="001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(bsp_id="PSC-001"))
        assert not r.passed

    def test_correct_prefix_passes(self):
        r = validate_pilot_batch_safety_clearance(_valid_entry(bsp_id="BSP-999"))
        assert r.passed


class TestSafetyScreenValidation:
    def test_dual_use_not_checked_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(dual_use_risk_checked=False)
        )
        assert not r.passed
        assert any("dual_use_risk_checked" in e for e in r.errors)

    def test_novelty_not_verified_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(novelty_verified=False)
        )
        assert not r.passed
        assert any("novelty_verified" in e for e in r.errors)

    def test_toxicity_not_screened_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(toxicity_screened=False)
        )
        assert not r.passed
        assert any("toxicity_screened" in e for e in r.errors)

    def test_hemolysis_not_screened_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(hemolysis_screened=False)
        )
        assert not r.passed
        assert any("hemolysis_screened" in e for e in r.errors)

    def test_all_screens_must_be_true(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(
                dual_use_risk_checked=False,
                novelty_verified=False,
                toxicity_screened=False,
                hemolysis_screened=False,
            )
        )
        assert not r.passed
        assert len(r.errors) >= 4


class TestRiskTierValidation:
    def test_invalid_tier_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="critical")
        )
        assert not r.passed
        assert any("max_safety_risk_tier" in e for e in r.errors)

    def test_empty_tier_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="")
        )
        assert not r.passed

    @pytest.mark.parametrize("tier", sorted(VALID_RISK_TIERS))
    def test_all_valid_tiers(self, tier):
        cleared = tier != HIGH_RISK_TIER
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier=tier, cleared_for_synthesis=cleared)
        )
        assert r.passed or all("max_safety_risk_tier" not in e for e in r.errors)

    def test_high_risk_cleared_fails(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(
                max_safety_risk_tier="high",
                cleared_for_synthesis=True,
            )
        )
        assert not r.passed
        assert any("high" in e for e in r.errors)

    def test_high_risk_not_cleared_passes(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(
                max_safety_risk_tier="high",
                cleared_for_synthesis=False,
            )
        )
        assert r.passed

    def test_low_risk_cleared_passes(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="low", cleared_for_synthesis=True)
        )
        assert r.passed

    def test_moderate_risk_cleared_passes_with_warning(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="moderate", cleared_for_synthesis=True)
        )
        assert r.passed
        assert any("moderate" in w for w in r.warnings)

    def test_moderate_risk_not_cleared_passes(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(max_safety_risk_tier="moderate", cleared_for_synthesis=False)
        )
        assert r.passed


class TestSafetyNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "n" * (SAFETY_NOTES_MAX_LENGTH + 1)
        r = validate_pilot_batch_safety_clearance(_valid_entry(safety_notes=notes))
        assert not r.passed
        assert any("safety_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "n" * SAFETY_NOTES_MAX_LENGTH
        r = validate_pilot_batch_safety_clearance(_valid_entry(safety_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            psc_id="PSC-001",
            bsp_id="BSP-001",
            pipeline_version="v1.0.0",
            dual_use_risk_checked=True,
            novelty_verified=True,
            toxicity_screened=True,
            hemolysis_screened=True,
            max_safety_risk_tier="low",
            cleared_for_synthesis=True,
            rejection_ids=[],
            safety_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_pilot_batch_safety_clearance_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["toxicity_screened"]
        r = validate_pilot_batch_safety_clearance_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields(self):
        d = self._valid_dict()
        del d["toxicity_screened"]
        del d["hemolysis_screened"]
        r = validate_pilot_batch_safety_clearance_dict(d)
        assert not r.passed

    def test_dry_lab_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_pilot_batch_safety_clearance_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_high_risk_cleared_in_dict_fails(self):
        r = validate_pilot_batch_safety_clearance_dict(
            self._valid_dict(max_safety_risk_tier="high", cleared_for_synthesis=True)
        )
        assert not r.passed

    def test_screens_false_in_dict_fails(self):
        r = validate_pilot_batch_safety_clearance_dict(
            self._valid_dict(dual_use_risk_checked=False)
        )
        assert not r.passed


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_pilot_batch_safety_clearance(
            _valid_entry(
                psc_id="wrong",
                bsp_id="wrong",
                dual_use_risk_checked=False,
                novelty_verified=False,
                toxicity_screened=False,
                hemolysis_screened=False,
                max_safety_risk_tier="invalid",
            )
        )
        assert not r.passed
        assert len(r.errors) >= 6


class TestConstants:
    def test_psc_prefix(self):
        assert PSC_PREFIX == "PSC-"

    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_valid_risk_tiers(self):
        assert "low" in VALID_RISK_TIERS
        assert "moderate" in VALID_RISK_TIERS
        assert "high" in VALID_RISK_TIERS
        assert len(VALID_RISK_TIERS) == 3

    def test_safety_notes_max_length(self):
        assert SAFETY_NOTES_MAX_LENGTH == 400

    def test_high_risk_tier(self):
        assert HIGH_RISK_TIER == "high"

    def test_moderate_risk_tier(self):
        assert MODERATE_RISK_TIER == "moderate"
