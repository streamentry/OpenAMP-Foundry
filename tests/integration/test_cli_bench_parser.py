from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_bench_leakage_parser_values():
    parser = build_parser()
    args = parser.parse_args([
        "bench",
        "leakage",
        "--candidates",
        "candidates.csv",
        "--references",
        "references.csv",
    ])

    assert args.command == "bench"
    assert args.bench_command == "leakage"
    assert args.threshold == 0.90
    assert args.out is None
