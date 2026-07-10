"""Tests for NSN- no-silent-network policy schema."""

import pytest
from openamp_foundry.simulation.no_silent_network_policy import (
    NoSilentNetworkPolicy,
    VALID_NSN_VERDICTS,
    SEQUENCE_EXPOSURE_KEYWORDS,
    build_no_silent_network_policy,
    format_no_silent_network_policy,
    validate_no_silent_network_policy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        nsn_id="NSN-001",
        adapter_id="ADAPTER-membrane-v1",
        pipeline_version="v1.0",
        declared_network_calls=[],
        observed_network_calls=[],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_no_silent_network_policy(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_nsn_verdicts_is_frozenset():
    assert isinstance(VALID_NSN_VERDICTS, frozenset)


def test_valid_nsn_verdicts_contains_compliant():
    assert "compliant" in VALID_NSN_VERDICTS


def test_valid_nsn_verdicts_contains_undeclared_calls_detected():
    assert "undeclared_calls_detected" in VALID_NSN_VERDICTS


def test_valid_nsn_verdicts_contains_sequence_exposure_risk():
    assert "sequence_exposure_risk" in VALID_NSN_VERDICTS


def test_sequence_exposure_keywords_is_tuple():
    assert isinstance(SEQUENCE_EXPOSURE_KEYWORDS, tuple)


def test_sequence_exposure_keywords_contains_sequence():
    assert "sequence" in SEQUENCE_EXPOSURE_KEYWORDS


def test_sequence_exposure_keywords_contains_fasta():
    assert "fasta" in SEQUENCE_EXPOSURE_KEYWORDS


def test_sequence_exposure_keywords_contains_peptide():
    assert "peptide" in SEQUENCE_EXPOSURE_KEYWORDS


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_no_silent_network_policy():
    assert isinstance(_build(), NoSilentNetworkPolicy)


def test_build_nsn_id_stored():
    assert _build().nsn_id == "NSN-001"


def test_build_adapter_id_stored():
    assert _build().adapter_id == "ADAPTER-membrane-v1"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_no_calls_gives_compliant():
    r = _build(declared_network_calls=[], observed_network_calls=[])
    assert r.policy_verdict == "compliant"


def test_build_declared_calls_observed_gives_compliant():
    r = _build(
        declared_network_calls=["https://api.example.com/score"],
        observed_network_calls=["https://api.example.com/score"],
    )
    assert r.policy_verdict == "compliant"


def test_build_undeclared_observed_call_gives_undeclared_calls_detected():
    r = _build(
        declared_network_calls=[],
        observed_network_calls=["https://external.example.com"],
    )
    assert r.policy_verdict == "undeclared_calls_detected"


def test_build_sequence_in_declared_gives_sequence_exposure_risk():
    r = _build(
        declared_network_calls=["https://api.example.com/sequence"],
        observed_network_calls=[],
    )
    assert r.policy_verdict == "sequence_exposure_risk"


def test_build_fasta_in_observed_gives_sequence_exposure_risk():
    r = _build(
        declared_network_calls=["https://api.example.com/fasta"],
        observed_network_calls=["https://api.example.com/fasta"],
    )
    assert r.policy_verdict == "sequence_exposure_risk"


def test_build_undeclared_call_wins_over_exposure_risk():
    r = _build(
        declared_network_calls=[],
        observed_network_calls=["https://api.example.com/sequence"],
    )
    assert r.policy_verdict == "undeclared_calls_detected"


def test_build_undeclared_calls_detected_false_when_compliant():
    assert _build().undeclared_calls_detected is False


def test_build_undeclared_calls_detected_true_when_undeclared():
    r = _build(observed_network_calls=["https://unknown.example.com"])
    assert r.undeclared_calls_detected is True


def test_build_sequence_exposure_risk_false_when_no_keywords():
    r = _build(
        declared_network_calls=["https://api.example.com/score"],
        observed_network_calls=["https://api.example.com/score"],
    )
    assert r.sequence_exposure_risk is False


def test_build_sequence_exposure_risk_true_with_keyword():
    r = _build(declared_network_calls=["https://api.example.com/peptide"])
    assert r.sequence_exposure_risk is True


def test_build_undeclared_calls_list_populated():
    r = _build(observed_network_calls=["https://unknown.example.com"])
    assert "https://unknown.example.com" in r.undeclared_calls


def test_build_undeclared_calls_list_empty_when_compliant():
    assert _build().undeclared_calls == []


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_peptide_keyword_case_insensitive():
    r = _build(declared_network_calls=["https://api.example.com/PEPTIDE"])
    assert r.sequence_exposure_risk is True


def test_build_amino_keyword_triggers_risk():
    r = _build(declared_network_calls=["https://api.example.com/amino-acid"])
    assert r.sequence_exposure_risk is True


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_nsn_id_prefix():
    with pytest.raises(ValueError, match="NSN-"):
        _build(nsn_id="BAD-001")


def test_validate_rejects_empty_adapter_id():
    with pytest.raises(ValueError, match="adapter_id"):
        _build(adapter_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_policy_verdict():
    nsn = _build()
    nsn.policy_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="policy_verdict"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_undeclared_calls_mismatch():
    nsn = _build()
    nsn.undeclared_calls = ["https://fake.com"]
    with pytest.raises(ValueError, match="undeclared_calls"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_undeclared_calls_detected_mismatch():
    nsn = _build()
    nsn.undeclared_calls_detected = True
    with pytest.raises(ValueError, match="undeclared_calls_detected"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_sequence_exposure_risk_mismatch():
    nsn = _build()
    nsn.sequence_exposure_risk = True
    with pytest.raises(ValueError, match="sequence_exposure_risk"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_wrong_verdict_when_undeclared():
    nsn = _build()
    nsn.observed_network_calls = ["https://unknown.com"]
    nsn.undeclared_calls = ["https://unknown.com"]
    nsn.undeclared_calls_detected = True
    nsn.policy_verdict = "compliant"
    with pytest.raises(ValueError, match="undeclared_calls_detected"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_dry_lab_only_false():
    nsn = _build()
    nsn.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_no_silent_network_policy(nsn)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_nsn_id():
    assert "NSN-001" in format_no_silent_network_policy(_build())


def test_format_contains_adapter_id():
    assert "ADAPTER-membrane-v1" in format_no_silent_network_policy(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_no_silent_network_policy(_build())


def test_format_contains_verdict():
    assert "compliant" in format_no_silent_network_policy(_build())


def test_format_contains_undeclared_calls_detected():
    assert "False" in format_no_silent_network_policy(_build())


def test_format_contains_undeclared_call_when_detected():
    r = _build(observed_network_calls=["https://unknown.example.com"])
    assert "https://unknown.example.com" in format_no_silent_network_policy(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_no_silent_network_policy(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_no_silent_network_policy(_build())


def test_format_is_string():
    assert isinstance(format_no_silent_network_policy(_build()), str)
