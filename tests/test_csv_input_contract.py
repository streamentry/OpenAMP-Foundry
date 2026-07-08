"""Test CSV input contract validation."""
from pathlib import Path
import csv


def test_required_columns_present():
    """CSV files should have required columns."""
    with open("examples/sequences/demo_candidates.csv", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
    required = {"id", "sequence"}
    assert required.issubset(set(headers)), f"Missing columns: {required - set(headers)}"


def test_sequences_are_strings():
    with open("examples/sequences/demo_candidates.csv", newline="") as f:
        for row in csv.DictReader(f):
            assert isinstance(row["sequence"], str)
            assert len(row["sequence"]) > 0


def test_ids_are_unique():
    ids = []
    with open("examples/sequences/demo_candidates.csv", newline="") as f:
        for row in csv.DictReader(f):
            ids.append(row["id"])
    assert len(ids) == len(set(ids))
