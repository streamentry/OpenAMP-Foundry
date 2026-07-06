from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_questionnaire_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["reviewer-questionnaire"])

    assert args.command == "reviewer-questionnaire"
    assert args.panel_csv == "outputs/confident_panel.csv"
    assert args.out == "outputs/questionnaire"
