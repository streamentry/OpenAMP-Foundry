from pathlib import Path

from openamp_foundry.pipeline import build_run_manifest, run_ranking_pipeline


def test_pipeline_demo(tmp_path):
    out = tmp_path / "ranked.jsonl"
    report = tmp_path / "report.md"
    certs = tmp_path / "certs"
    ranked = run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path=out,
        report_path=report,
        cert_dir=certs,
    )
    assert ranked
    assert out.exists()
    assert report.exists()
    assert any(Path(certs).glob("*.json"))


def test_manifest_missing_input_gets_na_hash(tmp_path):
    # pipeline.py:105 — non-existent path → "N/A" in input_hashes (no sha256 key)
    real = tmp_path / "a.csv"
    real.write_text("id,sequence\nC1,KWKLFK\n")
    missing = tmp_path / "missing.csv"
    m = build_run_manifest("r1", {}, [real, missing], ["out.csv"], "2026-01-01T00:00:00Z")
    hashes = m["input_hashes"]
    assert hashes[str(real)] != "N/A", "Existing file must have a real sha256"
    assert hashes[str(missing)] == "N/A", "Missing file must have N/A hash (line 105)"
