"""Regression guard: total collected test count must not drop below BASELINE."""
import subprocess
import sys


BASELINE = 7906
TOLERANCE = 0.05


def test_test_count_regression():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    output = result.stdout + result.stderr
    count = 0
    for line in output.splitlines():
        if "test session starts" in line or "selected" in line or "no tests ran" in line:
            continue
        if line.strip().endswith(("PASSED", "FAILED", "ERROR", "SKIPPED")):
            count += 1
    for line in output.splitlines():
        if "selected" in line and "test" in line:
            import re
            m = re.search(r"(\d+) test", line)
            if m:
                count = int(m.group(1))
                break
    min_allowed = int(BASELINE * (1 - TOLERANCE))
    assert count >= min_allowed, (
        f"Test count dropped from {BASELINE} to {count} "
        f"(threshold: {min_allowed}). Update BASELINE if intentional."
    )
