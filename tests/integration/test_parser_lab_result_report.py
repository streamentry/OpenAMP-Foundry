from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_lab_result_report_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "lab-result-report",
        "--results-dir",
        "results",
        "--out-json",
        "report.json",
    ])

    assert args.command == "lab-result-report"
    assert args.results_dir == "results"
    assert args.out_json == "report.json"
    assert args.out_md is None
