"""Test that limitations are documented for key areas."""
from pathlib import Path


def test_limitations_overview_exists():
    assert Path("docs/evidence/LIMITATIONS_OVERVIEW.md").exists()


def test_limitations_covers_key_areas():
    text = Path("docs/evidence/LIMITATIONS_OVERVIEW.md").read_text()
    for area in ["Model", "Data", "Benchmark", "Calibration", "Safety"]:
        assert area in text, f"Missing limitations section: {area}"


def test_simulation_benchmark_has_limitations():
    text = Path("docs/evidence/SIMULATION_BENCHMARK.md").read_text()
    assert "No improvement" in text or "blocked" in text or "experimental" in text


def test_metrics_current_has_caveats():
    text = Path("docs/evidence/METRICS_CURRENT.md").read_text()
    assert "limitation" in text.lower() or "caveat" in text.lower()
