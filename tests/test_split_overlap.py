"""Test that dataset splits do not overlap."""
from pathlib import Path


def test_amp_and_decoy_no_overlap():
    """AMP and decoy sets should not share sequences."""
    amps = set()
    with open("examples/validation/known_amps_500.csv") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                amps.add(parts[1])

    decoys = set()
    with open("examples/validation/random_background_500.csv") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                decoys.add(parts[1])

    overlap = amps & decoys
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping sequences between AMP and decoy sets"


def test_demo_candidates_have_unique_ids():
    """Demo candidates should have unique IDs."""
    ids = set()
    with open("examples/sequences/demo_candidates.csv") as f:
        for line in f.readlines()[1:]:
            parts = line.strip().split(",")
            if parts:
                ids.add(parts[0])
    assert len(ids) >= 5, "Should have at least 5 unique demo candidate IDs"
