"""Tests for path traversal in archive builders."""
import zipfile
import tempfile
from pathlib import Path


def test_zip_path_traversal_detected():
    """Verify that path traversal via ../ in zip entries can be detected."""
    with tempfile.TemporaryDirectory() as tmp:
        malicious_zip = Path(tmp) / "malicious.zip"
        with zipfile.ZipFile(malicious_zip, "w") as zf:
            zf.writestr("../../etc/passwd", "malicious")
        detected = False
        with zipfile.ZipFile(malicious_zip, "r") as zf:
            for name in zf.namelist():
                resolved = (Path(tmp) / name).resolve()
                if not str(resolved).startswith(str(Path(tmp).resolve())):
                    detected = True
        assert detected, "Path traversal was not detected"
        assert "../../" in name, "Path traversal pattern should contain ../"
