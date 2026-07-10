"""Tests for ERP- external review packet schema."""

import pytest
from openamp_foundry.evidence.external_review_packet import (
    ExternalReviewPacket,
    PacketComponent,
    REQUIRED_PACKET_COMPONENTS,
    VALID_PACKET_STATUSES,
    build_external_review_packet,
    format_external_review_packet,
    validate_external_review_packet,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        erp_id="ERP-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        brc_artifact_id="BRC-001",
        eci_artifact_id="ECI-001",
        fet_artifact_id="FET-001",
        ptr_artifact_id="PTR-001",
        srs_artifact_id="SRS-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_external_review_packet(**defaults)


def _build_partial(**kwargs):
    defaults = dict(
        erp_id="ERP-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        brc_artifact_id="BRC-001",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_external_review_packet(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_packet_components_is_tuple():
    assert isinstance(REQUIRED_PACKET_COMPONENTS, tuple)


def test_required_packet_components_contains_brc():
    assert "BRC" in REQUIRED_PACKET_COMPONENTS


def test_required_packet_components_contains_eci():
    assert "ECI" in REQUIRED_PACKET_COMPONENTS


def test_required_packet_components_contains_fet():
    assert "FET" in REQUIRED_PACKET_COMPONENTS


def test_required_packet_components_contains_ptr():
    assert "PTR" in REQUIRED_PACKET_COMPONENTS


def test_required_packet_components_contains_srs():
    assert "SRS" in REQUIRED_PACKET_COMPONENTS


def test_required_packet_components_count():
    assert len(REQUIRED_PACKET_COMPONENTS) == 5


def test_valid_packet_statuses_is_frozenset():
    assert isinstance(VALID_PACKET_STATUSES, frozenset)


def test_valid_packet_statuses_contains_ready():
    assert "ready" in VALID_PACKET_STATUSES


def test_valid_packet_statuses_contains_incomplete():
    assert "incomplete" in VALID_PACKET_STATUSES


def test_valid_packet_statuses_contains_draft():
    assert "draft" in VALID_PACKET_STATUSES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_external_review_packet():
    assert isinstance(_build(), ExternalReviewPacket)


def test_build_erp_id_stored():
    assert _build().erp_id == "ERP-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_ready_when_all_present():
    r = _build()
    assert r.packet_status == "ready"


def test_build_incomplete_when_some_present():
    r = _build_partial()
    assert r.packet_status == "incomplete"


def test_build_draft_when_none_present():
    r = _build_partial(brc_artifact_id="")
    assert r.packet_status == "draft"


def test_build_n_components_required_is_5():
    assert _build().n_components_required == 5


def test_build_n_components_present_5_when_all():
    assert _build().n_components_present == 5


def test_build_n_components_present_1_when_partial():
    r = _build_partial()
    assert r.n_components_present == 1


def test_build_missing_empty_when_all_present():
    assert _build().missing_component_types == []


def test_build_missing_sorted_when_partial():
    r = _build_partial()
    assert r.missing_component_types == sorted(r.missing_component_types)


def test_build_missing_contains_eci_when_absent():
    r = _build_partial()
    assert "ECI" in r.missing_component_types


def test_build_components_are_packet_component():
    for c in _build().components:
        assert isinstance(c, PacketComponent)


def test_build_brc_component_present():
    r = _build()
    brc = next(c for c in r.components if c.component_type == "BRC")
    assert brc.present is True


def test_build_brc_component_absent_when_empty_id():
    r = _build_partial(brc_artifact_id="")
    brc = next(c for c in r.components if c.component_type == "BRC")
    assert brc.present is False


def test_build_srs_artifact_id_stored():
    r = _build()
    srs = next(c for c in r.components if c.component_type == "SRS")
    assert srs.artifact_id == "SRS-001"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_erp_id_prefix():
    with pytest.raises(ValueError, match="ERP-"):
        _build(erp_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_erp_id():
    assert "ERP-001" in format_external_review_packet(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_external_review_packet(_build())


def test_format_contains_status():
    assert "ready" in format_external_review_packet(_build())


def test_format_contains_present_markers():
    assert "[PRESENT]" in format_external_review_packet(_build())


def test_format_contains_missing_markers():
    r = _build_partial()
    assert "[MISSING]" in format_external_review_packet(r)


def test_format_contains_component_types():
    formatted = format_external_review_packet(_build())
    for ct in REQUIRED_PACKET_COMPONENTS:
        assert ct in formatted


def test_format_contains_limitations():
    assert "dry-lab only" in format_external_review_packet(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_external_review_packet(_build())


def test_format_is_string():
    assert isinstance(format_external_review_packet(_build()), str)
