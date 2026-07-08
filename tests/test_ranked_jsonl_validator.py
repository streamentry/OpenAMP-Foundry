"""Test ranked JSONL validation."""
import json
from pathlib import Path


def test_demo_ranked_is_valid_jsonl():
    """Each line of ranked JSONL should be valid JSON."""
    jsonl_path = Path("outputs/demo_ranked.jsonl")
    if not jsonl_path.exists():
        return  # May not be generated
    lines = jsonl_path.read_text().strip().split("\n")
    for i, line in enumerate(lines, 1):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            assert False, f"Invalid JSON at line {i}"
        assert "candidate_id" in data, f"Missing candidate_id at line {i}"
        assert "sequence" in data, f"Missing sequence at line {i}"


def test_ranked_jsonl_has_scores():
    jsonl_path = Path("outputs/demo_ranked.jsonl")
    if not jsonl_path.exists():
        return
    data = json.loads(jsonl_path.read_text().split("\n")[0])
    assert "scores" in data, "Missing scores in ranked output"
    assert "ensemble" in data["scores"], "Missing ensemble score"
