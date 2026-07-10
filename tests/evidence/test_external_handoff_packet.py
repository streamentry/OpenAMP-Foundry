"""Tests for EHP- external handoff packet schema."""

import pytest
from openamp_foundry.evidence.external_handoff_packet import (
    ExternalHandoffPacket,
    VALID_EHP_HANDOFF_PURPOSES,
    VALID_EHP_ARTIFACT_TYPES,
    VALID_EHP_VERDICTS,
    SAFETY_CLEARANCE_ARTIFACT_TYPES,
    MINIMUM_ARTIFACTS_FOR_COMPLETE,
    build_external_handoff_packet,
    format_external_handoff_packet,
    validate_external_handoff_packet,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        ehp_id="EHP-001",
        pipeline_version="v1.0",
        candidate_family_id="fam-001",
        handoff_purpose="external_review",
        included_artifact_types=["WHR", "CBR", "SEG"],
        limitations=["No wet-lab partner available."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_external_handoff_packet(**defaults)


def _make_ehp(**kwargs):
    defaults = dict(
        ehp_id="EHP-001",
        pipeline_version="v1.0",
        candidate_family_id="fam-001",
        handoff_purpose="external_review",
        included_artifact_types=["WHR", "CBR", "SEG"],
        n_artifacts_included=3,
        has_safety_clearance=False,
        verdict="partial",
        dry_lab_only=True,
        limitations=["No wet-lab partner available."],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return ExternalHandoffPacket(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (8 tests)
# ---------------------------------------------------------------------------


def test_valid_ehp_handoff_purposes_is_frozenset():
    assert isinstance(VALID_EHP_HANDOFF_PURPOSES, frozenset)


def test_valid_ehp_handoff_purposes_has_five():
    assert len(VALID_EHP_HANDOFF_PURPOSES) == 5


def test_valid_ehp_handoff_purposes_contains_wet_lab_synthesis():
    assert "wet_lab_synthesis" in VALID_EHP_HANDOFF_PURPOSES


def test_valid_ehp_artifact_types_is_frozenset():
    assert isinstance(VALID_EHP_ARTIFACT_TYPES, frozenset)


def test_valid_ehp_artifact_types_has_fifteen():
    assert len(VALID_EHP_ARTIFACT_TYPES) == 15


def test_valid_ehp_artifact_types_contains_psc():
    assert "PSC" in VALID_EHP_ARTIFACT_TYPES


def test_valid_ehp_verdicts_is_frozenset():
    assert isinstance(VALID_EHP_VERDICTS, frozenset)


def test_valid_ehp_verdicts_has_three():
    assert len(VALID_EHP_VERDICTS) == 3


# ---------------------------------------------------------------------------
# 2. Build – happy paths (16 tests)
# ---------------------------------------------------------------------------


def test_build_returns_external_handoff_packet():
    assert isinstance(_build(), ExternalHandoffPacket)


def test_build_ehp_id_stored():
    ehp = _build(ehp_id="EHP-099")
    assert ehp.ehp_id == "EHP-099"


def test_build_pipeline_version_stored():
    ehp = _build(pipeline_version="v2.0")
    assert ehp.pipeline_version == "v2.0"


def test_build_candidate_family_id_stored():
    ehp = _build(candidate_family_id="fam-099")
    assert ehp.candidate_family_id == "fam-099"


def test_build_n_artifacts_included_auto_computed():
    ehp = _build(included_artifact_types=["WHR", "CBR", "SEG"])
    assert ehp.n_artifacts_included == 3


def test_build_has_safety_clearance_true_when_psc_included():
    ehp = _build(included_artifact_types=["WHR", "PSC"])
    assert ehp.has_safety_clearance is True


def test_build_has_safety_clearance_true_when_fnr_included():
    ehp = _build(included_artifact_types=["WHR", "FNR"])
    assert ehp.has_safety_clearance is True


def test_build_has_safety_clearance_false_when_neither_psc_nor_fnr():
    ehp = _build(included_artifact_types=["WHR", "CBR"])
    assert ehp.has_safety_clearance is False


def test_build_verdict_incomplete_when_less_than_two_artifacts():
    ehp = _build(included_artifact_types=["WHR"])
    assert ehp.verdict == "incomplete"


def test_build_verdict_partial_when_two_artifacts():
    ehp = _build(included_artifact_types=["WHR", "CBR"])
    assert ehp.verdict == "partial"


def test_build_verdict_partial_when_three_artifacts():
    ehp = _build(included_artifact_types=["WHR", "CBR", "SEG"])
    assert ehp.verdict == "partial"


def test_build_verdict_complete_when_four_artifacts():
    ehp = _build(included_artifact_types=["WHR", "CBR", "SEG", "CFC"])
    assert ehp.verdict == "complete"


def test_build_verdict_complete_when_five_artifacts():
    ehp = _build(
        included_artifact_types=["WHR", "CBR", "SEG", "CFC", "FNR"]
    )
    assert ehp.verdict == "complete"


def test_build_dry_lab_only_always_true():
    ehp = _build()
    assert ehp.dry_lab_only is True


def test_build_limitations_stored():
    ehp = _build(limitations=["No partner.", "Expensive assay."])
    assert len(ehp.limitations) == 2
    assert "No partner." in ehp.limitations


@pytest.mark.parametrize("purpose", [
    "wet_lab_synthesis",
    "external_review",
    "regulatory_filing",
    "publication_support",
    "collaboration_transfer",
])
def test_build_all_handoff_purposes_accepted(purpose):
    artifacts = ["WHR", "CBR", "PSC"] if purpose == "wet_lab_synthesis" else ["WHR", "CBR"]
    ehp = _build(handoff_purpose=purpose, included_artifact_types=artifacts)
    assert ehp.handoff_purpose == purpose


# ---------------------------------------------------------------------------
# 3. Validate – rejection cases (24 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_ehp_id_prefix():
    with pytest.raises(ValueError, match="EHP-"):
        _build(ehp_id="BAD-001")


def test_validate_rejects_empty_ehp_id():
    with pytest.raises(ValueError, match="EHP-"):
        _build(ehp_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_candidate_family_id():
    with pytest.raises(ValueError):
        _build(candidate_family_id="")


def test_validate_rejects_invalid_handoff_purpose():
    with pytest.raises(ValueError, match="handoff_purpose"):
        _build(handoff_purpose="invalid_purpose")


def test_validate_rejects_invalid_artifact_type():
    with pytest.raises(ValueError, match="artifact type"):
        _build(included_artifact_types=["WHR", "INVALID"])


def test_validate_rejects_duplicate_artifact_type():
    with pytest.raises(ValueError, match="duplicate"):
        _build(included_artifact_types=["WHR", "CBR", "WHR"])


def test_validate_rejects_empty_limitations():
    ehp = _make_ehp()
    ehp.limitations = []
    with pytest.raises(ValueError, match="limitations"):
        validate_external_handoff_packet(ehp)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_dry_lab_only_false():
    ehp = _make_ehp()
    ehp.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_external_handoff_packet(ehp)


def test_validate_rejects_wet_lab_synthesis_without_safety_clearance():
    with pytest.raises(ValueError, match="wet_lab_synthesis"):
        _build(
            handoff_purpose="wet_lab_synthesis",
            included_artifact_types=["WHR", "CBR"],
        )


def test_validate_wet_lab_synthesis_with_psc_succeeds():
    ehp = _build(
        handoff_purpose="wet_lab_synthesis",
        included_artifact_types=["WHR", "CBR", "PSC"],
    )
    assert ehp.has_safety_clearance is True
    assert ehp.handoff_purpose == "wet_lab_synthesis"


def test_validate_wet_lab_synthesis_with_fnr_succeeds():
    ehp = _build(
        handoff_purpose="wet_lab_synthesis",
        included_artifact_types=["WHR", "CBR", "FNR"],
    )
    assert ehp.has_safety_clearance is True
    assert ehp.handoff_purpose == "wet_lab_synthesis"


def test_validate_external_review_without_safety_clearance_succeeds():
    ehp = _build(
        handoff_purpose="external_review",
        included_artifact_types=["WHR", "CBR"],
    )
    assert ehp.has_safety_clearance is False
    assert ehp.handoff_purpose == "external_review"


def test_validate_publication_support_without_safety_clearance_succeeds():
    ehp = _build(
        handoff_purpose="publication_support",
        included_artifact_types=["WHR", "CBR"],
    )
    assert ehp.has_safety_clearance is False
    assert ehp.handoff_purpose == "publication_support"


def test_validate_minimum_artifacts_threshold_three_is_partial():
    ehp = _build(included_artifact_types=["WHR", "CBR", "SEG"])
    assert ehp.verdict == "partial"
    assert ehp.n_artifacts_included < MINIMUM_ARTIFACTS_FOR_COMPLETE


def test_validate_minimum_artifacts_threshold_four_is_complete():
    ehp = _build(included_artifact_types=["WHR", "CBR", "SEG", "CFC"])
    assert ehp.verdict == "complete"
    assert ehp.n_artifacts_included >= MINIMUM_ARTIFACTS_FOR_COMPLETE


def test_validate_verdict_consistency_zero_artifacts():
    ehp = _build(included_artifact_types=[])
    assert ehp.verdict == "incomplete"
    assert ehp.n_artifacts_included == 0


def test_validate_verdict_consistency_two_artifacts_partial():
    ehp = _build(included_artifact_types=["WHR", "CBR"])
    assert ehp.n_artifacts_included == 2
    assert ehp.verdict == "partial"


def test_validate_verdict_consistency_six_artifacts_complete():
    ehp = _build(
        included_artifact_types=["WHR", "CBR", "SEG", "CFC", "FNR", "PSC"]
    )
    assert ehp.n_artifacts_included == 6
    assert ehp.verdict == "complete"


# ---------------------------------------------------------------------------
# 4. Format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_ehp_id():
    assert "EHP-001" in format_external_handoff_packet(_build())


def test_format_contains_handoff_purpose():
    assert "external_review" in format_external_handoff_packet(_build())


def test_format_contains_verdict():
    assert "partial" in format_external_handoff_packet(_build())


def test_format_contains_has_safety_clearance():
    assert "False" in format_external_handoff_packet(_build())


def test_format_contains_n_artifacts_included():
    assert "3" in format_external_handoff_packet(_build())


def test_format_contains_limitation_text():
    result = format_external_handoff_packet(_build())
    assert "Limitation:" in result
    assert "No wet-lab partner available." in result


def test_format_contains_dry_lab_only():
    assert "True" in format_external_handoff_packet(_build())


def test_format_returns_string():
    assert isinstance(format_external_handoff_packet(_build()), str)
