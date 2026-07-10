"""Tests for batch_evidence_gap_report module — Phase T T3 (BEG-)."""
import pytest
from openamp_foundry.evidence.batch_evidence_gap_report import (
    FamilyGapEntry,
    BatchEvidenceGapReport,
    REQUIRED_ARTIFACT_TYPES,
    VALID_GAP_VERDICTS,
    BEGValidationResult,
    validate_batch_evidence_gap_report,
    build_batch_evidence_gap_report,
    format_batch_evidence_gap_report,
)


def _make_complete_dict(fid="FAM-001"):
    return {"candidate_family_id": fid, "artifact_ids": {"BSP": "a", "SEG": "b", "ECC": "c", "STL": "d"}}


def _make_gap_dict(fid="FAM-002", missing=("ECC", "STL")):
    present = {k: "x" for k in ["BSP", "SEG", "ECC", "STL"] if k not in missing}
    return {"candidate_family_id": fid, "artifact_ids": present}


def _make_empty_dict(fid="FAM-003"):
    return {"candidate_family_id": fid, "artifact_ids": {}}


def _build(family_dicts, beg_id="BEG-001", limitations=["dry-lab only"]):
    return build_batch_evidence_gap_report(
        beg_id=beg_id,
        batch_id="BATCH-001",
        pipeline_version="1.0.0",
        family_artifact_dicts=family_dicts,
        limitations=limitations,
        created_at="2026-07-10T00:00:00",
    )


def _make_entry(fid="FAM-001", present=None, missing=None, gap_count=None, has_gap=None):
    if present is None:
        present = sorted(REQUIRED_ARTIFACT_TYPES)
    if missing is None:
        missing = []
    if gap_count is None:
        gap_count = len(missing)
    if has_gap is None:
        has_gap = gap_count > 0
    return FamilyGapEntry(
        candidate_family_id=fid,
        present_artifact_types=present,
        missing_artifact_types=missing,
        gap_count=gap_count,
        has_gap=has_gap,
    )


class TestFamilyGapEntry:
    def test_complete_family(self):
        entry = _make_entry(present=sorted(REQUIRED_ARTIFACT_TYPES), missing=[])
        assert entry.present_artifact_types == ["BSP", "ECC", "SEG", "STL"]
        assert entry.missing_artifact_types == []
        assert entry.gap_count == 0
        assert entry.has_gap is False

    def test_family_with_2_missing(self):
        entry = _make_entry(present=["BSP", "SEG"], missing=["ECC", "STL"], gap_count=2, has_gap=True)
        assert entry.missing_artifact_types == ["ECC", "STL"]
        assert entry.gap_count == 2
        assert entry.has_gap is True

    def test_family_all_missing(self):
        entry = _make_entry(present=[], missing=["BSP", "ECC", "SEG", "STL"], gap_count=4, has_gap=True)
        assert entry.gap_count == 4
        assert entry.has_gap is True

    def test_present_artifact_types_is_list(self):
        entry = _make_entry(present=["BSP", "SEG"], missing=["ECC", "STL"])
        assert isinstance(entry.present_artifact_types, list)

    def test_missing_artifact_types_is_list(self):
        entry = _make_entry(present=["BSP", "SEG"], missing=["ECC", "STL"])
        assert isinstance(entry.missing_artifact_types, list)

    def test_candidate_family_id_stored(self):
        entry = _make_entry(fid="FAM-X007")
        assert entry.candidate_family_id == "FAM-X007"


class TestValidateBatchEvidenceGapReport:
    def test_beg_id_not_starting_with_beg(self):
        report = _build([_make_complete_dict()], beg_id="XEG-001")
        report.beg_id = "XEG-001"
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("beg_id must start with 'BEG-'" in v for v in result.violations)

    def test_dry_lab_only_false(self):
        report = _build([_make_complete_dict()])
        report.dry_lab_only = False
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("dry_lab_only must be True" in v for v in result.violations)

    def test_n_families_total_mismatch(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        report.n_families_total = 99
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("n_families_total" in v for v in result.violations)

    def test_n_families_with_gaps_mismatch(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        report.n_families_with_gaps = 99
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("n_families_with_gaps" in v for v in result.violations)

    def test_n_families_complete_mismatch(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        report.n_families_complete = 99
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("n_families_complete" in v for v in result.violations)

    def test_total_missing_count_mismatch(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        report.total_missing_count = 99
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("total_missing_count" in v for v in result.violations)

    def test_overall_gap_verdict_wrong(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        report.overall_gap_verdict = "invalid_verdict"
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("overall_gap_verdict" in v for v in result.violations)

    def test_required_artifact_types_wrong(self):
        report = _build([_make_complete_dict()])
        report.required_artifact_types = ["BSP", "ECC"]
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("required_artifact_types" in v for v in result.violations)

    def test_toy_family_id(self):
        report = _build([_make_complete_dict(fid="TOY-001")])
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_present_unsorted(self):
        report = _build([_make_complete_dict()])
        report.family_gap_entries[0].present_artifact_types = ["SEG", "BSP"]
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("present_artifact_types must be sorted" in v for v in result.violations)

    def test_missing_unsorted(self):
        report = _build([_make_gap_dict(missing=("ECC", "STL"))])
        report.family_gap_entries[0].missing_artifact_types = ["STL", "ECC"]
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("missing_artifact_types must be sorted" in v for v in result.violations)

    def test_gap_count_mismatch_missing_len(self):
        report = _build([_make_gap_dict(missing=("ECC", "STL"))])
        report.family_gap_entries[0].gap_count = 99
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("gap_count" in v for v in result.violations)

    def test_has_gap_inconsistent(self):
        report = _build([_make_gap_dict(missing=("ECC", "STL"))])
        report.family_gap_entries[0].has_gap = False
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("has_gap" in v for v in result.violations)

    def test_empty_limitations(self):
        report = _build([_make_complete_dict()], limitations=[])
        report.limitations = []
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("limitations must be non-empty" in v for v in result.violations)

    def test_valid_no_gaps_report(self):
        report = _build([_make_complete_dict(), _make_complete_dict(fid="FAM-002")])
        result = validate_batch_evidence_gap_report(report)
        assert result.valid

    def test_valid_no_families_report(self):
        report = _build([])
        result = validate_batch_evidence_gap_report(report)
        assert result.valid

    def test_valid_critical_gaps_report(self):
        report = _build([_make_empty_dict(), _make_empty_dict(fid="FAM-004")])
        result = validate_batch_evidence_gap_report(report)
        assert result.valid

    def test_valid_partial_gaps_report(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        result = validate_batch_evidence_gap_report(report)
        assert result.valid


class TestBuildBatchEvidenceGapReport:
    def test_all_complete_no_gaps(self):
        report = _build([_make_complete_dict(), _make_complete_dict(fid="FAM-002")])
        assert report.overall_gap_verdict == "no_gaps"
        assert report.n_families_with_gaps == 0

    def test_zero_families_no_families(self):
        report = _build([])
        assert report.overall_gap_verdict == "no_families"
        assert report.n_families_total == 0
        assert report.n_families_with_gaps == 0
        assert report.n_families_complete == 0
        assert report.total_missing_count == 0

    def test_all_missing_critical_gaps(self):
        report = _build([_make_empty_dict(), _make_empty_dict(fid="FAM-004")])
        assert report.overall_gap_verdict == "critical_gaps"
        assert report.n_families_with_gaps == report.n_families_total

    def test_mixed_partial_gaps(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        assert report.overall_gap_verdict == "partial_gaps"
        assert report.n_families_with_gaps == 1
        assert report.n_families_total == 2

    def test_dry_lab_only_auto_set_true(self):
        report = _build([_make_complete_dict()])
        assert report.dry_lab_only is True

    def test_n_families_total_len(self):
        report = _build([_make_complete_dict(), _make_gap_dict(), _make_empty_dict()])
        assert report.n_families_total == 3

    def test_n_families_with_gaps_counted(self):
        report = _build([_make_complete_dict(), _make_gap_dict(missing=("ECC",)), _make_gap_dict(missing=("BSP", "SEG"))])
        assert report.n_families_with_gaps == 2

    def test_n_families_complete_counted(self):
        report = _build([_make_complete_dict(), _make_gap_dict(), _make_complete_dict(fid="FAM-005")])
        assert report.n_families_complete == 2

    def test_total_missing_count_sum(self):
        report = _build([_make_gap_dict(missing=("ECC", "STL")), _make_gap_dict(missing=("BSP",))])
        assert report.total_missing_count == 3

    def test_required_artifact_types_correct(self):
        report = _build([_make_complete_dict()])
        assert report.required_artifact_types == ["BSP", "ECC", "SEG", "STL"]

    def test_present_only_required_types(self):
        d = {"candidate_family_id": "FAM-001", "artifact_ids": {"BSP": "a", "ECC": "b", "XYZ": "c", "EXTRA": "d"}}
        report = _build([d])
        assert report.family_gap_entries[0].present_artifact_types == ["BSP", "ECC"]

    def test_missing_sorted(self):
        d = {"candidate_family_id": "FAM-001", "artifact_ids": {"BSP": "a"}}
        report = _build([d])
        assert report.family_gap_entries[0].missing_artifact_types == ["ECC", "SEG", "STL"]

    def test_gap_count_matches_missing(self):
        report = _build([_make_gap_dict(missing=("STL",))])
        assert report.family_gap_entries[0].gap_count == 1
        assert len(report.family_gap_entries[0].missing_artifact_types) == 1

    def test_has_gap_true_when_missing(self):
        report = _build([_make_gap_dict(missing=("BSP",))])
        assert report.family_gap_entries[0].has_gap is True

    def test_has_gap_false_when_complete(self):
        report = _build([_make_complete_dict()])
        assert report.family_gap_entries[0].has_gap is False

    def test_one_complete_one_gap_total_count(self):
        report = _build([_make_complete_dict(), _make_gap_dict(missing=("BSP", "ECC", "STL"))])
        assert report.total_missing_count == 3

    def test_xyz_only_present_empty_missing_all(self):
        d = {"candidate_family_id": "FAM-001", "artifact_ids": {"XYZ": "x"}}
        report = _build([d])
        entry = report.family_gap_entries[0]
        assert entry.present_artifact_types == []
        assert entry.missing_artifact_types == ["BSP", "ECC", "SEG", "STL"]
        assert entry.gap_count == 4

    def test_single_family_complete_no_gaps(self):
        report = _build([_make_complete_dict()])
        assert report.overall_gap_verdict == "no_gaps"
        assert report.n_families_total == 1
        assert report.n_families_with_gaps == 0
        assert report.n_families_complete == 1


class TestBatchEvidenceGapReportIntegration:
    def test_round_trip_build_validate(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        result = validate_batch_evidence_gap_report(report)
        assert result.valid

    def test_no_families_verdict_zero_dicts(self):
        report = _build([])
        assert report.overall_gap_verdict == "no_families"
        assert report.n_families_total == 0
        assert report.family_gap_entries == []

    def test_no_gaps_all_complete(self):
        families = [_make_complete_dict(fid=f"FAM-{i:03d}") for i in range(1, 5)]
        report = _build(families)
        assert report.overall_gap_verdict == "no_gaps"
        assert report.n_families_with_gaps == 0
        assert report.n_families_complete == 4

    def test_critical_gaps_no_required_artifacts(self):
        families = [_make_empty_dict(fid=f"FAM-{i:03d}") for i in range(1, 4)]
        report = _build(families)
        assert report.overall_gap_verdict == "critical_gaps"
        assert report.n_families_with_gaps == 3
        assert report.total_missing_count == 12

    def test_partial_gaps_boundary(self):
        report = _build([_make_complete_dict(), _make_gap_dict(missing=("BSP", "ECC", "SEG", "STL"))])
        assert report.overall_gap_verdict == "partial_gaps"
        assert report.n_families_with_gaps == 1
        assert report.n_families_complete == 1
        assert report.n_families_total == 2

    def test_total_missing_count_aggregates(self):
        families = [
            _make_complete_dict(fid="FAM-001"),
            _make_gap_dict(fid="FAM-002", missing=("ECC",)),
            _make_gap_dict(fid="FAM-003", missing=("STL", "BSP")),
            _make_empty_dict(fid="FAM-004"),
        ]
        report = _build(families)
        assert report.total_missing_count == 7

    def test_toy_in_build_then_validate_catches(self):
        report = _build([_make_complete_dict(fid="TOY-TEST")])
        assert report.family_gap_entries[0].has_gap is False
        result = validate_batch_evidence_gap_report(report)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_format_contains_key_fields(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        output = format_batch_evidence_gap_report(report)
        assert report.beg_id in output
        assert report.overall_gap_verdict in output
        assert str(report.n_families_total) in output


class TestFormatBatchEvidenceGapReport:
    def test_returns_string(self):
        report = _build([_make_complete_dict()])
        output = format_batch_evidence_gap_report(report)
        assert isinstance(output, str)

    def test_contains_beg_id(self):
        report = _build([_make_complete_dict()], beg_id="BEG-042")
        output = format_batch_evidence_gap_report(report)
        assert "BEG-042" in output

    def test_contains_overall_gap_verdict(self):
        report = _build([_make_complete_dict(), _make_gap_dict()])
        output = format_batch_evidence_gap_report(report)
        assert "partial_gaps" in output

    def test_contains_n_families_total(self):
        report = _build([_make_complete_dict(), _make_gap_dict(), _make_empty_dict()])
        output = format_batch_evidence_gap_report(report)
        assert "3" in output

    def test_contains_dry_lab_only(self):
        report = _build([_make_complete_dict()])
        output = format_batch_evidence_gap_report(report)
        assert "dry_lab_only" in output
