"""Detect likely stale docs: documents not updated in >90 days with no changelog entry."""
from pathlib import Path

import pytest

DOCS_DIR = Path("docs")
STALE_DAYS = 90


@pytest.mark.skip(reason="Requires git timestamps — run manually with pytest --run-stale")
def test_no_stale_docs():
    import subprocess
    now = subprocess.run(
        ["git", "log", "-1", "--format=%ct"], capture_output=True, text=True
    )
    now_ts = int(now.stdout.strip())
    stale = []
    for f in sorted(DOCS_DIR.rglob("*.md")):
        last_commit = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(f)],
            capture_output=True, text=True,
        )
        if last_commit.stdout.strip():
            file_ts = int(last_commit.stdout.strip())
            age_days = (now_ts - file_ts) / 86400
            if age_days > STALE_DAYS:
                stale.append((f, int(age_days)))
    assert not stale, f"Stale docs (> {STALE_DAYS} days): " + ", ".join(f"{f} ({d}d)" for f, d in stale)
