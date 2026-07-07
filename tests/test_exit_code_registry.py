"""Tests for CLI exit code registry."""
import json
from pathlib import Path


def _registry():
    return json.loads(Path("configs/exit_code_registry.json").read_text())


def test_file_exists():
    assert Path("configs/exit_code_registry.json").exists()


def test_is_valid_json():
    r = _registry()
    assert "codes" in r
    assert "command_patterns" in r


def test_exit_codes_defined():
    r = _registry()
    for code_str, info in r["codes"].items():
        assert "meaning" in info
        assert "description" in info
        assert isinstance(int(code_str), int)


def test_rank_has_expected_codes():
    r = _registry()
    assert "rank" in r["command_patterns"]
    assert 0 in r["command_patterns"]["rank"]["expected"]


def test_check_scripts_have_exit_3():
    r = _registry()
    for name, info in r["command_patterns"].items():
        if name.endswith(".py"):
            assert 3 in info["expected"], f"{name} should have exit code 3"


def test_all_expected_codes_are_defined():
    r = _registry()
    defined = set(int(k) for k in r["codes"])
    for name, info in r["command_patterns"].items():
        for code in info["expected"]:
            assert code in defined, f"{name} expects code {code} which is not defined"
