from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_synthesis_order_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["synthesis-order"])

    assert args.command == "synthesis-order"
    assert args.panel_csv == "outputs/confident_panel.csv"
    assert args.out_csv == "outputs/synthesis_order.csv"
    assert args.out_md == "outputs/synthesis_checklist.md"
    assert args.quantity_mg == 5.0
