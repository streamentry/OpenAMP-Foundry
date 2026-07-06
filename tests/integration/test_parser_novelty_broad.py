from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_novelty_broad_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "novelty-check-broad",
        "--panel-csv",
        "panel.csv",
    ])

    assert args.command == "novelty-check-broad"
    assert args.panel_csv == "panel.csv"
    assert args.references_csv == "examples/known_reference/amp_curated_references.csv"
    assert args.out == "outputs/novelty_broad_report.md"
    assert args.threshold_known == 0.70
    assert args.threshold_close == 0.50
