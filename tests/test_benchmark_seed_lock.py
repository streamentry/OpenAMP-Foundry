"""Test benchmark seed locking."""
from pathlib import Path
import random


def test_benchmark_seed_is_deterministic():
    rng = random.Random(20260705)
    a = rng.random()
    rng = random.Random(20260705)
    b = rng.random()
    assert a == b, "Same seed should produce same random value"


def test_different_seeds_different():
    rng1 = random.Random(20260705)
    rng2 = random.Random(20260706)
    assert rng1.random() != rng2.random(), "Different seeds should produce different values"


def test_seed_used_in_benchmark_scripts():
    """Check that benchmark scripts use fixed seeds."""
    import glob
    for script in glob.glob("scripts/benchmark_*.py"):
        text = open(script).read()
        if "random" in text or "Random" in text or "seed" in text:
            # Script uses randomness; should have a fixed seed
            assert "seed" in text.lower() or "Random(" in text or "rng" in text, \
                f"{script} uses randomness but may lack fixed seed"
