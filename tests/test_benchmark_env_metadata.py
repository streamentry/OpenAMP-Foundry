"""Capture benchmark environment metadata for reproducibility."""
import sys
import platform


def test_python_version():
    assert sys.version_info >= (3, 11), f"Python {sys.version} is too old"


def test_platform_info():
    info = {
        "python": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
    }
    assert len(info["python"]) > 0
    assert len(info["platform"]) > 0


def test_main_package_importable():
    import openamp_foundry  # noqa: F401
    assert hasattr(openamp_foundry, "__version__")
