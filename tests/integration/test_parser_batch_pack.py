from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_batch_pack_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "batch-pack",
        "--ranked",
        "ranked.jsonl",
        "--out-json",
        "batch.json",
    ])

    assert args.command == "batch-pack"
    assert args.ranked == "ranked.jsonl"
    assert args.out_json == "batch.json"
    assert args.out_md is None
    assert args.diversity_threshold == 0.80
