"""Test that artifact sizes are within budget."""
import os
from pathlib import Path


def test_schema_files_under_budget():
    """Schema files should be under 50 KB each."""
    for f in Path("schemas").rglob("*.json"):
        size = os.path.getsize(f)
        assert size < 50000, f"{f} is {size} bytes (limit 50000)"


def test_docs_files_under_budget():
    """Documentation files should be under 200 KB each."""
    for f in Path("docs").rglob("*.md"):
        size = os.path.getsize(f)
        assert size < 200000, f"{f} is {size} bytes (limit 200000)"


def test_example_files_under_budget():
    """Example data files should be under 5 MB each."""
    for f in Path("examples").rglob("*.csv"):
        size = os.path.getsize(f)
        assert size < 5000000, f"{f} is {size} bytes (limit 5MB)"
