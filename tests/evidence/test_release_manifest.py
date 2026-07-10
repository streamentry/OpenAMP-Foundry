"""Tests for I8 machine-readable release manifest schema."""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.release_manifest import (
    MIN_CANDIDATE_IDS,
    MIN_SCHEMA_VERSION_LENGTH,
    RELEASE_MANIFEST_ID_PREFIX,
    VALID_RELEASE_STATUSES,
    ManifestValidationResult,
    ReleaseManifest,
    format_release_manifest,
    validate_release_manifest,
)


def _make_manifest(**kwargs) -> ReleaseManifest:
    defaults = dict(
        manifest_id="RMF-2026-001",
        release_name="Wave 0.5 External Review Release",
        generated_at="2026-01-01T00:00:00Z",
        pipeline_version="openamp-foundry==0.1.0",
        git_sha="abc1234def5678901234567890123456789abcde",
        schema_version="1.0.0",
        candidate_ids=["CAND-001", "CAND-002"],
        evidence_certificate_ids=["EVC-001", "EVC-002"],
        benchmark_card_ids=["BMC-0001"],
        is_dry_lab_only=True,
        total_candidates=2,
        contact="reviewer@lab.example",
        release_status="under_review",
        notes="First external review release.",
    )
    defaults.update(kwargs)
    return ReleaseManifest(**defaults)


class TestReleaseManifestConstants:
    def test_prefix_starts_with_rmf(self):
        assert RELEASE_MANIFEST_ID_PREFIX == "RMF-"

    def test_dry_lab_only_required(self):
        from openamp_foundry.evidence.release_manifest import DRY_LAB_ONLY_REQUIRED
        assert DRY_LAB_ONLY_REQUIRED is True

    def test_min_candidate_ids(self):
        assert MIN_CANDIDATE_IDS >= 1

    def test_min_schema_version_length(self):
        assert MIN_SCHEMA_VERSION_LENGTH >= 3

    def test_valid_statuses_is_frozenset(self):
        assert isinstance(VALID_RELEASE_STATUSES, frozenset)

    def test_valid_statuses_includes_draft(self):
        assert "draft" in VALID_RELEASE_STATUSES

    def test_valid_statuses_includes_released(self):
        assert "released" in VALID_RELEASE_STATUSES

    def test_valid_statuses_includes_retracted(self):
        assert "retracted" in VALID_RELEASE_STATUSES

    def test_valid_statuses_includes_approved(self):
        assert "approved" in VALID_RELEASE_STATUSES

    def test_valid_statuses_includes_under_review(self):
        assert "under_review" in VALID_RELEASE_STATUSES


class TestReleaseManifestDataclass:
    def test_creates_successfully(self):
        m = _make_manifest()
        assert m.manifest_id == "RMF-2026-001"

    def test_candidate_ids_stored(self):
        m = _make_manifest(candidate_ids=["A", "B", "C"])
        assert m.candidate_ids == ["A", "B", "C"]

    def test_is_dry_lab_only_stored(self):
        m = _make_manifest()
        assert m.is_dry_lab_only is True

    def test_evidence_certificate_ids_stored(self):
        m = _make_manifest(evidence_certificate_ids=["EVC-X"])
        assert m.evidence_certificate_ids == ["EVC-X"]

    def test_benchmark_card_ids_stored(self):
        m = _make_manifest(benchmark_card_ids=["BMC-9999"])
        assert m.benchmark_card_ids == ["BMC-9999"]

    def test_release_status_stored(self):
        m = _make_manifest(release_status="released")
        assert m.release_status == "released"


class TestValidateReleaseManifest:
    def test_valid_manifest_passes(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert result.is_valid is True

    def test_valid_result_no_violations(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert result.violations == []

    def test_result_is_manifest_validation_result(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert isinstance(result, ManifestValidationResult)

    def test_manifest_id_in_result(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert result.manifest_id == "RMF-2026-001"

    def test_summary_nonempty(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert len(result.validation_summary) > 0

    def test_bad_prefix_fails(self):
        m = _make_manifest(manifest_id="BAD-001")
        result = validate_release_manifest(m)
        assert not result.is_valid
        assert any("RMF-" in v for v in result.violations)

    def test_prefix_only_id_fails(self):
        m = _make_manifest(manifest_id="RMF-")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_release_name_fails(self):
        m = _make_manifest(release_name="")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_whitespace_release_name_fails(self):
        m = _make_manifest(release_name="   ")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_generated_at_fails(self):
        m = _make_manifest(generated_at="")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_pipeline_version_fails(self):
        m = _make_manifest(pipeline_version="")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_git_sha_fails(self):
        m = _make_manifest(git_sha="")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_short_schema_version_fails(self):
        m = _make_manifest(schema_version="1")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_schema_version_two_chars_fails(self):
        m = _make_manifest(schema_version="1.")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_schema_version_three_chars_passes(self):
        m = _make_manifest(schema_version="1.0")
        result = validate_release_manifest(m)
        assert result.is_valid

    def test_empty_candidate_ids_fails(self):
        m = _make_manifest(candidate_ids=[], total_candidates=0)
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_mismatched_total_candidates_fails(self):
        m = _make_manifest(candidate_ids=["X"], total_candidates=99)
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_dry_lab_false_fails(self):
        m = _make_manifest(is_dry_lab_only=False)
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_contact_fails(self):
        m = _make_manifest(contact="")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_invalid_release_status_fails(self):
        m = _make_manifest(release_status="published_to_nature")
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_duplicate_candidate_ids_fails(self):
        m = _make_manifest(
            candidate_ids=["CAND-001", "CAND-001"],
            total_candidates=2,
        )
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_duplicate_evidence_ids_fails(self):
        m = _make_manifest(
            evidence_certificate_ids=["EVC-001", "EVC-001"],
        )
        result = validate_release_manifest(m)
        assert not result.is_valid

    def test_empty_evidence_ids_warns(self):
        m = _make_manifest(evidence_certificate_ids=[])
        result = validate_release_manifest(m)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_empty_benchmark_ids_warns(self):
        m = _make_manifest(benchmark_card_ids=[])
        result = validate_release_manifest(m)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_all_release_statuses_pass(self):
        for status in VALID_RELEASE_STATUSES:
            m = _make_manifest(release_status=status)
            result = validate_release_manifest(m)
            assert result.is_valid, f"Status {status!r} should pass"

    def test_draft_status_passes(self):
        m = _make_manifest(release_status="draft")
        result = validate_release_manifest(m)
        assert result.is_valid

    def test_retracted_status_passes(self):
        m = _make_manifest(release_status="retracted")
        result = validate_release_manifest(m)
        assert result.is_valid

    def test_many_candidates_pass(self):
        ids = [f"CAND-{i:04d}" for i in range(50)]
        m = _make_manifest(candidate_ids=ids, total_candidates=50)
        result = validate_release_manifest(m)
        assert result.is_valid

    def test_single_candidate_passes(self):
        m = _make_manifest(candidate_ids=["CAND-001"], total_candidates=1)
        result = validate_release_manifest(m)
        assert result.is_valid

    def test_violations_list_is_list(self):
        m = _make_manifest(manifest_id="BAD-001")
        result = validate_release_manifest(m)
        assert isinstance(result.violations, list)

    def test_warnings_list_is_list(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert isinstance(result.warnings, list)

    def test_valid_summary_contains_candidate_count(self):
        m = _make_manifest()
        result = validate_release_manifest(m)
        assert "2" in result.validation_summary

    def test_invalid_summary_contains_violations_count(self):
        m = _make_manifest(manifest_id="BAD-001", is_dry_lab_only=False)
        result = validate_release_manifest(m)
        assert "violation" in result.validation_summary.lower()


class TestFormatReleaseManifest:
    def setup_method(self):
        self.manifest = _make_manifest()
        self.formatted = format_release_manifest(self.manifest)

    def test_returns_string(self):
        assert isinstance(self.formatted, str)

    def test_contains_manifest_id(self):
        assert "RMF-2026-001" in self.formatted

    def test_contains_release_name(self):
        assert "Wave 0.5" in self.formatted

    def test_contains_status(self):
        assert "under_review" in self.formatted

    def test_contains_pipeline_version(self):
        assert "openamp-foundry" in self.formatted

    def test_contains_git_sha(self):
        assert "abc1234" in self.formatted

    def test_contains_schema_version(self):
        assert "1.0.0" in self.formatted

    def test_contains_dry_lab_flag(self):
        assert "True" in self.formatted

    def test_contains_candidate_count(self):
        assert "2" in self.formatted

    def test_contains_candidate_ids(self):
        assert "CAND-001" in self.formatted
        assert "CAND-002" in self.formatted

    def test_contains_evidence_ids(self):
        assert "EVC-001" in self.formatted

    def test_contains_benchmark_ids(self):
        assert "BMC-0001" in self.formatted

    def test_contains_contact(self):
        assert "reviewer@lab.example" in self.formatted

    def test_contains_notes(self):
        assert "First external review" in self.formatted

    def test_no_evidence_ids_omits_section(self):
        m = _make_manifest(evidence_certificate_ids=[])
        text = format_release_manifest(m)
        assert "Evidence certificates" not in text

    def test_no_benchmark_ids_omits_section(self):
        m = _make_manifest(benchmark_card_ids=[])
        text = format_release_manifest(m)
        assert "Benchmark cards" not in text
