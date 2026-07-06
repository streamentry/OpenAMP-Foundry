from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_external_predict_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "external-predict",
        "--pilot-csv",
        "panel.csv",
    ])

    assert args.command == "external-predict"
    assert args.pilot_csv == "panel.csv"
    assert args.out_fasta == "outputs/pilot_panel.fasta"
    assert args.out_checklist == "outputs/external_predict_checklist.md"
