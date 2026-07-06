from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_pilot_panel_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "pilot-panel",
        "--ranked",
        "ranked.jsonl",
        "--out-csv",
        "panel.csv",
    ])

    assert args.command == "pilot-panel"
    assert args.ranked == "ranked.jsonl"
    assert args.out_csv == "panel.csv"
    assert args.out_md is None
    assert args.n == 20
    assert args.max_per_seed is None
    assert args.similarity_threshold is None
    assert args.min_per_structural_class == 0
