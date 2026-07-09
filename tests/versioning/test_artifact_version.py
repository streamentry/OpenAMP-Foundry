"""Tests for artifact versioning module."""
import pytest

from openamp_foundry.versioning.artifact_version import (
    STABILITY_TIERS,
    ArtifactVersionInfo,
    VERSIONED_ARTIFACTS,
    get_artifact_version,
    list_versioned_artifacts,
    validate_version_format,
    artifact_version_summary,
)


class TestVERSIONED_ARTIFACTS:
    def test_at_least_5_entries(self):
        assert len(VERSIONED_ARTIFACTS) >= 5

    def test_all_versions_valid_format(self):
        for entry in VERSIONED_ARTIFACTS:
            assert validate_version_format(entry.version), (
                f"{entry.artifact_name} has invalid version: {entry.version}"
            )

    def test_all_stability_tiers_valid(self):
        valid_tiers = set(STABILITY_TIERS.keys())
        for entry in VERSIONED_ARTIFACTS:
            assert entry.stability_tier in valid_tiers, (
                f"{entry.artifact_name} has invalid tier: {entry.stability_tier}"
            )

    def test_no_duplicate_artifact_names(self):
        names = [entry.artifact_name for entry in VERSIONED_ARTIFACTS]
        assert len(names) == len(set(names)), "Duplicate artifact_name found"


class TestGetArtifactVersion:
    def test_known_name_returns_entry(self):
        entry = get_artifact_version("candidate")
        assert entry is not None
        assert entry.artifact_name == "candidate"

    def test_unknown_name_returns_none(self):
        entry = get_artifact_version("nonexistent_schema")
        assert entry is None


class TestListVersionedArtifacts:
    def test_no_filter_returns_all(self):
        all_entries = list_versioned_artifacts()
        assert len(all_entries) == len(VERSIONED_ARTIFACTS)

    def test_tier_stable_filters_correctly(self):
        stable = list_versioned_artifacts(tier="stable")
        for entry in stable:
            assert entry.stability_tier == "stable"
        assert len(stable) > 0

    def test_tier_experimental_filters_correctly(self):
        experimental = list_versioned_artifacts(tier="experimental")
        for entry in experimental:
            assert entry.stability_tier == "experimental"


class TestValidateVersionFormat:
    def test_valid_semver(self):
        assert validate_version_format("1.0.0") is True

    def test_missing_patch(self):
        assert validate_version_format("1.0") is False

    def test_non_numeric_components(self):
        assert validate_version_format("a.b.c") is False

    def test_large_numbers(self):
        assert validate_version_format("999.999.999") is True

    def test_leading_zeros(self):
        assert validate_version_format("01.0.0") is True


class TestArtifactVersionSummary:
    def test_dry_lab_only_true(self):
        summary = artifact_version_summary()
        assert summary["dry_lab_only"] is True

    def test_total_correct(self):
        summary = artifact_version_summary()
        assert summary["total"] == len(VERSIONED_ARTIFACTS)

    def test_stable_count_matches(self):
        summary = artifact_version_summary()
        expected_stable = len(list_versioned_artifacts(tier="stable"))
        assert summary["stable_count"] == expected_stable

    def test_experimental_count_matches(self):
        summary = artifact_version_summary()
        expected_exp = len(list_versioned_artifacts(tier="experimental"))
        assert summary["experimental_count"] == expected_exp

    def test_by_tier_sums_to_total(self):
        summary = artifact_version_summary()
        assert sum(summary["by_tier"].values()) == summary["total"]
