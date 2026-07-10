"""Tests for SRS- scientific reproducibility seal schema."""

import pytest
from openamp_foundry.evidence.scientific_reproducibility_seal import (
    ScientificReproducibilitySeal,
    VALID_SEAL_STATUSES,
    VALID_REVIEW_LEVELS,
    SCHEMA_HASH_PLACEHOLDER,
    build_scientific_reproducibility_seal,
    format_scientific_reproducibility_seal,
    validate_scientific_reproducibility_seal,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        srs_id="SRS-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        ebm_id="EBM-001",
        prg_id="PRG-001",
        seal_status="sealed",
        review_level="human_reviewed",
        human_reviewed=True,
        sealed_at="2026-07-10T12:00:00Z",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_scientific_reproducibility_seal(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_seal_statuses_is_frozenset():
    assert isinstance(VALID_SEAL_STATUSES, frozenset)


def test_valid_seal_statuses_contains_sealed():
    assert "sealed" in VALID_SEAL_STATUSES


def test_valid_seal_statuses_contains_provisional():
    assert "provisional" in VALID_SEAL_STATUSES


def test_valid_seal_statuses_contains_invalidated():
    assert "invalidated" in VALID_SEAL_STATUSES


def test_valid_review_levels_is_frozenset():
    assert isinstance(VALID_REVIEW_LEVELS, frozenset)


def test_valid_review_levels_contains_human_reviewed():
    assert "human_reviewed" in VALID_REVIEW_LEVELS


def test_valid_review_levels_contains_automated_only():
    assert "automated_only" in VALID_REVIEW_LEVELS


def test_valid_review_levels_contains_not_reviewed():
    assert "not_reviewed" in VALID_REVIEW_LEVELS


def test_schema_hash_placeholder():
    assert SCHEMA_HASH_PLACEHOLDER == "PENDING"


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_scientific_reproducibility_seal():
    assert isinstance(_build(), ScientificReproducibilitySeal)


def test_build_srs_id_stored():
    assert _build().srs_id == "SRS-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_seal_status_stored():
    assert _build().seal_status == "sealed"


def test_build_review_level_stored():
    assert _build().review_level == "human_reviewed"


def test_build_human_reviewed_stored():
    assert _build().human_reviewed is True


def test_build_ebm_id_stored():
    assert _build().ebm_id == "EBM-001"


def test_build_prg_id_stored():
    assert _build().prg_id == "PRG-001"


def test_build_sealed_at_stored():
    assert _build().sealed_at == "2026-07-10T12:00:00Z"


def test_build_schema_hash_defaults_to_pending():
    r = _build()
    assert r.schema_hash == SCHEMA_HASH_PLACEHOLDER


def test_build_custom_schema_hash():
    r = _build(schema_hash="sha256:abc123")
    assert r.schema_hash == "sha256:abc123"


def test_build_provisional_status():
    r = _build(seal_status="provisional", review_level="automated_only")
    assert r.seal_status == "provisional"


def test_build_automated_only_review_level():
    r = _build(seal_status="provisional", review_level="automated_only", human_reviewed=False)
    assert r.review_level == "automated_only"


def test_build_invalidated_status():
    r = _build(seal_status="invalidated", review_level="automated_only", human_reviewed=False)
    assert r.seal_status == "invalidated"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_srs_id_prefix():
    with pytest.raises(ValueError, match="SRS-"):
        _build(srs_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_short_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="x")


def test_validate_rejects_bad_ebm_id_prefix():
    with pytest.raises(ValueError, match="EBM-"):
        _build(ebm_id="BAD-001")


def test_validate_rejects_bad_prg_id_prefix():
    with pytest.raises(ValueError, match="PRG-"):
        _build(prg_id="BAD-001")


def test_validate_rejects_empty_schema_hash():
    with pytest.raises(ValueError):
        _build(schema_hash="")


def test_validate_rejects_invalid_seal_status():
    with pytest.raises(ValueError, match="seal_status"):
        _build(seal_status="UNKNOWN")


def test_validate_rejects_invalid_review_level():
    with pytest.raises(ValueError, match="review_level"):
        _build(review_level="UNKNOWN")


def test_validate_rejects_human_reviewed_false_when_level_is_human_reviewed():
    with pytest.raises(ValueError, match="human_reviewed"):
        _build(review_level="human_reviewed", human_reviewed=False)


def test_validate_rejects_sealed_with_not_reviewed():
    with pytest.raises(ValueError, match="sealed"):
        _build(seal_status="sealed", review_level="not_reviewed", human_reviewed=False)


def test_validate_rejects_empty_sealed_at():
    with pytest.raises(ValueError):
        _build(sealed_at="")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_srs_id():
    assert "SRS-001" in format_scientific_reproducibility_seal(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_scientific_reproducibility_seal(_build())


def test_format_contains_seal_status():
    assert "sealed" in format_scientific_reproducibility_seal(_build())


def test_format_contains_review_level():
    assert "human_reviewed" in format_scientific_reproducibility_seal(_build())


def test_format_contains_ebm_id():
    assert "EBM-001" in format_scientific_reproducibility_seal(_build())


def test_format_contains_prg_id():
    assert "PRG-001" in format_scientific_reproducibility_seal(_build())


def test_format_contains_schema_hash():
    assert "PENDING" in format_scientific_reproducibility_seal(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_scientific_reproducibility_seal(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_scientific_reproducibility_seal(_build())


def test_format_is_string():
    assert isinstance(format_scientific_reproducibility_seal(_build()), str)
