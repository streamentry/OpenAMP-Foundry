"""Tests for PAS- public API policy stub schema."""

import pytest
from openamp_foundry.interop.public_api_policy_stub import (
    PublicApiPolicyStub,
    VALID_AUTH_METHODS,
    VALID_DATA_COLLECTION_CATEGORIES,
    REQUIRED_NOT_COLLECTED,
    MIN_RATE_LIMIT_RPM,
    MAX_RATE_LIMIT_RPM,
    build_public_api_policy_stub,
    format_public_api_policy_stub,
    validate_public_api_policy_stub,
)

_REQUIRED_NC = list(REQUIRED_NOT_COLLECTED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        pas_id="PAS-001",
        api_version="v1.0-stub",
        pipeline_version="v1.0",
        auth_method="api_key",
        rate_limit_requests_per_minute=60,
        rate_limit_requests_per_day=1000,
        data_collected=["request_timestamp", "endpoint_called"],
        data_not_collected=["raw_sequence_data", "candidate_ids"],
        limitations=["dry-lab only, public API not yet live"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_public_api_policy_stub(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_auth_methods_is_frozenset():
    assert isinstance(VALID_AUTH_METHODS, frozenset)


def test_valid_auth_methods_contains_api_key():
    assert "api_key" in VALID_AUTH_METHODS


def test_valid_auth_methods_contains_oauth2():
    assert "oauth2" in VALID_AUTH_METHODS


def test_valid_auth_methods_contains_none():
    assert "none" in VALID_AUTH_METHODS


def test_valid_data_collection_categories_is_frozenset():
    assert isinstance(VALID_DATA_COLLECTION_CATEGORIES, frozenset)


def test_valid_data_collection_categories_contains_raw_sequence_data():
    assert "raw_sequence_data" in VALID_DATA_COLLECTION_CATEGORIES


def test_valid_data_collection_categories_contains_candidate_ids():
    assert "candidate_ids" in VALID_DATA_COLLECTION_CATEGORIES


def test_required_not_collected_is_tuple():
    assert isinstance(REQUIRED_NOT_COLLECTED, tuple)


def test_required_not_collected_contains_raw_sequence_data():
    assert "raw_sequence_data" in REQUIRED_NOT_COLLECTED


def test_required_not_collected_contains_candidate_ids():
    assert "candidate_ids" in REQUIRED_NOT_COLLECTED


def test_min_rate_limit_rpm_is_positive():
    assert MIN_RATE_LIMIT_RPM >= 1


def test_max_rate_limit_rpm():
    assert MAX_RATE_LIMIT_RPM == 1000


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_public_api_policy_stub():
    assert isinstance(_build(), PublicApiPolicyStub)


def test_build_pas_id_stored():
    assert _build().pas_id == "PAS-001"


def test_build_api_version_stored():
    assert _build().api_version == "v1.0-stub"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_sequence_data_accepted_false():
    assert _build().sequence_data_accepted is False


def test_build_auth_method_api_key():
    assert _build().auth_method == "api_key"


def test_build_auth_method_oauth2():
    r = _build(auth_method="oauth2")
    assert r.auth_method == "oauth2"


def test_build_auth_method_none():
    r = _build(auth_method="none")
    assert r.auth_method == "none"


def test_build_rate_limit_rpm_stored():
    assert _build().rate_limit_requests_per_minute == 60


def test_build_rate_limit_rpd_stored():
    assert _build().rate_limit_requests_per_day == 1000


def test_build_data_collected_stored():
    r = _build()
    assert "request_timestamp" in r.data_collected


def test_build_data_not_collected_stored():
    r = _build()
    assert "raw_sequence_data" in r.data_not_collected


def test_build_required_not_collected_declared_true():
    assert _build().required_not_collected_declared is True


def test_build_limitations_stored():
    assert "dry-lab only" in _build().limitations[0]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_empty_data_collected_allowed():
    r = _build(data_collected=[])
    assert r.data_collected == []


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_pas_id_prefix():
    with pytest.raises(ValueError, match="PAS-"):
        _build(pas_id="BAD-001")


def test_validate_rejects_empty_api_version():
    with pytest.raises(ValueError, match="api_version"):
        _build(api_version="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_auth_method():
    with pytest.raises(ValueError, match="auth_method"):
        _build(auth_method="UNKNOWN")


def test_validate_rejects_rpm_below_minimum():
    with pytest.raises(ValueError, match="rate_limit_requests_per_minute"):
        _build(rate_limit_requests_per_minute=0)


def test_validate_rejects_rpm_above_maximum():
    with pytest.raises(ValueError, match="rate_limit_requests_per_minute"):
        _build(rate_limit_requests_per_minute=1001)


def test_validate_rejects_rpd_less_than_rpm():
    with pytest.raises(ValueError, match="rate_limit_requests_per_day"):
        _build(
            rate_limit_requests_per_minute=100,
            rate_limit_requests_per_day=50,
        )


def test_validate_rejects_invalid_data_collected_category():
    with pytest.raises(ValueError, match="data_collected"):
        _build(data_collected=["UNKNOWN_CATEGORY"])


def test_validate_rejects_invalid_data_not_collected_category():
    with pytest.raises(ValueError, match="data_not_collected"):
        _build(data_not_collected=["raw_sequence_data", "candidate_ids", "UNKNOWN"])


def test_validate_rejects_overlap_between_collected_and_not_collected():
    with pytest.raises(ValueError, match="overlap"):
        _build(
            data_collected=["raw_sequence_data"],
            data_not_collected=["raw_sequence_data", "candidate_ids"],
        )


def test_validate_rejects_missing_raw_sequence_data_in_not_collected():
    with pytest.raises(ValueError, match="raw_sequence_data"):
        _build(data_not_collected=["candidate_ids"])


def test_validate_rejects_missing_candidate_ids_in_not_collected():
    with pytest.raises(ValueError, match="candidate_ids"):
        _build(data_not_collected=["raw_sequence_data"])


def test_validate_rejects_dry_lab_only_false():
    pas = _build()
    pas.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_public_api_policy_stub(pas)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_sequence_data_accepted_true():
    pas = _build()
    pas.sequence_data_accepted = True
    with pytest.raises(ValueError, match="sequence_data_accepted"):
        validate_public_api_policy_stub(pas)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_pas_id():
    assert "PAS-001" in format_public_api_policy_stub(_build())


def test_format_contains_api_version():
    assert "v1.0-stub" in format_public_api_policy_stub(_build())


def test_format_contains_auth_method():
    assert "api_key" in format_public_api_policy_stub(_build())


def test_format_contains_rate_limits():
    assert "60" in format_public_api_policy_stub(_build())


def test_format_contains_sequence_data_accepted():
    assert "False" in format_public_api_policy_stub(_build())


def test_format_contains_data_not_collected():
    assert "raw_sequence_data" in format_public_api_policy_stub(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_public_api_policy_stub(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_public_api_policy_stub(_build())


def test_format_is_string():
    assert isinstance(format_public_api_policy_stub(_build()), str)
