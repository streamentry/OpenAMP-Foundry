"""Test package import for installed mode."""
import subprocess
import sys


def test_core_import():
    r = subprocess.run([sys.executable, "-c", "import openamp_foundry; print(openamp_foundry.__version__)"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0
    assert len(r.stdout.strip()) > 0


def test_cli_import():
    r = subprocess.run([sys.executable, "-c", "from openamp_foundry.cli import main; print('ok')"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0
    assert r.stdout.strip() == "ok"
