from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_pilot_confident_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "pilot-confident",
        "--pilot-csv",
        "panel.csv",
        "--keep",
        "A,B",
    ])

    assert args.command == "pilot-confident"
    assert args.pilot_csv == "panel.csv"
    assert args.keep == "A,B"
    assert args.out == "outputs/confident_panel"
