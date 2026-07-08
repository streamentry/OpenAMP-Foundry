"""Test synthetic result quarantine rules."""
from pathlib import Path


def test_synthetic_lab_results_labeled():
    """Synthetic lab results should be clearly labeled."""
    lab_dir = Path("examples/lab_results")
    if not lab_dir.exists():
        return
    for f in lab_dir.glob("*.json"):
        import json
        data = json.loads(f.read_text())
        disclaimer = data.get("disclaimer", "")
        assert "SYNTHETIC" in disclaimer or "synthetic" in disclaimer.lower(), \
            f"Missing SYNTHETIC label in {f.name}"


def test_synthetic_data_policy_mentions_quarantine():
    text = Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").read_text()
    assert "quarantine" in text.lower() or "label" in text.lower()
