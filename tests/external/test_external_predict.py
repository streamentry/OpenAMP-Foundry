"""Tests for reports/external_predict.py — FASTA generation, checklist, confident panel."""
from __future__ import annotations

import tempfile
from pathlib import Path

from openamp_foundry.reports.external_predict import (
    write_confident_panel,
    write_external_predict_checklist,
    write_pilot_fasta,
)

_PANEL = [
    {"candidate_id": "SEED-001_VAR_001", "sequence": "KWKLFKKIGAVLKVL", "pilot_rank": 1, "seed": "SEED-001"},
    {"candidate_id": "SEED-002_VAR_002", "sequence": "GIGKFLHSAKKFGKA", "pilot_rank": 2, "seed": "SEED-002"},
    {"candidate_id": "SEED-003_VAR_003", "sequence": "FLPAIGRLLNGIL", "pilot_rank": 3, "seed": "SEED-003"},
]


class TestWritePilotFasta:
    def test_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            assert path.exists()

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "dir" / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            assert path.exists()

    def test_one_header_per_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            headers = [ln for ln in path.read_text().splitlines() if ln.startswith(">")]
        assert len(headers) == len(_PANEL)

    def test_header_contains_candidate_id(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            content = path.read_text()
        assert "SEED-001_VAR_001" in content

    def test_header_contains_rank(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            lines = path.read_text().splitlines()
        header_lines = [line for line in lines if line.startswith(">")]
        assert "rank=1" in header_lines[0]

    def test_header_contains_seed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            lines = path.read_text().splitlines()
        assert "seed=SEED-001" in lines[0]

    def test_sequences_present_in_body(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            content = path.read_text()
        for c in _PANEL:
            assert c["sequence"] in content

    def test_file_ends_with_newline(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(_PANEL, path)
            content = path.read_text()
        assert content.endswith("\n")

    def test_empty_panel_produces_empty_like_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta([], path)
            content = path.read_text()
        assert content.strip() == ""

    def test_missing_optional_fields_do_not_crash(self):
        minimal = [{"sequence": "KWKLF"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(minimal, path)
            content = path.read_text()
        assert "KWKLF" in content

    def test_empty_sequence_in_candidate_writes_blank_body_line(self):
        # write_pilot_fasta writes an empty sequence line for candidates with seq="".
        # External predictor tools may reject or misparse this — callers should
        # validate sequences before calling write_pilot_fasta.
        panel_with_empty = [{"candidate_id": "EMPTY", "sequence": "", "pilot_rank": 1}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "pilot.fasta"
            write_pilot_fasta(panel_with_empty, path)
            lines = path.read_text().splitlines()
        assert lines[0].startswith(">EMPTY")
        assert lines[1] == ""  # blank body line — documents the current contract


class TestWriteExternalPredictChecklist:
    def test_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            assert out.exists()

    def test_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "sub" / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            assert out.exists()

    def test_contains_title_header(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "External Predictor Checklist" in content

    def test_contains_all_three_tools(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "CAMPR4" in content
        assert "AMPScanner" in content
        assert "dbAMP" in content

    def test_contains_panel_size(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "3 candidates" in content

    def test_contains_result_table_headers(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "CAMPR4" in content
        assert "Tools Agree" in content

    def test_each_candidate_in_result_table(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        for c in _PANEL:
            assert c["candidate_id"] in content

    def test_contains_synthesis_gate_decision_table(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "STOP" in content or "Proceed" in content

    def test_contains_disclaimer_text(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "wet-lab" in content.lower() or "expert" in content.lower()

    def test_generated_at_included_when_provided(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(
                _PANEL, "pilot.fasta", out, generated_at="2026-01-01T00:00:00+00:00"
            )
            content = out.read_text()
        assert "2026-01-01" in content

    def test_generated_at_omitted_when_empty(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out, generated_at="")
            content = out.read_text()
        assert "Generated:" not in content

    def test_file_ends_with_newline(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert content.endswith("\n")

    def test_fasta_path_referenced_in_checklist(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "my_panel.fasta", out)
            content = out.read_text()
        assert "my_panel.fasta" in content

    def test_two_thirds_agreement_rule_stated(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "checklist.md"
            write_external_predict_checklist(_PANEL, "pilot.fasta", out)
            content = out.read_text()
        assert "≥2" in content or "2/3" in content


class TestWriteConfidentPanel:
    def test_filters_to_kept_ids(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(
                _PANEL,
                ["SEED-001_VAR_001", "SEED-003_VAR_003"],
                out,
            )
        ids = {c["candidate_id"] for c in result}
        assert ids == {"SEED-001_VAR_001", "SEED-003_VAR_003"}

    def test_reranks_confident_panel(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(
                _PANEL,
                ["SEED-002_VAR_002", "SEED-003_VAR_003"],
                out,
            )
        ranks = [c["pilot_rank"] for c in result]
        assert ranks == [1, 2]

    def test_empty_keep_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(_PANEL, [], out)
        assert result == []

    def test_unknown_keep_id_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(_PANEL, ["NONEXISTENT"], out)
        assert result == []

    def test_creates_csv_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            write_confident_panel(_PANEL, ["SEED-001_VAR_001"], out)
            assert (Path(d) / "confident.csv").exists()

    def test_creates_markdown_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            write_confident_panel(_PANEL, ["SEED-001_VAR_001"], out)
            assert (Path(d) / "confident.md").exists()

    def test_returns_list_of_dicts(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(_PANEL, ["SEED-001_VAR_001"], out)
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_output_order_follows_panel_not_keep_ids(self):
        # keep_ids is converted to a set internally; output order is determined
        # by the original panel order, NOT the order of keep_ids.
        # This documents the current contract so any future reordering is explicit.
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "confident"
            result = write_confident_panel(
                _PANEL,
                ["SEED-003_VAR_003", "SEED-001_VAR_001"],  # reversed from panel order
                out,
            )
        assert result[0]["candidate_id"] == "SEED-001_VAR_001"  # panel order wins
        assert result[1]["candidate_id"] == "SEED-003_VAR_003"
