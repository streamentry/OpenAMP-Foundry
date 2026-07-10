"""Tests for cross_batch_audit_summary module — CBA2- schema."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.cross_batch_audit_summary import (
    BatchSummaryEntry,
    CrossBatchAuditSummary,
    VALID_BATCH_GRADES,
    LOW_COMPLETENESS_GRADES,
    VALID_AUDIT_VERDICTS,
    COMPLETENESS_AUDIT_THRESHOLD,
    validate_cross_batch_audit_summary,
    build_cross_batch_audit_summary,
    format_cross_batch_audit_summary,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_full_entry(batch_id="B001", bti_id="BTI-001", n=3):
    return {"batch_id": batch_id, "bti_id": bti_id, "n_families_total": n,
            "n_families_complete": n, "n_families_partial": 0, "n_families_empty": 0,
            "batch_completeness_grade": "full"}


def _make_none_entry(batch_id="B002", bti_id="BTI-002", n=3):
    return {"batch_id": batch_id, "bti_id": bti_id, "n_families_total": n,
            "n_families_complete": 0, "n_families_partial": n, "n_families_empty": 0,
            "batch_completeness_grade": "none"}


def _make_minority_entry(batch_id="B003", bti_id="BTI-003", n=3):
    return {"batch_id": batch_id, "bti_id": bti_id, "n_families_total": n,
            "n_families_complete": 1, "n_families_partial": 2, "n_families_empty": 0,
            "batch_completeness_grade": "minority"}


def _make_majority_entry(batch_id="B004", bti_id="BTI-004", n=4):
    return {"batch_id": batch_id, "bti_id": bti_id, "n_families_total": n,
            "n_families_complete": 3, "n_families_partial": 1, "n_families_empty": 0,
            "batch_completeness_grade": "majority"}


# ---------------------------------------------------------------------------
# Class 1 — BatchSummaryEntry dataclass
# ---------------------------------------------------------------------------

class TestBatchSummaryEntry:

    def test_full_entry_flagged_false(self):
        entry = BatchSummaryEntry(
            batch_id="B001", bti_id="BTI-001",
            n_families_total=3, n_families_complete=3,
            n_families_partial=0, n_families_empty=0,
            batch_completeness_grade="full", flagged_low_completeness=False,
        )
        assert entry.batch_completeness_grade == "full"
        assert entry.flagged_low_completeness is False

    def test_none_entry_flagged_true(self):
        entry = BatchSummaryEntry(
            batch_id="B002", bti_id="BTI-002",
            n_families_total=3, n_families_complete=0,
            n_families_partial=3, n_families_empty=0,
            batch_completeness_grade="none", flagged_low_completeness=True,
        )
        assert entry.batch_completeness_grade == "none"
        assert entry.flagged_low_completeness is True

    def test_minority_entry_flagged_true(self):
        entry = BatchSummaryEntry(
            batch_id="B003", bti_id="BTI-003",
            n_families_total=3, n_families_complete=1,
            n_families_partial=2, n_families_empty=0,
            batch_completeness_grade="minority", flagged_low_completeness=True,
        )
        assert entry.batch_completeness_grade == "minority"
        assert entry.flagged_low_completeness is True

    def test_majority_entry_flagged_false(self):
        entry = BatchSummaryEntry(
            batch_id="B004", bti_id="BTI-004",
            n_families_total=4, n_families_complete=3,
            n_families_partial=1, n_families_empty=0,
            batch_completeness_grade="majority", flagged_low_completeness=False,
        )
        assert entry.batch_completeness_grade == "majority"
        assert entry.flagged_low_completeness is False

    def test_batch_completeness_grade_in_valid_set(self):
        for grade in ("full", "majority", "minority", "none"):
            entry = BatchSummaryEntry(
                batch_id="B001", bti_id="BTI-001",
                n_families_total=1, n_families_complete=1,
                n_families_partial=0, n_families_empty=0,
                batch_completeness_grade=grade, flagged_low_completeness=False,
            )
            assert entry.batch_completeness_grade in VALID_BATCH_GRADES

    def test_bti_id_field_present(self):
        entry = BatchSummaryEntry(
            batch_id="B001", bti_id="BTI-001",
            n_families_total=3, n_families_complete=3,
            n_families_partial=0, n_families_empty=0,
            batch_completeness_grade="full", flagged_low_completeness=False,
        )
        assert hasattr(entry, "bti_id")
        assert entry.bti_id == "BTI-001"


# ---------------------------------------------------------------------------
# Class 2 — validate_cross_batch_audit_summary
# ---------------------------------------------------------------------------

class TestValidateCrossBatchAuditSummary:

    def _valid_summary(self, **overrides):
        d = dict(
            cba2_id="CBA2-001",
            pipeline_version="v1.0",
            n_batches_total=2,
            n_batches_flagged=0,
            total_families_across_batches=6,
            total_families_complete=6,
            total_families_partial=0,
            total_families_empty=0,
            batch_entries=[
                BatchSummaryEntry(
                    batch_id="B001", bti_id="BTI-001",
                    n_families_total=3, n_families_complete=3,
                    n_families_partial=0, n_families_empty=0,
                    batch_completeness_grade="full", flagged_low_completeness=False,
                ),
                BatchSummaryEntry(
                    batch_id="B002", bti_id="BTI-002",
                    n_families_total=3, n_families_complete=3,
                    n_families_partial=0, n_families_empty=0,
                    batch_completeness_grade="full", flagged_low_completeness=False,
                ),
            ],
            overall_audit_verdict="all_complete",
            flagged_batch_ids=[],
            audit_coverage_rate=1.0,
            dry_lab_only=True,
            limitations=["toy data only"],
            created_at="2025-01-01T00:00:00Z",
        )
        d.update(overrides)
        return CrossBatchAuditSummary(**d)

    def test_valid_all_complete(self):
        violations = validate_cross_batch_audit_summary(self._valid_summary())
        assert violations == []

    def test_valid_no_batches(self):
        s = self._valid_summary(
            n_batches_total=0, n_batches_flagged=0,
            total_families_across_batches=0, total_families_complete=0,
            total_families_partial=0, total_families_empty=0,
            batch_entries=[], overall_audit_verdict="no_batches",
            flagged_batch_ids=[], audit_coverage_rate=0.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert violations == []

    def test_invalid_cba2_id_prefix(self):
        s = self._valid_summary(cba2_id="INVALID-001")
        violations = validate_cross_batch_audit_summary(s)
        assert any("cba2_id must start with 'CBA2-'" in v for v in violations)

    def test_dry_lab_only_false(self):
        s = self._valid_summary(dry_lab_only=False)
        violations = validate_cross_batch_audit_summary(s)
        assert any("dry_lab_only must be True" in v for v in violations)

    def test_n_batches_total_mismatch(self):
        s = self._valid_summary(n_batches_total=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("n_batches_total" in v for v in violations)

    def test_n_batches_flagged_mismatch(self):
        s = self._valid_summary(n_batches_flagged=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("n_batches_flagged" in v for v in violations)

    def test_total_families_across_batches_mismatch(self):
        s = self._valid_summary(total_families_across_batches=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("total_families_across_batches" in v for v in violations)

    def test_total_families_complete_mismatch(self):
        s = self._valid_summary(total_families_complete=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("total_families_complete" in v for v in violations)

    def test_total_families_partial_mismatch(self):
        s = self._valid_summary(total_families_partial=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("total_families_partial" in v for v in violations)

    def test_total_families_empty_mismatch(self):
        s = self._valid_summary(total_families_empty=99)
        violations = validate_cross_batch_audit_summary(s)
        assert any("total_families_empty" in v for v in violations)

    def test_entry_flagged_inconsistent_with_grade(self):
        entry = BatchSummaryEntry(
            batch_id="B001", bti_id="BTI-001",
            n_families_total=3, n_families_complete=0,
            n_families_partial=3, n_families_empty=0,
            batch_completeness_grade="none", flagged_low_completeness=False,
        )
        s = self._valid_summary(
            batch_entries=[entry],
            n_batches_total=1, n_batches_flagged=0,
            total_families_across_batches=3, total_families_complete=0,
            total_families_partial=3, total_families_empty=0,
            overall_audit_verdict="none_complete",
            flagged_batch_ids=[], audit_coverage_rate=0.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("flagged_low_completeness" in v for v in violations)

    def test_flagged_batch_ids_not_sorted(self):
        entries = [
            BatchSummaryEntry(
                batch_id="B003", bti_id="BTI-003",
                n_families_total=3, n_families_complete=0,
                n_families_partial=3, n_families_empty=0,
                batch_completeness_grade="none", flagged_low_completeness=True,
            ),
            BatchSummaryEntry(
                batch_id="B002", bti_id="BTI-002",
                n_families_total=3, n_families_complete=0,
                n_families_partial=3, n_families_empty=0,
                batch_completeness_grade="none", flagged_low_completeness=True,
            ),
        ]
        s = self._valid_summary(
            batch_entries=entries,
            n_batches_total=2, n_batches_flagged=2,
            total_families_across_batches=6, total_families_complete=0,
            total_families_partial=6, total_families_empty=0,
            overall_audit_verdict="none_complete",
            flagged_batch_ids=["B003", "B002"],
            audit_coverage_rate=0.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("flagged_batch_ids" in v for v in violations)

    def test_flagged_batch_ids_missing_flagged(self):
        entry = BatchSummaryEntry(
            batch_id="B002", bti_id="BTI-002",
            n_families_total=3, n_families_complete=0,
            n_families_partial=3, n_families_empty=0,
            batch_completeness_grade="none", flagged_low_completeness=True,
        )
        s = self._valid_summary(
            batch_entries=[entry],
            n_batches_total=1, n_batches_flagged=1,
            total_families_across_batches=3, total_families_complete=0,
            total_families_partial=3, total_families_empty=0,
            overall_audit_verdict="none_complete",
            flagged_batch_ids=[],
            audit_coverage_rate=0.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("flagged_batch_ids" in v for v in violations)

    def test_audit_coverage_rate_mismatch(self):
        s = self._valid_summary(audit_coverage_rate=0.5)
        violations = validate_cross_batch_audit_summary(s)
        assert any("audit_coverage_rate" in v for v in violations)

    def test_verdict_all_complete_with_not_all_full_fails(self):
        entries = [
            BatchSummaryEntry(
                batch_id="B001", bti_id="BTI-001",
                n_families_total=3, n_families_complete=3,
                n_families_partial=0, n_families_empty=0,
                batch_completeness_grade="full", flagged_low_completeness=False,
            ),
            BatchSummaryEntry(
                batch_id="B002", bti_id="BTI-002",
                n_families_total=3, n_families_complete=0,
                n_families_partial=3, n_families_empty=0,
                batch_completeness_grade="none", flagged_low_completeness=True,
            ),
        ]
        s = self._valid_summary(
            batch_entries=entries,
            n_batches_total=2, n_batches_flagged=1,
            total_families_across_batches=6, total_families_complete=3,
            total_families_partial=3, total_families_empty=0,
            overall_audit_verdict="all_complete",
            flagged_batch_ids=["B002"],
            audit_coverage_rate=0.5,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("overall_audit_verdict" in v for v in violations)

    def test_verdict_none_complete_with_some_full_fails(self):
        entries = [
            BatchSummaryEntry(
                batch_id="B001", bti_id="BTI-001",
                n_families_total=3, n_families_complete=3,
                n_families_partial=0, n_families_empty=0,
                batch_completeness_grade="full", flagged_low_completeness=False,
            ),
        ]
        s = self._valid_summary(
            batch_entries=entries,
            n_batches_total=1, n_batches_flagged=0,
            total_families_across_batches=3, total_families_complete=3,
            total_families_partial=0, total_families_empty=0,
            overall_audit_verdict="none_complete",
            flagged_batch_ids=[], audit_coverage_rate=1.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("overall_audit_verdict" in v for v in violations)

    def test_verdict_no_batches_with_n_positive_fails(self):
        entry = BatchSummaryEntry(
            batch_id="B001", bti_id="BTI-001",
            n_families_total=3, n_families_complete=3,
            n_families_partial=0, n_families_empty=0,
            batch_completeness_grade="full", flagged_low_completeness=False,
        )
        s = self._valid_summary(
            batch_entries=[entry],
            n_batches_total=1, n_batches_flagged=0,
            total_families_across_batches=3, total_families_complete=3,
            total_families_partial=0, total_families_empty=0,
            overall_audit_verdict="no_batches",
            flagged_batch_ids=[], audit_coverage_rate=1.0,
        )
        violations = validate_cross_batch_audit_summary(s)
        assert any("overall_audit_verdict" in v for v in violations)

    def test_limitations_empty_fails(self):
        s = self._valid_summary(limitations=[])
        violations = validate_cross_batch_audit_summary(s)
        assert any("limitations" in v for v in violations)


# ---------------------------------------------------------------------------
# Class 3 — build_cross_batch_audit_summary
# ---------------------------------------------------------------------------

class TestBuildCrossBatchAuditSummary:

    def test_three_full_batches(self):
        d = [
            _make_full_entry("B001", "BTI-001"),
            _make_full_entry("B002", "BTI-002"),
            _make_full_entry("B003", "BTI-003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy data"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "all_complete"
        assert s.n_batches_flagged == 0

    def test_zero_batches(self):
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", [], ["toy data"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "no_batches"
        assert s.n_batches_total == 0
        assert s.total_families_across_batches == 0
        assert s.total_families_complete == 0
        assert s.total_families_partial == 0
        assert s.total_families_empty == 0

    def test_two_full_one_none(self):
        d = [
            _make_full_entry("B001", "BTI-001"),
            _make_full_entry("B002", "BTI-002"),
            _make_none_entry("B003", "BTI-003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy data"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "majority_complete"
        assert s.n_batches_flagged == 1

    def test_one_full_two_none(self):
        d = [
            _make_full_entry("B001", "BTI-001"),
            _make_none_entry("B002", "BTI-002"),
            _make_none_entry("B003", "BTI-003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy data"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "minority_complete"
        assert s.n_batches_flagged == 2

    def test_three_none(self):
        d = [
            _make_none_entry("B001", "BTI-001"),
            _make_none_entry("B002", "BTI-002"),
            _make_none_entry("B003", "BTI-003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy data"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "none_complete"
        assert s.n_batches_flagged == 3

    def test_dry_lab_only_auto_true(self):
        d = [_make_full_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.dry_lab_only is True

    def test_n_batches_total_matches_len(self):
        d = [_make_full_entry("B001"), _make_full_entry("B002")]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.n_batches_total == len(d)

    def test_total_families_across_batches_sum(self):
        d = [
            _make_full_entry("B001", n=3),
            _make_full_entry("B002", n=5),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.total_families_across_batches == 8

    def test_total_families_complete_sum(self):
        d = [
            _make_full_entry("B001", n=3),
            _make_minority_entry("B002", n=3),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.total_families_complete == 4

    def test_total_families_partial_sum(self):
        d = [
            _make_full_entry("B001", n=3),
            _make_minority_entry("B002", n=3),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.total_families_partial == 2

    def test_total_families_empty_sum(self):
        d = [
            _make_full_entry("B001", n=3),
            _make_full_entry("B002", n=3),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.total_families_empty == 0

    def test_n_batches_flagged_counted_correctly(self):
        d = [
            _make_full_entry("B001"),
            _make_minority_entry("B002"),
            _make_none_entry("B003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.n_batches_flagged == 2

    def test_flagged_batch_ids_sorted(self):
        d = [
            _make_none_entry("B003"),
            _make_full_entry("B001"),
            _make_minority_entry("B002"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.flagged_batch_ids == ["B002", "B003"]

    def test_audit_coverage_rate_computed(self):
        d = [
            _make_full_entry("B001", n=4),
            _make_minority_entry("B002", n=4),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.audit_coverage_rate == pytest.approx(5 / 8)

    def test_one_full_one_full_all_complete(self):
        d = [
            _make_full_entry("B001"),
            _make_full_entry("B002"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "all_complete"

    def test_one_full_one_majority_majority_complete(self):
        d = [
            _make_full_entry("B001"),
            _make_majority_entry("B002"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "majority_complete"

    def test_zero_full_but_n_positive_none_complete(self):
        d = [
            _make_minority_entry("B001"),
            _make_none_entry("B002"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "none_complete"

    def test_audit_coverage_rate_zero_when_zero_families(self):
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", [], ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.audit_coverage_rate == 0.0


# ---------------------------------------------------------------------------
# Class 4 — Integration
# ---------------------------------------------------------------------------

class TestCrossBatchAuditSummaryIntegration:

    def test_full_round_trip_build_validate(self):
        d = [
            _make_full_entry("B001"),
            _make_none_entry("B002"),
            _make_minority_entry("B003"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy data"], "2025-01-01T00:00:00Z",
        )
        violations = validate_cross_batch_audit_summary(s)
        assert violations == []

    def test_flagged_batches_are_minority_or_none(self):
        d = [
            _make_full_entry("B001"),
            _make_majority_entry("B002"),
            _make_minority_entry("B003"),
            _make_none_entry("B004"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.n_batches_flagged == 2
        assert all(
            e.batch_completeness_grade in LOW_COMPLETENESS_GRADES
            for e in s.batch_entries if e.flagged_low_completeness
        )

    def test_flagged_batch_ids_are_sorted(self):
        d = [
            _make_none_entry("Z001"),
            _make_minority_entry("A001"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.flagged_batch_ids == sorted(s.flagged_batch_ids)

    def test_all_complete_requires_all_full(self):
        d = [
            _make_full_entry("B001"),
            _make_majority_entry("B002"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict != "all_complete"

    def test_audit_coverage_rate_in_range(self):
        d = [
            _make_full_entry("B001"),
            _make_none_entry("B002"),
            _make_minority_entry("B003"),
            _make_majority_entry("B004"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert 0.0 <= s.audit_coverage_rate <= 1.0

    def test_multiple_batches_different_grades(self):
        d = [
            _make_full_entry("B001"),
            _make_majority_entry("B002"),
            _make_minority_entry("B003"),
            _make_none_entry("B004"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        grades = {e.batch_id: e.batch_completeness_grade for e in s.batch_entries}
        assert grades["B001"] == "full"
        assert grades["B002"] == "majority"
        assert grades["B003"] == "minority"
        assert grades["B004"] == "none"

    def test_majority_complete_at_exactly_half(self):
        d = [
            _make_full_entry("B001"),
            _make_full_entry("B002"),
            _make_none_entry("B003"),
            _make_none_entry("B004"),
        ]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "majority_complete"

    def test_empty_dicts_no_batches(self):
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", [], ["toy"], "2025-01-01T00:00:00Z",
        )
        assert s.overall_audit_verdict == "no_batches"
        assert s.n_batches_total == 0


# ---------------------------------------------------------------------------
# Class 5 — format_cross_batch_audit_summary
# ---------------------------------------------------------------------------

class TestFormatCrossBatchAuditSummary:

    def test_returns_string(self):
        d = [_make_full_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        result = format_cross_batch_audit_summary(s)
        assert isinstance(result, str)

    def test_contains_cba2_id(self):
        d = [_make_full_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        result = format_cross_batch_audit_summary(s)
        assert "CBA2-001" in result

    def test_contains_overall_audit_verdict(self):
        d = [_make_full_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        result = format_cross_batch_audit_summary(s)
        assert "all_complete" in result

    def test_contains_n_batches_total(self):
        d = [_make_full_entry(), _make_none_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        result = format_cross_batch_audit_summary(s)
        assert "2 total" in result

    def test_contains_n_batches_flagged(self):
        d = [_make_full_entry(), _make_none_entry()]
        s = build_cross_batch_audit_summary(
            "CBA2-001", "v1.0", d, ["toy"], "2025-01-01T00:00:00Z",
        )
        result = format_cross_batch_audit_summary(s)
        assert "1 flagged" in result
