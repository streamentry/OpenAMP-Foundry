"""Test CLI entrypoint."""


def test_main_help():
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "openamp_foundry.cli", "--help"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0
    assert "usage" in r.stdout.lower() or "usage" in r.stderr.lower()


def test_main_version():
    from openamp_foundry import __version__
    assert len(__version__) > 0
