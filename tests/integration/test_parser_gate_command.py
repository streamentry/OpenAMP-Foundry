from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_gate_command_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["gate-check"])

    assert args.command == "gate-check"
    assert args.gate == 0
    assert args.validation_json == "outputs/validate_scoring_report.json"
