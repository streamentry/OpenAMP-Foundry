from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_recalibration_gate_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "recalibration-gate",
        "--intake-report",
        "intake.json",
    ])

    assert args.command == "recalibration-gate"
    assert args.intake_report == "intake.json"
    assert args.policy == "configs/recalibration_policy.yaml"
    assert args.intake_report_date is None
    assert args.previous_recalibration_at is None
    assert args.weight_l1_distance is None
    assert args.project_root is None
    assert args.out_json is None
    assert args.out_md is None
