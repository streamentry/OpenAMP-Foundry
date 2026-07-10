"""Test count regression gate: alert if the test suite shrinks significantly."""
import subprocess
import sys

# Baseline: 3681 tests as of Loop 118 (2026-07-09) -- Phase J J10 (annual safety and benchmark review checklist)
# Note: 3 pre-existing collection errors in test_benchmark_calibration.py,
# test_benchmark_charge_distribution.py, test_benchmark_cheap_enemies.py.
# Raise threshold if legitimate tests are removed; lower threshold is okay.
BASELINE = 5225
TOLERANCE = 0.05  # allow 5% fluctuation


def test_test_count_not_below_threshold():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode in (0, 5), f"pytest collect failed: {r.stderr[:200]}"
    # Parse count from output like "2427 tests collected"
    for line in r.stdout.split("\n"):
        if "tests collected" in line:
            count = int(line.split()[0])
            min_allowed = int(BASELINE * (1 - TOLERANCE))
            assert count >= min_allowed, (
                f"Test count dropped from {BASELINE} to {count} "
                f"(threshold: {min_allowed}). Update BASELINE if intentional."
            )
            return
    raise AssertionError("Could not parse test count from pytest output")
