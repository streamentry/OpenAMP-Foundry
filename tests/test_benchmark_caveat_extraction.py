"""Test benchmark caveat extraction."""
from pathlib import Path


def test_metrics_current_has_caveats():
    text = Path("docs/evidence/METRICS_CURRENT.md").read_text()
    assert "limitation" in text.lower() or "caveat" in text.lower() or "note" in text.lower()


def test_benchmarking_plan_has_caveats():
    text = Path("docs/evidence/BENCHMARKING.md").read_text()
    assert "caveat" in text.lower() or "limitation" in text.lower() or "Note" in text


def test_simulation_benchmark_has_verdict():
    text = Path("docs/evidence/SIMULATION_BENCHMARK.md").read_text()
    assert "No improvement" in text
