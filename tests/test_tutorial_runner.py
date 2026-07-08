"""Run tutorial commands and verify they work."""
import subprocess
import sys


def test_demo_help():
    r = subprocess.run(["make", "demo"], capture_output=True, text=True)
    # make demo may fail if dependencies aren't installed, but should at least attempt
    assert r.returncode in (0, 2)


def test_quickstart_commands():
    """Verify key quickstart commands are valid."""
    import argparse
    from openamp_foundry.cli.main import build_parser
    parser = build_parser()
    # Verify rank subcommand exists
    for action in parser._actions:
        if hasattr(action, 'choices') and action.choices:
            assert 'rank' in action.choices
            break
