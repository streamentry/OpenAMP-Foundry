"""Tests for data license checker."""
from __future__ import annotations

from openamp_foundry.licensing.license_checker import (
    APPROVED_LICENSES,
    BLOCKED_LICENSES,
    RESTRICTED_LICENSES,
    VALID_USE_CONTEXTS,
    DataLicenseDeclaration,
    check_data_license,
    check_license_batch,
)


def _make_decl(
    source_id: str = "test-src",
    source_name: str = "Test Source",
    license_id: str = "CC0-1.0",
    use_context: str = "scoring",
    attribution_required: bool = True,
    commercial_use_allowed: bool = True,
    redistribution_allowed: bool = True,
    modifications_allowed: bool = True,
    human_review_required: bool = False,
    notes: str = "",
    dry_lab_only: bool = True,
) -> DataLicenseDeclaration:
    return DataLicenseDeclaration(
        source_id=source_id,
        source_name=source_name,
        license_id=license_id,
        use_context=use_context,
        attribution_required=attribution_required,
        commercial_use_allowed=commercial_use_allowed,
        redistribution_allowed=redistribution_allowed,
        modifications_allowed=modifications_allowed,
        human_review_required=human_review_required,
        notes=notes,
        dry_lab_only=dry_lab_only,
    )


class TestCheckDataLicense:
    def test_valid_cc0_passes(self):
        decl = _make_decl(license_id="CC0-1.0")
        result = check_data_license(decl)
        assert result.passed is True
        assert result.status == "approved"

    def test_valid_mit_passes(self):
        decl = _make_decl(license_id="MIT")
        result = check_data_license(decl)
        assert result.passed is True
        assert result.status == "approved"

    def test_blocked_unknown_fails(self):
        decl = _make_decl(license_id="unknown")
        result = check_data_license(decl)
        assert result.passed is False
        assert result.status == "blocked"
        assert any("blocked" in e for e in result.errors)

    def test_blocked_unlicensed_fails(self):
        decl = _make_decl(license_id="unlicensed")
        result = check_data_license(decl)
        assert result.passed is False
        assert result.status == "blocked"

    def test_blocked_all_rights_reserved_fails(self):
        decl = _make_decl(license_id="all-rights-reserved")
        result = check_data_license(decl)
        assert result.passed is False
        assert result.status == "blocked"

    def test_restricted_nc_without_human_review_fails(self):
        decl = _make_decl(license_id="CC-BY-NC-4.0", human_review_required=False)
        result = check_data_license(decl)
        assert result.passed is False
        assert result.status == "restricted"
        assert any("human_review_required" in e for e in result.errors)

    def test_restricted_nc_with_human_review_passes(self):
        decl = _make_decl(license_id="CC-BY-NC-4.0", human_review_required=True)
        result = check_data_license(decl)
        assert result.passed is True
        assert result.status == "restricted"

    def test_empty_source_id_fails(self):
        decl = _make_decl(source_id="")
        result = check_data_license(decl)
        assert result.passed is False
        assert any("source_id" in e for e in result.errors)

    def test_empty_source_name_fails(self):
        decl = _make_decl(source_name="")
        result = check_data_license(decl)
        assert result.passed is False
        assert any("source_name" in e for e in result.errors)

    def test_empty_license_id_fails(self):
        decl = _make_decl(license_id="")
        result = check_data_license(decl)
        assert result.passed is False
        assert any("license_id" in e for e in result.errors)

    def test_invalid_use_context_fails(self):
        decl = _make_decl(use_context="invalid_context")
        result = check_data_license(decl)
        assert result.passed is False
        assert any("use_context" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        decl = _make_decl(dry_lab_only=False)
        result = check_data_license(decl)
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)

    def test_publication_without_redistribution_fails(self):
        decl = _make_decl(
            license_id="CC-BY-4.0",
            use_context="publication",
            redistribution_allowed=False,
        )
        result = check_data_license(decl)
        assert result.passed is False
        assert any("redistribution_allowed" in e for e in result.errors)

    def test_unknown_license_not_in_any_list_fails(self):
        decl = _make_decl(license_id="Unlicense")
        result = check_data_license(decl)
        assert result.passed is False
        assert result.status == "unknown_license"
        assert any("not in approved" in e for e in result.errors)


class TestCheckLicenseBatch:
    def test_batch_counts_correct(self):
        decls = [
            _make_decl(source_id="src-1", license_id="CC0-1.0"),
            _make_decl(source_id="src-2", license_id="MIT"),
            _make_decl(source_id="src-3", license_id="unknown"),
            _make_decl(source_id="src-4", license_id="CC-BY-NC-4.0", human_review_required=True),
            _make_decl(source_id="src-5", license_id=""),
        ]
        summary = check_license_batch(decls)
        assert summary["total"] == 5
        assert summary["passed"] == 3  # src-1, src-2, src-4
        assert summary["failed"] == 2  # src-3, src-5
        assert summary["blocked"] == 1  # src-3
        assert summary["any_blocked"] is True
        assert summary["all_passed"] is False

    def test_all_results_have_dry_lab_only(self):
        decls = [
            _make_decl(license_id="CC0-1.0"),
            _make_decl(license_id="MIT"),
            _make_decl(license_id="Apache-2.0"),
        ]
        summary = check_license_batch(decls)
        assert summary["dry_lab_only"] is True
        for r in summary["results"]:
            assert r["dry_lab_only"] is True


class TestConstants:
    def test_approved_licenses_count(self):
        assert len(APPROVED_LICENSES) == 11

    def test_restricted_licenses_count(self):
        assert len(RESTRICTED_LICENSES) == 4

    def test_blocked_licenses_count(self):
        assert len(BLOCKED_LICENSES) == 3

    def test_valid_use_contexts_count(self):
        assert len(VALID_USE_CONTEXTS) == 6
