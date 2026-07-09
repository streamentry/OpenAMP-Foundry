"""Tests for calibration cycle summary schema — Phase P P5."""

import pytest
from openamp_foundry.evidence.calibration_cycle_summary import (
    CalibrationCycleSummaryEntry,
    validate_calibration_cycle_summary,
    validate_calibration_cycle_summary_dict,
    CCS_PREFIX,
    BSP_PREFIX,
    PSC_PREFIX,
    BOS_PREFIX,
    CPS_PREFIX,
    CBA_PREFIX,
    CRG_PREFIX,
    VALID_CYCLE_OUTCOMES,
    CYCLE_NOTES_MAX_LENGTH,
)


def _valid_entry(**kwargs) -> CalibrationCycleSummaryEntry:
    defaults = dict(
        ccs_id="CCS-001",
        pipeline_version="v1.0.0",
        bsp_id="BSP-001",
        psc_id="PSC-001",
        bos_id="BOS-001",
        cps_id="CPS-001",
        cba_id="CBA-001",
        crg_id_previous="CRG-001",
        crg_id_next="CRG-002",
        cycle_outcome="improved",
        cycle_notes="First calibration cycle complete.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return CalibrationCycleSummaryEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_calibration_cycle_summary(_valid_entry())
        assert r.ccs_id == "CCS-001"
        assert r.bsp_id == "BSP-001"
        assert r.psc_id == "PSC-001"
        assert r.bos_id == "BOS-001"
        assert r.cps_id == "CPS-001"
        assert r.cba_id == "CBA-001"
        assert r.crg_id_previous == "CRG-001"
        assert r.crg_id_next == "CRG-002"
        assert r.cycle_outcome == "improved"
        assert r.dry_lab_only is True

    def test_stable_outcome_passes(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(cycle_outcome="stable")
        )
        assert r.passed

    def test_degraded_outcome_passes_with_warning(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(cycle_outcome="degraded")
        )
        assert r.passed
        assert any("degraded" in w for w in r.warnings)

    def test_dry_lab_warns(self):
        r = validate_calibration_cycle_summary(_valid_entry(dry_lab_only=True))
        assert r.passed
        assert any("synthetic" in w or "dry_lab" in w or "computational" in w for w in r.warnings)

    def test_no_dry_lab_warning_when_false(self):
        r = validate_calibration_cycle_summary(_valid_entry(dry_lab_only=False))
        assert r.passed
        assert not any("dry_lab_only=True" in w for w in r.warnings)

    def test_empty_cycle_notes_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(cycle_notes=""))
        assert r.passed

    def test_max_length_notes_passes(self):
        notes = "c" * CYCLE_NOTES_MAX_LENGTH
        r = validate_calibration_cycle_summary(_valid_entry(cycle_notes=notes))
        assert r.passed

    def test_different_crg_ids_passes(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_previous="CRG-001", crg_id_next="CRG-002")
        )
        assert r.passed


class TestCcsIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(ccs_id="001"))
        assert not r.passed
        assert any("ccs_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(ccs_id="CRG-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(ccs_id="ccs-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(ccs_id="CCS-"))
        assert r.passed


class TestArtifactIdValidation:
    def test_invalid_bsp_id_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(bsp_id="001"))
        assert not r.passed
        assert any("bsp_id" in e for e in r.errors)

    def test_invalid_psc_id_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(psc_id="001"))
        assert not r.passed
        assert any("psc_id" in e for e in r.errors)

    def test_invalid_bos_id_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(bos_id="001"))
        assert not r.passed
        assert any("bos_id" in e for e in r.errors)

    def test_invalid_cps_id_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(cps_id="001"))
        assert not r.passed
        assert any("cps_id" in e for e in r.errors)

    def test_invalid_cba_id_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(cba_id="001"))
        assert not r.passed
        assert any("cba_id" in e for e in r.errors)

    def test_wrong_prefix_bsp_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(bsp_id="CCS-001"))
        assert not r.passed

    def test_correct_prefix_bsp_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(bsp_id="BSP-999"))
        assert r.passed

    def test_correct_prefix_psc_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(psc_id="PSC-999"))
        assert r.passed

    def test_correct_prefix_bos_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(bos_id="BOS-999"))
        assert r.passed

    def test_correct_prefix_cps_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(cps_id="CPS-999"))
        assert r.passed

    def test_correct_prefix_cba_passes(self):
        r = validate_calibration_cycle_summary(_valid_entry(cba_id="CBA-999"))
        assert r.passed


class TestCrgIdValidation:
    def test_invalid_crg_previous_fails(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_previous="001")
        )
        assert not r.passed
        assert any("crg_id_previous" in e for e in r.errors)

    def test_invalid_crg_next_fails(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_next="001")
        )
        assert not r.passed
        assert any("crg_id_next" in e for e in r.errors)

    def test_same_crg_ids_fails(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_previous="CRG-001", crg_id_next="CRG-001")
        )
        assert not r.passed
        assert any("differ" in e for e in r.errors)

    def test_different_crg_ids_passes(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_previous="CRG-001", crg_id_next="CRG-002")
        )
        assert r.passed

    def test_wrong_prefix_crg_previous_fails(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(crg_id_previous="CPS-001")
        )
        assert not r.passed


class TestCycleOutcomeValidation:
    def test_invalid_outcome_fails(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(cycle_outcome="worsened")
        )
        assert not r.passed
        assert any("cycle_outcome" in e for e in r.errors)

    def test_empty_outcome_fails(self):
        r = validate_calibration_cycle_summary(_valid_entry(cycle_outcome=""))
        assert not r.passed

    @pytest.mark.parametrize("outcome", sorted(VALID_CYCLE_OUTCOMES))
    def test_all_valid_outcomes(self, outcome):
        r = validate_calibration_cycle_summary(_valid_entry(cycle_outcome=outcome))
        assert r.passed or all("cycle_outcome" not in e for e in r.errors)

    def test_improved_passes_without_warning(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(cycle_outcome="improved", dry_lab_only=False)
        )
        assert r.passed
        assert not any("degraded" in w for w in r.warnings)

    def test_stable_passes_without_degraded_warning(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(cycle_outcome="stable", dry_lab_only=False)
        )
        assert r.passed
        assert not any("degraded" in w for w in r.warnings)


class TestCycleNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "c" * (CYCLE_NOTES_MAX_LENGTH + 1)
        r = validate_calibration_cycle_summary(_valid_entry(cycle_notes=notes))
        assert not r.passed
        assert any("cycle_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "c" * CYCLE_NOTES_MAX_LENGTH
        r = validate_calibration_cycle_summary(_valid_entry(cycle_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            ccs_id="CCS-001",
            pipeline_version="v1.0.0",
            bsp_id="BSP-001",
            psc_id="PSC-001",
            bos_id="BOS-001",
            cps_id="CPS-001",
            cba_id="CBA-001",
            crg_id_previous="CRG-001",
            crg_id_next="CRG-002",
            cycle_outcome="improved",
            cycle_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_calibration_cycle_summary_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["cba_id"]
        r = validate_calibration_cycle_summary_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields(self):
        d = self._valid_dict()
        del d["cba_id"]
        del d["bos_id"]
        r = validate_calibration_cycle_summary_dict(d)
        assert not r.passed

    def test_dry_lab_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_calibration_cycle_summary_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_same_crg_ids_in_dict_fails(self):
        r = validate_calibration_cycle_summary_dict(
            self._valid_dict(crg_id_previous="CRG-001", crg_id_next="CRG-001")
        )
        assert not r.passed

    def test_invalid_outcome_in_dict_fails(self):
        r = validate_calibration_cycle_summary_dict(
            self._valid_dict(cycle_outcome="broken")
        )
        assert not r.passed


class TestMultipleErrors:
    def test_many_errors_accumulated(self):
        r = validate_calibration_cycle_summary(
            _valid_entry(
                ccs_id="bad",
                bsp_id="bad",
                psc_id="bad",
                bos_id="bad",
                cps_id="bad",
                cba_id="bad",
                crg_id_previous="bad",
                crg_id_next="bad",
                cycle_outcome="broken",
            )
        )
        assert not r.passed
        assert len(r.errors) >= 9


class TestConstants:
    def test_all_prefixes(self):
        assert CCS_PREFIX == "CCS-"
        assert BSP_PREFIX == "BSP-"
        assert PSC_PREFIX == "PSC-"
        assert BOS_PREFIX == "BOS-"
        assert CPS_PREFIX == "CPS-"
        assert CBA_PREFIX == "CBA-"
        assert CRG_PREFIX == "CRG-"

    def test_valid_outcomes(self):
        assert "improved" in VALID_CYCLE_OUTCOMES
        assert "stable" in VALID_CYCLE_OUTCOMES
        assert "degraded" in VALID_CYCLE_OUTCOMES
        assert len(VALID_CYCLE_OUTCOMES) == 3

    def test_notes_max_length(self):
        assert CYCLE_NOTES_MAX_LENGTH == 400
