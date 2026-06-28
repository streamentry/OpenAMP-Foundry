"""Validation tests for the curated AMP reference set.

These tests guard against accidental introduction of malformed sequences,
duplicate IDs, or entries that would break the novelty scoring pipeline.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

REF_CSV = Path("examples/known_reference/amp_curated_references.csv")
CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")
MIN_LEN = 6
MAX_LEN = 50  # permissive — reference entries need not match the pipeline filter


def _load_references() -> list[dict]:
    with open(REF_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestReferenceSetStructure:
    def test_file_exists(self):
        assert REF_CSV.exists(), f"Reference CSV not found: {REF_CSV}"

    def test_has_required_columns(self):
        rows = _load_references()
        assert rows, "Reference CSV is empty"
        required = {"id", "sequence", "source", "family", "reference", "hemolytic_risk_note"}
        assert required.issubset(rows[0].keys()), f"Missing columns: {required - rows[0].keys()}"

    def test_minimum_sequence_count(self):
        rows = _load_references()
        assert len(rows) >= 70, f"Expected ≥70 reference sequences, got {len(rows)}"

    def test_no_duplicate_ids(self):
        rows = _load_references()
        ids = [r["id"] for r in rows]
        duplicates = [i for i in set(ids) if ids.count(i) > 1]
        assert not duplicates, f"Duplicate IDs: {duplicates}"

    def test_no_duplicate_sequences(self):
        rows = _load_references()
        seqs = [r["sequence"] for r in rows]
        duplicates = [s for s in set(seqs) if seqs.count(s) > 1]
        assert not duplicates, f"Duplicate sequences: {duplicates}"

    def test_all_sequences_canonical_amino_acids(self):
        rows = _load_references()
        violations = []
        for r in rows:
            seq = r["sequence"]
            non_can = set(seq) - CANONICAL_AA
            if non_can:
                violations.append((r["id"], non_can))
        assert not violations, f"Non-canonical amino acids in: {violations}"

    def test_all_sequences_nonempty(self):
        rows = _load_references()
        empty = [r["id"] for r in rows if not r["sequence"].strip()]
        assert not empty, f"Empty sequences: {empty}"

    def test_sequence_length_range(self):
        rows = _load_references()
        out_of_range = [
            (r["id"], len(r["sequence"]))
            for r in rows
            if not (MIN_LEN <= len(r["sequence"]) <= MAX_LEN)
        ]
        assert not out_of_range, f"Sequences outside [{MIN_LEN},{MAX_LEN}]: {out_of_range}"

    def test_all_ids_nonempty(self):
        rows = _load_references()
        empty = [i for i, r in enumerate(rows) if not r["id"].strip()]
        assert not empty, f"Empty IDs at rows: {empty}"


class TestReferenceSetCoverage:
    def test_multiple_families_represented(self):
        rows = _load_references()
        families = {r["family"] for r in rows if r["family"].strip()}
        assert len(families) >= 20, f"Expected ≥20 distinct families, got {len(families)}: {families}"

    def test_cathelicidin_family_present(self):
        rows = _load_references()
        families = {r["family"] for r in rows}
        cathelicidin = any("ll37" in f or "cathelicidin" in f for f in families)
        assert cathelicidin, "No cathelicidin/LL-37 family found in reference set"

    def test_proline_rich_family_present(self):
        rows = _load_references()
        families = {r["family"] for r in rows}
        pr_rich = any("proline" in f or "apidaecin" in f or "oncocin" in f for f in families)
        assert pr_rich, "No proline-rich AMP family found in reference set"

    def test_magainin_family_present(self):
        rows = _load_references()
        families = {r["family"] for r in rows}
        assert any("magainin" in f for f in families), "No magainin family in reference set"

    def test_temporin_family_present(self):
        rows = _load_references()
        families = {r["family"] for r in rows}
        assert any("temporin" in f for f in families), "No temporin family in reference set"
