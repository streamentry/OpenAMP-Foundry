"""Tests for simulation-result provenance chain."""
from __future__ import annotations

import pytest

from openamp_foundry.simulation.provenance import (
    SimulationProvenanceRecord,
    make_provenance_record,
    provenance_summary,
    validate_provenance_record,
)


def _make_valid_record(**overrides) -> SimulationProvenanceRecord:
    record = SimulationProvenanceRecord(
        run_id="test-run-001",
        module_id="membrane_proxy",
        module_version="0.1.0",
        timestamp_utc="2026-07-09T12:00:00Z",
        input_hash="a" * 64,
        result_hash="b" * 64,
    )
    for k, v in overrides.items():
        setattr(record, k, v)
    return record


class TestMakeProvenanceRecord:
    def test_returns_simulation_provenance_record(self):
        record = make_provenance_record(
            run_id="test-run-001",
            module_id="membrane_proxy",
            module_version="0.1.0",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="GIGKFLHSAKKFGKAFVGEIMNS",
            result_scores={"binding_energy": 0.75, "stability": 0.42},
        )
        assert isinstance(record, SimulationProvenanceRecord)
        assert record.run_id == "test-run-001"
        assert record.module_id == "membrane_proxy"

    def test_input_hash_is_64_char_hex(self):
        record = make_provenance_record(
            run_id="r1",
            module_id="m",
            module_version="1",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="AKLWKR",
            result_scores={"x": 0.5},
        )
        assert len(record.input_hash) == 64
        int(record.input_hash, 16)

    def test_result_hash_is_64_char_hex(self):
        record = make_provenance_record(
            run_id="r1",
            module_id="m",
            module_version="1",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="AKLWKR",
            result_scores={"x": 0.5},
        )
        assert len(record.result_hash) == 64
        int(record.result_hash, 16)

    def test_same_input_same_input_hash(self):
        scores = {"binding_energy": 0.75}
        r1 = make_provenance_record("r1", "m", "1", "2026-07-09T12:00:00Z", "AKLWKR", scores)
        r2 = make_provenance_record("r2", "m", "1", "2026-07-09T12:00:00Z", "AKLWKR", scores)
        assert r1.input_hash == r2.input_hash

    def test_different_input_different_input_hash(self):
        scores = {"binding_energy": 0.75}
        r1 = make_provenance_record("r1", "m", "1", "2026-07-09T12:00:00Z", "AKLWKR", scores)
        r2 = make_provenance_record("r2", "m", "1", "2026-07-09T12:00:00Z", "GIGKFL", scores)
        assert r1.input_hash != r2.input_hash

    def test_same_scores_same_result_hash(self):
        r1 = make_provenance_record("r1", "m", "1", "2026-07-09T12:00:00Z", "AKLWKR", {"a": 0.5, "b": 0.3})
        r2 = make_provenance_record("r2", "m", "1", "2026-07-09T12:00:00Z", "AKLWKR", {"b": 0.3, "a": 0.5})
        assert r1.result_hash == r2.result_hash

    def test_dry_lab_only_always_true(self):
        record = make_provenance_record(
            run_id="r1",
            module_id="m",
            module_version="1",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="AKLWKR",
            result_scores={"x": 0.5},
        )
        assert record.dry_lab_only is True

    def test_calibration_set_preserved(self):
        record = make_provenance_record(
            run_id="r1",
            module_id="m",
            module_version="1",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="AKLWKR",
            result_scores={"x": 0.5},
            calibration_set="demo_2026",
        )
        assert record.calibration_set == "demo_2026"

    def test_notes_stored(self):
        record = make_provenance_record(
            run_id="r1",
            module_id="m",
            module_version="1",
            timestamp_utc="2026-07-09T12:00:00Z",
            input_sequence="AKLWKR",
            result_scores={"x": 0.5},
            notes=["Test note."],
        )
        assert record.notes == ["Test note."]


class TestValidateProvenanceRecord:
    def test_valid_record_returns_empty_list(self):
        record = _make_valid_record()
        errors = validate_provenance_record(record)
        assert errors == []

    def test_empty_run_id(self):
        record = _make_valid_record(run_id="")
        errors = validate_provenance_record(record)
        assert "run_id must be non-empty" in errors

    def test_empty_module_id(self):
        record = _make_valid_record(module_id="")
        errors = validate_provenance_record(record)
        assert "module_id must be non-empty" in errors

    def test_empty_module_version(self):
        record = _make_valid_record(module_version="")
        errors = validate_provenance_record(record)
        assert "module_version must be non-empty" in errors

    def test_missing_t_in_timestamp(self):
        record = _make_valid_record(timestamp_utc="2026-07-09 12:00:00")
        errors = validate_provenance_record(record)
        assert any("T" in e for e in errors)

    def test_wrong_length_hash(self):
        record = _make_valid_record(input_hash="abc123")
        errors = validate_provenance_record(record)
        assert "input_hash must be a 64-character hex string" in errors

    def test_dry_lab_only_not_true(self):
        record = _make_valid_record(dry_lab_only=False)
        errors = validate_provenance_record(record)
        assert "dry_lab_only must be True" in errors


class TestProvenanceSummary:
    def test_zero_records(self):
        summary = provenance_summary([])
        assert summary["total"] == 0
        assert summary["modules"] == []
        assert summary["runs"] == []

    def test_n_records_correct_total_and_modules(self):
        r1 = _make_valid_record(run_id="r1", module_id="membrane_proxy")
        r2 = _make_valid_record(run_id="r2", module_id="structure_proxy")
        r3 = _make_valid_record(run_id="r3", module_id="membrane_proxy")
        summary = provenance_summary([r1, r2, r3])
        assert summary["total"] == 3
        assert summary["modules"] == ["membrane_proxy", "structure_proxy"]
        assert summary["runs"] == ["r1", "r2", "r3"]

    def test_dry_lab_only_true(self):
        summary = provenance_summary([])
        assert summary["dry_lab_only"] is True
