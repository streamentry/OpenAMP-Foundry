"""Tests for selection_transparency_ledger module — Phase S S2 (STL-)."""
import pytest
from openamp_foundry.evidence.selection_transparency_ledger import (
    SelectionTransparencyLedger, ArtifactReference,
    VALID_SELECTION_BASES, VALID_LEDGER_COMPLETENESS_GRADES,
    VALID_SELECTION_OUTCOME_TYPES, REQUIRED_SELECTION_ARTIFACT_TYPES,
    validate_selection_transparency_ledger,
    build_selection_transparency_ledger,
    format_selection_transparency_ledger,
)


def _ref(t="BSP", i="BSP-001", d="Batch selection basis"): return ArtifactReference(artifact_type=t, artifact_id=i, influence_description=d)
def _all_refs(): return [_ref("BSP","BSP-001","Batch basis"), _ref("SEG","SEG-001","Score gap"), _ref("SRG","SRG-001","Review gate")]


def _make(**kw):
    refs = _all_refs()
    d = dict(stl_id="STL-001", run_id="RUN-001", candidate_family_id="FAM-001",
             selection_basis="score_rank", selection_outcome="selected_for_pilot",
             completeness_grade="complete", artifact_references=refs,
             n_artifacts_referenced=3, has_required_artifacts=True,
             missing_required_artifact_types=[], seg_id=None, srg_id=None, bsp_id=None,
             dry_lab_only=True, limitations="Dry-lab only. Selection based on computational scores.", notes="")
    d.update(kw)
    return SelectionTransparencyLedger(**d)


class TestSTLIDValidation:
    def test_valid_stl_id(self): assert validate_selection_transparency_ledger(_make(stl_id="STL-001")).valid
    def test_invalid_stl_id(self):
        r = validate_selection_transparency_ledger(_make(stl_id="001"))
        assert not r.valid and any("stl_id" in v for v in r.violations)
    def test_wrong_prefix(self): assert not validate_selection_transparency_ledger(_make(stl_id="SEG-001")).valid
    def test_toy_family_blocked(self):
        r = validate_selection_transparency_ledger(_make(candidate_family_id="TOY-001"))
        assert not r.valid and any("TOY-" in v for v in r.violations)
    def test_run_id_required(self):
        r = validate_selection_transparency_ledger(_make(run_id=""))
        assert not r.valid and any("run_id" in v for v in r.violations)
    def test_family_id_required(self): assert not validate_selection_transparency_ledger(_make(candidate_family_id="")).valid
    def test_seg_id_prefix_required(self):
        r = validate_selection_transparency_ledger(_make(seg_id="001"))
        assert not r.valid and any("seg_id" in v for v in r.violations)
    def test_srg_id_prefix_required(self):
        r = validate_selection_transparency_ledger(_make(srg_id="001"))
        assert not r.valid and any("srg_id" in v for v in r.violations)
    def test_bsp_id_prefix_required(self):
        r = validate_selection_transparency_ledger(_make(bsp_id="001"))
        assert not r.valid and any("bsp_id" in v for v in r.violations)
    def test_all_optional_ids_valid(self): assert validate_selection_transparency_ledger(_make(seg_id="SEG-001", srg_id="SRG-001", bsp_id="BSP-001")).valid


class TestSelectionBasisValidation:
    def test_all_valid_bases_accepted(self):
        for b in VALID_SELECTION_BASES - {"not_specified"}:
            assert validate_selection_transparency_ledger(_make(selection_basis=b)).valid
    def test_invalid_basis_rejected(self):
        r = validate_selection_transparency_ledger(_make(selection_basis="gut_feeling"))
        assert not r.valid and any("selection_basis" in v for v in r.violations)
    def test_not_specified_blocked(self):
        r = validate_selection_transparency_ledger(_make(selection_basis="not_specified"))
        assert not r.valid and any("not_specified" in v for v in r.violations)
    def test_score_rank_valid(self): assert validate_selection_transparency_ledger(_make(selection_basis="score_rank")).valid
    def test_expert_review_valid(self): assert validate_selection_transparency_ledger(_make(selection_basis="expert_review")).valid
    def test_novelty_evidence_valid(self): assert validate_selection_transparency_ledger(_make(selection_basis="novelty_evidence")).valid
    def test_diversity_criteria_valid(self): assert validate_selection_transparency_ledger(_make(selection_basis="diversity_criteria")).valid


class TestSelectionOutcomeValidation:
    def test_all_valid_outcomes_accepted(self):
        for o in VALID_SELECTION_OUTCOME_TYPES:
            assert validate_selection_transparency_ledger(_make(selection_outcome=o)).valid
    def test_invalid_outcome_rejected(self):
        r = validate_selection_transparency_ledger(_make(selection_outcome="maybe_selected"))
        assert not r.valid and any("selection_outcome" in v for v in r.violations)
    def test_selected_for_pilot_valid(self): assert validate_selection_transparency_ledger(_make(selection_outcome="selected_for_pilot")).valid
    def test_deselected_safety_valid(self): assert validate_selection_transparency_ledger(_make(selection_outcome="deselected_safety")).valid
    def test_held_pending_review_valid(self): assert validate_selection_transparency_ledger(_make(selection_outcome="held_pending_review")).valid


class TestCompletenessValidation:
    def test_complete_grade_all_required_valid(self): assert validate_selection_transparency_ledger(_make(completeness_grade="complete")).valid
    def test_complete_without_required_rejected(self):
        refs = [_ref("BSP","BSP-001","Batch")]
        r = validate_selection_transparency_ledger(_make(completeness_grade="complete", artifact_references=refs,
            n_artifacts_referenced=1, has_required_artifacts=False, missing_required_artifact_types=["SEG","SRG"]))
        assert not r.valid and any("complete" in v for v in r.violations)
    def test_partial_grade_valid(self):
        refs = [_ref("BSP","BSP-001","Batch basis"), _ref("SEG","SEG-001","Score gap")]
        assert validate_selection_transparency_ledger(_make(completeness_grade="partial", artifact_references=refs,
            n_artifacts_referenced=2, has_required_artifacts=False, missing_required_artifact_types=["SRG"])).valid
    def test_incomplete_with_all_required_rejected(self):
        r = validate_selection_transparency_ledger(_make(completeness_grade="incomplete", has_required_artifacts=True, missing_required_artifact_types=[]))
        assert not r.valid
    def test_grades_count(self): assert len(VALID_LEDGER_COMPLETENESS_GRADES) == 4
    def test_n_artifacts_must_match(self):
        r = validate_selection_transparency_ledger(_make(n_artifacts_referenced=5))
        assert not r.valid and any("n_artifacts_referenced" in v for v in r.violations)
    def test_at_least_one_artifact_required(self):
        r = validate_selection_transparency_ledger(_make(artifact_references=[], n_artifacts_referenced=0,
            has_required_artifacts=False, missing_required_artifact_types=["BSP","SEG","SRG"], completeness_grade="incomplete"))
        assert not r.valid
    def test_missing_types_must_be_correct(self):
        refs = [_ref("BSP","BSP-001","Batch")]
        r = validate_selection_transparency_ledger(_make(artifact_references=refs, n_artifacts_referenced=1,
            has_required_artifacts=False, missing_required_artifact_types=["SEG"], completeness_grade="partial"))
        assert not r.valid and any("missing_required_artifact_types" in v for v in r.violations)
    def test_has_required_inconsistency_rejected(self):
        r = validate_selection_transparency_ledger(_make(has_required_artifacts=False, missing_required_artifact_types=[]))
        assert not r.valid
    def test_required_types_count(self): assert len(REQUIRED_SELECTION_ARTIFACT_TYPES) == 3


class TestArtifactReferenceValidation:
    def test_empty_type_rejected(self):
        bad = ArtifactReference(artifact_type="", artifact_id="X-001", influence_description="Test thing")
        refs = [bad, _ref("SEG","SEG-001","Gap"), _ref("SRG","SRG-001","Gate")]
        r = validate_selection_transparency_ledger(_make(artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=False, missing_required_artifact_types=["BSP"], completeness_grade="partial"))
        assert not r.valid
    def test_empty_id_rejected(self):
        bad = ArtifactReference(artifact_type="BSP", artifact_id="", influence_description="Batch basis")
        refs = [bad, _ref("SEG","SEG-001","Gap"), _ref("SRG","SRG-001","Gate")]
        r = validate_selection_transparency_ledger(_make(artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=True, missing_required_artifact_types=[], completeness_grade="complete"))
        assert not r.valid
    def test_short_description_rejected(self):
        bad = ArtifactReference(artifact_type="BSP", artifact_id="BSP-001", influence_description="hi")
        refs = [bad, _ref("SEG","SEG-001","Gap"), _ref("SRG","SRG-001","Gate")]
        r = validate_selection_transparency_ledger(_make(artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=True, missing_required_artifact_types=[], completeness_grade="complete"))
        assert not r.valid and any("influence_description" in v for v in r.violations)


class TestDryLabAndLimitations:
    def test_dry_lab_false_rejected(self):
        r = validate_selection_transparency_ledger(_make(dry_lab_only=False))
        assert not r.valid and any("dry_lab_only" in v for v in r.violations)
    def test_limitations_required(self):
        r = validate_selection_transparency_ledger(_make(limitations=""))
        assert not r.valid and any("limitations" in v for v in r.violations)
    def test_limitations_short_rejected(self): assert not validate_selection_transparency_ledger(_make(limitations="Too short")).valid
    def test_limitations_sufficient_valid(self): assert validate_selection_transparency_ledger(_make(limitations="Dry-lab only. Selection based on computational scores.")).valid


class TestBuildAndFormat:
    def test_build_complete_grade(self):
        l = build_selection_transparency_ledger("STL-001","RUN-001","FAM-001","score_rank","selected_for_pilot",
            _all_refs(), "Dry-lab only. Selection based on computational scores.")
        assert l.completeness_grade == "complete" and l.has_required_artifacts is True and l.dry_lab_only is True
    def test_build_partial_grade(self):
        refs = [_ref("BSP","BSP-001","Batch basis"), _ref("SEG","SEG-001","Score gap")]
        l = build_selection_transparency_ledger("STL-001","RUN-001","FAM-001","score_rank","selected_for_pilot",
            refs, "Dry-lab only. Selection based on computational scores.")
        assert l.completeness_grade == "partial" and "SRG" in l.missing_required_artifact_types
    def test_build_raises_invalid(self):
        with pytest.raises(ValueError):
            build_selection_transparency_ledger("INVALID","RUN-001","FAM-001","score_rank","selected_for_pilot",
                _all_refs(), "Dry-lab only. Selection based on computational scores.")
    def test_build_raises_not_specified(self):
        with pytest.raises(ValueError):
            build_selection_transparency_ledger("STL-001","RUN-001","FAM-001","not_specified","selected_for_pilot",
                _all_refs(), "Dry-lab only. Selection based on computational scores.")
    def test_format_includes_stl_id(self): assert "STL-001" in format_selection_transparency_ledger(_make())
    def test_format_includes_selection_basis(self): assert "score_rank" in format_selection_transparency_ledger(_make())
    def test_format_includes_completeness_grade(self): assert "complete" in format_selection_transparency_ledger(_make())
    def test_format_includes_seg_link(self): assert "SEG-001" in format_selection_transparency_ledger(_make(seg_id="SEG-001"))
    def test_format_is_multiline(self): assert "\n" in format_selection_transparency_ledger(_make())
    def test_valid_ledger(self):
        r = validate_selection_transparency_ledger(_make())
        assert r.valid and r.violations == []
    def test_multiple_violations(self):
        r = validate_selection_transparency_ledger(_make(stl_id="INVALID", selection_basis="bad"))
        assert not r.valid and len(r.violations) >= 2
