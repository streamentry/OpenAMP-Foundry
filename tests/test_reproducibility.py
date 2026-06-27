"""Reproducibility tests — Phase 2 requirement.

AGENTS.md: "Reproducibility — Another machine can reproduce rankings from the same inputs."

These tests verify that:
1. Rankings are deterministic: same inputs always produce the same output order.
2. A run manifest is generated alongside every ranked output.
3. The run manifest validates against its JSON Schema.
4. The manifest contains all required reproducibility fields.
5. Input file SHA-256 hashes in the manifest match the actual files.
6. The config hash changes when the config changes.
7. Pipeline version is recorded in the manifest.

All scores are computational proxies. No biological activity is implied.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openamp_foundry import __version__
from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.pipeline import build_run_manifest, run_ranking_pipeline
from openamp_foundry.utils.hashing import file_sha256, stable_json_hash


CANDIDATE_CSV = "examples/sequences/demo_candidates.csv"
REFERENCE_CSV = "examples/known_reference/demo_known_amps.csv"
MANIFEST_SCHEMA = "schemas/run_manifest.schema.json"


class TestDeterministicRanking:
    def test_two_runs_produce_identical_jsonl_order(self, tmp_path):
        """Rankings must be identical across two independent pipeline runs."""
        out1 = tmp_path / "run1.jsonl"
        out2 = tmp_path / "run2.jsonl"

        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out1,
        )
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out2,
        )

        rows1 = [json.loads(line) for line in out1.read_text().splitlines() if line.strip()]
        rows2 = [json.loads(line) for line in out2.read_text().splitlines() if line.strip()]

        ids1 = [r["candidate_id"] for r in rows1]
        ids2 = [r["candidate_id"] for r in rows2]
        assert ids1 == ids2, (
            f"Ranking order differs between runs:\nRun 1: {ids1}\nRun 2: {ids2}"
        )

    def test_two_runs_produce_identical_scores(self, tmp_path):
        """Scores must be identical across two independent pipeline runs."""
        out1 = tmp_path / "run1.jsonl"
        out2 = tmp_path / "run2.jsonl"

        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out1,
        )
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out2,
        )

        rows1 = [json.loads(line) for line in out1.read_text().splitlines() if line.strip()]
        rows2 = [json.loads(line) for line in out2.read_text().splitlines() if line.strip()]

        for r1, r2 in zip(rows1, rows2):
            assert r1["scores"] == r2["scores"], (
                f"{r1['candidate_id']}: scores differ between runs: "
                f"{r1['scores']} vs {r2['scores']}"
            )

    def test_selected_candidates_identical_across_runs(self, tmp_path):
        """Selection (which candidates pass all filters) must be deterministic."""
        out1 = tmp_path / "run1.jsonl"
        out2 = tmp_path / "run2.jsonl"

        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out1,
        )
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out2,
        )

        sel1 = {
            r["candidate_id"]
            for r in [json.loads(line) for line in out1.read_text().splitlines() if line.strip()]
            if r["selected"]
        }
        sel2 = {
            r["candidate_id"]
            for r in [json.loads(line) for line in out2.read_text().splitlines() if line.strip()]
            if r["selected"]
        }
        assert sel1 == sel2, (
            f"Selected candidates differ between runs: "
            f"only_in_run1={sel1 - sel2}, only_in_run2={sel2 - sel1}"
        )


class TestRunManifestGeneration:
    def test_manifest_generated_alongside_output(self, tmp_path):
        """run_manifest.json should be generated in the same directory as the output."""
        out = tmp_path / "ranked.jsonl"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
        )
        manifest_path = tmp_path / "run_manifest.json"
        assert manifest_path.exists(), (
            "run_manifest.json should be generated alongside ranked.jsonl"
        )

    def test_manifest_at_explicit_path(self, tmp_path):
        """Explicit --manifest path should be respected."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "my_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        assert manifest_out.exists(), "Manifest should be written to the explicit path"

    def test_manifest_validates_against_schema(self, tmp_path):
        """run_manifest.json must validate against schemas/run_manifest.schema.json."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        validate_json_schema(data, MANIFEST_SCHEMA)

    def test_manifest_contains_required_fields(self, tmp_path):
        """Manifest must include all fields required for external reproducibility."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        required = ["run_id", "pipeline_version", "config_hash", "generated_at",
                    "inputs", "input_hashes", "outputs"]
        for field in required:
            assert field in data, f"Manifest missing required field: {field!r}"

    def test_manifest_pipeline_version_matches_package(self, tmp_path):
        """Pipeline version in manifest must match the installed package version."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        assert data["pipeline_version"] == __version__, (
            f"Manifest pipeline_version={data['pipeline_version']!r} "
            f"should match __version__={__version__!r}"
        )

    def test_manifest_run_id_is_non_empty_string(self, tmp_path):
        """run_id must be a non-empty string (UUID format)."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        assert isinstance(data["run_id"], str) and len(data["run_id"]) > 0
        # Basic UUID format check (8-4-4-4-12 hyphenated)
        parts = data["run_id"].split("-")
        assert len(parts) == 5, f"run_id should be UUID format: {data['run_id']!r}"

    def test_manifest_two_runs_have_different_run_ids(self, tmp_path):
        """Each run should produce a unique run_id."""
        out1, out2 = tmp_path / "r1.jsonl", tmp_path / "r2.jsonl"
        m1, m2 = tmp_path / "m1.json", tmp_path / "m2.json"
        run_ranking_pipeline(CANDIDATE_CSV, REFERENCE_CSV, out1, manifest_path=m1)
        run_ranking_pipeline(CANDIDATE_CSV, REFERENCE_CSV, out2, manifest_path=m2)
        d1 = json.loads(m1.read_text())
        d2 = json.loads(m2.read_text())
        assert d1["run_id"] != d2["run_id"], "Different runs should have different run_ids"


class TestInputHashIntegrity:
    def test_input_hash_matches_actual_file(self, tmp_path):
        """SHA-256 in manifest for candidate CSV must match the actual file hash."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        for path_str, recorded_hash in data["input_hashes"].items():
            if recorded_hash == "N/A":
                continue  # path not found at run time (optional inputs)
            actual_hash = file_sha256(path_str)
            assert recorded_hash == actual_hash, (
                f"Input hash mismatch for {path_str}: "
                f"recorded={recorded_hash[:16]}... actual={actual_hash[:16]}..."
            )

    def test_manifest_lists_candidate_and_reference_inputs(self, tmp_path):
        """Manifest inputs should include both candidate and reference file paths."""
        out = tmp_path / "ranked.jsonl"
        manifest_out = tmp_path / "run_manifest.json"
        run_ranking_pipeline(
            candidate_path=CANDIDATE_CSV,
            reference_path=REFERENCE_CSV,
            out_path=out,
            manifest_path=manifest_out,
        )
        data = json.loads(manifest_out.read_text())
        inputs = data["inputs"]
        assert any(CANDIDATE_CSV in p for p in inputs), (
            f"Candidate CSV not found in manifest inputs: {inputs}"
        )
        assert any(REFERENCE_CSV in p for p in inputs), (
            f"Reference CSV not found in manifest inputs: {inputs}"
        )

    def test_config_hash_is_deterministic(self):
        """Same config → same config_hash across calls."""
        config = {"weights": {"activity": 0.40, "safety": 0.25}, "filters": {}}
        h1 = stable_json_hash(config)
        h2 = stable_json_hash(config)
        assert h1 == h2, "Config hash should be deterministic for the same config"

    def test_config_hash_changes_with_config(self):
        """Different config → different config_hash."""
        config_a = {"weights": {"activity": 0.40}}
        config_b = {"weights": {"activity": 0.50}}
        ha = stable_json_hash(config_a)
        hb = stable_json_hash(config_b)
        assert ha != hb, "Config hash should differ when config changes"

    def test_build_run_manifest_structure(self, tmp_path):
        """build_run_manifest() returns correct structure without running full pipeline."""
        config = {"weights": {"activity": 0.40}}
        manifest = build_run_manifest(
            run_id="test-run-id",
            config=config,
            input_paths=[Path(CANDIDATE_CSV), Path(REFERENCE_CSV)],
            output_paths=["outputs/test.jsonl"],
            generated_at="2026-01-01T00:00:00+00:00",
        )
        assert manifest["run_id"] == "test-run-id"
        assert manifest["pipeline_version"] == __version__
        assert manifest["config_hash"] == stable_json_hash(config)
        assert CANDIDATE_CSV in " ".join(manifest["inputs"])
        assert len(manifest["input_hashes"]) == 2

    def test_manifest_sha256_is_64_char_hex(self, tmp_path):
        """SHA-256 hashes should be 64-character lowercase hexadecimal strings."""
        actual_hash = file_sha256(CANDIDATE_CSV)
        assert len(actual_hash) == 64, f"SHA-256 should be 64 chars, got {len(actual_hash)}"
        assert actual_hash == actual_hash.lower(), "SHA-256 should be lowercase"
        assert all(c in "0123456789abcdef" for c in actual_hash), "SHA-256 should be hex"

    def test_sha256_changes_with_content(self, tmp_path):
        """Different file contents → different SHA-256 hash."""
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        f1.write_text("id,sequence,source\nA-001,KWKLFK,test\n")
        f2.write_text("id,sequence,source\nA-001,KWKLFR,test\n")
        h1 = file_sha256(f1)
        h2 = file_sha256(f2)
        assert h1 != h2, "Different file content should produce different SHA-256 hashes"

    def test_file_hash_equals_stdlib_sha256(self):
        """Verify file_sha256() matches direct stdlib computation."""
        h = hashlib.sha256()
        with open(CANDIDATE_CSV, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        expected = h.hexdigest()
        actual = file_sha256(CANDIDATE_CSV)
        assert actual == expected, "file_sha256() should match stdlib sha256"
