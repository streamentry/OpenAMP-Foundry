from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_generate_batch_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "generate-batch",
        "--seeds",
        "seeds.csv",
        "--out",
        "candidates.csv",
    ])

    assert args.command == "generate-batch"
    assert args.seeds == "seeds.csv"
    assert args.out == "candidates.csv"
    assert args.n_double == 25
    assert args.n_charge == 12
    assert args.rng_seed == 2024
