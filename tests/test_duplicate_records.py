"""Test duplicate record handling."""
from pathlib import Path


def test_demo_candidates_no_duplicates():
    """Demo candidates should not have duplicate IDs."""
    ids = []
    with open("examples/sequences/demo_candidates.csv") as f:
        for line in f.readlines()[1:]:
            cid = line.strip().split(",")[0]
            ids.append(cid)
    assert len(ids) == len(set(ids)), "Duplicate candidate IDs found"


def test_demo_references_no_duplicates():
    ids = []
    with open("examples/known_reference/demo_known_amps.csv") as f:
        for line in f.readlines()[1:]:
            cid = line.strip().split(",")[0]
            ids.append(cid)
    assert len(ids) == len(set(ids))


def test_evidence_certificates_unique():
    ev_dir = Path("outputs/evidence")
    if ev_dir.exists():
        files = list(ev_dir.glob("*.json"))
        ids = [f.stem for f in files]
        assert len(ids) == len(set(ids))
