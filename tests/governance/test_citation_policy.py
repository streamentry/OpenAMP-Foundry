"""Tests for citation and reuse policy validation."""
import pytest
from openamp_foundry.governance.citation_policy import (
    VALID_CITATION_TYPES,
    VALID_LICENSE_IDENTIFIERS,
    VALID_REUSE_CLASSES,
    CitationEntry,
    CitationValidationResult,
    validate_citation_dict,
    validate_citation_entry,
)


def _valid_entry(**kwargs) -> CitationEntry:
    defaults = dict(
        artifact_id="OAMP-v0.7.5",
        citation_type="software",
        title="OpenAMP Foundry",
        version="v0.7.5",
        authors=["Open-Problem-Lab"],
        year="2026",
        license_identifier="MIT",
        reuse_class="open",
        url="https://github.com/Open-Problem-Lab/OpenAMP-Foundry",
        bibtex_key="openamp_foundry_2026",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return CitationEntry(**defaults)


class TestValidCitationEntry:
    def test_valid_entry_passes(self):
        result = validate_citation_entry(_valid_entry())
        assert result.passed is True
        assert result.errors == []

    def test_result_has_correct_artifact_id(self):
        result = validate_citation_entry(_valid_entry())
        assert result.artifact_id == "OAMP-v0.7.5"

    def test_result_has_correct_citation_type(self):
        result = validate_citation_entry(_valid_entry())
        assert result.citation_type == "software"

    def test_all_citation_types_accepted(self):
        for ct in VALID_CITATION_TYPES:
            result = validate_citation_entry(_valid_entry(citation_type=ct))
            assert result.passed is True, f"Expected {ct} to pass"

    def test_all_reuse_classes_accepted_except_warnings(self):
        for rc in VALID_REUSE_CLASSES:
            entry = _valid_entry(reuse_class=rc, url="https://example.com")
            result = validate_citation_entry(entry)
            assert result.passed is True, f"Expected {rc} to pass"

    def test_all_license_identifiers_accepted(self):
        for lic in VALID_LICENSE_IDENTIFIERS:
            result = validate_citation_entry(_valid_entry(license_identifier=lic))
            assert result.passed is True, f"Expected {lic} to pass"


class TestInvalidCitationEntry:
    def test_empty_artifact_id_fails(self):
        result = validate_citation_entry(_valid_entry(artifact_id=""))
        assert result.passed is False
        assert any("artifact_id" in e for e in result.errors)

    def test_invalid_citation_type_fails(self):
        result = validate_citation_entry(_valid_entry(citation_type="paper"))
        assert result.passed is False
        assert any("citation_type" in e for e in result.errors)

    def test_empty_title_fails(self):
        result = validate_citation_entry(_valid_entry(title=""))
        assert result.passed is False
        assert any("title" in e for e in result.errors)

    def test_empty_version_fails(self):
        result = validate_citation_entry(_valid_entry(version=""))
        assert result.passed is False
        assert any("version" in e for e in result.errors)

    def test_empty_authors_fails(self):
        result = validate_citation_entry(_valid_entry(authors=[]))
        assert result.passed is False
        assert any("authors" in e for e in result.errors)

    def test_invalid_year_fails(self):
        result = validate_citation_entry(_valid_entry(year="26"))
        assert result.passed is False
        assert any("year" in e for e in result.errors)

    def test_invalid_license_identifier_fails(self):
        result = validate_citation_entry(_valid_entry(license_identifier="GPL-3.0"))
        assert result.passed is False
        assert any("license_identifier" in e for e in result.errors)

    def test_invalid_reuse_class_fails(self):
        result = validate_citation_entry(_valid_entry(reuse_class="free"))
        assert result.passed is False
        assert any("reuse_class" in e for e in result.errors)

    def test_dry_lab_only_false_fails(self):
        result = validate_citation_entry(_valid_entry(dry_lab_only=False))
        assert result.passed is False
        assert any("dry_lab_only" in e for e in result.errors)


class TestCitationWarnings:
    def test_restricted_reuse_warns(self):
        result = validate_citation_entry(_valid_entry(reuse_class="restricted"))
        assert result.passed is True
        assert any("restricted" in w for w in result.warnings)

    def test_contact_required_without_url_warns(self):
        result = validate_citation_entry(
            _valid_entry(reuse_class="contact_required", url="")
        )
        assert result.passed is True
        assert any("url" in w for w in result.warnings)

    def test_empty_bibtex_key_warns(self):
        result = validate_citation_entry(_valid_entry(bibtex_key=""))
        assert result.passed is True
        assert any("bibtex_key" in w for w in result.warnings)


class TestValidateCitationDict:
    def test_valid_dict_passes(self):
        d = {
            "artifact_id": "OAMP-v0.7.5",
            "citation_type": "software",
            "title": "OpenAMP Foundry",
            "version": "v0.7.5",
            "authors": ["Open-Problem-Lab"],
            "year": "2026",
            "license_identifier": "MIT",
            "reuse_class": "open",
        }
        result = validate_citation_dict(d)
        assert result.passed is True

    def test_missing_fields_fails(self):
        result = validate_citation_dict({"artifact_id": "OAMP-v0.7.5"})
        assert result.passed is False
        assert any("Missing" in e for e in result.errors)


class TestConstants:
    def test_valid_citation_types_has_4(self):
        assert len(VALID_CITATION_TYPES) == 4

    def test_valid_reuse_classes_has_4(self):
        assert len(VALID_REUSE_CLASSES) == 4

    def test_valid_license_identifiers_has_5(self):
        assert len(VALID_LICENSE_IDENTIFIERS) == 5

    def test_all_results_dry_lab_only_true(self):
        result = validate_citation_entry(_valid_entry())
        assert result.dry_lab_only is True
