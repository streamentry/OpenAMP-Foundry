"""Keep the live roadmap, index, metrics note, and bounded backlog aligned."""

import re
from pathlib import Path


ROOT = Path(__file__).parents[1]

RECENT_SHIPPED_ITEMS = (
    "AA1",
    "AA2",
    "AA3",
    "AA4",
    "AA5",
    "AA6",
    "AB1",
    "AB2",
    "AB3",
    "AB4",
    "AB5",
    "AC1",
    "AC2",
    "AC3",
)


def _current_state_date(text: str) -> str:
    match = re.search(r"Current state — (\d{4}-\d{2}-\d{2})", text)
    assert match, "ROADMAP.md must expose a dated current-state line"
    return match.group(1)


def test_recent_shipped_frontier_is_marked_complete_in_bounded_backlog():
    backlog = (ROOT / "docs/research/NEXT_100_PR_MAP.md").read_text()

    for item in RECENT_SHIPPED_ITEMS:
        rows = [line for line in backlog.splitlines() if line.startswith(f"| {item} |")]
        assert len(rows) == 1, item
        assert "(complete)" in rows[0], item


def test_current_authorities_expose_the_same_aa_ac_frontier():
    roadmap = (ROOT / "docs/research/ROADMAP.md").read_text()
    metrics = (ROOT / "docs/evidence/METRICS_CURRENT.md").read_text()
    project_index = (ROOT / "docs/PROJECT_INDEX.md").read_text()
    metrics_date = re.search(
        r"Current verification note \((\d{4}-\d{2}-\d{2})\)", metrics
    )

    assert metrics_date, "METRICS_CURRENT.md must expose a dated verification note"
    assert _current_state_date(roadmap) == metrics_date.group(1)
    assert "Phase AC is complete" in roadmap
    assert "Phase AA" in roadmap and "AA6" in roadmap
    assert "AA6" in metrics and "AC3" in metrics
    assert "Phase AA" in project_index and "AA6" in project_index


def test_phase_gate_make_targets_use_the_repository_python_fallback():
    makefile = (ROOT / "Makefile").read_text()

    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "phase-aa-reproducibility-gate-check"
    ) in makefile
    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "phase-ac-disconfirming-gate-check"
    ) in makefile
