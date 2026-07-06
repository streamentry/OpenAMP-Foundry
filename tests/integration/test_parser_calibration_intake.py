from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_calibration_intake_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "calibration-intake",
        "--panel",
        "panel.csv",
        "--results-dir",
        "results",
        "--out-json",
        "intake.json",
    ])

    assert args.command == "calibration-intake"
    assert args.panel == "panel.csv"
    assert args.results_dir == "results"
    assert args.out_json == "intake.json"
    assert args.out_md is None
