"""CLI integration tests."""
from __future__ import annotations

import json


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


def test_phase_ac_disconfirming_gate_check_reports_verified(capsys):
    ret = main([
        "phase-ac-disconfirming-gate-check",
        "--entry-json",
        json.dumps({
            "acdg_id": "ACDG-CLI-001",
            "pipeline_version": "v1.0",
            "records": [{
                "dtr_id": "DTR-CLI-001",
                "pipeline_version": "v1.0",
                "claim_tested": "The pipeline adds signal beyond a cheap enemy.",
                "test_type": "cheapest_explanation_check",
                "test_description": "Compared the pipeline with a charge-only baseline.",
                "test_outcome": "not_refuted",
                "evidence_summary": "The recorded challenge did not refute the claim.",
                "limitations": ["Toy benchmark only."],
                "created_at": "2026-07-15",
            }],
            "resolved_dtr_ids": [],
            "limitations": ["Dry-lab review control, not biological proof."],
            "created_at": "2026-07-15",
        }),
        "--format", "json",
    ])
    assert ret == 0
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "disconfirming_evidence_verified"
    assert result["dry_lab_only"] is True


def test_phase_ac_disconfirming_gate_check_fails_when_follow_up_is_unresolved():
    payload = {
        "acdg_id": "ACDG-CLI-002",
        "pipeline_version": "v1.0",
        "records": [{
            "dtr_id": "DTR-CLI-002",
            "pipeline_version": "v1.0",
            "claim_tested": "The pipeline adds signal beyond a cheap enemy.",
            "test_type": "cheapest_explanation_check",
            "test_description": "Compared the pipeline with a charge-only baseline.",
            "test_outcome": "refuted",
            "evidence_summary": "The cheap baseline matched or exceeded the pipeline.",
            "limitations": ["Toy benchmark only."],
            "created_at": "2026-07-15",
        }],
        "resolved_dtr_ids": [],
        "limitations": ["Dry-lab review control, not biological proof."],
        "created_at": "2026-07-15",
    }
    assert main([
        "phase-ac-disconfirming-gate-check",
        "--entry-json", json.dumps(payload),
    ]) == 3


def test_phase_aa_reproducibility_gate_check_reports_verified(capsys):
    ret = main([
        "phase-aa-reproducibility-gate-check",
        "--entry-json",
        json.dumps({
            "aarg_id": "AARG-CLI-001",
            "pipeline_version": "v1.0",
            "rmc_id": "RMC-CLI-001",
            "dcr_id": "DCR-CLI-001",
            "cfp_id": "CFP-CLI-001",
            "sbw_id": "SBW-CLI-001",
            "created_at": "2026-07-16",
        }),
        "--format", "json",
    ])
    assert ret == 0
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "reproducibility_verified"
    assert result["n_components_present"] == 4
    assert result["dry_lab_only"] is True


def test_phase_aa_reproducibility_gate_check_fails_when_components_are_missing():
    payload = {
        "aarg_id": "AARG-CLI-002",
        "pipeline_version": "v1.0",
        "rmc_id": "RMC-CLI-002",
        "dcr_id": "DCR-CLI-002",
        "created_at": "2026-07-16",
    }
    assert main([
        "phase-aa-reproducibility-gate-check",
        "--entry-json", json.dumps(payload),
    ]) == 3


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
    assert data["n_positives"] >= 90  # expanded to 95 AMPs (PR #110)
    assert data["n_negatives"] >= 90  # expanded to 96 decoys (PR #110)
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
        assert "AUROC=" in text  # expanded benchmark PR #110: AUROC=0.7832 on 95+96
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

    def test_diversity_check_family_structural_warning(self, tmp_path):
        # Three variants from the same seed, all with ≥4 interior trypsin sites → TRYPSIN_STABILITY family warning
        panel = tmp_path / "fam_panel.csv"
        panel.write_text(
            PANEL_CSV_HEADER
            + "1,SEED-001_VAR_001,KWKLFKKIGAVLKVL,15,SEED-001,0.75,0.70,0.60,0.10,0.90,0.85,0.70,0.60,1.0,0.80\n"
            + "2,SEED-001_VAR_002,KWKLFKRIGAVLKVL,15,SEED-001,0.74,0.70,0.60,0.10,0.90,0.85,0.70,0.60,1.0,0.79\n"
            + "3,SEED-001_VAR_003,KWKLFRRIGAVLKVL,15,SEED-001,0.73,0.70,0.60,0.10,0.90,0.85,0.70,0.60,1.0,0.78\n",
            encoding="utf-8",
        )
        out = tmp_path / "diversity.md"
        rc = main(["diversity-check", "--panel-csv", str(panel), "--out", str(out)])
        assert rc == 0
        text = out.read_text(encoding="utf-8")
        assert "Family-Level Structural" in text

    def test_diversity_check_redundancy_and_optimal_diff_sections(self, tmp_path):
        # Two candidates nearly identical (sim=0.889>0.60) → same cluster.
        # Lower pilot_rank wins in minimal but lower ensemble wins in optimal.
        # This triggers both the redundancy warning section (n_redundant>0)
        # and the optimal-cluster-representatives section (optimal_ids != minimal_ids).
        panel = tmp_path / "similar_panel.csv"
        panel.write_text(
            PANEL_CSV_HEADER
            + "1,CAND-A,KWKLFKKIG,9,SEED-001,0.70,0.60,0.55,0.10,0.90,0.85,0.70,0.60,1.0,0.80\n"
            + "2,CAND-B,KWKLFKKIA,9,SEED-001,0.90,0.75,0.60,0.10,0.90,0.85,0.70,0.60,1.0,0.82\n",
            encoding="utf-8",
        )
        out = tmp_path / "diversity.md"
        rc = main(["diversity-check", "--panel-csv", str(panel), "--out", str(out)])
        assert rc == 0
        text = out.read_text(encoding="utf-8")
        # Redundancy section appears when n_redundant > 0
        assert "Redundancy Warning" in text or "redundant" in text.lower()
        # Optimal section appears when optimal picks differ from minimal
        assert "Optimal Cluster" in text


def _write_ranked_jsonl(tmp_path, n: int = 3) -> str:
    """Minimal ranked JSONL with n selected candidates from distinct seeds."""
    rows = []
    for i in range(n):
        seed = f"SEED-00{i + 1}"
        rows.append({
            "candidate_id": f"{seed}_VAR_001",
            "sequence": f"KWKLFK{'A' * i}LG",
            "source": f"template_mutation_from_{seed}",
            "selected": True,
            "valid": True,
            "scores": {
                "ensemble": round(0.80 - i * 0.05, 3),
                "activity": 0.70,
                "safety": 0.90,
                "synthesis": 0.85,
                "novelty": 0.70,
                "disagreement": 0.10,
                "serum_stability": 0.60,
                "boman_activity": 0.60,
                "selectivity_proxy": 1.0,
            },
            "features": {},
            "selection_reason": [],
            "known_failure_modes": [],
            "nearest_reference": {
                "candidate_id": "REF-001",
                "sequence": "KWKLFK",
                "similarity": 0.5,
                "source": "demo",
            },
        })
    p = tmp_path / "ranked.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(p)


def test_pilot_panel_ranked_file_not_found_returns_error(tmp_path, capsys):
    rc = main([
        "pilot-panel",
        "--ranked", str(tmp_path / "nonexistent.jsonl"),
        "--out-csv", str(tmp_path / "panel.csv"),
    ])
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_pilot_panel_blank_lines_skipped_and_output_produced(tmp_path, capsys):
    ranked = _write_ranked_jsonl(tmp_path)
    # Prepend/append blank lines to trigger the blank-line-skip branch
    from pathlib import Path as _Path
    content = _Path(ranked).read_text(encoding="utf-8")
    _Path(ranked).write_text("\n" + content + "\n\n", encoding="utf-8")

    out_csv = str(tmp_path / "panel.csv")
    out_md = str(tmp_path / "panel.md")
    rc = main(["pilot-panel", "--ranked", ranked, "--out-csv", out_csv, "--out-md", out_md, "--n", "2"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ok"
    assert data["n_panel"] == 2
    assert "No antimicrobial activity" in data["disclaimer"]
    assert (tmp_path / "panel.md").exists()


def test_pilot_panel_reports_structural_classes_and_floor_flag(tmp_path, capsys):
    ranked = tmp_path / "ranked.jsonl"
    rows = [
        {
            "candidate_id": "HIGH",
            "sequence": "KKKKAAAAAAAAL",
            "source": "template_mutation_from_SEED-H",
            "selected": True,
            "scores": {"ensemble": 0.95, "activity": 0.95, "boman_activity": 0.90, "disagreement": 0.05},
            "features": {"length": 13, "net_charge_ph74": 5.0, "proline_fraction": 0.0},
        },
        {
            "candidate_id": "LOW",
            "sequence": "AAAAAAAALLLLL",
            "source": "template_mutation_from_SEED-L",
            "selected": True,
            "scores": {"ensemble": 0.50, "activity": 0.50, "boman_activity": 0.45, "disagreement": 0.05},
            "features": {"length": 13, "net_charge_ph74": 1.0, "proline_fraction": 0.0},
        },
    ]
    ranked.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    out_csv = str(tmp_path / "panel.csv")
    rc = main([
        "pilot-panel",
        "--ranked", str(ranked),
        "--out-csv", out_csv,
        "--n", "2",
        "--min-per-structural-class", "1",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["structural_classes_represented"] == ["highly_cationic", "low_charge"]


def test_generate_batch_missing_seeds_file_returns_error(tmp_path, capsys):
    rc = main([
        "generate-batch",
        "--seeds", str(tmp_path / "nonexistent.csv"),
        "--out", str(tmp_path / "pool.csv"),
    ])
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "error"
    assert "Seeds file not found" in data["message"]


def test_generate_batch_creates_candidate_pool(tmp_path, capsys):
    seeds = tmp_path / "seeds.csv"
    seeds.write_text(
        "id,sequence,source\nSEED-001,GIGKFLHSAGKFGKAFVGEIMKS,test\n",
        encoding="utf-8",
    )
    out = str(tmp_path / "pool.csv")
    rc = main([
        "generate-batch",
        "--seeds", str(seeds),
        "--out", out,
        "--n-double", "3",
        "--n-charge", "2",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ok"
    assert data["n_seeds"] == 1
    assert data["n_candidates_generated"] > 0
    import csv as _csv
    with open(out, encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    assert len(rows) == data["n_candidates_generated"]


def test_batch_pack_creates_json_output(tmp_path, capsys):
    ranked = str(tmp_path / "ranked.jsonl")
    main([
        "rank",
        "--candidates", "examples/sequences/demo_candidates.csv",
        "--references", "examples/known_reference/demo_known_amps.csv",
        "--out", ranked,
    ])
    capsys.readouterr()  # discard rank stdout

    out_json = str(tmp_path / "batch.json")
    out_md = str(tmp_path / "batch.md")
    rc = main(["batch-pack", "--ranked", ranked, "--out-json", out_json, "--out-md", out_md])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ok"
    assert "n_selected" in data
    with open(out_json, encoding="utf-8") as fh:
        pack = json.loads(fh.read())
    assert "summary" in pack
    assert (tmp_path / "batch.md").exists()


def test_lab_result_report_creates_outputs(tmp_path, capsys):
    results_dir = tmp_path / "lab_results"
    results_dir.mkdir()
    base = {
        "assay_type": "MIC",
        "organism_or_cell_line": "E. coli ATCC 25922",
        "result_value": 4.0,
        "result_unit": "µg/mL",
        "positive_control_id": "ciprofloxacin 0.25 µg/mL",
        "negative_control_id": "PBS",
        "assay_date": "2026-07-01",
        "replicate_count": 3,
        "performed_by_lab": "University Test Lab",
        "raw_data_sha256": None,
        "computational_candidate_certificate_hash": "abc123def456",
        "notes": None,
        "disclaimer": (
            "This is an experimental result on a computationally nominated candidate. "
            "It does not constitute a drug or clinical claim."
        ),
    }
    good = {
        **base,
        "result_id": "RES-001",
        "candidate_id": "CAND-001",
        "result_qualitative": "active",
        "positive_control_passed": True,
        "negative_control_passed": True,
    }
    failed_control = {
        **base,
        "result_id": "RES-002",
        "candidate_id": "CAND-001",
        "assay_type": "hemolysis_RBC",
        "result_value": 18.0,
        "result_unit": "%",
        "result_qualitative": "toxic",
        "positive_control_passed": False,
        "negative_control_passed": True,
    }
    (results_dir / "res1.json").write_text(json.dumps(good), encoding="utf-8")
    (results_dir / "res2.json").write_text(json.dumps(failed_control), encoding="utf-8")

    out_json = tmp_path / "lab_report.json"
    out_md = tmp_path / "lab_report.md"
    rc = main([
        "lab-result-report",
        "--results-dir", str(results_dir),
        "--out-json", str(out_json),
        "--out-md", str(out_md),
    ])
    assert rc == 0
    captured = json.loads(capsys.readouterr().out)
    assert captured["status"] == "ok"
    assert captured["n_results"] == 2
    assert captured["n_control_failures"] == 1
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["summary"]["n_results"] == 2
    assert report["n_candidates"] == 1
    assert len(report["control_failures"]) == 1
    text = out_md.read_text(encoding="utf-8")
    assert "Wet-Lab Result Report" in text
    assert "CAND-001" in text
    assert "RES-002" in text


def test_lab_result_report_blocks_invalid_files(tmp_path, capsys):
    results_dir = tmp_path / "lab_results"
    results_dir.mkdir()
    (results_dir / "invalid.json").write_text(
        json.dumps({"result_id": "BAD-001"}), encoding="utf-8"
    )

    out_json = tmp_path / "lab_report.json"
    rc = main([
        "lab-result-report",
        "--results-dir", str(results_dir),
        "--out-json", str(out_json),
    ])

    assert rc == 3
    captured = json.loads(capsys.readouterr().out)
    assert captured["status"] == "blocked"
    assert captured["n_invalid_lab_result_files"] == 1
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["input_validation_status"] == "blocked_on_invalid_results"


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

    def test_novelty_check_broad_empty_panel_csv_returns_error(self, tmp_path, capsys):
        empty_panel = tmp_path / "empty.csv"
        empty_panel.write_text(PANEL_CSV_HEADER, encoding="utf-8")  # header only, no rows
        rc = main([
            "novelty-check-broad",
            "--panel-csv", str(empty_panel),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"
        assert "empty" in data["message"]

    def test_novelty_check_broad_missing_references_csv_returns_error(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        rc = main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--references-csv", str(tmp_path / "nonexistent_refs.csv"),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"
        assert "not found" in data["message"]

    def test_novelty_check_broad_empty_references_csv_returns_error(self, tmp_path, capsys):
        panel_csv = _write_panel(tmp_path)
        refs = tmp_path / "refs.csv"
        refs.write_text("id,sequence,family,reference\n", encoding="utf-8")  # header only
        rc = main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--references-csv", str(refs),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "error"
        assert "no valid sequences" in data["message"]

    def test_novelty_check_broad_empty_sequence_row_is_skipped(self, tmp_path, capsys):
        panel = tmp_path / "panel.csv"
        panel.write_text(
            PANEL_CSV_HEADER
            + PANEL_CSV_ROW1
            + "3,EMPTY-001,,0,SEED-009,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n",
            encoding="utf-8",
        )
        rc = main([
            "novelty-check-broad",
            "--panel-csv", str(panel),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        # Only the row with a sequence is scored; the empty row is skipped
        assert data["n_candidates"] == 1

    def test_novelty_check_broad_close_relative_classification_and_report(self, tmp_path, capsys):
        # Reference ~66.7% similar to SEED-009_VAR_033 (RRLPRPGYMPRP): 4 substitutions
        # sim = 1 - 4/12 = 0.667 → CLOSE_RELATIVE (0.50 ≤ sim < 0.70)
        ref_csv = tmp_path / "refs.csv"
        ref_csv.write_text(
            "id,sequence,family,reference\n"
            "REF-CLOSE,RRLPAAGYMAAP,test_family,test_ref\n",
            encoding="utf-8",
        )
        panel_csv = _write_panel(tmp_path, two_rows=False)  # SEED-009_VAR_033 only
        rc = main([
            "novelty-check-broad",
            "--panel-csv", panel_csv,
            "--references-csv", str(ref_csv),
            "--out", str(tmp_path / "out.md"),
        ])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["status"] == "ok"
        assert data["n_close_relative"] == 1
        assert data["n_novel"] == 0
        report = (tmp_path / "out.md").read_text(encoding="utf-8")
        assert "CLOSE_RELATIVE" in report
