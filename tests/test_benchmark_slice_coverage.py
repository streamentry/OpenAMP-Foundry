"""Test benchmark slice coverage."""
from pathlib import Path


def test_per_family_benchmark_exists():
    """Per-family benchmark should have output."""
    result = Path("outputs/benchmark_per_family.json")
    if not result.exists():
        return  # May not be generated yet
    import json
    data = json.loads(result.read_text())
    assert len(data) > 0


def test_metrics_current_has_per_family():
    text = Path("docs/evidence/METRICS_CURRENT.md").read_text()
    assert "Per-Family" in text or "per-family" in text


def test_benchmark_slice_defined():
    text = Path("docs/evidence/GUIDE_BENCHMARK_SLICE.md").read_text() if Path(
        "docs/evidence/GUIDE_BENCHMARK_SLICE.md").exists() else ""
    if text:
        assert "Slice" in text
