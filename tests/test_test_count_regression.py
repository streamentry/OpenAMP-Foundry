"""Regression test: total test count must stay within 5% of BASELINE."""

import subprocess
import sys
import math

BASELINE = 10367


def test_test_count_regression():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        capture_output=True,
        text=True,
    )
    lines = result.stdout.strip().splitlines()
    count_line = next(
        (l for l in reversed(lines) if "test" in l and ("selected" in l or "error" in l)),
        None,
    )
    if count_line is None:
        for l in reversed(lines):
            if l.strip() and l[0].isdigit():
                count_line = l
                break
    assert count_line is not None, f"Could not find test count line. Output:\n{result.stdout}\n"
    import re
    m = re.search(r"(\d+)", count_line)
    assert m is not None, f"No number in count line: {count_line}"
    actual = int(m.group(1))
    tolerance = math.ceil(BASELINE * 0.05)
    assert abs(actual - BASELINE) <= tolerance, (
        f"Test count {actual} deviates from BASELINE {BASELINE} by more than {tolerance}. "
        f"Update BASELINE in this file if tests were intentionally added or removed."
    )
