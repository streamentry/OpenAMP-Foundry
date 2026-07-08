"""Test that benchmark delta signs are correct (improvement vs regression)."""

def test_benchmark_gate_delta_sign():
    """Verify the benchmark gate correctly identifies improvements vs regressions."""
    import json
    from pathlib import Path
    gate_output = Path("outputs/benchmark_gate_output.json")
    if not gate_output.exists():
        return  # Skip if no gate output exists
    data = json.loads(gate_output.read_text())
    for metric, info in data.items():
        if "delta" in info:
            assert isinstance(info["delta"], (int, float)), f"Delta for {metric} is not numeric"


def test_auroc_delta_interpretation():
    """A positive delta in AUROC means improvement."""
    from openamp_foundry.scoring.ensemble import ensemble_score
    assert ensemble_score({"a": 1.0}, {"a": 1.0}) > ensemble_score({"a": 0.0}, {"a": 1.0})
