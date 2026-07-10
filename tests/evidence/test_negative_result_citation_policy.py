"""Tests for NRC- negative-result citation policy schema."""

import pytest
from openamp_foundry.evidence.negative_result_citation_policy import (
    NegativeResultCitationPolicy,
    VALID_NRC_VERDICTS,
    build_negative_result_citation_policy,
    format_negative_result_citation_policy,
    validate_negative_result_citation_policy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        nrc_id="NRC-001",
        claim_id="CLM-001",
        pipeline_version="v1.0",
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001", "NRR-002"],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_negative_result_citation_policy(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_nrc_verdicts_is_frozenset():
    assert isinstance(VALID_NRC_VERDICTS, frozenset)


def test_valid_nrc_verdicts_contains_compliant():
    assert "compliant" in VALID_NRC_VERDICTS


def test_valid_nrc_verdicts_contains_non_compliant():
    assert "non_compliant" in VALID_NRC_VERDICTS


def test_valid_nrc_verdicts_contains_no_relevant_negatives():
    assert "no_relevant_negatives" in VALID_NRC_VERDICTS


def test_valid_nrc_verdicts_has_three_values():
    assert len(VALID_NRC_VERDICTS) == 3


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_negative_result_citation_policy():
    assert isinstance(_build(), NegativeResultCitationPolicy)


def test_build_nrc_id_stored():
    assert _build().nrc_id == "NRC-001"


def test_build_claim_id_stored():
    assert _build().claim_id == "CLM-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_cited_gives_compliant():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001", "NRR-002"],
    )
    assert r.policy_verdict == "compliant"


def test_build_no_relevant_gives_no_relevant_negatives():
    r = _build(relevant_nrr_ids=[], cited_nrr_ids=[])
    assert r.policy_verdict == "no_relevant_negatives"


def test_build_uncited_gives_non_compliant():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001"],
    )
    assert r.policy_verdict == "non_compliant"


def test_build_all_relevant_cited_true_when_compliant():
    assert _build().all_relevant_cited is True


def test_build_all_relevant_cited_false_when_non_compliant():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001"],
    )
    assert r.all_relevant_cited is False


def test_build_uncited_count_zero_when_compliant():
    assert _build().uncited_count == 0


def test_build_uncited_count_correct_when_non_compliant():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001"],
    )
    assert r.uncited_count == 1


def test_build_uncited_nrr_ids_correct():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001"],
    )
    assert r.uncited_nrr_ids == ["NRR-002"]


def test_build_uncited_nrr_ids_empty_when_compliant():
    assert _build().uncited_nrr_ids == []


def test_build_no_relevant_uncited_count_zero():
    r = _build(relevant_nrr_ids=[], cited_nrr_ids=[])
    assert r.uncited_count == 0


def test_build_relevant_nrr_ids_stored():
    r = _build(relevant_nrr_ids=["NRR-001"], cited_nrr_ids=["NRR-001"])
    assert "NRR-001" in r.relevant_nrr_ids


def test_build_cited_nrr_ids_stored():
    r = _build(relevant_nrr_ids=["NRR-001"], cited_nrr_ids=["NRR-001"])
    assert "NRR-001" in r.cited_nrr_ids


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_single_relevant_single_cited_compliant():
    r = _build(relevant_nrr_ids=["NRR-010"], cited_nrr_ids=["NRR-010"])
    assert r.policy_verdict == "compliant"


def test_build_many_relevant_none_cited_non_compliant():
    relevant = [f"NRR-{i:03d}" for i in range(1, 6)]
    r = _build(relevant_nrr_ids=relevant, cited_nrr_ids=[])
    assert r.policy_verdict == "non_compliant"
    assert r.uncited_count == 5


def test_build_many_relevant_some_cited_non_compliant():
    relevant = ["NRR-001", "NRR-002", "NRR-003"]
    r = _build(relevant_nrr_ids=relevant, cited_nrr_ids=["NRR-001"])
    assert r.uncited_count == 2


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_nrc_id_prefix():
    with pytest.raises(ValueError, match="NRC-"):
        _build(nrc_id="BAD-001")


def test_validate_rejects_empty_claim_id():
    with pytest.raises(ValueError, match="claim_id"):
        _build(claim_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_relevant_nrr_id_prefix():
    with pytest.raises(ValueError, match="NRR-"):
        _build(relevant_nrr_ids=["BAD-001"], cited_nrr_ids=[])


def test_validate_rejects_bad_cited_nrr_id_prefix():
    with pytest.raises(ValueError, match="NRR-"):
        _build(
            relevant_nrr_ids=["NRR-001"],
            cited_nrr_ids=["BAD-001"],
        )


def test_validate_rejects_cited_not_in_relevant():
    with pytest.raises(ValueError, match="not in relevant_nrr_ids"):
        _build(
            relevant_nrr_ids=["NRR-001"],
            cited_nrr_ids=["NRR-999"],
        )


def test_validate_rejects_uncited_count_mismatch():
    nrc = _build()
    nrc.uncited_count = 99
    with pytest.raises(ValueError, match="uncited_count"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_all_relevant_cited_mismatch():
    nrc = _build()
    nrc.all_relevant_cited = False
    with pytest.raises(ValueError, match="all_relevant_cited"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_invalid_policy_verdict():
    nrc = _build()
    nrc.policy_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="policy_verdict"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_compliant_when_no_relevant():
    nrc = _build(relevant_nrr_ids=[], cited_nrr_ids=[])
    nrc.policy_verdict = "compliant"
    with pytest.raises(ValueError, match="no_relevant_negatives"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_non_compliant_when_all_cited():
    nrc = _build()
    nrc.policy_verdict = "non_compliant"
    with pytest.raises(ValueError, match="compliant"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_dry_lab_only_false():
    nrc = _build()
    nrc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_negative_result_citation_policy(nrc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_nrc_id():
    assert "NRC-001" in format_negative_result_citation_policy(_build())


def test_format_contains_claim_id():
    assert "CLM-001" in format_negative_result_citation_policy(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_negative_result_citation_policy(_build())


def test_format_contains_verdict():
    assert "compliant" in format_negative_result_citation_policy(_build())


def test_format_contains_uncited_nrr_when_non_compliant():
    r = _build(
        relevant_nrr_ids=["NRR-001", "NRR-002"],
        cited_nrr_ids=["NRR-001"],
    )
    assert "NRR-002" in format_negative_result_citation_policy(r)


def test_format_contains_all_relevant_cited():
    assert "True" in format_negative_result_citation_policy(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_negative_result_citation_policy(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_negative_result_citation_policy(_build())


def test_format_is_string():
    assert isinstance(format_negative_result_citation_policy(_build()), str)
