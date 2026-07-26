"""Keep the live roadmap, index, metrics note, and bounded backlog aligned."""

import re
import subprocess
import sys
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
    "Y5",
    "Z5",
)


def _current_state_date(text: str) -> str:
    match = re.search(r"Current state — (\d{4}-\d{2}-\d{2})", text)
    assert match, "ROADMAP.md must expose a dated current-state line"
    return match.group(1)


def _collected_test_count() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"([\d,]+) tests? collected", result.stdout)
    assert match, f"Could not find collection count in pytest output:\n{result.stdout}"
    return int(match.group(1).replace(",", ""))


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
    assert "Phase AB" in roadmap and "AB5" in roadmap
    assert "Phase Y" in roadmap and "Y5" in roadmap
    assert "Phase Z is complete" in roadmap
    assert "Phase AA" in roadmap and "AA6" in roadmap
    assert "AA6" in metrics and "AB5" in metrics and "AC3" in metrics and "Z5" in metrics
    assert "Phase AA" in project_index and "AA6" in project_index
    assert "Phase Z5" in project_index


def test_metrics_current_records_the_live_test_collection_count():
    metrics = (ROOT / "docs/evidence/METRICS_CURRENT.md").read_text()
    match = re.search(r"collection\s+succeeds at ([\d,]+) tests;", metrics)
    assert match, "METRICS_CURRENT.md must record the live pytest collection count"
    assert int(match.group(1).replace(",", "")) == _collected_test_count()


def test_external_review_package_identity_boundary_is_documented():
    roadmap = (ROOT / "docs/research/ROADMAP.md").read_text()
    metrics = (ROOT / "docs/evidence/METRICS_CURRENT.md").read_text()
    skill = (ROOT / "SKILL.md").read_text()

    for text in (roadmap, metrics, skill):
        assert "pep_sha256" in text
        assert (
            "does not authenticate" in text
            or "not reviewer authentication" in text
        )


def test_synthetic_result_recalibration_boundary_is_documented():
    roadmap = (ROOT / "docs/research/ROADMAP.md").read_text()
    metrics = (ROOT / "docs/evidence/METRICS_CURRENT.md").read_text()
    policy = (ROOT / "docs/evidence/CALIBRATION_POLICY.md").read_text()
    skill = (ROOT / "SKILL.md").read_text()

    for text in (roadmap, metrics, policy, skill):
        assert "SYNTHETIC" in text
        assert "recalibration gate" in text
        assert any(
            phrase in text
            for phrase in (
                "not asserted to be real",
                "not inferred to be real",
                "does not infer that they are real",
            )
        )


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
    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "phase-ab-claim-integrity-gate-check"
    ) in makefile
    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "scientific-review-readiness-check"
    ) in makefile
    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "phase-z-accountability-gate-check"
    ) in makefile
    assert (
        "PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli "
        "phase-y-accountability-gate-check"
    ) in makefile
