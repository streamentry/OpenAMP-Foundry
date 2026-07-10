"""Tests for E7 validate-packet CLI command (tests/cli/test_validate_packet.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openamp_foundry.cli.commands.validate_packet import (
    _parse_candidate_entries,
    _parse_benchmark_summaries,
    _parse_calibration_summary,
    _parse_safety_attestations,
    load_packet_from_json,
    validate_packet_file,
    _run_validate_packet,
)


def _make_valid_packet_dict():
    return {
        "packet_id": "ERP-TEST-0001",
        "candidate_entries": [
            {
                "candidate_id": "TOY-0001",
                "sequence": "KWKLFKKIEK",
                "ensemble_score": 0.85,
                "proof_ladder_level": 1,
                "family": "cationic",
                "selection_rationale": "high score",
                "safety_notes": "screened",
            }
        ],
        "benchmark_summaries": [
            {
                "auroc": 0.82,
                "benchmark_name": "charge_matched",
                "n_positives": 50,
                "n_negatives": 50,
            }
        ],
        "calibration_summary": {
            "calibration_error": 0.08,
            "n_bins": 10,
            "assessment": "well_calibrated",
        },
        "safety_attestations": {
            "no_known_toxicity_claim": True,
            "dual_use_screened": True,
            "hemolysis_risk_flagged": True,
        },
        "limitations": ["Dry-lab only. No wet-lab validation performed."],
        "pipeline_version": "1.0.0",
        "git_sha": "abc1234",
        "dry_lab_only_attestation": True,
        "calibration_assessment": "well_calibrated",
    }


class TestParseCandidateEntries:
    def test_empty_list_returns_empty(self):
        result = _parse_candidate_entries([])
        assert result == []

    def test_single_entry_parsed(self):
        raw = [{"candidate_id": "TOY-0001", "sequence": "KWKL",
                "ensemble_score": 0.8, "proof_ladder_level": 1}]
        result = _parse_candidate_entries(raw)
        assert len(result) == 1
        assert result[0].candidate_id == "TOY-0001"

    def test_sequence_field_set(self):
        raw = [{"candidate_id": "T", "sequence": "ACDE",
                "ensemble_score": 0.5, "proof_ladder_level": 0}]
        result = _parse_candidate_entries(raw)
        assert result[0].sequence == "ACDE"

    def test_ensemble_score_is_float(self):
        raw = [{"candidate_id": "T", "sequence": "A",
                "ensemble_score": "0.7", "proof_ladder_level": 1}]
        result = _parse_candidate_entries(raw)
        assert isinstance(result[0].ensemble_score, float)

    def test_proof_ladder_level_is_int(self):
        raw = [{"candidate_id": "T", "sequence": "A",
                "ensemble_score": 0.5, "proof_ladder_level": "2"}]
        result = _parse_candidate_entries(raw)
        assert isinstance(result[0].proof_ladder_level, int)

    def test_multiple_entries(self):
        raw = [
            {"candidate_id": f"T{i}", "sequence": "A",
             "ensemble_score": 0.5, "proof_ladder_level": 1}
            for i in range(3)
        ]
        result = _parse_candidate_entries(raw)
        assert len(result) == 3


class TestParseBenchmarkSummaries:
    def test_empty_returns_empty(self):
        assert _parse_benchmark_summaries([]) == []

    def test_auroc_is_float(self):
        raw = [{"auroc": "0.82", "benchmark_name": "test",
                "n_positives": 10, "n_negatives": 10}]
        result = _parse_benchmark_summaries(raw)
        assert isinstance(result[0].auroc, float)

    def test_benchmark_name_set(self):
        raw = [{"auroc": 0.8, "benchmark_name": "charge_matched",
                "n_positives": 10, "n_negatives": 10}]
        result = _parse_benchmark_summaries(raw)
        assert result[0].benchmark_name == "charge_matched"

    def test_counts_are_int(self):
        raw = [{"auroc": 0.8, "benchmark_name": "t",
                "n_positives": "5", "n_negatives": "5"}]
        result = _parse_benchmark_summaries(raw)
        assert isinstance(result[0].n_positives, int)
        assert isinstance(result[0].n_negatives, int)


class TestParseCalibrationSummary:
    def test_calibration_error_float(self):
        raw = {"calibration_error": "0.08", "n_bins": 10, "assessment": "well_calibrated"}
        result = _parse_calibration_summary(raw)
        assert isinstance(result.calibration_error, float)

    def test_n_bins_int(self):
        raw = {"calibration_error": 0.08, "n_bins": "10", "assessment": "uninformative"}
        result = _parse_calibration_summary(raw)
        assert isinstance(result.n_bins, int)

    def test_assessment_set(self):
        raw = {"calibration_error": 0.08, "n_bins": 10, "assessment": "moderately_calibrated"}
        result = _parse_calibration_summary(raw)
        assert result.assessment == "moderately_calibrated"


class TestParseSafetyAttestations:
    def test_no_toxicity_claim_bool(self):
        raw = {"no_known_toxicity_claim": True, "dual_use_screened": True,
               "hemolysis_risk_flagged": True}
        result = _parse_safety_attestations(raw)
        assert result.no_known_toxicity_claim is True

    def test_dual_use_screened_bool(self):
        raw = {"no_known_toxicity_claim": True, "dual_use_screened": False,
               "hemolysis_risk_flagged": True}
        result = _parse_safety_attestations(raw)
        assert result.dual_use_screened is False

    def test_hemolysis_flagged_bool(self):
        raw = {"no_known_toxicity_claim": True, "dual_use_screened": True,
               "hemolysis_risk_flagged": False}
        result = _parse_safety_attestations(raw)
        assert result.hemolysis_risk_flagged is False

    def test_defaults_false_when_missing(self):
        result = _parse_safety_attestations({})
        assert result.no_known_toxicity_claim is False


class TestLoadPacketFromJson:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_packet_from_json(tmp_path / "missing.json")

    def test_invalid_json_raises_value_error(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json {{")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_packet_from_json(p)

    def test_non_dict_raises_value_error(self, tmp_path):
        p = tmp_path / "arr.json"
        p.write_text("[1, 2, 3]")
        with pytest.raises(ValueError, match="must be an object"):
            load_packet_from_json(p)

    def test_valid_packet_loads(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert packet.packet_id == "ERP-TEST-0001"

    def test_candidate_entries_loaded(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert len(packet.candidate_entries) == 1

    def test_dry_lab_only_preserved(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert packet.dry_lab_only_attestation is True

    def test_limitations_loaded(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert len(packet.limitations) >= 1

    def test_pipeline_version_loaded(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert packet.pipeline_version == "1.0.0"

    def test_benchmark_summaries_loaded(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        packet = load_packet_from_json(p)
        assert len(packet.benchmark_summaries) == 1


class TestValidatePacketFile:
    def test_missing_file_returns_invalid(self, tmp_path):
        result = validate_packet_file(tmp_path / "missing.json")
        assert result["valid"] is False
        assert len(result["violations"]) > 0

    def test_invalid_json_returns_invalid(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("bad json {{{")
        result = validate_packet_file(p)
        assert result["valid"] is False

    def test_valid_packet_returns_valid(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert result["valid"] is True

    def test_result_has_required_keys(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        for key in ["path", "valid", "violations", "packet_id", "error"]:
            assert key in result

    def test_path_in_result(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert str(p) in result["path"] or result["path"] == str(p)

    def test_violations_is_list(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert isinstance(result["violations"], list)

    def test_valid_packet_no_violations(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert result["violations"] == []

    def test_packet_id_in_result(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert result["packet_id"] == "ERP-TEST-0001"

    def test_dry_lab_false_fails(self, tmp_path):
        d = _make_valid_packet_dict()
        d["dry_lab_only_attestation"] = False
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(d))
        result = validate_packet_file(p)
        assert result["valid"] is False

    def test_empty_limitations_fails(self, tmp_path):
        d = _make_valid_packet_dict()
        d["limitations"] = []
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(d))
        result = validate_packet_file(p)
        assert result["valid"] is False

    def test_missing_file_error_not_none(self, tmp_path):
        result = validate_packet_file(tmp_path / "missing.json")
        assert result["error"] is not None

    def test_valid_packet_error_is_none(self, tmp_path):
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        result = validate_packet_file(p)
        assert result["error"] is None


class TestRunValidatePacketCLI:
    def test_valid_packet_returns_zero(self, tmp_path):
        import types
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        args = types.SimpleNamespace(packet_path=str(p))
        result = _run_validate_packet(args)
        assert result == 0

    def test_missing_file_returns_one(self, tmp_path):
        import types
        args = types.SimpleNamespace(packet_path=str(tmp_path / "missing.json"))
        result = _run_validate_packet(args)
        assert result == 1

    def test_invalid_packet_returns_one(self, tmp_path):
        import types
        d = _make_valid_packet_dict()
        d["dry_lab_only_attestation"] = False
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(d))
        args = types.SimpleNamespace(packet_path=str(p))
        result = _run_validate_packet(args)
        assert result == 1

    def test_output_contains_pass_on_valid(self, tmp_path, capsys):
        import types
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        args = types.SimpleNamespace(packet_path=str(p))
        _run_validate_packet(args)
        captured = capsys.readouterr()
        assert "PASS" in captured.out

    def test_output_contains_fail_on_invalid(self, tmp_path, capsys):
        import types
        d = _make_valid_packet_dict()
        d["dry_lab_only_attestation"] = False
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(d))
        args = types.SimpleNamespace(packet_path=str(p))
        _run_validate_packet(args)
        captured = capsys.readouterr()
        assert "FAIL" in captured.out

    def test_output_contains_packet_path(self, tmp_path, capsys):
        import types
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(_make_valid_packet_dict()))
        args = types.SimpleNamespace(packet_path=str(p))
        _run_validate_packet(args)
        captured = capsys.readouterr()
        assert "packet" in captured.out.lower() or str(p) in captured.out

    def test_output_contains_violation_on_invalid(self, tmp_path, capsys):
        import types
        d = _make_valid_packet_dict()
        d["limitations"] = []
        p = tmp_path / "packet.json"
        p.write_text(json.dumps(d))
        args = types.SimpleNamespace(packet_path=str(p))
        _run_validate_packet(args)
        captured = capsys.readouterr()
        assert "VIOLATION" in captured.out
