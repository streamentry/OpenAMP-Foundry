from __future__ import annotations

from openamp_foundry.cli.main import build_parser


def test_validate_policy_version_parser_defaults_are_stable():
    parser = build_parser()
    args = parser.parse_args([
        "validate-policy-version",
        "--current-policy",
        "current.yaml",
        "--previous-policy",
        "previous.yaml",
    ])

    assert args.command == "validate-policy-version"
    assert args.current_policy == "current.yaml"
    assert args.previous_policy == "previous.yaml"
    assert args.decision_log_dir is None
    assert args.today is None
