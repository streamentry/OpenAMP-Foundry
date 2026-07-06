from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_rank_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["rank", "--candidates", "candidates.csv", "--out", "ranked.jsonl"])

    assert args.command == "rank"
    assert args.references is None
    assert args.config == "configs/pipeline.yaml"
    assert args.ranking_mode == "ensemble"
    assert args.simulation_mode == "off"
