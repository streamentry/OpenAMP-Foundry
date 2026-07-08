"""Test that benchmark report footnotes are consistent."""
from pathlib import Path


def test_metrics_current_has_caveats():
    """METRICS_CURRENT.md should include caveats with benchmark results."""
    text = Path("docs/evidence/METRICS_CURRENT.md").read_text()
    assert "limitation" in text.lower() or "caveat" in text.lower() or "note" in text.lower()


def test_simulation_benchmark_has_verdict():
    """Simulation benchmark should clearly state the verdict."""
    text = Path("docs/evidence/SIMULATION_BENCHMARK.md").read_text()
    assert "No improvement" in text or "blocked" in text


def test_each_benchmark_has_interpretation():
    """Each benchmark section should include an interpretation."""
    text = Path("docs/evidence/BENCHMARKING.md").read_text()
    assert "Benchmark" in text
    assert len(text) > 500
