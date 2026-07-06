from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_validate_parser_records_paths():
    parser = build_parser()
    args = parser.parse_args([
        "validate",
        "--certificate",
        "candidate.json",
        "--schema",
        "candidate.schema.json",
    ])

    assert args.command == "validate"
    assert args.certificate == "candidate.json"
    assert args.schema == "candidate.schema.json"
