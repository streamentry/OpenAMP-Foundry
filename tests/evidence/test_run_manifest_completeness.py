"""Tests for RMC- run manifest completeness schema."""

import pytest
from openamp_foundry.evidence.run_manifest_completeness import (
    RunManifestCompleteness,
    FieldPresenceRecord,
    REQUIRED_MANIFEST_FIELDS,
    VALID_RMC_VERDICTS,
    PLACEHOLDER_SENTINELS,
    build_run_manifest_completeness,
    format_run_manifest_completeness,
    validate_run_manifest_completeness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


COMPLETE_MANIFEST = {
    "commit_hash": "a1b2c3d4",
    "config_path": "/path/to/config.yaml",
    "config_hash": "cfg_hash_001",
    "input_path": "/path/to/input.fasta",
    "input_hash": "inp_hash_001",
    "random_seed": "42",
    "package_version": "v1.0.0",
    "generation_command": "python run_pipeline.py --config config.yaml",
    "run_timestamp": "2026-07-10T12:00:00Z",
}

LIMITATIONS = ["Dry-lab only, not biological validation."]


def _build(**kwargs):
    defaults = dict(
        rmc_id="RMC-001",
        pipeline_version="v1.0",
        run_id="run-20260710-001",
        manifest_dict=dict(COMPLETE_MANIFEST),
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_run_manifest_completeness(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (10 tests)
# ---------------------------------------------------------------------------


def test_required_manifest_fields_is_tuple():
    assert isinstance(REQUIRED_MANIFEST_FIELDS, tuple)


def test_required_manifest_fields_has_nine():
    assert len(REQUIRED_MANIFEST_FIELDS) == 9


def test_required_manifest_fields_contains_commit_hash():
    assert "commit_hash" in REQUIRED_MANIFEST_FIELDS


def test_required_manifest_fields_contains_config_hash():
    assert "config_hash" in REQUIRED_MANIFEST_FIELDS


def test_required_manifest_fields_contains_input_hash():
    assert "input_hash" in REQUIRED_MANIFEST_FIELDS


def test_valid_rmc_verdicts_is_frozenset():
    assert isinstance(VALID_RMC_VERDICTS, frozenset)


def test_valid_rmc_verdicts_has_three():
    assert len(VALID_RMC_VERDICTS) == 3


def test_placeholder_sentinels_contains_unknown():
    assert "UNKNOWN" in PLACEHOLDER_SENTINELS


def test_placeholder_sentinels_contains_na():
    assert "N/A" in PLACEHOLDER_SENTINELS


def test_placeholder_sentinels_contains_empty_string():
    assert "" in PLACEHOLDER_SENTINELS


# ---------------------------------------------------------------------------
# 2. build – happy paths (20 tests)
# ---------------------------------------------------------------------------


def test_build_returns_run_manifest_completeness():
    assert isinstance(_build(), RunManifestCompleteness)


def test_build_rmc_id_stored():
    assert _build().rmc_id == "RMC-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_run_id_stored():
    assert _build().run_id == "run-20260710-001"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_complete_manifest_verdict_complete():
    assert _build().verdict == "complete"


def test_build_complete_manifest_n_fields_required_9():
    assert _build().n_fields_required == 9


def test_build_complete_manifest_n_fields_present_9():
    assert _build().n_fields_present == 9


def test_build_complete_manifest_n_fields_complete_9():
    assert _build().n_fields_complete == 9


def test_build_complete_manifest_missing_fields_empty():
    assert _build().missing_fields == []


def test_build_complete_manifest_placeholder_fields_empty():
    assert _build().placeholder_fields == []


def test_build_missing_one_field_verdict_incomplete():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    r = _build(manifest_dict=manifest)
    assert r.verdict == "incomplete"


def test_build_missing_one_field_n_fields_present_8():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    r = _build(manifest_dict=manifest)
    assert r.n_fields_present == 8


def test_build_missing_one_field_n_fields_complete_8():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["input_hash"]
    r = _build(manifest_dict=manifest)
    assert r.n_fields_complete == 8


def test_build_missing_one_field_missing_fields_list():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    r = _build(manifest_dict=manifest)
    assert "config_hash" in r.missing_fields


def test_build_placeholder_unknown_verdict_partial():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    r = _build(manifest_dict=manifest)
    assert r.verdict == "partial"


def test_build_placeholder_unknown_n_fields_present_9():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    r = _build(manifest_dict=manifest)
    assert r.n_fields_present == 9


def test_build_placeholder_unknown_n_fields_complete_8():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    r = _build(manifest_dict=manifest)
    assert r.n_fields_complete == 8


def test_build_placeholder_unknown_placeholder_fields():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    r = _build(manifest_dict=manifest)
    assert "input_hash" in r.placeholder_fields


def test_build_value_snippet_truncated_at_40():
    manifest = dict(COMPLETE_MANIFEST)
    long_val = "x" * 100
    manifest["generation_command"] = long_val
    r = _build(manifest_dict=manifest)
    rec = next(f for f in r.field_records if f.field_name == "generation_command")
    assert len(rec.value_snippet) == 40
    assert rec.value_snippet == "x" * 40


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_rmc_id_prefix():
    with pytest.raises(ValueError, match="RMC-"):
        _build(rmc_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_run_id():
    with pytest.raises(ValueError):
        _build(run_id="")


def test_validate_rejects_n_fields_required_not_9():
    rmc = _build()
    rmc.n_fields_required = 5
    with pytest.raises(ValueError, match="n_fields_required"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_n_fields_present_mismatch_higher():
    rmc = _build()
    rmc.n_fields_present = 99
    with pytest.raises(ValueError, match="n_fields_present"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_n_fields_present_mismatch_lower():
    rmc = _build()
    rmc.n_fields_present = 3
    with pytest.raises(ValueError, match="n_fields_present"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_n_fields_complete_mismatch_higher():
    rmc = _build()
    rmc.n_fields_complete = 99
    with pytest.raises(ValueError, match="n_fields_complete"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_n_fields_complete_mismatch_lower():
    rmc = _build()
    rmc.n_fields_complete = 3
    with pytest.raises(ValueError, match="n_fields_complete"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_missing_fields_mismatch():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    rmc = _build(manifest_dict=manifest)
    rmc.missing_fields = []
    with pytest.raises(ValueError, match="missing_fields"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_placeholder_fields_mismatch():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    rmc = _build(manifest_dict=manifest)
    rmc.placeholder_fields = []
    with pytest.raises(ValueError, match="placeholder_fields"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_verdict_complete_to_incomplete():
    rmc = _build()
    rmc.verdict = "incomplete"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_verdict_incomplete_to_complete():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    rmc = _build(manifest_dict=manifest)
    rmc.verdict = "complete"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_verdict_partial_to_complete():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    rmc = _build(manifest_dict=manifest)
    rmc.verdict = "complete"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_verdict_partial_to_incomplete():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    rmc = _build(manifest_dict=manifest)
    rmc.verdict = "incomplete"
    with pytest.raises(ValueError, match="inconsistent"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_verdict_not_in_valid_set():
    rmc = _build()
    rmc.verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="verdict"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_dry_lab_only_false():
    rmc = _build()
    rmc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_run_manifest_completeness(rmc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_rmc_id():
    assert "RMC-001" in format_run_manifest_completeness(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_run_manifest_completeness(_build())


def test_format_contains_run_id():
    assert "run-20260710-001" in format_run_manifest_completeness(_build())


def test_format_contains_verdict():
    assert "complete" in format_run_manifest_completeness(_build())


def test_format_contains_missing_section():
    manifest = dict(COMPLETE_MANIFEST)
    del manifest["config_hash"]
    output = format_run_manifest_completeness(_build(manifest_dict=manifest))
    assert "Missing:" in output
    assert "config_hash" in output


def test_format_contains_placeholder_section():
    manifest = dict(COMPLETE_MANIFEST)
    manifest["input_hash"] = "UNKNOWN"
    output = format_run_manifest_completeness(_build(manifest_dict=manifest))
    assert "Placeholders:" in output
    assert "input_hash" in output


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_run_manifest_completeness(_build())


def test_format_is_string():
    assert isinstance(format_run_manifest_completeness(_build()), str)
