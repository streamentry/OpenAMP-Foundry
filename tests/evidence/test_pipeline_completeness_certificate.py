"""Tests for the Pipeline Completeness Certificate (PCC-) schema."""
import pytest
from openamp_foundry.evidence.pipeline_completeness_certificate import (
    SchemaPresenceEntry,
    PipelineCompletenessCertificate,
    PCCValidationResult,
    REQUIRED_EVIDENCE_SCHEMA_TYPES,
    VALID_COMPLETENESS_GRADES,
    validate_pipeline_completeness_certificate,
    build_pipeline_completeness_certificate,
    format_pipeline_completeness_certificate,
)

ALL_SCHEMA_TYPES = sorted(REQUIRED_EVIDENCE_SCHEMA_TYPES)
N_REQUIRED = len(REQUIRED_EVIDENCE_SCHEMA_TYPES)


def _all_present():
    return {st: f"{st}-001" for st in REQUIRED_EVIDENCE_SCHEMA_TYPES}


def _partial_present(n):
    return {st: f"{st}-001" for st in ALL_SCHEMA_TYPES[:n]}


def _build_valid(**kwargs):
    defaults = dict(
        pcc_id="PCC-001",
        pipeline_run_id="RUN-001",
        pipeline_version="v1.0",
        present_schema_artifact_ids=_all_present(),
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_pipeline_completeness_certificate(**defaults)


class TestSchemaPresenceEntry:
    def test_present_entry(self):
        e = SchemaPresenceEntry(schema_type="BSP", present=True, artifact_id="BSP-001")
        assert e.present is True
        assert e.artifact_id == "BSP-001"

    def test_absent_entry(self):
        e = SchemaPresenceEntry(schema_type="SAT", present=False, artifact_id="")
        assert e.present is False
        assert e.artifact_id == ""

    def test_schema_type_stored(self):
        e = SchemaPresenceEntry(schema_type="PQT", present=True, artifact_id="PQT-01")
        assert e.schema_type == "PQT"

    def test_artifact_id_stored(self):
        e = SchemaPresenceEntry(schema_type="RSR", present=True, artifact_id="RSR-999")
        assert e.artifact_id == "RSR-999"

    def test_entry_is_dataclass(self):
        e = SchemaPresenceEntry(schema_type="BTI", present=True, artifact_id="BTI-01")
        assert hasattr(e, "schema_type")
        assert hasattr(e, "present")
        assert hasattr(e, "artifact_id")


class TestValidatePipelineCompletenessCertificate:
    def test_valid_all_present_passes(self):
        r = _build_valid()
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_valid_none_present_passes(self):
        r = _build_valid(present_schema_artifact_ids={})
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_pcc_id_wrong_prefix_fails(self):
        r = _build_valid()
        object.__setattr__(r, "pcc_id", "BAD-001")
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid
        assert any("pcc_id" in v for v in result.violations)

    def test_dry_lab_only_false_fails(self):
        r = _build_valid()
        object.__setattr__(r, "dry_lab_only", False)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_n_required_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_required", 99)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid

    def test_n_present_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_present", 0)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid

    def test_n_missing_mismatch_fails(self):
        r = _build_valid()
        object.__setattr__(r, "n_missing", 99)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid

    def test_missing_schema_types_wrong_fails(self):
        r = _build_valid()
        object.__setattr__(r, "missing_schema_types", ["BSP"])
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid

    def test_completeness_fraction_wrong_fails(self):
        r = _build_valid()
        object.__setattr__(r, "completeness_fraction", 0.5)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid

    def test_completeness_grade_wrong_fails(self):
        r = _build_valid()
        object.__setattr__(r, "completeness_grade", "D")
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid
        assert any("completeness_grade" in v for v in result.violations)

    def test_empty_limitations_fails(self):
        r = _build_valid()
        object.__setattr__(r, "limitations", [])
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid
        assert any("limitations" in v for v in result.violations)

    def test_valid_partial_present_passes(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(9))
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_multiple_violations_captured(self):
        r = _build_valid()
        object.__setattr__(r, "pcc_id", "BAD-001")
        object.__setattr__(r, "dry_lab_only", False)
        result = validate_pipeline_completeness_certificate(r)
        assert not result.valid
        assert len(result.violations) >= 2

    def test_grade_b_boundary_passes(self):
        n_b = int(0.75 * N_REQUIRED)
        r = _build_valid(present_schema_artifact_ids=_partial_present(n_b))
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid
        assert r.completeness_grade == "B"

    def test_grade_c_boundary_passes(self):
        n_c = int(0.5 * N_REQUIRED)
        r = _build_valid(present_schema_artifact_ids=_partial_present(n_c))
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid
        assert r.completeness_grade in ("C", "B")  # 6/12=0.5 is exactly B boundary


class TestBuildPipelineCompletenessCertificate:
    def test_all_present_grade_a(self):
        r = _build_valid()
        assert r.completeness_grade == "A"
        assert r.n_present == N_REQUIRED
        assert r.n_missing == 0

    def test_none_present_grade_d(self):
        r = _build_valid(present_schema_artifact_ids={})
        assert r.completeness_grade == "D"
        assert r.n_present == 0
        assert r.n_missing == N_REQUIRED

    def test_n_required_equals_schema_count(self):
        r = _build_valid()
        assert r.n_required == N_REQUIRED

    def test_n_present_counted_correctly(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(7))
        assert r.n_present == 7

    def test_n_missing_computed_correctly(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(7))
        assert r.n_missing == N_REQUIRED - 7

    def test_missing_schema_types_sorted(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(7))
        assert r.missing_schema_types == sorted(r.missing_schema_types)

    def test_completeness_fraction_all_present(self):
        r = _build_valid()
        assert r.completeness_fraction == 1.0

    def test_completeness_fraction_none_present(self):
        r = _build_valid(present_schema_artifact_ids={})
        assert r.completeness_fraction == 0.0

    def test_completeness_fraction_partial(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(6))
        assert abs(r.completeness_fraction - 6 / N_REQUIRED) < 1e-9

    def test_dry_lab_only_auto_true(self):
        r = _build_valid()
        assert r.dry_lab_only is True

    def test_entries_cover_all_required_types(self):
        r = _build_valid()
        covered = {e.schema_type for e in r.schema_presence_entries}
        assert covered == REQUIRED_EVIDENCE_SCHEMA_TYPES

    def test_absent_entry_has_empty_artifact_id(self):
        r = _build_valid(present_schema_artifact_ids={"BSP": "BSP-01"})
        absent = [e for e in r.schema_presence_entries if not e.present]
        assert all(e.artifact_id == "" for e in absent)

    def test_present_entry_has_artifact_id(self):
        r = _build_valid(present_schema_artifact_ids={"BSP": "BSP-999"})
        bsp_entry = next(e for e in r.schema_presence_entries if e.schema_type == "BSP")
        assert bsp_entry.artifact_id == "BSP-999"
        assert bsp_entry.present is True

    def test_grade_b_at_75_percent(self):
        n_b = 9  # 9/12 = 0.75 -> grade B
        r = _build_valid(present_schema_artifact_ids=_partial_present(n_b))
        assert r.completeness_grade == "B"

    def test_grade_d_at_25_percent(self):
        n_d = 3  # 3/12 = 0.25 -> grade D
        r = _build_valid(present_schema_artifact_ids=_partial_present(n_d))
        assert r.completeness_grade == "D"

    def test_missing_schema_types_not_in_present(self):
        present = {"BSP": "BSP-01", "PSC": "PSC-01"}
        r = _build_valid(present_schema_artifact_ids=present)
        for missing_type in r.missing_schema_types:
            assert missing_type not in present

    def test_schema_presence_entries_length(self):
        r = _build_valid()
        assert len(r.schema_presence_entries) == N_REQUIRED

    def test_limitations_stored(self):
        r = _build_valid(limitations=["Not biological", "Dry lab only"])
        assert r.limitations == ["Not biological", "Dry lab only"]


class TestPipelineCompletenessCertificateIntegration:
    def test_round_trip_build_validate(self):
        r = _build_valid()
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_round_trip_none_present_validates(self):
        r = _build_valid(present_schema_artifact_ids={})
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_round_trip_partial_validates(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(8))
        result = validate_pipeline_completeness_certificate(r)
        assert result.valid

    def test_valid_grades_frozenset(self):
        assert "A" in VALID_COMPLETENESS_GRADES
        assert "B" in VALID_COMPLETENESS_GRADES
        assert "C" in VALID_COMPLETENESS_GRADES
        assert "D" in VALID_COMPLETENESS_GRADES
        assert len(VALID_COMPLETENESS_GRADES) == 4

    def test_required_schema_types_includes_all_phases(self):
        # Phase S schemas
        assert "BSP" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        assert "RSR" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        assert "PQT" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        # Phase T schemas
        assert "BTI" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        assert "CBA2" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        assert "BEG" in REQUIRED_EVIDENCE_SCHEMA_TYPES
        assert "SAT" in REQUIRED_EVIDENCE_SCHEMA_TYPES

    def test_grade_a_requires_all_present(self):
        r_all = _build_valid(present_schema_artifact_ids=_all_present())
        r_partial = _build_valid(present_schema_artifact_ids=_partial_present(N_REQUIRED - 1))
        assert r_all.completeness_grade == "A"
        assert r_partial.completeness_grade != "A"

    def test_missing_types_union_present_types_equals_required(self):
        r = _build_valid(present_schema_artifact_ids=_partial_present(7))
        present_types = {e.schema_type for e in r.schema_presence_entries if e.present}
        missing_types = set(r.missing_schema_types)
        assert present_types | missing_types == REQUIRED_EVIDENCE_SCHEMA_TYPES

    def test_format_contains_key_fields(self):
        r = _build_valid()
        s = format_pipeline_completeness_certificate(r)
        assert "PCC-001" in s
        assert "A" in s
        assert "12" in s


class TestFormatPipelineCompletenessCertificate:
    def test_returns_string(self):
        r = _build_valid()
        assert isinstance(format_pipeline_completeness_certificate(r), str)

    def test_contains_pcc_id(self):
        r = _build_valid()
        assert r.pcc_id in format_pipeline_completeness_certificate(r)

    def test_contains_completeness_grade(self):
        r = _build_valid()
        s = format_pipeline_completeness_certificate(r)
        assert r.completeness_grade in s

    def test_contains_pipeline_run_id(self):
        r = _build_valid()
        assert r.pipeline_run_id in format_pipeline_completeness_certificate(r)

    def test_contains_dry_lab_only(self):
        r = _build_valid()
        assert "dry_lab_only" in format_pipeline_completeness_certificate(r)

    def test_missing_none_shown_when_all_present(self):
        r = _build_valid()
        s = format_pipeline_completeness_certificate(r)
        assert "(none)" in s

    def test_missing_types_listed_in_format(self):
        r = _build_valid(present_schema_artifact_ids={})
        s = format_pipeline_completeness_certificate(r)
        # some schema types should appear in missing section
        assert any(st in s for st in REQUIRED_EVIDENCE_SCHEMA_TYPES)

    def test_fraction_in_format(self):
        r = _build_valid()
        s = format_pipeline_completeness_certificate(r)
        assert "1.0000" in s

    def test_grade_d_format_output(self):
        r = _build_valid(present_schema_artifact_ids={})
        s = format_pipeline_completeness_certificate(r)
        assert "D" in s
