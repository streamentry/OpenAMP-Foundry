"""Tests for CSV- cross-schema linkage validator schema."""

import pytest
from openamp_foundry.evidence.cross_schema_linkage_validator import (
    CrossSchemaLinkageValidator,
    OrphanEntry,
    VALID_LINKAGE_VERDICTS,
    VALID_REFERENCE_SOURCES,
    build_cross_schema_linkage_validator,
    format_cross_schema_linkage_validator,
    validate_cross_schema_linkage_validator,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KNOWN = ["ART-001", "ART-002", "ART-003"]
_REFS_CLEAN = [
    {"artifact_id": "ART-001", "reference_source": "SAT"},
    {"artifact_id": "ART-002", "reference_source": "BEG"},
]
_REFS_WITH_ORPHAN = [
    {"artifact_id": "ART-001", "reference_source": "SAT"},
    {"artifact_id": "ART-999", "reference_source": "BTI"},
]


def _build(**kwargs):
    defaults = dict(
        csv_id="CSV-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        sat_id="SAT-001",
        beg_id="BEG-001",
        bti_id="BTI-001",
        known_artifact_ids=_KNOWN,
        reference_dicts=_REFS_CLEAN,
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_cross_schema_linkage_validator(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_linkage_verdicts_is_frozenset():
    assert isinstance(VALID_LINKAGE_VERDICTS, frozenset)


def test_valid_linkage_verdicts_contains_all_valid():
    assert "all_valid" in VALID_LINKAGE_VERDICTS


def test_valid_linkage_verdicts_contains_orphans_found():
    assert "orphans_found" in VALID_LINKAGE_VERDICTS


def test_valid_linkage_verdicts_contains_no_references():
    assert "no_references" in VALID_LINKAGE_VERDICTS


def test_valid_reference_sources_is_frozenset():
    assert isinstance(VALID_REFERENCE_SOURCES, frozenset)


def test_valid_reference_sources_contains_sat():
    assert "SAT" in VALID_REFERENCE_SOURCES


def test_valid_reference_sources_contains_beg():
    assert "BEG" in VALID_REFERENCE_SOURCES


def test_valid_reference_sources_contains_bti():
    assert "BTI" in VALID_REFERENCE_SOURCES


def test_valid_reference_sources_count():
    assert len(VALID_REFERENCE_SOURCES) == 3


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_cross_schema_linkage_validator():
    assert isinstance(_build(), CrossSchemaLinkageValidator)


def test_build_csv_id_stored():
    assert _build().csv_id == "CSV-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_all_valid_verdict_when_no_orphans():
    r = _build()
    assert r.linkage_verdict == "all_valid"


def test_build_orphans_found_verdict_when_unknown_ref():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    assert r.linkage_verdict == "orphans_found"


def test_build_no_references_verdict_when_empty_refs():
    r = _build(reference_dicts=[])
    assert r.linkage_verdict == "no_references"


def test_build_n_orphans_zero_when_clean():
    assert _build().n_orphans_found == 0


def test_build_n_orphans_one_when_unknown_ref():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    assert r.n_orphans_found == 1


def test_build_n_references_checked_matches_unique_refs():
    r = _build()
    assert r.n_references_checked == len(set(d["artifact_id"] for d in _REFS_CLEAN))


def test_build_referenced_artifact_ids_sorted():
    r = _build()
    assert r.referenced_artifact_ids == sorted(r.referenced_artifact_ids)


def test_build_all_known_artifact_ids_sorted():
    r = _build()
    assert r.all_known_artifact_ids == sorted(r.all_known_artifact_ids)


def test_build_orphan_entries_are_orphan_entry():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    for entry in r.orphan_entries:
        assert isinstance(entry, OrphanEntry)


def test_build_orphan_artifact_id_correct():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    assert r.orphan_entries[0].artifact_id == "ART-999"


def test_build_orphan_reference_source_correct():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    assert r.orphan_entries[0].reference_source == "BTI"


def test_build_no_orphan_when_all_known():
    refs = [{"artifact_id": aid, "reference_source": "SAT"} for aid in _KNOWN]
    r = _build(reference_dicts=refs)
    assert r.orphan_entries == []


def test_build_deduplicates_referenced_ids():
    refs = [
        {"artifact_id": "ART-001", "reference_source": "SAT"},
        {"artifact_id": "ART-001", "reference_source": "BEG"},
    ]
    r = _build(reference_dicts=refs)
    assert r.n_references_checked == 1


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_sat_id_stored():
    assert _build().sat_id == "SAT-001"


def test_build_beg_id_stored():
    assert _build().beg_id == "BEG-001"


def test_build_bti_id_stored():
    assert _build().bti_id == "BTI-001"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_csv_id_prefix():
    with pytest.raises(ValueError, match="CSV-"):
        _build(csv_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_bad_sat_id_prefix():
    with pytest.raises(ValueError, match="SAT-"):
        _build(sat_id="BAD-001")


def test_validate_rejects_bad_beg_id_prefix():
    with pytest.raises(ValueError, match="BEG-"):
        _build(beg_id="BAD-001")


def test_validate_rejects_bad_bti_id_prefix():
    with pytest.raises(ValueError, match="BTI-"):
        _build(bti_id="BAD-001")


def test_validate_rejects_invalid_reference_source():
    refs = [{"artifact_id": "ART-001", "reference_source": "UNKNOWN"}]
    with pytest.raises(ValueError, match="VALID_REFERENCE_SOURCES"):
        _build(reference_dicts=refs)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_csv_id():
    assert "CSV-001" in format_cross_schema_linkage_validator(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_cross_schema_linkage_validator(_build())


def test_format_contains_verdict():
    assert "all_valid" in format_cross_schema_linkage_validator(_build())


def test_format_contains_sat_id():
    assert "SAT-001" in format_cross_schema_linkage_validator(_build())


def test_format_contains_beg_id():
    assert "BEG-001" in format_cross_schema_linkage_validator(_build())


def test_format_contains_bti_id():
    assert "BTI-001" in format_cross_schema_linkage_validator(_build())


def test_format_contains_orphan_id_when_present():
    r = _build(reference_dicts=_REFS_WITH_ORPHAN)
    assert "ART-999" in format_cross_schema_linkage_validator(r)


def test_format_no_orphan_message_when_clean():
    formatted = format_cross_schema_linkage_validator(_build())
    assert "No orphaned references found." in formatted


def test_format_contains_limitations():
    assert "dry-lab only" in format_cross_schema_linkage_validator(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_cross_schema_linkage_validator(_build())


def test_format_is_string():
    assert isinstance(format_cross_schema_linkage_validator(_build()), str)
