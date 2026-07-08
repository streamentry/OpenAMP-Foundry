"""Verify the synthetic-data policy is documented in required locations."""
from pathlib import Path


def test_virtual_assay_scope_mentions_synthetic_policy():
    text = Path("docs/evidence/VIRTUAL_ASSAY_SCOPE.md").read_text()
    assert "Synthetic" in text
    assert "proof_ladder_level" in text


def test_calibration_policy_mentions_synthetic_restriction():
    text = Path("docs/evidence/CALIBRATION_POLICY.md").read_text()
    assert "Synthetic" in text
    assert "proof_ladder_level" in text
