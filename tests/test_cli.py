"""CLI integration tests."""
from __future__ import annotations

import json

import pytest

from openamp_foundry.cli import main


PANEL_CSV_HEADER = (
    "pilot_rank,candidate_id,sequence,length,seed,ensemble,activity,boman_activity,"
    "disagreement,safety,synthesis,novelty,serum_stability,selectivity_proxy,pilot_priority\n"
)
PANEL_CSV_ROW1 = "1,SEED-009_VAR_033,RRLPRPGYMPRP,12,SEED-009,0.8073,0.6385,0.5915,0.047,1.0,0.9,0.6923,0.5715,1.0,0.9064\n"
PANEL_CSV_ROW2 = "2,SEED-007_VAR_009,IKFTTMLRKLG,11,SEED-007,0.8493,0.6968,0.4751,0.2217,1.0,0.9818,0.7273,0.6364,1.0,0.901\n"


def _write_panel(tmp_path, two_rows: bool = True):
    panel = tmp_path / "panel.csv"
    rows_content = (PANEL_CSV_ROW1 + PANEL_CSV_ROW2) if two_rows else PANEL_CSV_ROW1
    panel.write_text(PANEL_CSV_HEADER + rows_content, encoding="utf-8")
    return str(panel)


def test_rank_command_success(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    ret = main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
    ])
    assert ret == 0


def test_rank_command_with_report_and_certs(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    report = str(tmp_path / "report.md")
    certs = str(tmp_path / "certs")
    ret = main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--report", report,
        "--cert-dir", certs,
    ])
    assert ret == 0


def test_validate_command_success(tmp_path):
    # First generate a certificate
    out = str(tmp_path / "ranked.jsonl")
    certs = str(tmp_path / "certs")
    main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--cert-dir", certs,
    ])
    cert_files = list((tmp_path / "certs").glob("*.json"))
    assert cert_files, "No certificates were generated"
    ret = main([
        "validate",
        "--certificate", str(cert_files[0]),
        "--schema", "schemas/candidate.schema.json",
    ])
    assert ret == 0


def test_bench_leakage_detects_duplicates(tmp_path, capsys):
    # Demo candidates 1, 2, 5 are exact copies of references
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["near_duplicate_count"] == 3
    assert result["warning"] is not None


def test_bench_leakage_no_duplicates(tmp_path, capsys):
    # Use negative examples as candidates — they won't match the reference AMPs
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/negative/demo_negative_peptides.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--threshold", "0.90",
    ])
    assert ret == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["near_duplicate_count"] == 0
    assert result["warning"] is None


def test_bench_leakage_output_file(tmp_path, capsys):
    out = str(tmp_path / "leakage_report.json")
    ret = main([
        "bench", "leakage",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
    ])
    assert ret == 0
    data = json.loads((tmp_path / "leakage_report.json").read_text())
    assert "near_duplicates" in data


def test_report_contains_disclaimer(tmp_path):
    out = str(tmp_path / "ranked.jsonl")
    report = str(tmp_path / "report.md")
    main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", out,
        "--report", report,
    ])
    text = (tmp_path / "report.md").read_text()
    assert "NOT validated biological predictors" in text
    assert "no antimicrobial activity has been demonstrated" in text.lower() or "No antimicrobial activity" in text


def test_presynth_qc_command_returns_zero(tmp_path):
    panel = tmp_path / "panel.csv"
    panel.write_text(
        "candidate_id,sequence,source\n"
        "SEED-001,KWKLFKKIGAVLKVL,test\n"
        "SEED-002,RRWQWRMKKLG,test\n"
    )
    out = str(tmp_path / "report.md")
    ret = main(["presynth-qc", "--panel-csv", str(panel), "--out", out])
    assert ret == 0


def test_presynth_qc_command_creates_report(tmp_path):
    panel = tmp_path / "panel.csv"
    panel.write_text(
        "candidate_id,sequence,source\n"
        "SEED-001,KWKLFKKIGAVLKVL,test\n"
    )
    out_path = tmp_path / "qc_report.md"
    main(["presynth-qc", "--panel-csv", str(panel), "--out", str(out_path)])
    assert out_path.exists()
    text = out_path.read_text()
    assert "Pre-Synthesis QC Report" in text
    assert "SEED-001" in text


def test_presynth_qc_command_flags_met_residue(tmp_path):
    panel = tmp_path / "panel.csv"
    panel.write_text(
        "candidate_id,sequence,source\n"
        "MET-001,KRLMKKIGSAIKFL,test\n"
    )
    out_path = tmp_path / "qc_report.md"
    main(["presynth-qc", "--panel-csv", str(panel), "--out", str(out_path)])
    text = out_path.read_text()
    # Both the candidate ID and the MET flag must appear — avoids a false pass from
    # a generic preamble sentence that happens to contain the word "oxidation".
    assert "MET-001" in text and "MET" in text


def test_presynth_qc_command_contains_summary_table(tmp_path):
    panel = tmp_path / "panel.csv"
    panel.write_text(
        "candidate_id,sequence,source\n"
        "A,KWKLFKKIGAVLKVL,test\n"
        "B,AAAAAAAAGGGGGGGG,test\n"
    )
    out_path = tmp_path / "qc_report.md"
    main(["presynth-qc", "--panel-csv", str(panel), "--out", str(out_path)])
    text = out_path.read_text()
    assert "Summary Table" in text
    assert "Candidates checked: 2" in text


def test_validate_scoring_stdout_includes_n_and_auprc(tmp_path, capsys):
    """validate-scoring stdout must include n_positives, n_negatives, benchmark_type, auprc."""
    import pathlib
    amp_csv = pathlib.Path("examples/validation/known_amps.csv")
    bg_csv = pathlib.Path("examples/validation/random_background.csv")
    if not amp_csv.exists() or not bg_csv.exists():
        import pytest
        pytest.skip("Validation data not found — run from project root")
    out = str(tmp_path / "report.json")
    main([
        "validate-scoring",
        "--amp-csv", str(amp_csv),
        "--decoy-csv", str(bg_csv),
        "--config", "configs/pipeline.yaml",
        "--benchmark-type", "standard",
        "--out", out,
    ])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "n_positives" in data, "stdout missing n_positives"
    assert "n_negatives" in data, "stdout missing n_negatives"
    assert "benchmark_type" in data, "stdout missing benchmark_type"
    assert "auprc" in data, "stdout missing auprc"
    assert data["n_positives"] == 43  # 44 AMPs - 1 duplicate (REF-GIG-001 removed in PR #66)
    assert data["n_negatives"] == 44
    assert data["benchmark_type"] == "standard"
    assert 0.0 < data["auprc"] < 1.0


def test_pilot_panel_malformed_jsonl_returns_error(tmp_path, capsys):
    """pilot-panel must return structured error on malformed JSONL, not crash."""
    bad_jsonl = tmp_path / "bad.jsonl"
    bad_jsonl.write_text('{"candidate_id": "X", "selected": true}\n{BROKEN JSON LINE\n')
    out_csv = str(tmp_path / "panel.csv")
    out_md = str(tmp_path / "panel.md")
    rc = main([
        "pilot-panel",
        "--ranked", str(bad_jsonl),
        "--out-csv", out_csv,
        "--out-md", out_md,
    ])
    assert rc == 1, "Expected non-zero exit code on malformed JSONL"
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert "line 2" in data["message"]
    assert "line_preview" in data


def test_synthesis_order_missing_columns_returns_error(tmp_path, capsys):
    """synthesis-order must return structured error when panel CSV lacks required columns."""
    bad_panel = tmp_path / "bad_panel.csv"
    bad_panel.write_text("pilot_rank,candidate_id\n1,SEED-003_VAR_001\n")  # missing 'sequence'
    out_csv = str(tmp_path / "order.csv")
    rc = main([
        "synthesis-order",
        "--panel-csv", str(bad_panel),
        "--out-csv", out_csv,
    ])
    assert rc == 1, "Expected non-zero exit code on missing columns"
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "error"
    assert "sequence" in data["message"]


class TestGoldStandard:
    def test_gold_standard_creates_output_file(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "calibration.md"
        rc = main(["gold-standard", "--panel-csv", panel_csv, "--out", str(out), "--config", "configs/pipeline.yaml"])
        assert rc == 0
        assert out.exists()

    def test_gold_standard_output_has_panel_range(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "calibration.md"
        main(["gold-standard", "--panel-csv", panel_csv, "--out", str(out), "--config", "configs/pipeline.yaml"])
        text = out.read_text()
        assert "Confident panel score range" in text
        assert "Min ensemble" in text

    def test_gold_standard_stdout_has_status_ok(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        out = str(tmp_path / "calibration.md")
        main(["gold-standard", "--panel-csv", panel_csv, "--out", out, "--config", "configs/pipeline.yaml"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert "panel_range" in data
        assert "panel_mean" in data
        assert data["n_gold_scored"] == 6  # 7 entries − Polymyxin-B1 (non-standard AA)

    def test_gold_standard_includes_disclaimer(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "calibration.md"
        main(["gold-standard", "--panel-csv", panel_csv, "--out", str(out), "--config", "configs/pipeline.yaml"])
        text = out.read_text()
        assert "AUROC=0.8420" in text
        assert "Disclaimer" in text


class TestExternalPredict:
    def test_external_predict_returns_zero(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        rc = main([
            "external-predict",
            "--pilot-csv", panel_csv,
            "--out-fasta", str(tmp_path / "panel.fasta"),
            "--out-checklist", str(tmp_path / "checklist.md"),
        ])
        assert rc == 0

    def test_external_predict_creates_fasta(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        fasta = tmp_path / "panel.fasta"
        main([
            "external-predict",
            "--pilot-csv", panel_csv,
            "--out-fasta", str(fasta),
            "--out-checklist", str(tmp_path / "checklist.md"),
        ])
        assert fasta.exists()
        content = fasta.read_text()
        assert ">SEED-009_VAR_033" in content
        assert "RRLPRPGYMPRP" in content

    def test_external_predict_creates_checklist(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        checklist = tmp_path / "checklist.md"
        main([
            "external-predict",
            "--pilot-csv", panel_csv,
            "--out-fasta", str(tmp_path / "panel.fasta"),
            "--out-checklist", str(checklist),
        ])
        assert checklist.exists()
        text = checklist.read_text()
        assert "CAMPR4" in text
        assert "SEED-009_VAR_033" in text

    def test_external_predict_stdout_n_candidates(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        main([
            "external-predict",
            "--pilot-csv", panel_csv,
            "--out-fasta", str(tmp_path / "panel.fasta"),
            "--out-checklist", str(tmp_path / "checklist.md"),
        ])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["n_candidates"] == 2


class TestPilotConfident:
    def test_pilot_confident_returns_zero(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        rc = main([
            "pilot-confident",
            "--pilot-csv", panel_csv,
            "--keep", "SEED-009_VAR_033",
            "--out", str(tmp_path / "confident"),
        ])
        assert rc == 0

    def test_pilot_confident_creates_csv_and_md(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "confident"
        main([
            "pilot-confident",
            "--pilot-csv", panel_csv,
            "--keep", "SEED-009_VAR_033",
            "--out", str(out),
        ])
        assert (tmp_path / "confident.csv").exists()
        assert (tmp_path / "confident.md").exists()

    def test_pilot_confident_filters_to_keep_ids(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        main([
            "pilot-confident",
            "--pilot-csv", panel_csv,
            "--keep", "SEED-009_VAR_033",
            "--out", str(tmp_path / "confident"),
        ])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["n_confident"] == 1
        assert data["n_input"] == 2


class TestDiversityCheck:
    def test_diversity_check_returns_zero(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        out = str(tmp_path / "diversity.md")
        rc = main(["diversity-check", "--panel-csv", panel_csv, "--out", out])
        assert rc == 0

    def test_diversity_check_creates_report(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "diversity.md"
        main(["diversity-check", "--panel-csv", panel_csv, "--out", str(out)])
        assert out.exists()
        text = out.read_text()
        assert "Diversity" in text
        assert "SEED-009_VAR_033" in text
        assert "SEED-007_VAR_009" in text


class TestNoveltyCheckBroad:
    def test_novelty_check_broad_returns_zero(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        rc = main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--out", str(tmp_path / "novelty.md"),
        ])
        assert rc == 0

    def test_novelty_check_broad_creates_report(self, tmp_path):
        panel_csv = _write_panel(tmp_path)
        out = tmp_path / "novelty.md"
        main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--out", str(out),
        ])
        assert out.exists()
        text = out.read_text()
        assert "Broad Novelty Check" in text
        assert "SEED-009_VAR_033" in text
        assert "SEED-007_VAR_009" in text

    def test_novelty_check_broad_stdout_summary(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--out", str(tmp_path / "novelty.md"),
        ])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["n_candidates"] == 2
        assert data["n_references"] > 0
        # Both SEED-009 and SEED-007 variants are genuinely novel (<50% to any reference)
        assert data["n_novel"] == 2

    def test_novelty_check_broad_missing_panel_returns_error(self, tmp_path, capsys):
        rc = main([
            "novelty-check-broad",
            "--panel-csv", str(tmp_path / "nonexistent.csv"),
            "--out", str(tmp_path / "novelty.md"),
        ])
        assert rc == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "error"

    def test_novelty_check_broad_known_variant_classification(self, tmp_path, capsys):
        # Craft a reference that is 100% identical to PANEL_CSV_ROW1's sequence
        # so SEED-009_VAR_033 is classified as KNOWN_VARIANT at threshold 0.70
        ref_csv = tmp_path / "refs.csv"
        ref_csv.write_text(
            "id,sequence,family,reference\n"
            "KNOWN-001,RRLPRPGYMPRP,test_family,test_ref\n",  # exact match to SEED-009_VAR_033
            encoding="utf-8",
        )
        panel_csv = _write_panel(tmp_path, two_rows=False)  # single row: SEED-009_VAR_033
        main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--references-csv", str(ref_csv),
            "--out", str(tmp_path / "novelty.md"),
        ])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["n_known_variant"] == 1
        assert data["n_novel"] == 0

    def test_novelty_check_broad_inverted_thresholds_returns_error(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        rc = main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--out", str(tmp_path / "novelty.md"),
            "--threshold-known", "0.30",
            "--threshold-close", "0.70",  # close > known → invalid
        ])
        assert rc == 1
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "error"
        assert "threshold-close" in data["message"]
