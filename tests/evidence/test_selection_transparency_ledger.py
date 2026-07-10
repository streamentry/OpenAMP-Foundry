"""Tests for selection_transparency_ledger module — Phase S S2 (STL-)."""
import pytest
from openamp_foundry.evidence.selection_transparency_ledger import (
    SelectionTransparencyLedger,
    ArtifactReference,
    VALID_SELECTION_BASES,
    VALID_LEDGER_COMPLETENESS_GRADES,
    VALID_SELECTION_OUTCOME_TYPES,
    REQUIRED_SELECTION_ARTIFACT_TYPES,
    validate_selection_transparency_ledger,
    build_selection_transparency_ledger,
    format_selection_transparency_ledger,
)


def _make_ref(artifact_type="BSP", artifact_id="BSP-001", desc="Batch selection basis"):
    return ArtifactReference(artifact_type=artifact_type, artifact_id=artifact_id, influence_description=desc)


def _all_required_refs():
    return [
        _make_ref("BSP", "BSP-001", "Batch selection basis"),
        _make_ref("SEG", "SEG-001", "Score vs enemy gap"),
        _make_ref("SRG", "SRG-001", "Review readiness gate"),
    ]


def _make_ledger(**kwargs):
    refs = _all_required_refs()
    defaults = dict(
        stl_id="STL-001", run_id="RUN-001", candidate_family_id="FAM-001",
        selection_basis="score_rank", selection_outcome="selected_for_pilot",
        completeness_grade="complete", artifact_references=refs,
        n_artifacts_referenced=3, has_required_artifacts=True,
        missing_required_artifact_types=[],
        seg_id=None, srg_id=None, bsp_id=None,
        dry_lab_only=True,
        limitations="Dry-lab only. Selection based on computational scores.",
        notes="",
    )
    defaults.update(kwargs)
    return SelectionTransparencyLedger(**defaults)


class TestSTLIDValidation:
    def test_valid_stl_id(self):
        assert validate_selection_transparency_ledger(_make_ledger(stl_id="STL-001")).valid

    def test_invalid_stl_id_missing_prefix(self):
        r = validate_selection_transparency_ledger(_make_ledger(stl_id="001"))
        assert not r.valid and any("stl_id" in v for v in r.violations)

    def test_invalid_stl_id_wrong_prefix(self):
        assert not validate_selection_transparency_ledger(_make_ledger(stl_id="SEG-001")).valid

    def test_toy_family_id_blocked(self):
        r = validate_selection_transparency_ledger(_make_ledger(candidate_family_id="TOY-001"))
        assert not r.valid and any("TOY-" in v for v in r.violations)

    def test_run_id_required(self):
        r = validate_selection_transparency_ledger(_make_ledger(run_id=""))
        assert not r.valid and any("run_id" in v for v in r.violations)

    def test_candidate_family_id_required(self):
        assert not validate_selection_transparency_ledger(_make_ledger(candidate_family_id="")).valid

    def test_seg_id_prefix_required_when_provided(self):
        r = validate_selection_transparency_ledger(_make_ledger(seg_id="001"))
        assert not r.valid and any("seg_id" in v for v in r.violations)

    def test_srg_id_prefix_required_when_provided(self):
        r = validate_selection_transparency_ledger(_make_ledger(srg_id="001"))
        assert not r.valid and any("srg_id" in v for v in r.violations)

    def test_bsp_id_prefix_required_when_provided(self):
        r = validate_selection_transparency_ledger(_make_ledger(bsp_id="001"))
        assert not r.valid and any("bsp_id" in v for v in r.violations)

    def test_all_optional_ids_valid_when_correct_prefix(self):
        ledger = _make_ledger(seg_id="SEG-001", srg_id="SRG-001", bsp_id="BSP-001")
        assert validate_selection_transparency_ledger(ledger).valid


class TestSelectionBasisValidation:
    def test_all_valid_bases_accepted(self):
        for basis in VALID_SELECTION_BASES - {"not_specified"}:
            assert validate_selection_transparency_ledger(_make_ledger(selection_basis=basis)).valid, f"Expected valid for basis={basis}"

    def test_invalid_basis_rejected(self):
        r = validate_selection_transparency_ledger(_make_ledger(selection_basis="gut_feeling"))
        assert not r.valid and any("selection_basis" in v for v in r.violations)

    def test_not_specified_basis_blocked(self):
        r = validate_selection_transparency_ledger(_make_ledger(selection_basis="not_specified"))
        assert not r.valid and any("not_specified" in v for v in r.violations)

    def test_score_rank_basis_valid(self):
        assert validate_selection_transparency_ledger(_make_ledger(selection_basis="score_rank")).valid

    def test_expert_review_basis_valid(self):
        assert validate_selection_transparency_ledger(_make_ledger(selection_basis="expert_review")).valid


class TestSelectionOutcomeValidation:
    def test_all_valid_outcomes_accepted(self):
        for outcome in VALID_SELECTION_OUTCOME_TYPES:
            assert validate_selection_transparency_ledger(_make_ledger(selection_outcome=outcome)).valid, f"Expected valid for outcome={outcome}"

    def test_invalid_outcome_rejected(self):
        r = validate_selection_transparency_ledger(_make_ledger(selection_outcome="maybe_selected"))
        assert not r.valid and any("selection_outcome" in v for v in r.violations)

    def test_selected_for_pilot_valid(self):
        assert validate_selection_transparency_ledger(_make_ledger(selection_outcome="selected_for_pilot")).valid

    def test_deselected_safety_valid(self):
        assert validate_selection_transparency_ledger(_make_ledger(selection_outcome="deselected_safety")).valid


class TestCompletenessValidation:
    def test_complete_grade_with_all_required_valid(self):
        ledger = _make_ledger(completeness_grade="complete", has_required_artifacts=True, missing_required_artifact_types=[])
        assert validate_selection_transparency_ledger(ledger).valid

    def test_complete_grade_without_required_rejected(self):
        refs = [_make_ref("BSP", "BSP-001", "Batch basis")]  # missing SEG, SRG
        ledger = _make_ledger(
            completeness_grade="complete", artifact_references=refs,
            n_artifacts_referenced=1, has_required_artifacts=False,
            missing_required_artifact_types=["SEG", "SRG"]
        )
        r = validate_selection_transparency_ledger(ledger)
        assert not r.valid and any("complete" in v for v in r.violations)

    def test_partial_grade_with_some_missing_valid(self):
        refs = [_make_ref("BSP", "BSP-001", "Batch basis"), _make_ref("SEG", "SEG-001", "Gap")]
        ledger = _make_ledger(
            completeness_grade="partial", artifact_references=refs,
            n_artifacts_referenced=2, has_required_artifacts=False,
            missing_required_artifact_types=["SRG"]
        )
        assert validate_selection_transparency_ledger(ledger).valid

    def test_incomplete_grade_with_all_required_rejected(self):
        refs = _all_required_refs()
        ledger = _make_ledger(
            completeness_grade="incomplete", artifact_references=refs,
            n_artifacts_referenced=3, has_required_artifacts=True,
            missing_required_artifact_types=[]
        )
        r = validate_selection_transparency_ledger(ledger)
        assert not r.valid

    def test_all_valid_grades_in_constant(self):
        assert len(VALID_LEDGER_COMPLETENESS_GRADES) == 4

    def test_n_artifacts_must_match_refs(self):
        refs = _all_required_refs()
        r = validate_selection_transparency_ledger(_make_ledger(artifact_references=refs, n_artifacts_referenced=5))
        assert not r.valid and any("n_artifacts_referenced" in v for v in r.violations)

    def test_at_least_one_artifact_required(self):
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=[], n_artifacts_referenced=0,
            has_required_artifacts=False, missing_required_artifact_types=["BSP","SEG","SRG"],
            completeness_grade="incomplete"
        ))
        assert not r.valid

    def test_missing_required_types_computed_correctly(self):
        refs = [_make_ref("BSP", "BSP-001", "Batch basis")]
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=refs, n_artifacts_referenced=1,
            has_required_artifacts=False, missing_required_artifact_types=["SEG"],  # wrong — SRG also missing
            completeness_grade="partial"
        ))
        assert not r.valid and any("missing_required_artifact_types" in v for v in r.violations)

    def test_has_required_inconsistency_rejected(self):
        refs = _all_required_refs()
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=False,  # wrong — all required present
            missing_required_artifact_types=[]
        ))
        assert not r.valid

    def test_required_artifact_types_count(self):
        assert len(REQUIRED_SELECTION_ARTIFACT_TYPES) == 3


class TestArtifactReferenceValidation:
    def test_empty_artifact_type_rejected(self):
        bad_ref = ArtifactReference(artifact_type="", artifact_id="BSP-001", influence_description="Batch basis")
        refs = [bad_ref, _make_ref("SEG", "SEG-001", "Gap"), _make_ref("SRG", "SRG-001", "Gate")]
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=False, missing_required_artifact_types=["BSP"],
            completeness_grade="partial"
        ))
        assert not r.valid

    def test_empty_artifact_id_rejected(self):
        bad_ref = ArtifactReference(artifact_type="BSP", artifact_id="", influence_description="Batch basis")
        refs = [bad_ref, _make_ref("SEG", "SEG-001", "Gap"), _make_ref("SRG", "SRG-001", "Gate")]
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=True, missing_required_artifact_types=[],
            completeness_grade="complete"
        ))
        assert not r.valid

    def test_too_short_influence_description_rejected(self):
        bad_ref = ArtifactReference(artifact_type="BSP", artifact_id="BSP-001", influence_description="hi")
        refs = [bad_ref, _make_ref("SEG", "SEG-001", "Gap"), _make_ref("SRG", "SRG-001", "Gate")]
        r = validate_selection_transparency_ledger(_make_ledger(
            artifact_references=refs, n_artifacts_referenced=3,
            has_required_artifacts=True, missing_required_artifact_types=[],
            completeness_grade="complete"
        ))
        assert not r.valid and any("influence_description" in v for v in r.violations)


class TestDryLabAndLimitations:
    def test_dry_lab_only_false_rejected(self):
        r = validate_selection_transparency_ledger(_make_ledger(dry_lab_only=False))
        assert not r.valid and any("dry_lab_only" in v for v in r.violations)

    def test_limitations_required(self):
        r = validate_selection_transparency_ledger(_make_ledger(limitations=""))
        assert not r.valid and any("limitations" in v for v in r.violations)

    def test_limitations_too_short_rejected(self):
        assert not validate_selection_transparency_ledger(_make_ledger(limitations="Too short")).valid

    def test_limitations_sufficient_valid(self):
        assert validate_selection_transparency_ledger(_make_ledger(limitations="Dry-lab only. Selection based on computational scores.")).valid


class TestBuildAndFormat:
    def test_build_auto_computes_complete_grade(self):
        refs = _all_required_refs()
        ledger = build_selection_transparency_ledger(
            stl_id="STL-001", run_id="RUN-001", candidate_family_id="FAM-001",
            selection_basis="score_rank", selection_outcome="selected_for_pilot",
            artifact_references=refs,
            limitations="Dry-lab only. Selection based on computational scores.",
        )
        assert ledger.completeness_grade == "complete"
        assert ledger.has_required_artifacts is True
        assert ledger.dry_lab_only is True

    def test_build_auto_computes_partial_grade(self):
        refs = [_make_ref("BSP", "BSP-001", "Batch basis"), _make_ref("SEG", "SEG-001", "Gap")]
        ledger = build_selection_transparency_ledger(
            stl_id="STL-001", run_id="RUN-001", candidate_family_id="FAM-001",
            selection_basis="score_rank", selection_outcome="selected_for_pilot",
            artifact_references=refs,
            limitations="Dry-lab only. Selection based on computational scores.",
        )
        assert ledger.completeness_grade == "partial"
        assert ledger.has_required_artifacts is False
        assert "SRG" in ledger.missing_required_artifact_types

    def test_build_raises_on_invalid(self):
        with pytest.raises(ValueError):
            build_selection_transparency_ledger(
                stl_id="INVALID", run_id="RUN-001", candidate_family_id="FAM-001",
                selection_basis="score_rank", selection_outcome="selected_for_pilot",
                artifact_references=_all_required_refs(),
                limitations="Dry-lab only. Selection based on computational scores.",
            )

    def test_build_raises_on_not_specified_basis(self):
        with pytest.raises(ValueError):
            build_selection_transparency_ledger(
                stl_id="STL-001", run_id="RUN-001", candidate_family_id="FAM-001",
                selection_basis="not_specified", selection_outcome="selected_for_pilot",
                artifact_references=_all_required_refs(),
                limitations="Dry-lab only. Selection based on computational scores.",
            )

    def test_format_includes_stl_id(self):
        assert "STL-001" in format_selection_transparency_ledger(_make_ledger())

    def test_format_includes_selection_basis(self):
        assert "score_rank" in format_selection_transparency_ledger(_make_ledger())

    def test_format_includes_completeness_grade(self):
        assert "complete" in format_selection_transparency_ledger(_make_ledger())

    def test_format_includes_artifact_count(self):
        assert "3" in format_selection_transparency_ledger(_make_ledger())

    def test_format_includes_seg_link_when_present(self):
        assert "SEG-001" in format_selection_transparency_ledger(_make_ledger(seg_id="SEG-001"))

    def test_format_is_multiline(self):
        assert "\n" in format_selection_transparency_ledger(_make_ledger())

    def test_valid_ledger_passes_validation(self):
        r = validate_selection_transparency_ledger(_make_ledger())
        assert r.valid and r.violations == []

    def test_multiple_violations_collected(self):
        r = validate_selection_transparency_ledger(_make_ledger(stl_id="INVALID", selection_basis="bad_basis"))
        assert not r.valid and len(r.violations) >= 2
