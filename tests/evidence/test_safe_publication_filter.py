"""Tests for SPF- safe-publication filter schema."""

import pytest
from openamp_foundry.evidence.safe_publication_filter import (
    SafePublicationFilter,
    VALID_SPF_VERDICTS,
    VALID_SPF_BLOCK_REASONS,
    VALID_REDACTION_TYPES,
    build_safe_publication_filter,
    format_safe_publication_filter,
    validate_safe_publication_filter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        spf_id="SPF-001",
        nrr_id="NRR-001",
        pipeline_version="v1.0",
        dual_use_clear=True,
        sequence_privacy_clear=True,
        informative_as_negative=True,
        blocked_reasons=[],
        redactions_applied=[],
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_safe_publication_filter(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_spf_verdicts_is_frozenset():
    assert isinstance(VALID_SPF_VERDICTS, frozenset)


def test_valid_spf_verdicts_contains_safe_to_publish():
    assert "safe_to_publish" in VALID_SPF_VERDICTS


def test_valid_spf_verdicts_contains_requires_redaction():
    assert "requires_redaction" in VALID_SPF_VERDICTS


def test_valid_spf_verdicts_contains_publication_blocked():
    assert "publication_blocked" in VALID_SPF_VERDICTS


def test_valid_spf_block_reasons_is_frozenset():
    assert isinstance(VALID_SPF_BLOCK_REASONS, frozenset)


def test_valid_spf_block_reasons_contains_dual_use_concern():
    assert "dual_use_concern" in VALID_SPF_BLOCK_REASONS


def test_valid_spf_block_reasons_contains_sequence_privacy_violation():
    assert "sequence_privacy_violation" in VALID_SPF_BLOCK_REASONS


def test_valid_spf_block_reasons_contains_proprietary_candidate_id():
    assert "proprietary_candidate_id_present" in VALID_SPF_BLOCK_REASONS


def test_valid_spf_block_reasons_contains_collaborator_identity():
    assert "collaborator_identity_exposed" in VALID_SPF_BLOCK_REASONS


def test_valid_spf_block_reasons_contains_preliminary_wet_lab():
    assert "preliminary_wet_lab_data_present" in VALID_SPF_BLOCK_REASONS


def test_valid_spf_block_reasons_contains_regulatory_restriction():
    assert "regulatory_restriction" in VALID_SPF_BLOCK_REASONS


def test_valid_redaction_types_is_frozenset():
    assert isinstance(VALID_REDACTION_TYPES, frozenset)


def test_valid_redaction_types_contains_candidate_id_anonymised():
    assert "candidate_id_anonymised" in VALID_REDACTION_TYPES


def test_valid_redaction_types_contains_sequence_truncated():
    assert "sequence_truncated" in VALID_REDACTION_TYPES


def test_valid_redaction_types_contains_batch_id_removed():
    assert "batch_id_removed" in VALID_REDACTION_TYPES


def test_valid_redaction_types_contains_collaborator_name_removed():
    assert "collaborator_name_removed" in VALID_REDACTION_TYPES


def test_valid_redaction_types_contains_score_precision_reduced():
    assert "score_precision_reduced" in VALID_REDACTION_TYPES


# ---------------------------------------------------------------------------
# 2. build happy paths
# ---------------------------------------------------------------------------


def test_build_returns_safe_publication_filter():
    assert isinstance(_build(), SafePublicationFilter)


def test_build_spf_id_stored():
    assert _build().spf_id == "SPF-001"


def test_build_nrr_id_stored():
    assert _build().nrr_id == "NRR-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_clear_gives_safe_to_publish():
    r = _build(dual_use_clear=True, sequence_privacy_clear=True)
    assert r.publication_verdict == "safe_to_publish"


def test_build_dual_use_false_gives_publication_blocked():
    r = _build(dual_use_clear=False, sequence_privacy_clear=True,
               blocked_reasons=["dual_use_concern"])
    assert r.publication_verdict == "publication_blocked"


def test_build_sequence_privacy_false_gives_requires_redaction():
    r = _build(
        dual_use_clear=True,
        sequence_privacy_clear=False,
        redactions_applied=["sequence_truncated"],
    )
    assert r.publication_verdict == "requires_redaction"


def test_build_with_block_reason_gives_publication_blocked():
    r = _build(
        dual_use_clear=False,
        sequence_privacy_clear=True,
        blocked_reasons=["regulatory_restriction"],
    )
    assert r.publication_verdict == "publication_blocked"


def test_build_with_redaction_gives_requires_redaction():
    r = _build(
        dual_use_clear=True,
        sequence_privacy_clear=True,
        redactions_applied=["candidate_id_anonymised"],
    )
    assert r.publication_verdict == "requires_redaction"


def test_build_blocked_reasons_stored():
    r = _build(
        dual_use_clear=False,
        blocked_reasons=["dual_use_concern"],
    )
    assert "dual_use_concern" in r.blocked_reasons


def test_build_redactions_applied_stored():
    r = _build(
        dual_use_clear=True,
        sequence_privacy_clear=False,
        redactions_applied=["sequence_truncated"],
    )
    assert "sequence_truncated" in r.redactions_applied


def test_build_informative_as_negative_true():
    assert _build(informative_as_negative=True).informative_as_negative is True


def test_build_informative_as_negative_false():
    r = _build(informative_as_negative=False)
    assert r.informative_as_negative is False


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_empty_blocked_reasons_default():
    assert _build().blocked_reasons == []


def test_build_empty_redactions_default():
    assert _build().redactions_applied == []


def test_build_multiple_block_reasons():
    r = _build(
        dual_use_clear=False,
        blocked_reasons=["dual_use_concern", "regulatory_restriction"],
    )
    assert len(r.blocked_reasons) == 2


def test_build_multiple_redactions():
    r = _build(
        dual_use_clear=True,
        sequence_privacy_clear=False,
        redactions_applied=["sequence_truncated", "candidate_id_anonymised"],
    )
    assert len(r.redactions_applied) == 2


# ---------------------------------------------------------------------------
# 3. validate rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_spf_id_prefix():
    with pytest.raises(ValueError, match="SPF-"):
        _build(spf_id="BAD-001")


def test_validate_rejects_bad_nrr_id_prefix():
    with pytest.raises(ValueError, match="NRR-"):
        _build(nrr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_publication_verdict():
    spf = _build()
    spf.publication_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="publication_verdict"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_invalid_block_reason():
    with pytest.raises(ValueError, match="block reason"):
        _build(dual_use_clear=False, blocked_reasons=["UNKNOWN_REASON"])


def test_validate_rejects_invalid_redaction_type():
    with pytest.raises(ValueError, match="redaction type"):
        _build(
            dual_use_clear=True,
            sequence_privacy_clear=False,
            redactions_applied=["UNKNOWN_REDACTION"],
        )


def test_validate_rejects_publication_blocked_without_reasons():
    spf = _build()
    spf.publication_verdict = "publication_blocked"
    spf.dual_use_clear = False
    with pytest.raises(ValueError, match="blocked_reasons"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_requires_redaction_without_redactions():
    spf = _build()
    spf.publication_verdict = "requires_redaction"
    spf.sequence_privacy_clear = False
    with pytest.raises(ValueError, match="redactions_applied"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_safe_to_publish_with_dual_use_false():
    spf = _build()
    spf.dual_use_clear = False
    with pytest.raises(ValueError, match="dual_use_clear"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_safe_to_publish_with_privacy_false():
    spf = _build()
    spf.sequence_privacy_clear = False
    with pytest.raises(ValueError, match="sequence_privacy_clear"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_dual_use_false_without_blocked_verdict():
    spf = _build()
    spf.dual_use_clear = False
    spf.publication_verdict = "requires_redaction"
    spf.redactions_applied = ["sequence_truncated"]
    spf.sequence_privacy_clear = False
    with pytest.raises(ValueError, match="publication_blocked"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_dry_lab_only_false():
    spf = _build()
    spf.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_safe_publication_filter(spf)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_spf_id():
    assert "SPF-001" in format_safe_publication_filter(_build())


def test_format_contains_nrr_id():
    assert "NRR-001" in format_safe_publication_filter(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_safe_publication_filter(_build())


def test_format_contains_verdict():
    assert "safe_to_publish" in format_safe_publication_filter(_build())


def test_format_contains_dual_use_clear():
    assert "True" in format_safe_publication_filter(_build())


def test_format_contains_blocked_reason_when_blocked():
    r = _build(dual_use_clear=False, blocked_reasons=["dual_use_concern"])
    assert "dual_use_concern" in format_safe_publication_filter(r)


def test_format_contains_redaction_when_applied():
    r = _build(
        dual_use_clear=True,
        sequence_privacy_clear=False,
        redactions_applied=["sequence_truncated"],
    )
    assert "sequence_truncated" in format_safe_publication_filter(r)


def test_format_contains_limitations():
    assert "dry-lab only" in format_safe_publication_filter(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_safe_publication_filter(_build())


def test_format_is_string():
    assert isinstance(format_safe_publication_filter(_build()), str)
