"""Verify CODEOWNERS file exists and covers safety-sensitive areas."""
from pathlib import Path


def test_codeowners_exists():
    assert Path(".github/CODEOWNERS").exists()


def test_codeowners_covers_safety():
    text = Path(".github/CODEOWNERS").read_text()
    assert "SAFETY.md" in text
    assert "SECURITY.md" in text
    assert "RESPONSIBLE_USE.md" in text
    assert "GOVERNANCE.md" in text


def test_codeowners_covers_agents():
    text = Path(".github/CODEOWNERS").read_text()
    assert "AGENTS.md" in text


def test_codeowners_covers_calibration():
    text = Path(".github/CODEOWNERS").read_text()
    assert "CALIBRATION_POLICY.md" in text
