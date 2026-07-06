from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_presynth_qc_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["presynth-qc"])

    assert args.command == "presynth-qc"
    assert args.panel_csv == "outputs/confident_panel.csv"
    assert args.out == "outputs/presynth_qc_report.md"
