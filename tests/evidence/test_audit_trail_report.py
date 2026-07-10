import pytest
from src.openamp_foundry.evidence.audit_trail_report import (
    VALID_TRAIL_COMPLETENESS_STATUSES,
    REQUIRED_ATR_STAGES,
    VALID_CHAIN_INTEGRITY_GRADES,
    AuditTrailReport,
    ATRValidationResult,
    validate_audit_trail_report,
    build_audit_trail_report,
    format_audit_trail_report,
)


def _valid_report(**kwargs):
    defaults = dict(
        atr_id="ATR-0001",
        candidate_family_id="AMPF-FAM-001",
        bsp_ids=["BSP-0001"],
        whr_ids=["WHR-0001"],
        pcu_ids=["PCU-0001"],
        hcr_ids=["HCR-0001"],
        pqg_id="PQG-0001",
        trail_completeness_status="complete",
        missing_stages=[],
        chain_integrity_grade="A",
        n_stages_complete=5,
        chain_link_failures=[],
        dry_lab_only=True,
        limitations="Single candidate family; multi-family trail not assessed.",
        notes="",
    )
    defaults.update(kwargs)
    return AuditTrailReport(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_trail_completeness_statuses_is_frozenset(self):
        assert isinstance(VALID_TRAIL_COMPLETENESS_STATUSES, frozenset)

    def test_trail_completeness_statuses_count(self):
        assert len(VALID_TRAIL_COMPLETENESS_STATUSES) == 4

    def test_complete_in_statuses(self):
        assert "complete" in VALID_TRAIL_COMPLETENESS_STATUSES

    def test_partial_in_statuses(self):
        assert "partial" in VALID_TRAIL_COMPLETENESS_STATUSES

    def test_dry_lab_only_in_statuses(self):
        assert "dry_lab_only" in VALID_TRAIL_COMPLETENESS_STATUSES

    def test_required_atr_stages_is_frozenset(self):
        assert isinstance(REQUIRED_ATR_STAGES, frozenset)

    def test_required_atr_stages_count(self):
        assert len(REQUIRED_ATR_STAGES) == 5

    def test_bsp_in_stages(self):
        assert "BSP" in REQUIRED_ATR_STAGES

    def test_whr_in_stages(self):
        assert "WHR" in REQUIRED_ATR_STAGES

    def test_pqg_in_stages(self):
        assert "PQG" in REQUIRED_ATR_STAGES

    def test_chain_integrity_grades_is_frozenset(self):
        assert isinstance(VALID_CHAIN_INTEGRITY_GRADES, frozenset)

    def test_chain_integrity_grades_count(self):
        assert len(VALID_CHAIN_INTEGRITY_GRADES) == 5

    def test_grade_a_in_grades(self):
        assert "A" in VALID_CHAIN_INTEGRITY_GRADES

    def test_grade_d_in_grades(self):
        assert "D" in VALID_CHAIN_INTEGRITY_GRADES

    def test_grade_na_in_grades(self):
        assert "N/A" in VALID_CHAIN_INTEGRITY_GRADES


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestAuditTrailReportDataclass:
    def test_instantiation(self):
        r = _valid_report()
        assert r.atr_id == "ATR-0001"

    def test_dry_lab_only_true(self):
        r = _valid_report()
        assert r.dry_lab_only is True

    def test_n_stages_complete(self):
        r = _valid_report()
        assert r.n_stages_complete == 5

    def test_pqg_id_optional(self):
        r = _valid_report(pqg_id=None, trail_completeness_status="partial", missing_stages=["PQG"], n_stages_complete=4)
        assert r.pqg_id is None

    def test_notes_empty(self):
        r = _valid_report(notes="")
        assert r.notes == ""


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateAuditTrailReport:
    def test_valid_report_passes(self):
        r = _valid_report()
        result = validate_audit_trail_report(r)
        assert result.valid

    def test_invalid_atr_id_prefix(self):
        r = _valid_report(atr_id="BAD-0001")
        result = validate_audit_trail_report(r)
        assert not result.valid
        assert any("atr_id" in v for v in result.violations)

    def test_empty_candidate_family_id_blocked(self):
        r = _valid_report(candidate_family_id="")
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_toy_candidate_family_id_blocked(self):
        r = _valid_report(candidate_family_id="TOY-FAM-001")
        result = validate_audit_trail_report(r)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_empty_bsp_ids_blocked(self):
        r = _valid_report(bsp_ids=[])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_bsp_id_prefix_blocked(self):
        r = _valid_report(bsp_ids=["BAD-0001"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_whr_id_prefix_blocked(self):
        r = _valid_report(whr_ids=["BAD-0001"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_pcu_id_prefix_blocked(self):
        r = _valid_report(pcu_ids=["BAD-0001"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_hcr_id_prefix_blocked(self):
        r = _valid_report(hcr_ids=["BAD-0001"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_pqg_id_prefix_blocked(self):
        r = _valid_report(pqg_id="BAD-0001")
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_trail_status_blocked(self):
        r = _valid_report(trail_completeness_status="done")
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_invalid_chain_grade_blocked(self):
        r = _valid_report(chain_integrity_grade="E")
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_n_stages_complete_negative_blocked(self):
        r = _valid_report(n_stages_complete=-1)
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_n_stages_complete_above_max_blocked(self):
        r = _valid_report(n_stages_complete=6)
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_complete_status_requires_whr(self):
        r = _valid_report(trail_completeness_status="complete", whr_ids=[])
        result = validate_audit_trail_report(r)
        assert not result.valid
        assert any("whr_id" in v for v in result.violations)

    def test_complete_status_requires_pcu(self):
        r = _valid_report(trail_completeness_status="complete", pcu_ids=[])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_complete_status_requires_hcr(self):
        r = _valid_report(trail_completeness_status="complete", hcr_ids=[])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_complete_status_requires_pqg(self):
        r = _valid_report(trail_completeness_status="complete", pqg_id=None)
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_complete_status_blocks_missing_stages(self):
        r = _valid_report(trail_completeness_status="complete", missing_stages=["PCU"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_complete_status_blocks_chain_failures(self):
        r = _valid_report(trail_completeness_status="complete", chain_link_failures=["WHR mismatch"])
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_dry_lab_only_status_blocks_whr(self):
        r = _valid_report(trail_completeness_status="dry_lab_only", whr_ids=["WHR-0001"], pcu_ids=[], hcr_ids=[], pqg_id=None)
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_grade_d_incompatible_with_complete_status(self):
        r = _valid_report(chain_integrity_grade="D")
        result = validate_audit_trail_report(r)
        assert not result.valid
        assert any("grade='D'" in v or "chain_integrity_grade='D'" in v for v in result.violations)

    def test_grade_a_requires_complete_or_partial(self):
        r = _valid_report(
            chain_integrity_grade="A",
            trail_completeness_status="broken_chain",
        )
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_dry_lab_only_field_false_blocked(self):
        r = _valid_report(dry_lab_only=False)
        result = validate_audit_trail_report(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_limitations_blocked(self):
        r = _valid_report(limitations="")
        result = validate_audit_trail_report(r)
        assert not result.valid

    def test_partial_status_valid_with_missing_stages(self):
        r = _valid_report(
            trail_completeness_status="partial",
            whr_ids=["WHR-0001"],
            pcu_ids=[],
            hcr_ids=[],
            pqg_id=None,
            missing_stages=["PCU", "HCR", "PQG"],
            chain_integrity_grade="B",
            n_stages_complete=2,
        )
        result = validate_audit_trail_report(r)
        assert result.valid

    def test_broken_chain_status_valid(self):
        r = _valid_report(
            trail_completeness_status="broken_chain",
            chain_link_failures=["WHR-0001 candidate_id mismatch"],
            chain_integrity_grade="C",
        )
        result = validate_audit_trail_report(r)
        assert result.valid

    def test_dry_lab_only_status_with_bsp_only_valid(self):
        r = _valid_report(
            trail_completeness_status="dry_lab_only",
            whr_ids=[],
            pcu_ids=[],
            hcr_ids=[],
            pqg_id=None,
            missing_stages=["WHR", "PCU", "HCR", "PQG"],
            chain_integrity_grade="N/A",
            n_stages_complete=1,
        )
        result = validate_audit_trail_report(r)
        assert result.valid

    def test_grade_b_valid(self):
        r = _valid_report(chain_integrity_grade="B")
        result = validate_audit_trail_report(r)
        assert result.valid

    def test_grade_na_valid_with_partial(self):
        r = _valid_report(
            trail_completeness_status="partial",
            pcu_ids=[],
            hcr_ids=[],
            pqg_id=None,
            missing_stages=["PCU", "HCR", "PQG"],
            chain_integrity_grade="N/A",
            n_stages_complete=2,
        )
        result = validate_audit_trail_report(r)
        assert result.valid


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildAuditTrailReport:
    def test_build_complete_trail(self):
        r = build_audit_trail_report(
            atr_id="ATR-0001",
            candidate_family_id="AMPF-FAM-001",
            bsp_ids=["BSP-0001"],
            whr_ids=["WHR-0001"],
            pcu_ids=["PCU-0001"],
            hcr_ids=["HCR-0001"],
            trail_completeness_status="complete",
            missing_stages=[],
            chain_integrity_grade="A",
            chain_link_failures=[],
            limitations="Single candidate family; multi-family trail not assessed.",
            pqg_id="PQG-0001",
        )
        assert r.atr_id == "ATR-0001"
        assert r.dry_lab_only is True
        assert r.n_stages_complete == 5

    def test_build_auto_computes_n_stages(self):
        r = build_audit_trail_report(
            atr_id="ATR-0002",
            candidate_family_id="AMPF-FAM-002",
            bsp_ids=["BSP-0002"],
            whr_ids=["WHR-0002"],
            pcu_ids=[],
            hcr_ids=[],
            trail_completeness_status="partial",
            missing_stages=["PCU", "HCR", "PQG"],
            chain_integrity_grade="B",
            chain_link_failures=[],
            limitations="PCU and HCR not yet available for this family.",
        )
        assert r.n_stages_complete == 2

    def test_build_enforces_dry_lab_only_true(self):
        r = build_audit_trail_report(
            atr_id="ATR-0003",
            candidate_family_id="AMPF-FAM-003",
            bsp_ids=["BSP-0003"],
            whr_ids=["WHR-0003"],
            pcu_ids=["PCU-0003"],
            hcr_ids=["HCR-0003"],
            trail_completeness_status="complete",
            missing_stages=[],
            chain_integrity_grade="A",
            chain_link_failures=[],
            limitations="Trail validated for single lab run only.",
            pqg_id="PQG-0003",
        )
        assert r.dry_lab_only is True

    def test_build_raises_on_toy_family(self):
        with pytest.raises(ValueError):
            build_audit_trail_report(
                atr_id="ATR-0004",
                candidate_family_id="TOY-FAM-001",
                bsp_ids=["BSP-0004"],
                whr_ids=["WHR-0004"],
                pcu_ids=["PCU-0004"],
                hcr_ids=["HCR-0004"],
                trail_completeness_status="complete",
                missing_stages=[],
                chain_integrity_grade="A",
                chain_link_failures=[],
                limitations="This should fail because of TOY- family.",
                pqg_id="PQG-0004",
            )

    def test_build_raises_on_complete_without_pqg(self):
        with pytest.raises(ValueError):
            build_audit_trail_report(
                atr_id="ATR-0005",
                candidate_family_id="AMPF-FAM-005",
                bsp_ids=["BSP-0005"],
                whr_ids=["WHR-0005"],
                pcu_ids=["PCU-0005"],
                hcr_ids=["HCR-0005"],
                trail_completeness_status="complete",
                missing_stages=[],
                chain_integrity_grade="A",
                chain_link_failures=[],
                limitations="PQG missing — should raise.",
                pqg_id=None,
            )

    def test_build_dry_lab_only_status(self):
        r = build_audit_trail_report(
            atr_id="ATR-0006",
            candidate_family_id="AMPF-FAM-006",
            bsp_ids=["BSP-0006"],
            whr_ids=[],
            pcu_ids=[],
            hcr_ids=[],
            trail_completeness_status="dry_lab_only",
            missing_stages=["WHR", "PCU", "HCR", "PQG"],
            chain_integrity_grade="N/A",
            chain_link_failures=[],
            limitations="Wet-lab experiments not yet started for this family.",
        )
        assert r.trail_completeness_status == "dry_lab_only"
        assert r.n_stages_complete == 1


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatAuditTrailReport:
    def _build(self, **kwargs):
        defaults = dict(
            atr_id="ATR-0001",
            candidate_family_id="AMPF-FAM-001",
            bsp_ids=["BSP-0001"],
            whr_ids=["WHR-0001"],
            pcu_ids=["PCU-0001"],
            hcr_ids=["HCR-0001"],
            trail_completeness_status="complete",
            missing_stages=[],
            chain_integrity_grade="A",
            chain_link_failures=[],
            limitations="Single candidate family; multi-family trail not assessed.",
            pqg_id="PQG-0001",
        )
        defaults.update(kwargs)
        return build_audit_trail_report(**defaults)

    def test_format_returns_string(self):
        r = self._build()
        assert isinstance(format_audit_trail_report(r), str)

    def test_format_contains_atr_id(self):
        r = self._build()
        assert "ATR-0001" in format_audit_trail_report(r)

    def test_format_contains_family_id(self):
        r = self._build()
        assert "AMPF-FAM-001" in format_audit_trail_report(r)

    def test_format_contains_trail_status(self):
        r = self._build()
        assert "complete" in format_audit_trail_report(r)

    def test_format_contains_chain_grade(self):
        r = self._build()
        assert "A" in format_audit_trail_report(r)

    def test_format_contains_bsp_id(self):
        r = self._build()
        assert "BSP-0001" in format_audit_trail_report(r)

    def test_format_contains_whr_id(self):
        r = self._build()
        assert "WHR-0001" in format_audit_trail_report(r)

    def test_format_contains_pqg_id(self):
        r = self._build()
        assert "PQG-0001" in format_audit_trail_report(r)

    def test_format_contains_stages_count(self):
        r = self._build()
        assert "5/5" in format_audit_trail_report(r)

    def test_format_contains_dry_lab_only_true(self):
        r = self._build()
        assert "dry_lab_only: True" in format_audit_trail_report(r)

    def test_format_contains_limitations(self):
        r = self._build()
        assert "Single candidate family" in format_audit_trail_report(r)

    def test_format_shows_missing_stages_when_present(self):
        r = self._build(
            trail_completeness_status="partial",
            whr_ids=["WHR-0001"],
            pcu_ids=[],
            hcr_ids=[],
            pqg_id=None,
            missing_stages=["PCU", "HCR", "PQG"],
            chain_integrity_grade="B",
        )
        assert "Missing Stages" in format_audit_trail_report(r)
        assert "PCU" in format_audit_trail_report(r)

    def test_format_shows_chain_failures_when_present(self):
        r = self._build(
            trail_completeness_status="broken_chain",
            chain_link_failures=["WHR-0001 mismatch"],
            chain_integrity_grade="C",
        )
        assert "Chain Link Failures" in format_audit_trail_report(r)

    def test_format_multiline(self):
        r = self._build()
        lines = format_audit_trail_report(r).split("\n")
        assert len(lines) >= 10
