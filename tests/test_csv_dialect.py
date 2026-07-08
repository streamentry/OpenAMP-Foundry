"""Test CSV dialect and encoding."""
from pathlib import Path
import csv


def test_demo_csv_is_readable():
    with open("examples/sequences/demo_candidates.csv", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) >= 2, "Should have at least 2 demo candidates"
    assert "id" in reader.fieldnames or "candidate_id" in reader.fieldnames


def test_demo_csv_utf8():
    text = Path("examples/sequences/demo_candidates.csv").read_bytes()
    text.decode("utf-8")  # Should not raise


def test_reference_csv_is_readable():
    with open("examples/known_reference/demo_known_amps.csv", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) >= 2
    assert "id" in reader.fieldnames or "candidate_id" in reader.fieldnames
