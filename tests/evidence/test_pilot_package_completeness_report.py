"""Tests for PilotPackageCompletenessReport (PPC-) schema — Phase K K3."""

import pytest
from openamp_foundry.evidence.pilot_package_completeness_report import (
    BCM_PREFIX,
    BSP_PREFIX,
    CCS_PREFIX,
    ESC_PREFIX,
    NOTES_MAX_LENGTH,
    PEP_PREFIX,
    PPC_PREFIX,
    PRE_PREFIX,
    PSC_PREFIX,
    PilotPackageCompletenessReport,
    PilotPackageCompletenessReportResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> PilotPackageCompletenessReport:
    defaults = dict(
        ppc_id="PPC-001",
        pipeline_version="v0.10.15",
        pep_id="PEP-007",
        esc_id="ESC-007",
        ccs_id="CCS-007",
        bsp_id="BSP-007",
        psc_id="PSC-007",
        pre_id="PRE-007",
        bcm_id="BCM-007",
        checked_date="2026-07-10",
        completeness_confirmed=True,
        notes="All components verified by automated check.",
    )
    defaults.update(kwargs)
    return PilotPackageCompletenessReport(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_report_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, PilotPackageCompletenessReportResult)

    def test_valid_no_warnings_with_notes(self):
        r = validate(_make(notes="Checked by pipeline v0.10.15."))
        assert r.valid
        assert r.warnings == []

    def test_valid_different_suffixes(self):
        r = validate(_make(
            pep_id="PEP-999",
            esc_id="ESC-001",
            ccs_id="CCS-042",
            bsp_id="BSP-013",
            psc_id="PSC-007",
            pre_id="PRE-003",
            bcm_id="BCM-099",
        ))
        assert r.valid

    def test_valid_with_long_notes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- ppc_id validation ---

class TestPpcIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(ppc_id="ESC-001"))
        assert not r.valid
        assert any("ppc_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(ppc_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(ppc_id="ppc-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(ppc_id="PPC-999"))
        assert r.valid


# --- pipeline_version validation ---

class TestPipelineVersionValidation:
    def test_empty_fails(self):
        r = validate(_make(pipeline_version=""))
        assert not r.valid
        assert any("pipeline_version" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(pipeline_version="   "))
        assert not r.valid

    def test_valid_version(self):
        r = validate(_make(pipeline_version="v1.2.3"))
        assert r.valid


# --- pep_id validation ---

class TestPepIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(pep_id="CCS-007"))
        assert not r.valid
        assert any("pep_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(pep_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(pep_id="PEP-123"))
        assert r.valid


# --- esc_id validation ---

class TestEscIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(esc_id="PEP-007"))
        assert not r.valid
        assert any("esc_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(esc_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(esc_id="ESC-123"))
        assert r.valid


# --- ccs_id validation ---

class TestCcsIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(ccs_id="BSP-007"))
        assert not r.valid
        assert any("ccs_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(ccs_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(ccs_id="CCS-042"))
        assert r.valid


# --- bsp_id validation ---

class TestBspIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(bsp_id="CCS-007"))
        assert not r.valid
        assert any("bsp_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(bsp_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(bsp_id="BSP-013"))
        assert r.valid


# --- psc_id validation ---

class TestPscIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(psc_id="PRE-007"))
        assert not r.valid
        assert any("psc_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(psc_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(psc_id="PSC-007"))
        assert r.valid


# --- pre_id validation ---

class TestPreIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(pre_id="PSC-007"))
        assert not r.valid
        assert any("pre_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(pre_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(pre_id="PRE-003"))
        assert r.valid


# --- bcm_id validation ---

class TestBcmIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(bcm_id="CCS-007"))
        assert not r.valid
        assert any("bcm_id" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(bcm_id=""))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(bcm_id="BCM-099"))
        assert r.valid


# --- checked_date validation ---

class TestCheckedDateValidation:
    def test_valid_date(self):
        r = validate(_make(checked_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(checked_date="15/01/2026"))
        assert not r.valid
        assert any("checked_date" in e for e in r.errors)

    def test_empty_date(self):
        r = validate(_make(checked_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(checked_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(checked_date="July 10 2026"))
        assert not r.valid


# --- completeness_confirmed validation ---

class TestCompletenessConfirmedValidation:
    def test_false_fails(self):
        r = validate(_make(completeness_confirmed=False))
        assert not r.valid
        assert any("completeness_confirmed" in e for e in r.errors)

    def test_true_passes(self):
        r = validate(_make(completeness_confirmed=True))
        assert r.valid or all("completeness" not in e for e in r.errors)


# --- notes validation ---

class TestNotesValidation:
    def test_empty_notes_valid(self):
        r = validate(_make(notes=""))
        assert r.valid

    def test_notes_too_long_fails(self):
        r = validate(_make(notes="x" * (NOTES_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("notes" in e for e in r.errors)

    def test_notes_at_max_passes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- Warnings ---

class TestWarnings:
    def test_empty_notes_warns(self):
        r = validate(_make(notes=""))
        assert any("notes" in w or "documenting" in w for w in r.warnings)

    def test_duplicate_component_ids_warns(self):
        r = validate(_make(ccs_id="CCS-007", bsp_id="CCS-007"))
        assert any("identical" in w or "unique" in w for w in r.warnings)

    def test_pep_id_as_component_warns(self):
        r = validate(_make(
            pep_id="PEP-007",
            ccs_id="PEP-007",
        ))
        assert any("pep_id" in w or "PEP-" in w for w in r.warnings)

    def test_no_warnings_with_notes_and_unique_ids(self):
        r = validate(_make())
        assert r.warnings == []

    def test_three_duplicate_ids_single_warning(self):
        r = validate(_make(ccs_id="CCS-001", bsp_id="CCS-001", psc_id="CCS-001"))
        dup_warns = [w for w in r.warnings if "identical" in w or "unique" in w]
        assert len(dup_warns) == 1


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            ppc_id="PPC-001",
            pipeline_version="v0.10.15",
            pep_id="PEP-007",
            esc_id="ESC-007",
            ccs_id="CCS-007",
            bsp_id="BSP-007",
            psc_id="PSC-007",
            pre_id="PRE-007",
            bcm_id="BCM-007",
            checked_date="2026-07-10",
            completeness_confirmed=True,
            notes="Verified.",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(ppc_id="ESC-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_false_confirmed_fails(self):
        r = validate_dict(self._valid_dict(completeness_confirmed=False))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_ppc_prefix(self):
        assert PPC_PREFIX == "PPC-"

    def test_pep_prefix(self):
        assert PEP_PREFIX == "PEP-"

    def test_esc_prefix(self):
        assert ESC_PREFIX == "ESC-"

    def test_ccs_prefix(self):
        assert CCS_PREFIX == "CCS-"

    def test_bsp_prefix(self):
        assert BSP_PREFIX == "BSP-"

    def test_psc_prefix(self):
        assert PSC_PREFIX == "PSC-"

    def test_pre_prefix(self):
        assert PRE_PREFIX == "PRE-"

    def test_bcm_prefix(self):
        assert BCM_PREFIX == "BCM-"

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300
