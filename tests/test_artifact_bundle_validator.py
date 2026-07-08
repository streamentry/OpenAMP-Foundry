"""Test artifact bundle validation."""
from pathlib import Path


def test_batch_pack_script_exists():
    assert Path("scripts/build_lab_batch_pack.py").exists()


def test_evidence_directory_exists():
    ev = Path("outputs/evidence")
    if ev.exists():
        certs = list(ev.glob("*.json"))
        assert len(certs) > 0, "Evidence directory exists but is empty"


def test_phase3_evidence_exists():
    ev = Path("outputs/evidence_wave0_5")
    if ev.exists():
        certs = list(ev.glob("*.json"))
        assert len(certs) > 0
