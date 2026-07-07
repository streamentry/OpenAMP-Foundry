"""Tests for unused script detector."""
from scripts.detect_unused_scripts import detect_unused


def test_detector_runs():
    r = detect_unused()
    assert "total_scripts" in r
    assert r["total_scripts"] > 0


def test_referenced_count_is_int():
    r = detect_unused()
    assert isinstance(r["referenced"], int)


def test_unreferenced_count_is_int():
    r = detect_unused()
    assert isinstance(r["unreferenced"], int)


def test_no_negative_counts():
    r = detect_unused()
    assert r["referenced"] >= 0
    assert r["unreferenced"] >= 0
    assert r["exempt"] >= 0
