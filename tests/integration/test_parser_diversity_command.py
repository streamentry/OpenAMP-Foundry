from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_diversity_command_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "diversity-check",
        "--panel-csv",
        "panel.csv",
    ])

    assert args.command == "diversity-check"
    assert args.panel_csv == "panel.csv"
    assert args.similarity_threshold == 0.60
    assert args.n_per_cluster == 1
    assert args.out == "outputs/diversity_report.md"
