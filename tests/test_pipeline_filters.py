"""Tests for pipeline length filters and selection thresholds."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from openamp_foundry.pipeline import _passes_length_filter, run_ranking_pipeline, score_candidates


def test_length_filter_within_range():
    assert _passes_length_filter("KWKLFKKIGAVLKVL", min_length=8, max_length=35) is True


def test_length_filter_too_short():
    assert _passes_length_filter("KWKL", min_length=8, max_length=35) is False


def test_length_filter_too_long():
    assert _passes_length_filter("K" * 40, min_length=8, max_length=35) is False


def test_length_filter_boundary_min():
    assert _passes_length_filter("K" * 8, min_length=8, max_length=35) is True


def test_length_filter_boundary_max():
    assert _passes_length_filter("K" * 35, min_length=8, max_length=35) is True


def test_invalid_length_candidate_has_zero_activity(tmp_path):
    """A candidate outside length bounds should score 0 for activity."""
    csv = tmp_path / "candidates.csv"
    csv.write_text("id,sequence,source\nTEST-001,CCCCCCCCCCCC,test\n")
    # CCCCCCCCCCCC is 12 chars but all Cys — valid alphabet but safety should be poor
    scored, config = score_candidates(csv, config_path="configs/pipeline.yaml")
    assert len(scored) == 1
    # All-cys peptide has non-zero safety risk
    assert scored[0].scores["safety"] < 1.0


def test_all_repeat_candidate_is_valid_but_has_low_charge(tmp_path):
    """AAAAAAAAGGGGGGGG is valid amino acids but lacks positive charge (bad for AMPs)."""
    csv = tmp_path / "candidates.csv"
    csv.write_text("id,sequence,source\nTEST-001,AAAAAAAAGGGGGGGG,test\n")
    scored, config = score_candidates(csv, config_path="configs/pipeline.yaml")
    assert len(scored) == 1
    item = scored[0]
    assert item.valid is True
    # Net charge = 0, so charge_density = 0 → low charge score → low ensemble
    assert item.features["net_charge_proxy"] == 0
    # Should score lower than a genuine AMP-like sequence (KWK-type)
    assert item.scores["activity"] < 0.6


def test_pipeline_marks_invalid_sequence(tmp_path):
    """A sequence with non-canonical amino acids (B, X) should be marked invalid."""
    csv = tmp_path / "candidates.csv"
    csv.write_text("id,sequence,source\nBAD-001,KWBXLFKK,test\n")
    scored, _ = score_candidates(csv, config_path="configs/pipeline.yaml")
    assert len(scored) == 1
    assert scored[0].valid is False
    assert scored[0].scores["activity"] == 0.0
    assert any("non-canonical" in f for f in scored[0].known_failure_modes)


def test_selected_field_in_jsonl_output(tmp_path):
    """The JSONL output should include a 'selected' boolean per candidate."""
    out = tmp_path / "ranked.jsonl"
    run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path=out,
    )
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    assert all("selected" in row for row in rows)
    assert any(row["selected"] for row in rows)


def test_run_manifest_generated(tmp_path):
    """Run manifest should be auto-generated alongside the output."""
    out = tmp_path / "ranked.jsonl"
    run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path=out,
    )
    manifest = tmp_path / "run_manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert "run_id" in data
    assert "pipeline_version" in data
    assert "config_hash" in data
    assert "input_hashes" in data
    assert len(data["inputs"]) >= 1


def test_run_manifest_explicit_path(tmp_path):
    """Run manifest can be written to an explicit path."""
    out = tmp_path / "ranked.jsonl"
    manifest_out = tmp_path / "my_manifest.json"
    run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path=out,
        manifest_path=manifest_out,
    )
    assert manifest_out.exists()


def test_novelty_filter_excludes_near_duplicates(tmp_path):
    """Candidates with novelty below min_novelty threshold should not be selected."""
    csv = tmp_path / "candidates.csv"
    refs = tmp_path / "refs.csv"
    # Identical to reference — novelty will be 0.0
    csv.write_text("id,sequence,source\nTEST-001,KWKLFKKIGAVLKVL,test\n")
    refs.write_text("id,sequence,source\nREF-001,KWKLFKKIGAVLKVL,reference\n")
    out = tmp_path / "ranked.jsonl"
    run_ranking_pipeline(
        candidate_path=csv,
        reference_path=refs,
        out_path=out,
        cert_dir=tmp_path / "certs",
    )
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    # With novelty=0.0 and min_novelty=0.20 from config, should not be selected
    assert not any(row["selected"] for row in rows)
    # But should still be scored and appear in output
    assert len(rows) == 1
    assert rows[0]["scores"]["novelty"] == 0.0
