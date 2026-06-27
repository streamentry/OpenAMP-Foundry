from pathlib import Path

from openamp_foundry.pipeline import run_ranking_pipeline


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
