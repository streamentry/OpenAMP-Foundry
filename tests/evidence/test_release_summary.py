"""Tests for RSM- release-summary schema and generator."""

import pytest
from openamp_foundry.evidence.release_summary import (
    ReleaseSummary,
    RESTRICTED_FIELDS,
    VALID_RSM_RELEASE_SCOPES,
    VALID_RSM_DECISIONS,
    build_release_summary,
    generate_release_summary,
    strip_restricted_fields,
    validate_release_summary,
    format_release_summary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        rsm_id="RSM-001",
        srd_id="SRD-001",
        pipeline_version="v1.0",
        release_scope="academic_collaboration",
        release_decision="authorized",
        candidate_count=5,
        safety_checks_summary=["dual_use_screened", "novelty_claims_bounded"],
        public_notes="dry-lab candidates only",
        limitations_summary="computational predictions, not validated in wet lab",
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_release_summary(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_restricted_fields_is_tuple():
    assert isinstance(RESTRICTED_FIELDS, tuple)


def test_restricted_fields_contains_erp_id():
    assert "erp_id" in RESTRICTED_FIELDS


def test_restricted_fields_contains_rejection_reason():
    assert "rejection_reason" in RESTRICTED_FIELDS


def test_restricted_fields_contains_restrictions():
    assert "restrictions" in RESTRICTED_FIELDS


def test_restricted_fields_contains_candidate_ids():
    assert "candidate_ids" in RESTRICTED_FIELDS


def test_restricted_fields_contains_reviewer_ids():
    assert "reviewer_ids" in RESTRICTED_FIELDS


def test_restricted_fields_contains_raw_sequences():
    assert "raw_sequences" in RESTRICTED_FIELDS


def test_restricted_fields_contains_batch_ids():
    assert "batch_ids" in RESTRICTED_FIELDS


def test_restricted_fields_contains_internal_notes():
    assert "internal_notes" in RESTRICTED_FIELDS


def test_valid_rsm_release_scopes_is_frozenset():
    assert isinstance(VALID_RSM_RELEASE_SCOPES, frozenset)


def test_valid_rsm_release_scopes_contains_academic_collaboration():
    assert "academic_collaboration" in VALID_RSM_RELEASE_SCOPES


def test_valid_rsm_release_scopes_contains_public_preprint():
    assert "public_preprint" in VALID_RSM_RELEASE_SCOPES


def test_valid_rsm_release_scopes_contains_internal_only():
    assert "internal_only" in VALID_RSM_RELEASE_SCOPES


def test_valid_rsm_release_scopes_contains_restricted_partner():
    assert "restricted_partner" in VALID_RSM_RELEASE_SCOPES


def test_valid_rsm_decisions_is_frozenset():
    assert isinstance(VALID_RSM_DECISIONS, frozenset)


def test_valid_rsm_decisions_contains_authorized():
    assert "authorized" in VALID_RSM_DECISIONS


def test_valid_rsm_decisions_contains_rejected():
    assert "rejected" in VALID_RSM_DECISIONS


def test_valid_rsm_decisions_contains_pending_review():
    assert "pending_review" in VALID_RSM_DECISIONS


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_release_summary():
    assert isinstance(_build(), ReleaseSummary)


def test_build_rsm_id_stored():
    assert _build().rsm_id == "RSM-001"


def test_build_srd_id_stored():
    assert _build().srd_id == "SRD-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_release_scope_stored():
    assert _build().release_scope == "academic_collaboration"


def test_build_release_decision_stored():
    assert _build().release_decision == "authorized"


def test_build_candidate_count_stored():
    assert _build().candidate_count == 5


def test_build_safety_checks_summary_stored():
    rsm = _build()
    assert "dual_use_screened" in rsm.safety_checks_summary
    assert "novelty_claims_bounded" in rsm.safety_checks_summary


def test_build_public_notes_stored():
    assert _build().public_notes == "dry-lab candidates only"


def test_build_limitations_summary_stored():
    assert "computational" in _build().limitations_summary


def test_build_restricted_fields_stripped_true():
    assert _build().restricted_fields_stripped is True


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_rejected_decision():
    r = _build(release_decision="rejected")
    assert r.release_decision == "rejected"


def test_build_pending_review_decision():
    r = _build(release_decision="pending_review")
    assert r.release_decision == "pending_review"


def test_build_public_preprint_scope():
    r = _build(release_scope="public_preprint")
    assert r.release_scope == "public_preprint"


def test_build_zero_candidates():
    r = _build(candidate_count=0)
    assert r.candidate_count == 0


def test_build_empty_public_notes_allowed():
    r = _build(public_notes="")
    assert r.public_notes == ""


def test_build_empty_safety_checks_summary_allowed():
    r = _build(safety_checks_summary=[])
    assert r.safety_checks_summary == []


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_rsm_id_prefix():
    with pytest.raises(ValueError, match="RSM-"):
        _build(rsm_id="BAD-001")


def test_validate_rejects_bad_srd_id_prefix():
    with pytest.raises(ValueError, match="SRD-"):
        _build(srd_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_release_scope():
    with pytest.raises(ValueError, match="release_scope"):
        _build(release_scope="UNKNOWN")


def test_validate_rejects_invalid_release_decision():
    with pytest.raises(ValueError, match="release_decision"):
        _build(release_decision="UNKNOWN")


def test_validate_rejects_negative_candidate_count():
    with pytest.raises(ValueError, match="candidate_count"):
        _build(candidate_count=-1)


def test_validate_rejects_restricted_fields_stripped_false():
    rsm = _build()
    rsm.restricted_fields_stripped = False
    with pytest.raises(ValueError, match="restricted_fields_stripped"):
        validate_release_summary(rsm)


def test_validate_rejects_dry_lab_only_false():
    rsm = _build()
    rsm.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_release_summary(rsm)


def test_validate_rejects_empty_limitations_summary():
    with pytest.raises(ValueError, match="limitations_summary"):
        _build(limitations_summary="")


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. strip_restricted_fields
# ---------------------------------------------------------------------------


def test_strip_removes_erp_id():
    source = {"erp_id": "ERP-001", "pipeline_version": "v1.0"}
    result = strip_restricted_fields(source)
    assert "erp_id" not in result


def test_strip_removes_rejection_reason():
    source = {"rejection_reason": "toxicity", "pipeline_version": "v1.0"}
    result = strip_restricted_fields(source)
    assert "rejection_reason" not in result


def test_strip_removes_candidate_ids():
    source = {"candidate_ids": ["C001", "C002"], "candidate_count": 2}
    result = strip_restricted_fields(source)
    assert "candidate_ids" not in result


def test_strip_keeps_non_restricted_fields():
    source = {"pipeline_version": "v1.0", "erp_id": "ERP-001"}
    result = strip_restricted_fields(source)
    assert result["pipeline_version"] == "v1.0"


def test_strip_all_restricted_fields_removed():
    source = {k: "value" for k in RESTRICTED_FIELDS}
    source["pipeline_version"] = "v1.0"
    result = strip_restricted_fields(source)
    for k in RESTRICTED_FIELDS:
        assert k not in result


def test_strip_returns_dict():
    assert isinstance(strip_restricted_fields({}), dict)


def test_strip_does_not_mutate_source():
    source = {"erp_id": "ERP-001", "pipeline_version": "v1.0"}
    strip_restricted_fields(source)
    assert "erp_id" in source


# ---------------------------------------------------------------------------
# 5. generate_release_summary
# ---------------------------------------------------------------------------


def _generate(**kwargs):
    defaults = dict(
        rsm_id="RSM-001",
        srd_id="SRD-001",
        pipeline_version="v1.0",
        release_scope="academic_collaboration",
        release_decision="authorized",
        candidate_count=5,
        safety_checks_summary=["dual_use_screened"],
        limitations_summary="dry-lab only",
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return generate_release_summary(**defaults)


def test_generate_returns_release_summary():
    assert isinstance(_generate(), ReleaseSummary)


def test_generate_restricted_fields_stripped_true():
    assert _generate().restricted_fields_stripped is True


def test_generate_dry_lab_only_true():
    assert _generate().dry_lab_only is True


def test_generate_raises_if_source_fields_has_erp_id():
    with pytest.raises(ValueError, match="erp_id"):
        _generate(source_fields={"erp_id": "ERP-001"})


def test_generate_raises_if_source_fields_has_rejection_reason():
    with pytest.raises(ValueError, match="rejection_reason"):
        _generate(source_fields={"rejection_reason": "toxicity"})


def test_generate_raises_if_source_fields_has_candidate_ids():
    with pytest.raises(ValueError, match="candidate_ids"):
        _generate(source_fields={"candidate_ids": ["C1"]})


def test_generate_raises_if_source_fields_has_raw_sequences():
    with pytest.raises(ValueError, match="raw_sequences"):
        _generate(source_fields={"raw_sequences": ["ACGT"]})


def test_generate_accepts_clean_source_fields():
    rsm = _generate(source_fields={"pipeline_version": "v1.0", "candidate_count": 5})
    assert rsm.candidate_count == 5


def test_generate_no_source_fields_ok():
    rsm = _generate(source_fields=None)
    assert isinstance(rsm, ReleaseSummary)


# ---------------------------------------------------------------------------
# 6. format
# ---------------------------------------------------------------------------


def test_format_contains_rsm_id():
    assert "RSM-001" in format_release_summary(_build())


def test_format_contains_srd_id():
    assert "SRD-001" in format_release_summary(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_release_summary(_build())


def test_format_contains_decision():
    assert "authorized" in format_release_summary(_build())


def test_format_contains_scope():
    assert "academic_collaboration" in format_release_summary(_build())


def test_format_contains_candidate_count():
    assert "5" in format_release_summary(_build())


def test_format_contains_safety_check():
    assert "dual_use_screened" in format_release_summary(_build())


def test_format_contains_limitations():
    assert "computational" in format_release_summary(_build())


def test_format_contains_restricted_fields_stripped():
    assert "True" in format_release_summary(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_release_summary(_build())


def test_format_is_string():
    assert isinstance(format_release_summary(_build()), str)
