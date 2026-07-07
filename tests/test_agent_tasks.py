"""Tests for AGENT_TASKS.json."""
import json
from pathlib import Path


def test_file_exists():
    assert Path("AGENT_TASKS.json").exists()


def test_is_valid_json():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    assert "task_categories" in data
    assert "stop_conditions" in data
    assert "non_negotiable" in data


def test_has_8_categories():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    assert len(data["task_categories"]) >= 8


def test_each_category_has_required_fields():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    for cat in data["task_categories"]:
        for field in ["category", "safe_paths", "review_class", "required_checks"]:
            assert field in cat, f"{cat['category']} missing {field}"


def test_review_classes():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    valid = {"light", "normal", "requires_human_review", "blocked"}
    for cat in data["task_categories"]:
        assert cat["review_class"] in valid, f"{cat['category']} has invalid review_class"


def test_stop_conditions():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    assert len(data["stop_conditions"]) >= 5


def test_non_negotiable():
    data = json.loads(Path("AGENT_TASKS.json").read_text())
    assert len(data["non_negotiable"]) >= 3
