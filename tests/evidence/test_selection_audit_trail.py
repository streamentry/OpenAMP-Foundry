"""Tests for the Selection Audit Trail (SAT-) schema."""
import pytest
from openamp_foundry.evidence.selection_audit_trail import (
    DecisionEntry,
    SelectionAuditTrail,
    SATValidationResult,
    VALID_DECISIONS,
    VALID_STAGES,
    validate_selection_audit_trail,
    build_selection_audit_trail,
    format_selection_audit_trail,
)


def _make_selected(fid="FAM-001", stage="shortlisting"):
    return {
        "candidate_family_id": fid,
        "decision": "selected",
        "decision_stage": stage,
        "rationale": "Top candidate",
        "evidence_artifact_ids": ["BSP-01", "ECC-01"],
        "decided_at": "2026-07-10",
    }


def _make_rejected(fid="FAM-002", stage="screening"):
    return {
        "candidate_family_id": fid,
        "decision": "rejected",
        "decision_stage": stage,
        "rationale": "Failed hemolysis screen",
        "evidence_artifact_ids": ["BSP-02"],
        "decided_at": "2026-07-10",
    }


def _make_deferred(fid="FAM-003", stage="ranking"):
    return {
        "candidate_family_id": fid,
        "decision": "deferred",
        "decision_stage": stage,
        "rationale": "Pending additional data",
        "evidence_artifact_ids": [],
        "decided_at": "2026-07-10",
    }


def _build_valid(**kwargs):
    defaults = dict(
        sat_id="SAT-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        decision_dicts=[_make_selected(), _make_rejected()],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_selection_audit_trail(**defaults)


class TestDecisionEntry:
    def test_selected_entry_stored(self):
        e = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="selected",
            decision_stage="shortlisting",
            rationale="High activity",
            evidence_artifact_ids=["BSP-01"],
            decided_at="2026-07-10",
        )
        assert e.decision == "selected"
        assert e.decision_stage == "shortlisting"

    def test_rejected_entry_stored(self):
        e = DecisionEntry(
            candidate_family_id="FAM-002",
            decision="rejected",
            decision_stage="screening",
            rationale="Toxic",
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        assert e.decision == "rejected"

    def test_deferred_entry_stored(self):
        e = DecisionEntry(
            candidate_family_id="FAM-003",
            decision="deferred",
            decision_stage="ranking",
            rationale="Need more data",
            evidence_artifact_ids=["SEG-01"],
            decided_at="2026-07-10",
        )
        assert e.decision == "deferred"

    def test_evidence_artifact_ids_is_list(self):
        e = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="selected",
            decision_stage="nomination",
            rationale="r",
            evidence_artifact_ids=["A", "B"],
            decided_at="2026-07-10",
        )
        assert isinstance(e.evidence_artifact_ids, list)

    def test_candidate_family_id_stored(self):
        e = DecisionEntry(
            candidate_family_id="FAM-XYZ",
            decision="selected",
            decision_stage="shortlisting",
            rationale="r",
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        assert e.candidate_family_id == "FAM-XYZ"

    def test_rationale_stored(self):
        e = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="rejected",
            decision_stage="screening",
            rationale="Specific rationale text",
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        assert e.rationale == "Specific rationale text"


class TestValidateSelectionAuditTrail:
    def test_valid_trail_passes(self):
        r = _build_valid()
        result = validate_selection_audit_trail(r)
        assert result.valid

    def test_valid_empty_entries_passes(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[],
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert result.valid

    def test_sat_id_wrong_prefix_fails(self):
        r = _build_valid()
        object.__setattr__(r, "sat_id", "BAD-001")
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("sat_id" in v for v in result.violations)

    def test_dry_lab_only_false_fails(self):
        r = _build_valid()
        object.__setattr__(r, "dry_lab_only", False)
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_n_entries_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_entries", 99)
        result = validate_selection_audit_trail(r)
        assert not result.valid

    def test_n_selected_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_selected", 99)
        result = validate_selection_audit_trail(r)
        assert not result.valid

    def test_n_rejected_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_rejected", 99)
        result = validate_selection_audit_trail(r)
        assert not result.valid

    def test_n_deferred_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_deferred", 99)
        result = validate_selection_audit_trail(r)
        assert not result.valid

    def test_final_shortlist_wrong_fails(self):
        r = _build_valid()
        object.__setattr__(r, "final_shortlist_ids", ["WRONG-ID"])
        result = validate_selection_audit_trail(r)
        assert not result.valid

    def test_toy_candidate_id_fails(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[{
                "candidate_family_id": "TOY-001",
                "decision": "selected",
                "decision_stage": "shortlisting",
                "rationale": "test",
                "evidence_artifact_ids": [],
                "decided_at": "2026-07-10",
            }],
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_invalid_decision_fails(self):
        entry = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="maybe",  # invalid
            decision_stage="shortlisting",
            rationale="test",
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        r = SelectionAuditTrail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            n_entries=1,
            entries=[entry],
            n_selected=0,
            n_rejected=0,
            n_deferred=0,
            final_shortlist_ids=[],
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("decision" in v for v in result.violations)

    def test_invalid_stage_fails(self):
        entry = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="selected",
            decision_stage="unknown_stage",  # invalid
            rationale="test",
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        r = SelectionAuditTrail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            n_entries=1,
            entries=[entry],
            n_selected=1,
            n_rejected=0,
            n_deferred=0,
            final_shortlist_ids=["FAM-001"],
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("decision_stage" in v for v in result.violations)

    def test_empty_rationale_fails(self):
        entry = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="selected",
            decision_stage="shortlisting",
            rationale="",  # empty
            evidence_artifact_ids=[],
            decided_at="2026-07-10",
        )
        r = SelectionAuditTrail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            n_entries=1,
            entries=[entry],
            n_selected=1,
            n_rejected=0,
            n_deferred=0,
            final_shortlist_ids=["FAM-001"],
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("rationale" in v for v in result.violations)

    def test_unsorted_evidence_ids_fails(self):
        entry = DecisionEntry(
            candidate_family_id="FAM-001",
            decision="selected",
            decision_stage="shortlisting",
            rationale="test",
            evidence_artifact_ids=["Z-01", "A-01"],  # unsorted
            decided_at="2026-07-10",
        )
        r = SelectionAuditTrail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            n_entries=1,
            entries=[entry],
            n_selected=1,
            n_rejected=0,
            n_deferred=0,
            final_shortlist_ids=["FAM-001"],
            dry_lab_only=True,
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("evidence_artifact_ids" in v for v in result.violations)

    def test_empty_limitations_fails(self):
        r = _build_valid()
        object.__setattr__(r, "limitations", [])
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_multiple_violations_captured(self):
        r = _build_valid()
        object.__setattr__(r, "sat_id", "BAD-001")
        object.__setattr__(r, "dry_lab_only", False)
        result = validate_selection_audit_trail(r)
        assert not result.valid
        assert len(result.violations) >= 2


class TestBuildSelectionAuditTrail:
    def test_build_counts_selected(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_selected("F2"), _make_rejected("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_selected == 2

    def test_build_counts_rejected(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_rejected("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_rejected == 2

    def test_build_counts_deferred(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_deferred("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_deferred == 2

    def test_build_n_entries_matches_len(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_entries == 3

    def test_build_final_shortlist_sorted_unique(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[
                _make_selected("FAM-C"),
                _make_selected("FAM-A"),
                _make_selected("FAM-A"),  # duplicate
                _make_rejected("FAM-B"),
            ],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.final_shortlist_ids == ["FAM-A", "FAM-C"]

    def test_build_dry_lab_only_true(self):
        r = _build_valid()
        assert r.dry_lab_only is True

    def test_build_zero_entries(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_entries == 0
        assert r.n_selected == 0
        assert r.final_shortlist_ids == []

    def test_build_evidence_artifact_ids_sorted(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[{
                "candidate_family_id": "FAM-001",
                "decision": "selected",
                "decision_stage": "shortlisting",
                "rationale": "Good",
                "evidence_artifact_ids": ["Z-01", "A-01", "M-01"],
                "decided_at": "2026-07-10",
            }],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.entries[0].evidence_artifact_ids == ["A-01", "M-01", "Z-01"]

    def test_build_only_selected_in_shortlist(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.final_shortlist_ids == ["F1"]

    def test_build_all_rejected_empty_shortlist(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_rejected("F1"), _make_rejected("F2")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.final_shortlist_ids == []
        assert r.n_selected == 0

    def test_build_all_decisions_stored(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        decisions = [e.decision for e in r.entries]
        assert "selected" in decisions
        assert "rejected" in decisions
        assert "deferred" in decisions

    def test_build_stage_preserved(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1", stage="nomination")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.entries[0].decision_stage == "nomination"

    def test_build_rationale_preserved(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[{
                "candidate_family_id": "FAM-001",
                "decision": "selected",
                "decision_stage": "shortlisting",
                "rationale": "Specific reason",
                "evidence_artifact_ids": [],
                "decided_at": "2026-07-10",
            }],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.entries[0].rationale == "Specific reason"

    def test_build_decided_at_preserved(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[{
                "candidate_family_id": "FAM-001",
                "decision": "selected",
                "decision_stage": "shortlisting",
                "rationale": "r",
                "evidence_artifact_ids": [],
                "decided_at": "2026-01-15",
            }],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.entries[0].decided_at == "2026-01-15"

    def test_build_multiple_stages_in_same_trail(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[
                _make_selected("F1", stage="nomination"),
                _make_rejected("F2", stage="screening"),
                _make_selected("F3", stage="shortlisting"),
            ],
            limitations=["test"],
            created_at="2026-07-10",
        )
        stages = {e.decision_stage for e in r.entries}
        assert "nomination" in stages
        assert "screening" in stages
        assert "shortlisting" in stages

    def test_build_shortlist_sorted_alphabetically(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("FAM-Z"), _make_selected("FAM-A"), _make_selected("FAM-M")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.final_shortlist_ids == ["FAM-A", "FAM-M", "FAM-Z"]

    def test_build_all_selected_shortlist_complete(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_selected("F2")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert set(r.final_shortlist_ids) == {"F1", "F2"}


class TestSelectionAuditTrailIntegration:
    def test_round_trip_build_validate(self):
        r = build_selection_audit_trail(
            sat_id="SAT-RT",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["Not biological validation"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert result.valid

    def test_empty_trail_validates(self):
        r = build_selection_audit_trail(
            sat_id="SAT-EMPTY",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[],
            limitations=["test"],
            created_at="2026-07-10",
        )
        result = validate_selection_audit_trail(r)
        assert result.valid

    def test_all_decisions_types_valid(self):
        for decision in ["selected", "rejected", "deferred"]:
            r = build_selection_audit_trail(
                sat_id="SAT-001",
                batch_id="B",
                pipeline_version="v1",
                decision_dicts=[{
                    "candidate_family_id": "FAM-001",
                    "decision": decision,
                    "decision_stage": "shortlisting",
                    "rationale": "test",
                    "evidence_artifact_ids": [],
                    "decided_at": "2026-07-10",
                }],
                limitations=["test"],
                created_at="2026-07-10",
            )
            result = validate_selection_audit_trail(r)
            assert result.valid

    def test_all_stage_types_valid(self):
        for stage in ["nomination", "screening", "ranking", "shortlisting"]:
            r = build_selection_audit_trail(
                sat_id="SAT-001",
                batch_id="B",
                pipeline_version="v1",
                decision_dicts=[{
                    "candidate_family_id": "FAM-001",
                    "decision": "selected",
                    "decision_stage": stage,
                    "rationale": "test",
                    "evidence_artifact_ids": [],
                    "decided_at": "2026-07-10",
                }],
                limitations=["test"],
                created_at="2026-07-10",
            )
            result = validate_selection_audit_trail(r)
            assert result.valid

    def test_valid_decisions_frozenset_complete(self):
        assert "selected" in VALID_DECISIONS
        assert "rejected" in VALID_DECISIONS
        assert "deferred" in VALID_DECISIONS
        assert len(VALID_DECISIONS) == 3

    def test_valid_stages_frozenset_complete(self):
        assert "nomination" in VALID_STAGES
        assert "screening" in VALID_STAGES
        assert "ranking" in VALID_STAGES
        assert "shortlisting" in VALID_STAGES
        assert len(VALID_STAGES) == 4

    def test_n_entries_plus_counts_consistent(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        assert r.n_selected + r.n_rejected + r.n_deferred == r.n_entries

    def test_shortlist_subset_of_entries(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[_make_selected("F1"), _make_rejected("F2"), _make_deferred("F3")],
            limitations=["test"],
            created_at="2026-07-10",
        )
        all_fids = {e.candidate_family_id for e in r.entries}
        assert all(fid in all_fids for fid in r.final_shortlist_ids)


class TestFormatSelectionAuditTrail:
    def test_returns_string(self):
        r = _build_valid()
        assert isinstance(format_selection_audit_trail(r), str)

    def test_contains_sat_id(self):
        r = _build_valid()
        assert r.sat_id in format_selection_audit_trail(r)

    def test_contains_n_entries(self):
        r = _build_valid()
        assert str(r.n_entries) in format_selection_audit_trail(r)

    def test_contains_n_selected(self):
        r = _build_valid()
        assert str(r.n_selected) in format_selection_audit_trail(r)

    def test_contains_dry_lab_only(self):
        r = _build_valid()
        assert "dry_lab_only" in format_selection_audit_trail(r)

    def test_contains_batch_id(self):
        r = _build_valid()
        assert r.batch_id in format_selection_audit_trail(r)

    def test_contains_shortlist_size(self):
        r = _build_valid()
        s = format_selection_audit_trail(r)
        assert str(len(r.final_shortlist_ids)) in s

    def test_no_empty_trail_shortlist_label(self):
        r = build_selection_audit_trail(
            sat_id="SAT-001",
            batch_id="B",
            pipeline_version="v1",
            decision_dicts=[],
            limitations=["test"],
            created_at="2026-07-10",
        )
        s = format_selection_audit_trail(r)
        assert "(none)" in s
