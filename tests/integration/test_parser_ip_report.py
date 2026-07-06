from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_ip_report_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["ip-report"])

    assert args.command == "ip-report"
    assert args.panel_csv == "outputs/confident_panel.csv"
    assert args.novelty_csv == "outputs/novelty_audit_full.csv"
    assert args.out == "outputs/ip_report.md"
