"""Tests for reproducibility manifest schema (Phase L L2)."""

import pytest
from openamp_foundry.evidence.reproducibility_manifest import (
    MINIMUM_DATA_FILES,
    MINIMUM_PACKAGES,
    RECOMMENDED_PACKAGES,
    ReproducibilityManifestEntry,
    ReproducibilityManifestResult,
    validate_reproducibility_manifest,
    validate_reproducibility_manifest_dict,
)


def _valid_entry(**kwargs) -> ReproducibilityManifestEntry:
    defaults = dict(
        manifest_id="RPM-001",
        batch_id="BATCH-001",
        pipeline_version="0.8.5",
        run_date="2026-07-09",
        python_version="3.11.9",
        package_checksums={
            "openamp_foundry": "0.8.4",
            "numpy": "1.26.4",
            "pandas": "2.2.2",
            "scikit-learn": "1.4.2",
            "torch": "2.3.0",
        },
        data_checksums={"data/amp_sequences.fasta": "abc123def456"},
        random_seeds={"ensemble_sampling": 42},
        hardware_summary="Apple M3 Pro, 36 GB RAM",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return ReproducibilityManifestEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_minimum_packages_is_three():
    assert MINIMUM_PACKAGES == 3


def test_minimum_data_files_is_one():
    assert MINIMUM_DATA_FILES == 1


def test_recommended_packages_is_five():
    assert RECOMMENDED_PACKAGES == 5


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.dry_lab_only is True


def test_result_package_count():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.package_count == 5


def test_result_data_file_count():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.data_file_count == 1


def test_result_fields_match():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.manifest_id == "RPM-001"
    assert result.batch_id == "BATCH-001"


def test_valid_with_multiple_data_files():
    result = validate_reproducibility_manifest(
        _valid_entry(
            data_checksums={
                "data/amp_sequences.fasta": "abc123",
                "data/negative_set.fasta": "def456",
            }
        )
    )
    assert result.passed


def test_valid_empty_random_seeds():
    result = validate_reproducibility_manifest(_valid_entry(random_seeds={}))
    assert result.passed


# ── manifest_id validation ────────────────────────────────────────────────────


def test_manifest_id_missing_prefix_fails():
    result = validate_reproducibility_manifest(_valid_entry(manifest_id="001"))
    assert not result.passed
    assert any("RPM-" in e for e in result.errors)


def test_manifest_id_wrong_prefix_fails():
    result = validate_reproducibility_manifest(_valid_entry(manifest_id="BND-001"))
    assert not result.passed


def test_manifest_id_correct_prefix_passes():
    result = validate_reproducibility_manifest(_valid_entry(manifest_id="RPM-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_reproducibility_manifest(_valid_entry(run_date="2026/07/09"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── package_checksums validation ──────────────────────────────────────────────


def test_too_few_packages_fails():
    result = validate_reproducibility_manifest(
        _valid_entry(package_checksums={"openamp_foundry": "0.8.4", "numpy": "1.26.4"})
    )
    assert not result.passed
    assert any("package_checksums" in e for e in result.errors)


def test_exactly_minimum_packages_passes():
    result = validate_reproducibility_manifest(
        _valid_entry(
            package_checksums={
                "openamp_foundry": "0.8.4",
                "numpy": "1.26.4",
                "pandas": "2.2.2",
            }
        )
    )
    assert result.passed


# ── data_checksums validation ─────────────────────────────────────────────────


def test_empty_data_checksums_fails():
    result = validate_reproducibility_manifest(_valid_entry(data_checksums={}))
    assert not result.passed
    assert any("data_checksums" in e for e in result.errors)


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_reproducibility_manifest(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_empty_seeds_warns():
    result = validate_reproducibility_manifest(_valid_entry(random_seeds={}))
    assert result.passed
    assert any("seed" in w.lower() for w in result.warnings)


def test_few_packages_warns():
    result = validate_reproducibility_manifest(
        _valid_entry(
            package_checksums={
                "openamp_foundry": "0.8.4",
                "numpy": "1.26.4",
                "pandas": "2.2.2",
            }
        )
    )
    assert result.passed
    assert any("package" in w for w in result.warnings)


def test_unknown_hardware_warns():
    result = validate_reproducibility_manifest(
        _valid_entry(hardware_summary="unknown hardware platform")
    )
    assert result.passed
    assert any("unknown" in w.lower() for w in result.warnings)


def test_known_hardware_no_warning():
    result = validate_reproducibility_manifest(
        _valid_entry(hardware_summary="Apple M3 Pro, 36 GB RAM")
    )
    assert result.passed
    assert not any("unknown" in w.lower() for w in result.warnings)


def test_full_manifest_no_warnings():
    result = validate_reproducibility_manifest(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        manifest_id="RPM-D01",
        batch_id="BATCH-D01",
        pipeline_version="0.8.5",
        run_date="2026-07-09",
        python_version="3.11.9",
        package_checksums={
            "openamp_foundry": "0.8.4",
            "numpy": "1.26.4",
            "pandas": "2.2.2",
            "scikit-learn": "1.4.2",
            "torch": "2.3.0",
        },
        data_checksums={"data/amp_sequences.fasta": "abc123"},
        random_seeds={"step1": 42},
        hardware_summary="Linux x86_64, 64 GB RAM",
        reviewer="alice",
        dry_lab_only=True,
    )
    result = validate_reproducibility_manifest_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        manifest_id="RPM-D02",
        batch_id="BATCH-D02",
        pipeline_version="0.8.5",
        run_date="2026-07-09",
        python_version="3.11.9",
        package_checksums={"a": "1", "b": "2", "c": "3"},
        data_checksums={"data/a.fasta": "abc"},
        random_seeds={},
        # missing hardware_summary
        reviewer="alice",
    )
    result = validate_reproducibility_manifest_dict(d)
    assert not result.passed
    assert any("hardware_summary" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        manifest_id="RPM-D03",
        batch_id="BATCH-D03",
        pipeline_version="0.8.5",
        run_date="2026-07-09",
        python_version="3.11.9",
        package_checksums={"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"},
        data_checksums={"data/a.fasta": "abc"},
        random_seeds={"step1": 99},
        hardware_summary="Linux x86_64",
        reviewer="alice",
    )
    result = validate_reproducibility_manifest_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
