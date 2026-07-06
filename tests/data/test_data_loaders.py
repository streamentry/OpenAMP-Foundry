"""Tests for data/loaders.py — sequence normalization, validation, and CSV loading."""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from openamp_foundry.data.loaders import (
    CANONICAL_AA,
    is_valid_sequence,
    load_candidates_csv,
    normalize_sequence,
)


class TestNormalizeSequence:
    def test_uppercase_conversion(self):
        assert normalize_sequence("kwklf") == "KWKLF"

    def test_strips_whitespace(self):
        assert normalize_sequence("  KWKLF  ") == "KWKLF"

    def test_removes_internal_whitespace(self):
        assert normalize_sequence("KWK LF") == "KWKLF"

    def test_empty_string(self):
        assert normalize_sequence("") == ""

    def test_already_normalized(self):
        assert normalize_sequence("KWKLFKKIGAVLKVL") == "KWKLFKKIGAVLKVL"

    def test_mixed_case_and_spaces(self):
        assert normalize_sequence(" kWk Lf ") == "KWKLF"


class TestIsValidSequence:
    def test_canonical_sequence_valid(self):
        assert is_valid_sequence("KWKLFKKIGAVLKVL") is True

    def test_all_canonical_aa_valid(self):
        assert is_valid_sequence("ACDEFGHIKLMNPQRSTVWY") is True

    def test_empty_string_invalid(self):
        assert is_valid_sequence("") is False

    def test_lowercase_normalizes_and_is_valid(self):
        # is_valid_sequence calls normalize_sequence internally, so lowercase is accepted
        assert is_valid_sequence("kwklf") is True

    def test_non_canonical_character_invalid(self):
        assert is_valid_sequence("KWKLFX") is False

    def test_number_in_sequence_invalid(self):
        assert is_valid_sequence("KWKLF1") is False

    def test_dash_in_sequence_invalid(self):
        assert is_valid_sequence("KWKLF-KVLF") is False

    def test_custom_allowed_set(self):
        assert is_valid_sequence("AAA", allowed={"A"}) is True
        assert is_valid_sequence("AAB", allowed={"A"}) is False

    def test_single_residue_valid(self):
        assert is_valid_sequence("K") is True

    def test_all_20_canonical_aa_are_allowed(self):
        for aa in CANONICAL_AA:
            assert is_valid_sequence(aa) is True, f"{aa!r} should be valid"


class TestLoadCandidatesCsv:
    def _write_csv(self, rows: list[dict], path: Path) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def test_loads_correct_count(self):
        rows = [
            {"id": "C1", "sequence": "KWKLFKKIGAVLKVL", "source": "test"},
            {"id": "C2", "sequence": "DEDEDEDE", "source": "test"},
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert len(candidates) == 2

    def test_sequence_normalized_to_upper(self):
        rows = [{"id": "C1", "sequence": "kwklf", "source": "test"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert candidates[0].sequence == "KWKLF"

    def test_id_preserved(self):
        rows = [{"id": "MY-SPECIAL-ID", "sequence": "KWKLF", "source": "test"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert candidates[0].candidate_id == "MY-SPECIAL-ID"

    def test_missing_id_gets_default(self):
        rows = [{"sequence": "KWKLF", "source": "test"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert candidates[0].candidate_id.startswith("candidate-")

    def test_source_preserved(self):
        rows = [{"id": "C1", "sequence": "KWKLF", "source": "my_dataset"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert candidates[0].source == "my_dataset"

    def test_missing_source_defaults_to_csv(self):
        rows = [{"id": "C1", "sequence": "KWKLF"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert candidates[0].source == "csv"

    def test_returns_peptide_candidate_objects(self):
        from openamp_foundry.types import PeptideCandidate
        rows = [{"id": "C1", "sequence": "KWKLF", "source": "test"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "candidates.csv"
            self._write_csv(rows, path)
            candidates = load_candidates_csv(path)
        assert isinstance(candidates[0], PeptideCandidate)

    def test_uses_demo_file_successfully(self):
        demo = Path(__file__).parents[2] / "examples" / "sequences" / "demo_candidates.csv"
        candidates = load_candidates_csv(demo)
        assert len(candidates) > 0
        for c in candidates:
            assert len(c.sequence) > 0

    def test_missing_sequence_column_raises_value_error(self):
        # A CSV with no 'sequence' column should give a helpful error, not a bare KeyError.
        # This guards against users passing in a wrongly-formatted file and getting
        # a cryptic crash deep in the pipeline.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "seq", "source"])
                writer.writeheader()
                writer.writerow({"id": "C1", "seq": "KWKLF", "source": "test"})
            with pytest.raises(ValueError, match="sequence"):
                load_candidates_csv(path)

    def test_missing_sequence_column_fires_on_header_only_csv(self):
        # Header validation happens before iterating rows — zero-row files are caught too.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "header_only.csv"
            path.write_text("id,seq,source\n")  # header only, no data rows
            with pytest.raises(ValueError, match="sequence"):
                load_candidates_csv(path)

    def test_missing_sequence_column_error_names_found_columns(self):
        # The error message should list what columns were found to help the user.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["peptide"])
                writer.writeheader()
                writer.writerow({"peptide": "KWKLF"})
            with pytest.raises(ValueError, match="peptide"):
                load_candidates_csv(path)
