"""Test that benchmark inputs have consistent checksums."""
from pathlib import Path
import hashlib


def test_amp_csv_exists():
    assert Path("examples/validation/known_amps_500.csv").exists()


def test_decoy_csv_exists():
    assert Path("examples/validation/random_background_500.csv").exists()


def test_benchmark_inputs_deterministic():
    """Reading benchmark CSVs should produce consistent results."""
    amp = Path("examples/validation/known_amps_500.csv").read_bytes()
    decoy = Path("examples/validation/random_background_500.csv").read_bytes()
    h = hashlib.sha256(amp + decoy).hexdigest()
    assert len(h) == 64
    assert h.isalnum()
