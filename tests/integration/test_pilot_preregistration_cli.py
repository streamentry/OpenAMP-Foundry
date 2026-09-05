"""Integration tests for the PRR pilot pre-registration CLI check."""

import dataclasses
import json

from openamp_foundry.cli.main import main
from openamp_foundry.evidence.pilot_preregistration import (
    PilotPreregistration,
    ScoreThreshold,
    lock_pilot_preregistration,
)


def _locked_payload() -> dict:
    draft = PilotPreregistration(
        record_id="PRR-CLI-001",
        version="1.0.0",
        frozen_at="2026-09-02T00:00:00Z",
        pipeline_version="0.9.0",
        git_sha="abc1234",
        primary_hypothesis="The selected panel will improve useful evidence over baseline.",
        selection_criteria=["ensemble_score >= 0.75"],
        score_thresholds=[ScoreThreshold("ensemble_score", 0.75, "above")],
        n_candidates_planned=5,
        positive_control="qualified_positive_control",
        negative_control="qualified_negative_control",
        outcome_metric="minimum_inhibitory_concentration",
    )
    return dataclasses.asdict(lock_pilot_preregistration(draft))


def test_locked_preregistration_cli_passes(capsys):
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(_locked_payload()),
    ])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out


def test_unlocked_preregistration_cli_fails_closed(capsys):
    payload = _locked_payload()
    payload["is_locked"] = False
    payload["freeze_sha256"] = ""
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
        "--format", "json",
    ])
    assert rc == 3
    result = json.loads(capsys.readouterr().out)
    assert result["is_valid"] is False
    assert any("is_locked" in error for error in result["violations"])


def test_tampered_preregistration_cli_fails_closed(capsys):
    payload = _locked_payload()
    payload["selection_criteria"].append("changed after freeze")
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 3
    assert "freeze_sha256 does not match" in capsys.readouterr().out


def test_invalid_preregistration_json_returns_input_error(capsys):
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", "not-json",
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "error"


def test_invalid_preregistration_field_type_returns_input_error(capsys):
    payload = _locked_payload()
    payload["selection_criteria"] = "not-a-list"
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert "selection_criteria must be a list" in result["error"]


def test_invalid_preregistration_threshold_type_returns_input_error(capsys):
    payload = _locked_payload()
    payload["score_thresholds"][0]["threshold_value"] = "0.75"
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert "threshold_value must be numeric" in result["error"]


def test_invalid_preregistration_scalar_type_returns_input_error(capsys):
    payload = _locked_payload()
    payload["primary_hypothesis"] = 42
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert "primary_hypothesis must be a string" in result["error"]


def test_invalid_preregistration_list_item_returns_input_error(capsys):
    payload = _locked_payload()
    payload["amendment_reasons"] = [{"reason": "not-a-string"}]
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert "amendment_reasons entries must be strings" in result["error"]


def test_non_string_selection_criterion_returns_input_error(capsys):
    payload = _locked_payload()
    payload["selection_criteria"] = [42]
    rc = main([
        "pilot-preregistration-check",
        "--entry-json", json.dumps(payload),
    ])
    assert rc == 2
    result = json.loads(capsys.readouterr().out)
    assert "selection_criteria entries must be strings" in result["error"]
