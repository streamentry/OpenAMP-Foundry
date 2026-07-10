import pytest
from src.openamp_foundry.evidence.scientific_review_readiness_gate import (
    REQUIRED_SRG_ARTIFACT_TYPES,
    VALID_READINESS_VERDICTS,
    VALID_SAFETY_FLAG_TYPES,
    VALID_REVIEW_SCOPE_TYPES,
    ScientificReviewReadinessGate,
    SRGValidationResult,
    validate_scientific_review_readiness_gate,
    build_scientific_review_readiness_gate,
    format_scientific_review_readiness_gate,
)


def _valid_gate(**kwargs):
    defaults = dict(
        srg_id="SRG-0001",
        candidate_family_id="AMPF-FAM-001",
        cfc_id="CFC-0001",
        fnr_id="FNR-0001",
        atr_id="ATR-0001",
        pqg_id="PQG-0001",
        readiness_verdict="ready_for_external_review",
        safety_flags=["no_flags"],
        failed_gates=[],
        review_scope="trusted_partner",
        n_confirmed_hits=2,
        n_total_candidates=10,
        dry_lab_only=True,
        limitations="Single candidate family; multi-family review not performed.",
        notes="",
    )
    defaults.update(kwargs)
    return ScientificReviewReadinessGate(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_required_artifact_types_is_frozenset(self):
        assert isinstance(REQUIRED_SRG_ARTIFACT_TYPES, frozenset)

    def test_required_artifact_types_count(self):
        assert len(REQUIRED_SRG_ARTIFACT_TYPES) == 4

    def test_cfc_in_required_types(self):
        assert "CFC" in REQUIRED_SRG_ARTIFACT_TYPES

    def test_fnr_in_required_types(self):
        assert "FNR" in REQUIRED_SRG_ARTIFACT_TYPES

    def test_atr_in_required_types(self):
        assert "ATR" in REQUIRED_SRG_ARTIFACT_TYPES

    def test_pqg_in_required_types(self):
        assert "PQG" in REQUIRED_SRG_ARTIFACT_TYPES

    def test_readiness_verdicts_is_frozenset(self):
        assert isinstance(VALID_READINESS_VERDICTS, frozenset)

    def test_readiness_verdicts_count(self):
        assert len(VALID_READINESS_VERDICTS) == 4

    def test_ready_for_external_review_in_verdicts(self):
        assert "ready_for_external_review" in VALID_READINESS_VERDICTS

    def test_review_blocked_by_safety_in_verdicts(self):
        assert "review_blocked_by_safety" in VALID_READINESS_VERDICTS

    def test_safety_flag_types_is_frozenset(self):
        assert isinstance(VALID_SAFETY_FLAG_TYPES, frozenset)

    def test_no_flags_in_safety_types(self):
        assert "no_flags" in VALID_SAFETY_FLAG_TYPES

    def test_dual_use_concern_in_safety_types(self):
        assert "dual_use_concern" in VALID_SAFETY_FLAG_TYPES

    def test_review_scope_types_is_frozenset(self):
        assert isinstance(VALID_REVIEW_SCOPE_TYPES, frozenset)

    def test_open_preprint_in_scope_types(self):
        assert "open_preprint" in VALID_REVIEW_SCOPE_TYPES


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestScientificReviewReadinessGateDataclass:
    def test_instantiation(self):
        g = _valid_gate()
        assert g.srg_id == "SRG-0001"

    def test_dry_lab_only_true(self):
        g = _valid_gate()
        assert g.dry_lab_only is True

    def test_safety_flags_list(self):
        g = _valid_gate()
        assert "no_flags" in g.safety_flags

    def test_failed_gates_empty(self):
        g = _valid_gate()
        assert g.failed_gates == []

    def test_notes_default_empty(self):
        g = _valid_gate(notes="")
        assert g.notes == ""


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateScientificReviewReadinessGate:
    def test_valid_gate_passes(self):
        g = _valid_gate()
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed

    def test_invalid_srg_id_prefix(self):
        g = _valid_gate(srg_id="BAD-0001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("srg_id" in v for v in result.violations)

    def test_empty_candidate_family_id_blocked(self):
        g = _valid_gate(candidate_family_id="")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_toy_candidate_family_id_blocked(self):
        g = _valid_gate(candidate_family_id="TOY-FAM-001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("TOY-" in v for v in result.violations)

    def test_invalid_cfc_id_prefix(self):
        g = _valid_gate(cfc_id="BAD-0001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_fnr_id_prefix(self):
        g = _valid_gate(fnr_id="BAD-0001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_atr_id_prefix(self):
        g = _valid_gate(atr_id="BAD-0001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_pqg_id_prefix(self):
        g = _valid_gate(pqg_id="BAD-0001")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_readiness_verdict_blocked(self):
        g = _valid_gate(readiness_verdict="probably_ready")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_safety_flag_blocked(self):
        g = _valid_gate(safety_flags=["unknown_flag"])
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_invalid_review_scope_blocked(self):
        g = _valid_gate(review_scope="social_media")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_n_confirmed_hits_negative_blocked(self):
        g = _valid_gate(n_confirmed_hits=-1)
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_n_total_candidates_zero_blocked(self):
        g = _valid_gate(n_total_candidates=0)
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_n_confirmed_hits_exceeds_total_blocked(self):
        g = _valid_gate(n_confirmed_hits=11, n_total_candidates=10)
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_review_blocked_requires_real_safety_flag(self):
        g = _valid_gate(readiness_verdict="review_blocked_by_safety", safety_flags=["no_flags"])
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("real safety flag" in v for v in result.violations)

    def test_ready_for_review_blocks_safety_flags(self):
        g = _valid_gate(readiness_verdict="ready_for_external_review", safety_flags=["dual_use_concern"])
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("safety flags" in v for v in result.violations)

    def test_ready_for_review_blocks_failed_gates(self):
        g = _valid_gate(readiness_verdict="ready_for_external_review", failed_gates=["ATR incomplete"])
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_ready_for_review_requires_n_confirmed_hits_ge_1(self):
        g = _valid_gate(readiness_verdict="ready_for_external_review", n_confirmed_hits=0)
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("n_confirmed_hits" in v for v in result.violations)

    def test_no_flags_cannot_coexist_with_other_flags(self):
        g = _valid_gate(safety_flags=["no_flags", "dual_use_concern"])
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed
        assert any("no_flags" in v for v in result.violations)

    def test_open_preprint_blocked_with_review_blocked(self):
        g = _valid_gate(
            readiness_verdict="review_blocked_by_safety",
            safety_flags=["dual_use_concern"],
            review_scope="open_preprint",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_peer_review_blocked_with_not_ready(self):
        g = _valid_gate(
            readiness_verdict="not_ready",
            safety_flags=["no_flags"],
            failed_gates=["FNR incomplete"],
            review_scope="peer_review_submission",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_dry_lab_only_false_blocked(self):
        g = _valid_gate(dry_lab_only=False)
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_empty_limitations_blocked(self):
        g = _valid_gate(limitations="")
        result = validate_scientific_review_readiness_gate(g)
        assert not result.passed

    def test_not_ready_verdict_valid(self):
        g = _valid_gate(
            readiness_verdict="not_ready",
            safety_flags=["no_flags"],
            failed_gates=["ATR grade D"],
            review_scope="internal_only",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed

    def test_conditionally_ready_verdict_valid(self):
        g = _valid_gate(
            readiness_verdict="conditionally_ready",
            safety_flags=["no_flags"],
            review_scope="trusted_partner",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed

    def test_review_blocked_with_real_flag_valid(self):
        g = _valid_gate(
            readiness_verdict="review_blocked_by_safety",
            safety_flags=["unresolved_hemolysis"],
            review_scope="internal_only",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed

    def test_open_preprint_with_ready_valid(self):
        g = _valid_gate(
            readiness_verdict="ready_for_external_review",
            safety_flags=["no_flags"],
            review_scope="open_preprint",
            n_confirmed_hits=3,
        )
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed

    def test_peer_review_with_conditionally_ready_valid(self):
        g = _valid_gate(
            readiness_verdict="conditionally_ready",
            safety_flags=["no_flags"],
            review_scope="peer_review_submission",
        )
        result = validate_scientific_review_readiness_gate(g)
        assert result.passed


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildScientificReviewReadinessGate:
    def test_build_valid(self):
        g = build_scientific_review_readiness_gate(
            srg_id="SRG-0001",
            candidate_family_id="AMPF-FAM-001",
            cfc_id="CFC-0001",
            fnr_id="FNR-0001",
            atr_id="ATR-0001",
            pqg_id="PQG-0001",
            readiness_verdict="ready_for_external_review",
            safety_flags=["no_flags"],
            failed_gates=[],
            review_scope="trusted_partner",
            n_confirmed_hits=2,
            n_total_candidates=10,
            limitations="Single candidate family; multi-family review not performed.",
        )
        assert g.srg_id == "SRG-0001"
        assert g.dry_lab_only is True

    def test_build_enforces_dry_lab_only_true(self):
        g = build_scientific_review_readiness_gate(
            srg_id="SRG-0002",
            candidate_family_id="AMPF-FAM-002",
            cfc_id="CFC-0002",
            fnr_id="FNR-0002",
            atr_id="ATR-0002",
            pqg_id="PQG-0002",
            readiness_verdict="conditionally_ready",
            safety_flags=["no_flags"],
            failed_gates=[],
            review_scope="internal_only",
            n_confirmed_hits=1,
            n_total_candidates=5,
            limitations="Conditional readiness due to limited replicate count.",
        )
        assert g.dry_lab_only is True

    def test_build_raises_on_toy_family(self):
        with pytest.raises(ValueError):
            build_scientific_review_readiness_gate(
                srg_id="SRG-0003",
                candidate_family_id="TOY-FAM-001",
                cfc_id="CFC-0003",
                fnr_id="FNR-0003",
                atr_id="ATR-0003",
                pqg_id="PQG-0003",
                readiness_verdict="ready_for_external_review",
                safety_flags=["no_flags"],
                failed_gates=[],
                review_scope="trusted_partner",
                n_confirmed_hits=1,
                n_total_candidates=5,
                limitations="TOY- family should fail.",
            )

    def test_build_raises_on_open_preprint_with_not_ready(self):
        with pytest.raises(ValueError):
            build_scientific_review_readiness_gate(
                srg_id="SRG-0004",
                candidate_family_id="AMPF-FAM-004",
                cfc_id="CFC-0004",
                fnr_id="FNR-0004",
                atr_id="ATR-0004",
                pqg_id="PQG-0004",
                readiness_verdict="not_ready",
                safety_flags=["no_flags"],
                failed_gates=["ATR incomplete"],
                review_scope="open_preprint",
                n_confirmed_hits=0,
                n_total_candidates=5,
                limitations="Not ready but open preprint scope — should fail.",
            )

    def test_build_not_ready_verdict(self):
        g = build_scientific_review_readiness_gate(
            srg_id="SRG-0005",
            candidate_family_id="AMPF-FAM-005",
            cfc_id="CFC-0005",
            fnr_id="FNR-0005",
            atr_id="ATR-0005",
            pqg_id="PQG-0005",
            readiness_verdict="not_ready",
            safety_flags=["no_flags"],
            failed_gates=["FNR grade weak"],
            review_scope="internal_only",
            n_confirmed_hits=0,
            n_total_candidates=8,
            limitations="FNR novelty grade too weak for external review.",
        )
        assert g.readiness_verdict == "not_ready"

    def test_build_review_blocked_by_safety(self):
        g = build_scientific_review_readiness_gate(
            srg_id="SRG-0006",
            candidate_family_id="AMPF-FAM-006",
            cfc_id="CFC-0006",
            fnr_id="FNR-0006",
            atr_id="ATR-0006",
            pqg_id="PQG-0006",
            readiness_verdict="review_blocked_by_safety",
            safety_flags=["dual_use_concern"],
            failed_gates=[],
            review_scope="internal_only",
            n_confirmed_hits=1,
            n_total_candidates=5,
            limitations="Dual-use concern must be resolved before any review.",
        )
        assert g.readiness_verdict == "review_blocked_by_safety"


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatScientificReviewReadinessGate:
    def _build(self, **kwargs):
        defaults = dict(
            srg_id="SRG-0001",
            candidate_family_id="AMPF-FAM-001",
            cfc_id="CFC-0001",
            fnr_id="FNR-0001",
            atr_id="ATR-0001",
            pqg_id="PQG-0001",
            readiness_verdict="ready_for_external_review",
            safety_flags=["no_flags"],
            failed_gates=[],
            review_scope="trusted_partner",
            n_confirmed_hits=2,
            n_total_candidates=10,
            limitations="Single candidate family; multi-family review not performed.",
        )
        defaults.update(kwargs)
        return build_scientific_review_readiness_gate(**defaults)

    def test_format_returns_string(self):
        g = self._build()
        assert isinstance(format_scientific_review_readiness_gate(g), str)

    def test_format_contains_srg_id(self):
        g = self._build()
        assert "SRG-0001" in format_scientific_review_readiness_gate(g)

    def test_format_contains_family_id(self):
        g = self._build()
        assert "AMPF-FAM-001" in format_scientific_review_readiness_gate(g)

    def test_format_contains_readiness_verdict(self):
        g = self._build()
        assert "ready_for_external_review" in format_scientific_review_readiness_gate(g)

    def test_format_contains_review_scope(self):
        g = self._build()
        assert "trusted_partner" in format_scientific_review_readiness_gate(g)

    def test_format_contains_artifact_ids(self):
        g = self._build()
        out = format_scientific_review_readiness_gate(g)
        assert "CFC-0001" in out
        assert "FNR-0001" in out
        assert "ATR-0001" in out
        assert "PQG-0001" in out

    def test_format_contains_confirmed_hits(self):
        g = self._build()
        assert "2/10" in format_scientific_review_readiness_gate(g)

    def test_format_contains_dry_lab_only_true(self):
        g = self._build()
        assert "dry_lab_only: True" in format_scientific_review_readiness_gate(g)

    def test_format_contains_limitations(self):
        g = self._build()
        assert "Single candidate family" in format_scientific_review_readiness_gate(g)

    def test_format_contains_failed_gates_when_present(self):
        g = self._build(
            readiness_verdict="not_ready",
            safety_flags=["no_flags"],
            failed_gates=["FNR grade weak"],
            review_scope="internal_only",
            n_confirmed_hits=0,
        )
        assert "Failed Gates" in format_scientific_review_readiness_gate(g)

    def test_format_omits_failed_gates_when_empty(self):
        g = self._build()
        assert "Failed Gates" not in format_scientific_review_readiness_gate(g)

    def test_format_multiline(self):
        g = self._build()
        lines = format_scientific_review_readiness_gate(g).split("\n")
        assert len(lines) >= 9
