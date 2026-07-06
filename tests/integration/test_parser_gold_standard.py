from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_gold_standard_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["gold-standard"])

    assert args.command == "gold-standard"
    assert args.panel_csv == "outputs/confident_panel.csv"
    assert args.out == "outputs/gold_standard_calibration.md"
    assert args.config == "configs/pipeline.yaml"
