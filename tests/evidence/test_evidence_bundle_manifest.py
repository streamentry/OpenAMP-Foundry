"""Tests for EBM- evidence bundle manifest schema."""

import pytest
from openamp_foundry.evidence.evidence_bundle_manifest import (
    EvidenceBundleManifest,
    ManifestEntry,
    VALID_MANIFEST_SCHEMA_TYPES,
    VALID_MANIFEST_STATUSES,
    build_evidence_bundle_manifest,
    format_evidence_bundle_manifest,
    validate_evidence_bundle_manifest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TWO_ENTRIES = [
    {"schema_type": "BSP", "artifact_id": "A1", "description": "batch selection"},
    {"schema_type": "PCC", "artifact_id": "A2", "description": "completeness cert"},
]


def _build(**kwargs):
    defaults = dict(
        ebm_id="EBM-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        entry_dicts=_TWO_ENTRIES,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_evidence_bundle_manifest(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_manifest_schema_types_is_frozenset():
    assert isinstance(VALID_MANIFEST_SCHEMA_TYPES, frozenset)


def test_valid_manifest_schema_types_contains_bsp():
    assert "BSP" in VALID_MANIFEST_SCHEMA_TYPES


def test_valid_manifest_schema_types_contains_pcc():
    assert "PCC" in VALID_MANIFEST_SCHEMA_TYPES


def test_valid_manifest_schema_types_contains_prg():
    assert "PRG" in VALID_MANIFEST_SCHEMA_TYPES


def test_valid_manifest_schema_types_contains_eci():
    assert "ECI" in VALID_MANIFEST_SCHEMA_TYPES


def test_valid_manifest_schema_types_count():
    assert len(VALID_MANIFEST_SCHEMA_TYPES) == 19


def test_valid_manifest_statuses_is_frozenset():
    assert isinstance(VALID_MANIFEST_STATUSES, frozenset)


def test_valid_manifest_statuses_contains_complete():
    assert "complete" in VALID_MANIFEST_STATUSES


def test_valid_manifest_statuses_contains_partial():
    assert "partial" in VALID_MANIFEST_STATUSES


def test_valid_manifest_statuses_contains_empty():
    assert "empty" in VALID_MANIFEST_STATUSES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_evidence_bundle_manifest():
    assert isinstance(_build(), EvidenceBundleManifest)


def test_build_ebm_id_stored():
    assert _build().ebm_id == "EBM-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_entries_matches_input():
    assert _build().n_entries == 2


def test_build_partial_status_when_subset():
    assert _build().manifest_status == "partial"


def test_build_empty_status_when_no_entries():
    r = _build(entry_dicts=[])
    assert r.manifest_status == "empty"


def test_build_schema_types_included_sorted():
    r = _build()
    assert r.schema_types_included == sorted(r.schema_types_included)


def test_build_schema_types_deduplicates():
    entries = [
        {"schema_type": "BSP", "artifact_id": "A1", "description": "d1"},
        {"schema_type": "BSP", "artifact_id": "A2", "description": "d2"},
    ]
    r = _build(entry_dicts=entries)
    assert r.schema_types_included == ["BSP"]
    assert r.n_entries == 2


def test_build_entries_are_manifest_entry():
    for e in _build().entries:
        assert isinstance(e, ManifestEntry)


def test_build_entry_artifact_id_stored():
    r = _build()
    assert r.entries[0].artifact_id == "A1"


def test_build_entry_description_stored():
    r = _build()
    assert r.entries[0].description == "batch selection"


def test_build_empty_description_defaults_to_empty_string():
    entries = [{"schema_type": "BSP", "artifact_id": "A1"}]
    r = _build(entry_dicts=entries)
    assert r.entries[0].description == ""


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_complete_status_when_all_types_present():
    all_entries = [
        {"schema_type": t, "artifact_id": f"ART-{t}", "description": ""}
        for t in VALID_MANIFEST_SCHEMA_TYPES
    ]
    r = _build(entry_dicts=all_entries)
    assert r.manifest_status == "complete"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_ebm_id_prefix():
    with pytest.raises(ValueError, match="EBM-"):
        _build(ebm_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_unknown_schema_type():
    entries = [{"schema_type": "UNKNOWN", "artifact_id": "A1", "description": "x"}]
    with pytest.raises(ValueError, match="VALID_MANIFEST_SCHEMA_TYPES"):
        _build(entry_dicts=entries)


def test_validate_rejects_empty_artifact_id():
    entries = [{"schema_type": "BSP", "artifact_id": "", "description": "x"}]
    with pytest.raises(ValueError, match="artifact_id"):
        _build(entry_dicts=entries)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_ebm_id():
    assert "EBM-001" in format_evidence_bundle_manifest(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_evidence_bundle_manifest(_build())


def test_format_contains_status():
    assert "partial" in format_evidence_bundle_manifest(_build())


def test_format_contains_schema_types():
    formatted = format_evidence_bundle_manifest(_build())
    assert "BSP" in formatted
    assert "PCC" in formatted


def test_format_contains_artifact_ids():
    assert "A1" in format_evidence_bundle_manifest(_build())


def test_format_contains_description():
    assert "batch selection" in format_evidence_bundle_manifest(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_evidence_bundle_manifest(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_evidence_bundle_manifest(_build())


def test_format_is_string():
    assert isinstance(format_evidence_bundle_manifest(_build()), str)
