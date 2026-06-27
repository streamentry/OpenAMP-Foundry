"""Tests for utils/hashing.py and utils/io.py."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from openamp_foundry.utils.hashing import file_sha256, stable_json_hash
from openamp_foundry.utils.io import read_json, write_json, write_jsonl


class TestStableJsonHash:
    def test_same_object_produces_same_hash(self):
        obj = {"a": 1, "b": [2, 3]}
        assert stable_json_hash(obj) == stable_json_hash(obj)

    def test_key_order_does_not_matter(self):
        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        assert stable_json_hash(a) == stable_json_hash(b)

    def test_different_values_differ(self):
        assert stable_json_hash({"v": 1}) != stable_json_hash({"v": 2})

    def test_returns_64_char_hex(self):
        h = stable_json_hash({"k": "v"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_empty_dict(self):
        h = stable_json_hash({})
        assert len(h) == 64

    def test_nested_structure(self):
        h1 = stable_json_hash({"nested": {"a": [1, 2]}})
        h2 = stable_json_hash({"nested": {"a": [1, 3]}})
        assert h1 != h2

    def test_list_input(self):
        h = stable_json_hash([1, 2, 3])
        assert len(h) == 64

    def test_string_input(self):
        h = stable_json_hash("hello")
        assert len(h) == 64


class TestFileSha256:
    def test_matches_content_hash(self):
        content = b"hello world"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.bin"
            path.write_bytes(content)
            expected = hashlib.sha256(content).hexdigest()
            assert file_sha256(path) == expected

    def test_different_files_differ(self):
        with tempfile.TemporaryDirectory() as d:
            p1 = Path(d) / "a.bin"
            p2 = Path(d) / "b.bin"
            p1.write_bytes(b"abc")
            p2.write_bytes(b"xyz")
            assert file_sha256(p1) != file_sha256(p2)

    def test_returns_64_char_hex(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.bin"
            path.write_bytes(b"data")
            assert len(file_sha256(path)) == 64

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "empty.bin"
            path.write_bytes(b"")
            expected = hashlib.sha256(b"").hexdigest()
            assert file_sha256(path) == expected


class TestWriteJsonl:
    def test_writes_one_line_per_row(self):
        rows = [{"a": 1}, {"b": 2}, {"c": 3}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.jsonl"
            write_jsonl(path, rows)
            lines = path.read_text().strip().splitlines()
        assert len(lines) == 3

    def test_each_line_is_valid_json(self):
        rows = [{"x": i} for i in range(5)]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.jsonl"
            write_jsonl(path, rows)
            lines = path.read_text().strip().splitlines()
        parsed = [json.loads(ln) for ln in lines]
        assert [p["x"] for p in parsed] == list(range(5))

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sub" / "dir" / "out.jsonl"
            write_jsonl(path, [{"k": "v"}])
            assert path.exists()

    def test_empty_iterable_creates_empty_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.jsonl"
            write_jsonl(path, [])
            assert path.read_text() == ""

    def test_unicode_values_preserved(self):
        rows = [{"name": "café"}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.jsonl"
            write_jsonl(path, rows)
            lines = path.read_text().strip().splitlines()
        assert json.loads(lines[0])["name"] == "café"


class TestReadWriteJson:
    def test_round_trip(self):
        payload = {"key": "value", "num": 42, "list": [1, 2, 3]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            write_json(path, payload)
            loaded = read_json(path)
        assert loaded == payload

    def test_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nested" / "data.json"
            write_json(path, {"x": 1})
            assert path.exists()

    def test_file_ends_with_newline(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            write_json(path, {"a": 1})
            content = path.read_text()
        assert content.endswith("\n")

    def test_keys_sorted_in_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            write_json(path, {"z": 3, "a": 1, "m": 2})
            content = path.read_text()
        first_key_pos = content.index('"a"')
        m_pos = content.index('"m"')
        z_pos = content.index('"z"')
        assert first_key_pos < m_pos < z_pos

    def test_unicode_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            write_json(path, {"name": "pré-synthèse"})
            loaded = read_json(path)
        assert loaded["name"] == "pré-synthèse"
