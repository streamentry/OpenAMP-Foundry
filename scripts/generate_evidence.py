from openamp_foundry.pipeline import run_ranking_pipeline


if __name__ == "__main__":
    run_ranking_pipeline(
        candidate_path="examples/sequences/demo_candidates.csv",
        reference_path="examples/known_reference/demo_known_amps.csv",
        out_path="outputs/demo_ranked.jsonl",
        report_path="outputs/demo_report.md",
        cert_dir="outputs/evidence",
    )
