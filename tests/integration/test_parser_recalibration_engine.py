from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_recalibration_engine_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "recalibration-engine",
        "--intake-report",
        "intake.json",
        "--gate-verdict",
        "gate.json",
        "--current-weights",
        "{}",
    ])

    assert args.command == "recalibration-engine"
    assert args.intake_report == "intake.json"
    assert args.gate_verdict == "gate.json"
    assert args.current_weights == "{}"
    assert args.l1_budget == 0.10
    assert args.out_json is None
    assert args.out_md is None
    assert args.dry_run is False
