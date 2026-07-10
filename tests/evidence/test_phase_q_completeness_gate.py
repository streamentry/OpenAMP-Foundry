import pytest
from src.openamp_foundry.evidence.phase_q_completeness_gate import (
    REQUIRED_RECORD_TYPES,
    VALID_LOOP_VERDICTS,
    PhaseQCompletenessGate,
    PhaseQGateResult,
    validate_phase_q_completeness_gate,
    build_phase_q_completeness_gate,
    format_phase_q_completeness_gate,
)


def _valid_gate(**kwargs):
    defaults = dict(
        gate_id="PQG-0001",
        candidate_family_id="AMPF-FAM-001",
        bsp_ids=["BSP-0001"],
        whr_ids=["WHR-0001"],
        pcu_ids=["PCU-0001"],
        hcr_ids=["HCR-0001"],
        loop_verdict="loop_complete",
        missing_record_types=[],
        cross_link_failures=[],
        n_candidates_with_whr=3,
        n_candidates_with_hcr=2,
        dry_lab_only=False,
        notes="",
    )
    defaults.update(kwargs)
    return PhaseQCompletenessGate(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_required_record_types_is_frozenset(self):
        assert isinstance(REQUIRED_RECORD_TYPES, frozenset)

    def test_required_record_types_count(self):
        assert len(REQUIRED_RECORD_TYPES) == 4

    def test_bsp_in_required_types(self):
        assert "BSP" in REQUIRED_RECORD_TYPES

    def test_whr_in_required_types(self):
        assert "WHR" in REQUIRED_RECORD_TYPES

    def test_pcu_in_required_types(self):
        assert "PCU" in REQUIRED_RECORD_TYPES

    def test_hcr_in_required_types(self):
        assert "HCR" in REQUIRED_RECORD_TYPES

    def test_valid_loop_verdicts_is_frozenset(self):
        assert isinstance(VALID_LOOP_VERDICTS, frozenset)

    def test_valid_loop_verdicts_count(self):
        assert len(VALID_LOOP_VERDICTS) == 4

    def test_loop_complete_in_verdicts(self):
        assert "loop_complete" in VALID_LOOP_VERDICTS

    def test_loop_partial_in_verdicts(self):
        assert "loop_partial" in VALID_LOOP_VERDICTS

    def test_loop_not_started_in_verdicts(self):
        assert "loop_not_started" in VALID_LOOP_VERDICTS

    def test_loop_broken_in_verdicts(self):
        assert "loop_broken" in VALID_LOOP_VERDICTS


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestPhaseQCompletenessGateDataclass:
    def test_instantiation(self):
        g = _valid_gate()
        assert g.gate_id == "PQG-0001"

    def test_dry_lab_only_false(self):
        g = _valid_gate()
        assert g.dry_lab_only is False

    def test_bsp_ids_list(self):
        g = _valid_gate(bsp_ids=["BSP-0001", "BSP-0002"])
        assert len(g.bsp_ids) == 2

    def test_missing_record_types_empty_list(self):
        g = _valid_gate()
        assert g.missing_record_types == []

    def test_cross_link_failures_empty_list(self):
        g = _valid_gate()
        assert g.cross_link_failures == []

    def test_notes_default_empty(self):
        g = _valid_gate(notes="")
        assert g.notes == ""


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidatePhaseQCompletenessGate:
    def test_valid_gate_passes(self):
        g = _valid_gate()
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_invalid_gate_id_prefix(self):
        g = _valid_gate(gate_id="BAD-0001")
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("gate_id" in v for v in result.violations)

    def test_empty_candidate_family_id_blocked(self):
        g = _valid_gate(candidate_family_id="")
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_toy_candidate_family_id_blocked(self):
        g = _valid_gate(candidate_family_id="TOY-FAM-001")
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("TOY-" in v for v in result.violations)

    def test_empty_bsp_ids_blocked(self):
        g = _valid_gate(bsp_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_invalid_bsp_id_prefix_blocked(self):
        g = _valid_gate(bsp_ids=["BAD-0001"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_invalid_loop_verdict_blocked(self):
        g = _valid_gate(loop_verdict="definitely_complete")
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_loop_complete_requires_whr_ids(self):
        g = _valid_gate(loop_verdict="loop_complete", whr_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("whr_id" in v for v in result.violations)

    def test_loop_complete_requires_pcu_ids(self):
        g = _valid_gate(loop_verdict="loop_complete", pcu_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("pcu_id" in v for v in result.violations)

    def test_loop_complete_requires_hcr_ids(self):
        g = _valid_gate(loop_verdict="loop_complete", hcr_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("hcr_id" in v for v in result.violations)

    def test_loop_complete_blocks_cross_link_failures(self):
        g = _valid_gate(loop_verdict="loop_complete", cross_link_failures=["candidate mismatch"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("cross_link_failures" in v for v in result.violations)

    def test_loop_complete_blocks_missing_record_types(self):
        g = _valid_gate(loop_verdict="loop_complete", missing_record_types=["PCU"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("missing_record_types" in v for v in result.violations)

    def test_loop_not_started_with_whr_blocked(self):
        g = _valid_gate(loop_verdict="loop_not_started", whr_ids=["WHR-0001"], pcu_ids=[], hcr_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("loop_not_started" in v for v in result.violations)

    def test_loop_not_started_with_pcu_blocked(self):
        g = _valid_gate(loop_verdict="loop_not_started", whr_ids=[], pcu_ids=["PCU-0001"], hcr_ids=[])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_loop_not_started_with_hcr_blocked(self):
        g = _valid_gate(loop_verdict="loop_not_started", whr_ids=[], pcu_ids=[], hcr_ids=["HCR-0001"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_invalid_whr_id_prefix_blocked(self):
        g = _valid_gate(whr_ids=["BAD-0001"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_invalid_pcu_id_prefix_blocked(self):
        g = _valid_gate(pcu_ids=["BAD-0001"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_invalid_hcr_id_prefix_blocked(self):
        g = _valid_gate(hcr_ids=["BAD-0001"])
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_n_candidates_with_whr_negative_blocked(self):
        g = _valid_gate(n_candidates_with_whr=-1)
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed

    def test_n_candidates_with_hcr_exceeds_whr_blocked(self):
        g = _valid_gate(n_candidates_with_whr=2, n_candidates_with_hcr=3)
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("n_candidates_with_hcr" in v for v in result.violations)

    def test_dry_lab_only_true_blocked(self):
        g = _valid_gate(dry_lab_only=True)
        result = validate_phase_q_completeness_gate(g)
        assert not result.passed
        assert any("dry_lab_only" in v for v in result.violations)

    def test_loop_partial_valid_with_some_missing(self):
        g = _valid_gate(
            loop_verdict="loop_partial",
            whr_ids=["WHR-0001"],
            pcu_ids=[],
            hcr_ids=[],
            missing_record_types=["PCU", "HCR"],
        )
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_loop_broken_with_failures_valid(self):
        g = _valid_gate(
            loop_verdict="loop_broken",
            cross_link_failures=["WHR candidate_id does not match BSP candidate_id"],
        )
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_loop_not_started_with_no_wet_lab_records_valid(self):
        g = _valid_gate(
            loop_verdict="loop_not_started",
            whr_ids=[],
            pcu_ids=[],
            hcr_ids=[],
            missing_record_types=["WHR", "PCU", "HCR"],
            n_candidates_with_whr=0,
            n_candidates_with_hcr=0,
        )
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_multiple_bsp_ids_valid(self):
        g = _valid_gate(bsp_ids=["BSP-0001", "BSP-0002"])
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_multiple_whr_ids_valid(self):
        g = _valid_gate(whr_ids=["WHR-0001", "WHR-0002", "WHR-0003"])
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_n_candidates_with_hcr_equal_whr_valid(self):
        g = _valid_gate(n_candidates_with_whr=5, n_candidates_with_hcr=5)
        result = validate_phase_q_completeness_gate(g)
        assert result.passed

    def test_n_candidates_with_hcr_zero_valid(self):
        g = _valid_gate(n_candidates_with_hcr=0)
        result = validate_phase_q_completeness_gate(g)
        assert result.passed


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildPhaseQCompletenessGate:
    def test_build_valid_complete_loop(self):
        g = build_phase_q_completeness_gate(
            gate_id="PQG-0001",
            candidate_family_id="AMPF-FAM-001",
            bsp_ids=["BSP-0001"],
            whr_ids=["WHR-0001"],
            pcu_ids=["PCU-0001"],
            hcr_ids=["HCR-0001"],
            loop_verdict="loop_complete",
            missing_record_types=[],
            cross_link_failures=[],
            n_candidates_with_whr=3,
            n_candidates_with_hcr=2,
        )
        assert g.gate_id == "PQG-0001"
        assert g.dry_lab_only is False
        assert g.loop_verdict == "loop_complete"

    def test_build_enforces_dry_lab_only_false(self):
        g = build_phase_q_completeness_gate(
            gate_id="PQG-0002",
            candidate_family_id="AMPF-FAM-002",
            bsp_ids=["BSP-0002"],
            whr_ids=["WHR-0002"],
            pcu_ids=["PCU-0002"],
            hcr_ids=["HCR-0002"],
            loop_verdict="loop_complete",
            missing_record_types=[],
            cross_link_failures=[],
            n_candidates_with_whr=2,
            n_candidates_with_hcr=1,
        )
        assert g.dry_lab_only is False

    def test_build_raises_on_toy_family_id(self):
        with pytest.raises(ValueError):
            build_phase_q_completeness_gate(
                gate_id="PQG-0003",
                candidate_family_id="TOY-FAM-001",
                bsp_ids=["BSP-0003"],
                whr_ids=["WHR-0003"],
                pcu_ids=["PCU-0003"],
                hcr_ids=["HCR-0003"],
                loop_verdict="loop_complete",
                missing_record_types=[],
                cross_link_failures=[],
                n_candidates_with_whr=1,
                n_candidates_with_hcr=1,
            )

    def test_build_raises_on_invalid_verdict(self):
        with pytest.raises(ValueError):
            build_phase_q_completeness_gate(
                gate_id="PQG-0004",
                candidate_family_id="AMPF-FAM-004",
                bsp_ids=["BSP-0004"],
                whr_ids=["WHR-0004"],
                pcu_ids=["PCU-0004"],
                hcr_ids=["HCR-0004"],
                loop_verdict="totally_done",
                missing_record_types=[],
                cross_link_failures=[],
                n_candidates_with_whr=1,
                n_candidates_with_hcr=1,
            )

    def test_build_loop_partial(self):
        g = build_phase_q_completeness_gate(
            gate_id="PQG-0005",
            candidate_family_id="AMPF-FAM-005",
            bsp_ids=["BSP-0005"],
            whr_ids=["WHR-0005"],
            pcu_ids=[],
            hcr_ids=[],
            loop_verdict="loop_partial",
            missing_record_types=["PCU", "HCR"],
            cross_link_failures=[],
            n_candidates_with_whr=1,
            n_candidates_with_hcr=0,
        )
        assert g.loop_verdict == "loop_partial"
        assert "PCU" in g.missing_record_types

    def test_build_loop_not_started(self):
        g = build_phase_q_completeness_gate(
            gate_id="PQG-0006",
            candidate_family_id="AMPF-FAM-006",
            bsp_ids=["BSP-0006"],
            whr_ids=[],
            pcu_ids=[],
            hcr_ids=[],
            loop_verdict="loop_not_started",
            missing_record_types=["WHR", "PCU", "HCR"],
            cross_link_failures=[],
            n_candidates_with_whr=0,
            n_candidates_with_hcr=0,
        )
        assert g.loop_verdict == "loop_not_started"

    def test_build_raises_on_missing_bsp(self):
        with pytest.raises(ValueError):
            build_phase_q_completeness_gate(
                gate_id="PQG-0007",
                candidate_family_id="AMPF-FAM-007",
                bsp_ids=[],
                whr_ids=["WHR-0007"],
                pcu_ids=["PCU-0007"],
                hcr_ids=["HCR-0007"],
                loop_verdict="loop_complete",
                missing_record_types=[],
                cross_link_failures=[],
                n_candidates_with_whr=1,
                n_candidates_with_hcr=1,
            )


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatPhaseQCompletenessGate:
    def _build(self, **kwargs):
        defaults = dict(
            gate_id="PQG-0001",
            candidate_family_id="AMPF-FAM-001",
            bsp_ids=["BSP-0001"],
            whr_ids=["WHR-0001"],
            pcu_ids=["PCU-0001"],
            hcr_ids=["HCR-0001"],
            loop_verdict="loop_complete",
            missing_record_types=[],
            cross_link_failures=[],
            n_candidates_with_whr=3,
            n_candidates_with_hcr=2,
        )
        defaults.update(kwargs)
        return build_phase_q_completeness_gate(**defaults)

    def test_format_returns_string(self):
        g = self._build()
        assert isinstance(format_phase_q_completeness_gate(g), str)

    def test_format_contains_gate_id(self):
        g = self._build()
        assert "PQG-0001" in format_phase_q_completeness_gate(g)

    def test_format_contains_family_id(self):
        g = self._build()
        assert "AMPF-FAM-001" in format_phase_q_completeness_gate(g)

    def test_format_contains_loop_verdict(self):
        g = self._build()
        assert "loop_complete" in format_phase_q_completeness_gate(g)

    def test_format_contains_bsp_ids(self):
        g = self._build()
        assert "BSP-0001" in format_phase_q_completeness_gate(g)

    def test_format_contains_whr_ids(self):
        g = self._build()
        assert "WHR-0001" in format_phase_q_completeness_gate(g)

    def test_format_contains_pcu_ids(self):
        g = self._build()
        assert "PCU-0001" in format_phase_q_completeness_gate(g)

    def test_format_contains_hcr_ids(self):
        g = self._build()
        assert "HCR-0001" in format_phase_q_completeness_gate(g)

    def test_format_contains_dry_lab_only_false(self):
        g = self._build()
        assert "dry_lab_only: False" in format_phase_q_completeness_gate(g)

    def test_format_contains_candidate_counts(self):
        g = self._build()
        out = format_phase_q_completeness_gate(g)
        assert "3" in out
        assert "2" in out

    def test_format_contains_missing_types_when_present(self):
        g = self._build(
            loop_verdict="loop_partial",
            whr_ids=["WHR-0001"],
            pcu_ids=[],
            hcr_ids=[],
            missing_record_types=["PCU", "HCR"],
            n_candidates_with_hcr=0,
        )
        assert "Missing Record Types" in format_phase_q_completeness_gate(g)
        assert "PCU" in format_phase_q_completeness_gate(g)

    def test_format_omits_missing_types_when_empty(self):
        g = self._build()
        assert "Missing Record Types" not in format_phase_q_completeness_gate(g)

    def test_format_contains_cross_link_failures_when_present(self):
        g = self._build(
            loop_verdict="loop_broken",
            cross_link_failures=["WHR-0001 candidate_id mismatch"],
        )
        assert "Cross-Link Failures" in format_phase_q_completeness_gate(g)

    def test_format_omits_cross_link_failures_when_empty(self):
        g = self._build()
        assert "Cross-Link Failures" not in format_phase_q_completeness_gate(g)

    def test_format_multiline(self):
        g = self._build()
        lines = format_phase_q_completeness_gate(g).split("\n")
        assert len(lines) >= 8
