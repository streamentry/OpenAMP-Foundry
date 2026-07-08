"""Tests for format consistency across generated artifacts."""
from pathlib import Path


def test_jsonl_files_are_valid():
    """Verify JSONL files in outputs/ have one JSON object per line."""
    for f in Path("outputs").glob("*.jsonl"):
        lines = f.read_text().strip().split("\n")
        for i, line in enumerate(lines, 1):
            import json
            try:
                json.loads(line)
            except json.JSONDecodeError:
                assert False, f"Invalid JSON at line {i} in {f}"


def test_markdown_files_have_no_broken_code_blocks():
    """Verify markdown code blocks are properly closed."""
    for md in Path("docs").rglob("*.md"):
        text = md.read_text()
        backtick_count = text.count("```")
        assert backtick_count % 2 == 0, f"Unclosed code block in {md}"
