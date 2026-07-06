from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_external_consensus_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "external-consensus",
        "--results-csv",
        "results.csv",
    ])

    assert args.command == "external-consensus"
    assert args.results_csv == "results.csv"
    assert args.pilot_csv == "outputs/pilot_panel.csv"
    assert args.out == "outputs/external_consensus_report.md"
