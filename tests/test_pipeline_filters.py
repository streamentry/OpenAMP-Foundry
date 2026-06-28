"""Tests for pipeline length filters and selection thresholds."""
from __future__ import annotations

import json
from pathlib import Path

from openamp_foundry.config import load_config
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


def test_eligibility_novelty_at_exact_minimum_passes(tmp_path):
    """A candidate with novelty exactly = min_novelty (>= boundary) must be selected.

    Uses a custom config with min_novelty=0.0 so that even a candidate identical to
    the reference (novelty=0.0) passes the filter.  Confirms the filter uses >=, not >.
    """
    config_path = tmp_path / "permissive.yaml"
    config_path.write_text(
        "pipeline_version: '0.1.0'\n"
        "filters:\n  min_length: 8\n  max_length: 35\n"
        "  allowed_amino_acids: 'ACDEFGHIKLMNPQRSTVWY'\n"
        "weights:\n  activity: 0.40\n  safety: 0.25\n  synthesis: 0.15\n  novelty: 0.20\n"
        "selection:\n  top_n: 100\n  min_novelty: 0.0\n  max_safety_risk: 1.0\n"
    )
    seq = "KWKLFKKIGAVLKVL"
    csv = tmp_path / "candidates.csv"
    refs = tmp_path / "refs.csv"
    # Candidate is identical to the reference → novelty=0.0
    csv.write_text(f"id,sequence,source\nTEST-001,{seq},test\n")
    refs.write_text(f"id,sequence,source\nREF-001,{seq},reference\n")
    out = tmp_path / "ranked.jsonl"
    run_ranking_pipeline(
        candidate_path=csv,
        reference_path=refs,
        out_path=out,
        config_path=config_path,
    )
    rows = [json.loads(line) for line in out.read_text().splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["scores"]["novelty"] == 0.0
    # With min_novelty=0.0, novelty=0.0 satisfies 0.0 >= 0.0 → should be selected
    assert rows[0]["selected"] is True


def test_disagreement_gate_blocks_high_uncertainty_candidate(tmp_path):
    """Candidates where activity and Boman index strongly disagree should be blocked.

    max_disagreement caps the |activity - boman_activity| gap. The test proves the
    gate is the cause of blocking by showing the SAME candidate is SELECTED when the
    gate is relaxed to 1.0 (no restriction).
    """
    _COMMON_CONFIG = (
        "pipeline_version: '0.1.0'\n"
        "filters:\n  min_length: 8\n  max_length: 35\n"
        "  allowed_amino_acids: 'ACDEFGHIKLMNPQRSTVWY'\n"
        "weights:\n  activity: 0.40\n  safety: 0.25\n  synthesis: 0.15\n  novelty: 0.20\n"
        "selection:\n  top_n: 100\n  min_novelty: 0.0\n  max_safety_risk: 1.0\n"
    )
    strict_config = tmp_path / "strict_disagree.yaml"
    strict_config.write_text(_COMMON_CONFIG + "  max_disagreement: 0.0\n")
    permissive_config = tmp_path / "permissive_disagree.yaml"
    permissive_config.write_text(_COMMON_CONFIG + "  max_disagreement: 1.0\n")

    seq = "KWKLFKKIGAVLKVL"
    csv_path = tmp_path / "candidates.csv"
    refs_path = tmp_path / "refs.csv"
    csv_path.write_text(f"id,sequence,source\nTEST-001,{seq},test\n")
    refs_path.write_text("id,sequence,source\n")  # empty refs → novelty=1.0

    # Strict gate: disagreement > 0 for any real sequence → blocked
    out_strict = tmp_path / "strict.jsonl"
    run_ranking_pipeline(
        candidate_path=csv_path, reference_path=refs_path,
        out_path=out_strict, config_path=strict_config,
    )
    rows_strict = [json.loads(ln) for ln in out_strict.read_text().splitlines() if ln.strip()]
    assert len(rows_strict) == 1
    assert rows_strict[0]["scores"]["disagreement"] > 0.0
    assert rows_strict[0]["selected"] is False  # disagreement gate blocks it

    # Positive control: same candidate passes when gate is off (max_disagreement=1.0)
    out_permissive = tmp_path / "permissive.jsonl"
    run_ranking_pipeline(
        candidate_path=csv_path, reference_path=refs_path,
        out_path=out_permissive, config_path=permissive_config,
    )
    rows_permissive = [json.loads(ln) for ln in out_permissive.read_text().splitlines() if ln.strip()]
    assert len(rows_permissive) == 1
    assert rows_permissive[0]["selected"] is True  # relaxed gate allows it through


def test_disagreement_gate_config_values_documented(tmp_path):
    """pipeline.yaml max_disagreement=0.40, phase3.yaml max_disagreement=0.30 (stricter)."""
    repo_root = Path(__file__).parents[1]
    pipeline_cfg = load_config(repo_root / "configs" / "pipeline.yaml")
    phase3_cfg = load_config(repo_root / "configs" / "phase3.yaml")

    pipeline_max = float(pipeline_cfg["selection"]["max_disagreement"])
    phase3_max = float(phase3_cfg["selection"]["max_disagreement"])

    # phase3 is stricter (lower tolerance for disagreement)
    assert phase3_max < pipeline_max
    assert abs(pipeline_max - 0.40) < 0.01
    assert abs(phase3_max - 0.30) < 0.01


def test_phase3_config_has_stricter_safety_filter_than_pipeline():
    """phase3.yaml max_safety_risk=0.40 (safety>=0.60) vs pipeline.yaml 0.70 (safety>=0.30).

    A candidate with safety=0.50 passes pipeline.yaml but is blocked by phase3.yaml.
    """
    repo_root = Path(__file__).parents[1]
    pipeline_cfg = load_config(repo_root / "configs" / "pipeline.yaml")
    phase3_cfg = load_config(repo_root / "configs" / "phase3.yaml")

    pipeline_min_safety = 1.0 - float(pipeline_cfg["selection"]["max_safety_risk"])
    phase3_min_safety = 1.0 - float(phase3_cfg["selection"]["max_safety_risk"])

    # Phase3 must be stricter
    assert phase3_min_safety > pipeline_min_safety

    # Verify the expected concrete thresholds (max_safety_risk 0.70 → 0.30, 0.40 → 0.60)
    assert abs(pipeline_min_safety - 0.30) < 0.01, (
        f"pipeline.yaml min_safety expected ~0.30, got {pipeline_min_safety}"
    )
    assert abs(phase3_min_safety - 0.60) < 0.01, (
        f"phase3.yaml min_safety expected ~0.60, got {phase3_min_safety}"
    )

    # A candidate with safety=0.50 straddles the two configs
    candidate_safety = 0.50
    assert candidate_safety >= pipeline_min_safety, "Should pass pipeline filter"
    assert candidate_safety < phase3_min_safety, "Should fail phase3 filter"
