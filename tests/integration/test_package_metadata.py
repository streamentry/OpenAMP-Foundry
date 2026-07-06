from __future__ import annotations

from openamp_foundry import __version__


def test_package_version_is_semver_like():
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
