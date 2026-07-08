"""Test leakage sentinel fixtures."""
from pathlib import Path


def test_sentinel_amps_detected_in_references():
    """Known AMPs like magainin-2 should be detectable in reference sets.
    This is expected — they are known sequences used as benchmarks."""
    known = "GIGKFLHSAKKFGKAFVGEIMNS"  # magainin-2
    found = False
    for csv_file in Path("examples").rglob("*.csv"):
        text = csv_file.read_text()
        if known in text:
            found = True
            break
    assert found, "Magainin-2 should be findable in example data"


def test_sentinel_amps_are_valid():
    """Sentinel AMPs should be valid sequences."""
    for seq in ["GIGKFLHSAKKFGKAFVGEIMNS", "GIGAVLKVLTTGLPALISWIKRKRQQ"]:
        for aa in seq:
            assert aa in "ACDEFGHIKLMNPQRSTVWY", f"Invalid amino acid {aa} in {seq[:10]}..."
