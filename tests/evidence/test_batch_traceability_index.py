"""Tests for batch_traceability_index — BTI- schema."""

import pytest
from openamp_foundry.evidence.batch_traceability_index import (
    FamilyArtifactEntry,
    BatchTraceabilityIndex,
    BTIValidationResult,
    REQUIRED_BATCH_ARTIFACT_TYPES,
    VALID_FAMILY_COMPLETENESS_GRADES,
    VALID_BATCH_COMPLETENESS_GRADES,
    validate_batch_traceability_index,
    build_batch_traceability_index,
    format_batch_traceability_index,
)


def _make_complete_family(fid="AMP-001"):
    return {
        "candidate_family_id": fid,
        "artifact_ids": {
            "BSP": "BSP-001",
            "SEG": "SEG-001",
            "ECC": "ECC-001",
            "STL": "STL-001",
        },
    }


def _make_partial_family(fid="AMP-002"):
    return {"candidate_family_id": fid, "artifact_ids": {"BSP": "BSP-002"}}


def _make_empty_family(fid="AMP-003"):
    return {"candidate_family_id": fid, "artifact_ids": {}}


def _make_valid_full_index(**overrides):
    families = [_make_complete_family("AMP-001"), _make_complete_family("AMP-004")]
    entries = [
        FamilyArtifactEntry(
            candidate_family_id=d["candidate_family_id"],
            artifact_ids=d["artifact_ids"],
            present_artifact_types=sorted(d["artifact_ids"].keys()),
            missing_artifact_types=sorted(
                REQUIRED_BATCH_ARTIFACT_TYPES - set(d["artifact_ids"].keys())
            ),
            family_completeness_grade="complete",
        )
        for d in families
    ]
    params = dict(
        bti_id="BTI-001",
        batch_id="BATCH-001",
        pipeline_version="1.0.0",
        n_families_total=2,
        n_families_complete=2,
        n_families_partial=0,
        n_families_empty=0,
        family_entries=entries,
        batch_completeness_grade="full",
        required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
        dry_lab_only=True,
        limitations=["test limitation"],
        created_at="2025-01-01",
        audit_notes="",
    )
    params.update(overrides)
    return BatchTraceabilityIndex(**params)


# ---------------------------------------------------------------------------
# Class 1 — TestFamilyArtifactEntry
# ---------------------------------------------------------------------------


class TestFamilyArtifactEntry:
    def test_valid_complete_construction(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="AMP-001",
            artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
            present_artifact_types=["BSP", "ECC", "SEG", "STL"],
            missing_artifact_types=[],
            family_completeness_grade="complete",
        )
        assert entry.candidate_family_id == "AMP-001"
        assert entry.family_completeness_grade == "complete"
        assert entry.missing_artifact_types == []

    def test_valid_partial_construction(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="AMP-002",
            artifact_ids={"BSP": "B-1"},
            present_artifact_types=["BSP"],
            missing_artifact_types=["ECC", "SEG", "STL"],
            family_completeness_grade="partial",
        )
        assert entry.candidate_family_id == "AMP-002"
        assert entry.family_completeness_grade == "partial"
        assert len(entry.artifact_ids) == 1

    def test_valid_empty_construction(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="AMP-003",
            artifact_ids={},
            present_artifact_types=[],
            missing_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            family_completeness_grade="empty",
        )
        assert entry.candidate_family_id == "AMP-003"
        assert entry.family_completeness_grade == "empty"
        assert entry.artifact_ids == {}
        assert entry.present_artifact_types == []

    def test_toy_prefix_not_blocked_at_entry_level(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="TOY-999",
            artifact_ids={"BSP": "B-1"},
            present_artifact_types=["BSP"],
            missing_artifact_types=["ECC", "SEG", "STL"],
            family_completeness_grade="partial",
        )
        assert entry.candidate_family_id == "TOY-999"

    def test_present_artifact_types_is_sorted_list(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="AMP-001",
            artifact_ids={"SEG": "S-1", "BSP": "B-1", "ECC": "E-1", "STL": "T-1"},
            present_artifact_types=["BSP", "ECC", "SEG", "STL"],
            missing_artifact_types=[],
            family_completeness_grade="complete",
        )
        assert entry.present_artifact_types == sorted(entry.artifact_ids.keys())

    def test_missing_artifact_types_is_sorted_list(self):
        entry = FamilyArtifactEntry(
            candidate_family_id="AMP-002",
            artifact_ids={"BSP": "B-1"},
            present_artifact_types=["BSP"],
            missing_artifact_types=["ECC", "SEG", "STL"],
            family_completeness_grade="partial",
        )
        assert entry.missing_artifact_types == sorted(
            REQUIRED_BATCH_ARTIFACT_TYPES - {"BSP"}
        )

    def test_family_completeness_grade_values(self):
        for grade in ("complete", "partial", "empty"):
            entry = FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={},
                present_artifact_types=[],
                missing_artifact_types=[],
                family_completeness_grade=grade,
            )
            assert entry.family_completeness_grade in VALID_FAMILY_COMPLETENESS_GRADES


# ---------------------------------------------------------------------------
# Class 2 — TestValidateBatchTraceabilityIndex
# ---------------------------------------------------------------------------


class TestValidateBatchTraceabilityIndex:
    def test_valid_full_batch_passes(self):
        index = _make_valid_full_index()
        result = validate_batch_traceability_index(index)
        assert result.valid
        assert result.violations == []

    def test_valid_none_batch_passes(self):
        families = [_make_empty_family("AMP-003")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id=d["candidate_family_id"],
                artifact_ids=d["artifact_ids"],
                present_artifact_types=[],
                missing_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
                family_completeness_grade="empty",
            )
            for d in families
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-002",
            batch_id="BATCH-002",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=0,
            n_families_partial=0,
            n_families_empty=1,
            family_entries=entries,
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test lim"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert result.valid

    def test_bti_id_not_starting_with_bti_fails(self):
        index = _make_valid_full_index(bti_id="INVALID-001")
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("BTI-" in v for v in result.violations)

    def test_batch_id_empty_fails(self):
        index = _make_valid_full_index(batch_id="")
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("batch_id" in v for v in result.violations)

    def test_dry_lab_only_false_fails(self):
        index = _make_valid_full_index(dry_lab_only=False)
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_n_families_total_mismatch_fails(self):
        index = _make_valid_full_index(n_families_total=99)
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("n_families_total" in v for v in result.violations)

    def test_n_families_complete_mismatch_fails(self):
        index = _make_valid_full_index(n_families_complete=0)
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("n_families_complete" in v for v in result.violations)

    def test_n_families_partial_mismatch_fails(self):
        families = [_make_complete_family("AMP-001"), _make_partial_family("AMP-002")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted(
                    {"BSP", "SEG", "ECC", "STL"}
                ),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=2,
            n_families_complete=1,
            n_families_partial=99,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="majority",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("n_families_partial" in v for v in result.violations)

    def test_n_families_empty_mismatch_fails(self):
        families = [_make_empty_family("AMP-003")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-003",
                artifact_ids={},
                present_artifact_types=[],
                missing_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
                family_completeness_grade="empty",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=0,
            n_families_partial=0,
            n_families_empty=99,
            family_entries=entries,
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("n_families_empty" in v for v in result.violations)

    def test_required_artifact_types_wrong_fails(self):
        index = _make_valid_full_index(required_artifact_types=["BSP", "SEG"])
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("required_artifact_types" in v for v in result.violations)

    def test_batch_completeness_grade_full_with_not_all_complete_fails(self):
        families = [_make_complete_family("AMP-001"), _make_partial_family("AMP-002")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted(
                    {"BSP", "SEG", "ECC", "STL"}
                ),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=2,
            n_families_complete=1,
            n_families_partial=1,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="full",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("full" in v for v in result.violations)

    def test_batch_completeness_grade_none_with_some_complete_fails(self):
        families = [_make_complete_family("AMP-001")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted(
                    {"BSP", "SEG", "ECC", "STL"}
                ),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=1,
            n_families_partial=0,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("none" in v for v in result.violations)

    def test_batch_completeness_grade_majority_requires_at_least_half(self):
        families = [_make_complete_family("AMP-001"), _make_complete_family("AMP-002"), _make_partial_family("AMP-003")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2", "SEG": "S-2", "ECC": "E-2", "STL": "T-2"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-003",
                artifact_ids={"BSP": "B-3"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=3,
            n_families_complete=2,
            n_families_partial=1,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="majority",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert result.valid

        bad = _make_valid_full_index(
            n_families_total=3,
            n_families_complete=1,
            n_families_partial=2,
            n_families_empty=0,
            batch_completeness_grade="majority",
        )
        r2 = validate_batch_traceability_index(bad)
        assert not r2.valid

    def test_batch_completeness_grade_minority_requires_positive_under_half(self):
        families = [_make_complete_family("AMP-001"), _make_partial_family("AMP-002"), _make_partial_family("AMP-003")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-003",
                artifact_ids={"BSP": "B-3"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=3,
            n_families_complete=1,
            n_families_partial=2,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="minority",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert result.valid

        bad = _make_valid_full_index(
            n_families_total=3,
            n_families_complete=2,
            n_families_partial=1,
            n_families_empty=0,
            batch_completeness_grade="minority",
        )
        r2 = validate_batch_traceability_index(bad)
        assert not r2.valid

    def test_toy_family_id_fails(self):
        families = [_make_complete_family("TOY-001")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="TOY-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=1,
            n_families_partial=0,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="full",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_present_artifact_types_mismatch_fails(self):
        families = [_make_complete_family("AMP-001")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=["BSP"],
                missing_artifact_types=[],
                family_completeness_grade="complete",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=1,
            n_families_partial=0,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="full",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("present_artifact_types" in v for v in result.violations)

    def test_missing_artifact_types_mismatch_fails(self):
        families = [_make_partial_family("AMP-002")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2"},
                present_artifact_types=["BSP"],
                missing_artifact_types=[],
                family_completeness_grade="partial",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=0,
            n_families_partial=1,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("missing_artifact_types" in v for v in result.violations)

    def test_family_completeness_grade_inconsistent_with_artifact_ids_fails(self):
        families = [_make_complete_family("AMP-001")]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="empty",
            )
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=1,
            n_families_complete=0,
            n_families_partial=0,
            n_families_empty=1,
            family_entries=entries,
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("family_completeness_grade" in v for v in result.violations)

    def test_empty_limitations_fails(self):
        index = _make_valid_full_index(limitations=[])
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_invalid_batch_completeness_grade_value_fails(self):
        index = _make_valid_full_index(batch_completeness_grade="invalid")
        result = validate_batch_traceability_index(index)
        assert not result.valid

    def test_zero_families_but_manual_mismatch_fails(self):
        index = BatchTraceabilityIndex(
            bti_id="BTI-001",
            batch_id="BATCH-001",
            pipeline_version="1.0.0",
            n_families_total=0,
            n_families_complete=0,
            n_families_partial=0,
            n_families_empty=0,
            family_entries=[],
            batch_completeness_grade="none",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["test"],
            created_at="2025-01-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert result.valid


# ---------------------------------------------------------------------------
# Class 3 — TestBuildBatchTraceabilityIndex
# ---------------------------------------------------------------------------


class TestBuildBatchTraceabilityIndex:
    def test_build_three_complete_families_full_grade(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_complete_family("AMP-004"),
            _make_complete_family("AMP-005"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-010",
            batch_id="BATCH-010",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "full"
        assert index.n_families_total == 3
        assert index.n_families_complete == 3
        assert index.n_families_partial == 0
        assert index.n_families_empty == 0

    def test_build_zero_families_none_grade(self):
        index = build_batch_traceability_index(
            bti_id="BTI-011",
            batch_id="BATCH-011",
            pipeline_version="2.0.0",
            family_artifact_dicts=[],
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "none"
        assert index.n_families_total == 0
        assert index.n_families_complete == 0
        assert index.n_families_partial == 0
        assert index.n_families_empty == 0

    def test_build_one_complete_one_partial_majority(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-012",
            batch_id="BATCH-012",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "majority"
        assert index.n_families_total == 2
        assert index.n_families_complete == 1
        assert index.n_families_partial == 1

    def test_build_all_partial_none_grade(self):
        families = [
            _make_partial_family("AMP-002"),
            _make_partial_family("AMP-006"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-013",
            batch_id="BATCH-013",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "none"
        assert index.n_families_complete == 0
        assert index.n_families_partial == 2

    def test_build_auto_sets_dry_lab_only_true(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-014",
            batch_id="BATCH-014",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.dry_lab_only is True

    def test_build_auto_sets_required_artifact_types(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-015",
            batch_id="BATCH-015",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.required_artifact_types == sorted(REQUIRED_BATCH_ARTIFACT_TYPES)

    def test_build_computes_present_artifact_types_correctly(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
            _make_empty_family("AMP-003"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-016",
            batch_id="BATCH-016",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.family_entries[0].present_artifact_types == sorted(
            {"BSP", "SEG", "ECC", "STL"}
        )
        assert index.family_entries[1].present_artifact_types == ["BSP"]
        assert index.family_entries[2].present_artifact_types == []

    def test_build_computes_missing_artifact_types_correctly(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
            _make_empty_family("AMP-003"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-017",
            batch_id="BATCH-017",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.family_entries[0].missing_artifact_types == []
        assert index.family_entries[1].missing_artifact_types == sorted(
            {"ECC", "SEG", "STL"}
        )
        assert index.family_entries[2].missing_artifact_types == sorted(
            REQUIRED_BATCH_ARTIFACT_TYPES
        )

    def test_build_complete_grade_when_all_required_types_present(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-018",
            batch_id="BATCH-018",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.family_entries[0].family_completeness_grade == "complete"

    def test_build_partial_grade_when_some_required_types_present(self):
        families = [_make_partial_family("AMP-002")]
        index = build_batch_traceability_index(
            bti_id="BTI-019",
            batch_id="BATCH-019",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.family_entries[0].family_completeness_grade == "partial"

    def test_build_empty_grade_when_artifact_ids_is_empty(self):
        families = [_make_empty_family("AMP-003")]
        index = build_batch_traceability_index(
            bti_id="BTI-020",
            batch_id="BATCH-020",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.family_entries[0].family_completeness_grade == "empty"

    def test_build_n_families_partial_counted_correctly(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
            _make_empty_family("AMP-003"),
            _make_partial_family("AMP-006"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-021",
            batch_id="BATCH-021",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.n_families_partial == 2

    def test_build_n_families_empty_counted_correctly(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_empty_family("AMP-003"),
            _make_empty_family("AMP-007"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-022",
            batch_id="BATCH-022",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.n_families_empty == 2

    def test_build_batch_majority_two_of_three_complete(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_complete_family("AMP-004"),
            _make_partial_family("AMP-002"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-023",
            batch_id="BATCH-023",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "majority"

    def test_build_batch_minority_one_of_three_complete(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
            _make_partial_family("AMP-006"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-024",
            batch_id="BATCH-024",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.batch_completeness_grade == "minority"

    def test_build_default_audit_notes_empty(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-025",
            batch_id="BATCH-025",
            pipeline_version="2.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-06-01",
        )
        assert index.audit_notes == ""


# ---------------------------------------------------------------------------
# Class 4 — TestBatchTraceabilityIndexIntegration
# ---------------------------------------------------------------------------


class TestBatchTraceabilityIndexIntegration:
    def test_full_round_trip_build_validate_passes(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
            _make_empty_family("AMP-003"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-100",
            batch_id="BATCH-100",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["some lim"],
            created_at="2025-07-01",
        )
        result = validate_batch_traceability_index(index)
        assert result.valid

    def test_toy_family_id_blocked_end_to_end(self):
        families = [_make_complete_family("TOY-001")]
        with pytest.raises(ValueError, match="TOY-"):
            build_batch_traceability_index(
                bti_id="BTI-101",
                batch_id="BATCH-101",
                pipeline_version="3.0.0",
                family_artifact_dicts=families,
                limitations=["lim"],
                created_at="2025-07-01",
            )

    def test_dry_lab_only_false_blocked_end_to_end(self):
        index = _make_valid_full_index()
        with pytest.raises(ValueError, match="dry_lab_only"):
            bad = _make_valid_full_index(dry_lab_only=False)
            result = validate_batch_traceability_index(bad)
            if not result.valid:
                raise ValueError(f"Invalid BTI: {result.violations}")

    def test_full_grade_requires_all_families_complete(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
        ]
        entries = [
            FamilyArtifactEntry(
                candidate_family_id="AMP-001",
                artifact_ids={"BSP": "B-1", "SEG": "S-1", "ECC": "E-1", "STL": "T-1"},
                present_artifact_types=sorted({"BSP", "SEG", "ECC", "STL"}),
                missing_artifact_types=[],
                family_completeness_grade="complete",
            ),
            FamilyArtifactEntry(
                candidate_family_id="AMP-002",
                artifact_ids={"BSP": "B-2"},
                present_artifact_types=["BSP"],
                missing_artifact_types=["ECC", "SEG", "STL"],
                family_completeness_grade="partial",
            ),
        ]
        index = BatchTraceabilityIndex(
            bti_id="BTI-102",
            batch_id="BATCH-102",
            pipeline_version="3.0.0",
            n_families_total=2,
            n_families_complete=1,
            n_families_partial=1,
            n_families_empty=0,
            family_entries=entries,
            batch_completeness_grade="full",
            required_artifact_types=sorted(REQUIRED_BATCH_ARTIFACT_TYPES),
            dry_lab_only=True,
            limitations=["lim"],
            created_at="2025-07-01",
            audit_notes="",
        )
        result = validate_batch_traceability_index(index)
        assert not result.valid
        assert any("full" in v for v in result.violations)

    def test_none_grade_when_no_families_complete(self):
        families = [
            _make_partial_family("AMP-002"),
            _make_partial_family("AMP-006"),
            _make_empty_family("AMP-003"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-103",
            batch_id="BATCH-103",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
        )
        assert index.batch_completeness_grade == "none"

    def test_required_artifact_types_always_sorted(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-104",
            batch_id="BATCH-104",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
        )
        assert index.required_artifact_types == sorted(REQUIRED_BATCH_ARTIFACT_TYPES)
        assert index.required_artifact_types == ["BSP", "ECC", "SEG", "STL"]

    def test_build_with_mixed_families(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_complete_family("AMP-004"),
            _make_partial_family("AMP-002"),
            _make_empty_family("AMP-003"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-105",
            batch_id="BATCH-105",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
        )
        assert index.n_families_total == 4
        assert index.n_families_complete == 2
        assert index.n_families_partial == 1
        assert index.n_families_empty == 1
        assert index.batch_completeness_grade == "majority"

    def test_audit_notes_can_be_nonempty_string(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-106",
            batch_id="BATCH-106",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
            audit_notes="Reviewed by JM.",
        )
        assert index.audit_notes == "Reviewed by JM."

    def test_build_with_single_partial_family(self):
        families = [_make_partial_family("AMP-002")]
        index = build_batch_traceability_index(
            bti_id="BTI-107",
            batch_id="BATCH-107",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
        )
        assert index.n_families_total == 1
        assert index.n_families_complete == 0
        assert index.n_families_partial == 1
        assert index.batch_completeness_grade == "none"

    def test_build_with_single_empty_family(self):
        families = [_make_empty_family("AMP-003")]
        index = build_batch_traceability_index(
            bti_id="BTI-108",
            batch_id="BATCH-108",
            pipeline_version="3.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-07-01",
        )
        assert index.n_families_total == 1
        assert index.n_families_empty == 1
        assert index.batch_completeness_grade == "none"


# ---------------------------------------------------------------------------
# Class 5 — TestFormatBatchTraceabilityIndex
# ---------------------------------------------------------------------------


class TestFormatBatchTraceabilityIndex:
    def test_format_returns_string(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert isinstance(result, str)

    def test_format_contains_bti_id(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert "BTI-200" in result

    def test_format_contains_batch_id(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert "BATCH-200" in result

    def test_format_contains_batch_completeness_grade(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert "full" in result

    def test_format_contains_n_families_total(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert "Total: 1" in result

    def test_format_contains_family_entries(self):
        families = [
            _make_complete_family("AMP-001"),
            _make_partial_family("AMP-002"),
        ]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
        )
        result = format_batch_traceability_index(index)
        assert "Family Entries:" in result
        assert "AMP-001" in result
        assert "AMP-002" in result

    def test_format_with_audit_notes(self):
        families = [_make_complete_family("AMP-001")]
        index = build_batch_traceability_index(
            bti_id="BTI-200",
            batch_id="BATCH-200",
            pipeline_version="4.0.0",
            family_artifact_dicts=families,
            limitations=["lim"],
            created_at="2025-08-01",
            audit_notes="Reviewed.",
        )
        result = format_batch_traceability_index(index)
        assert "Audit Notes:" in result
        assert "Reviewed." in result
