from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_validate_scoring_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args(["validate-scoring"])

    assert args.command == "validate-scoring"
    assert args.amp_csv == "examples/validation/known_amps.csv"
    assert args.decoy_csv == "examples/validation/random_background.csv"
    assert args.benchmark_type == "standard"
    assert args.config == "configs/pipeline.yaml"
    assert args.out is None
