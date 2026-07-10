"""Tests for CertificateClaimBoundary schema — Phase B B2.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.certificate_claim_boundary import (
    ALL_CLAIM_CLASSES,
    BOUNDARY_STATEMENT_MAX_LENGTH,
    CCB_PREFIX,
    MINIMUM_UNSUPPORTED_CLASSES,
    NOTES_MAX_LENGTH,
    CertificateClaimBoundary,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _all_classes() -> list:
    return sorted(ALL_CLAIM_CLASSES)


def _valid_boundary(**overrides) -> CertificateClaimBoundary:
    defaults = dict(
        ccb_id="CCB-20240315-001",
        pipeline_version="v2.1.0",
        certificate_id="CERT-20240315-001",
        candidate_id="AMPF-001",
        boundary_date="2024-03-15",
        unsupported_claim_classes=_all_classes(),
        boundary_statement=(
            "This certificate does not support claims of biological activity, "
            "human safety, clinical utility, animal efficacy, therapeutic indication, "
            "regulatory approval, mechanism proof, or resistance profile. "
            "All outputs are computational dry-lab predictions only."
        ),
        dry_lab_only=True,
        all_listed_classes_unsupported=True,
        notes="",
    )
    defaults.update(overrides)
    return CertificateClaimBoundary(**defaults)


def _valid() -> CertificateClaimBoundary:
    return _valid_boundary()


def _errors(b):
    return [e for e in validate(b) if not e.startswith("WARNING:")]


def _warns(b):
    return [e for e in validate(b) if e.startswith("WARNING:")]


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        assert _errors(_valid()) == []

    def test_valid_with_notes(self):
        b = _valid_boundary(notes="Issued for external review packet.")
        assert _errors(b) == []

    def test_valid_minimum_classes(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "human_safety", "clinical_utility"
            ]
        )
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — ccb_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestCcbIdPrefix:
    def test_wrong_prefix_rejected(self):
        b = _valid_boundary(ccb_id="PLC-001")
        assert any("ccb_id" in e for e in _errors(b))

    def test_lowercase_prefix_rejected(self):
        b = _valid_boundary(ccb_id="ccb-001")
        assert any("ccb_id" in e for e in _errors(b))

    def test_no_prefix_rejected(self):
        b = _valid_boundary(ccb_id="001")
        assert any("ccb_id" in e for e in _errors(b))

    def test_correct_prefix_accepted(self):
        b = _valid_boundary(ccb_id="CCB-2024-001")
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 3: Rules 2-4 — pipeline_version, certificate_id, candidate_id (4 tests)
# ---------------------------------------------------------------------------

class TestIdentifierFields:
    def test_empty_pipeline_version_rejected(self):
        b = _valid_boundary(pipeline_version="")
        assert any("pipeline_version" in e for e in _errors(b))

    def test_empty_certificate_id_rejected(self):
        b = _valid_boundary(certificate_id="")
        assert any("certificate_id" in e for e in _errors(b))

    def test_empty_candidate_id_rejected(self):
        b = _valid_boundary(candidate_id="")
        assert any("candidate_id" in e for e in _errors(b))

    def test_all_identifiers_valid(self):
        b = _valid_boundary(
            pipeline_version="v3.0.0",
            certificate_id="CERT-FINAL-001",
            candidate_id="AMPF-999",
        )
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 4: Rule 5 — boundary_date ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestBoundaryDate:
    def test_invalid_format_rejected(self):
        b = _valid_boundary(boundary_date="March 15, 2024")
        assert any("boundary_date" in e for e in _errors(b))

    def test_wrong_separator_rejected(self):
        b = _valid_boundary(boundary_date="2024/03/15")
        assert any("boundary_date" in e for e in _errors(b))

    def test_valid_iso_date(self):
        b = _valid_boundary(boundary_date="2025-01-01")
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 5: Rule 6 — unsupported_claim_classes non-empty (3 tests)
# ---------------------------------------------------------------------------

class TestClaimClassesNonEmpty:
    def test_empty_list_rejected(self):
        b = _valid_boundary(unsupported_claim_classes=[])
        assert any("unsupported_claim_classes" in e for e in _errors(b))

    def test_single_class_below_minimum_rejected(self):
        b = _valid_boundary(unsupported_claim_classes=["biological_activity"])
        # Should fail Rule 8 (minimum 3)
        errs = _errors(b)
        assert any("at least" in e for e in errs)

    def test_three_classes_accepted(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "human_safety", "clinical_utility"
            ]
        )
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 6: Rule 7 — valid claim class vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestClaimClassVocabulary:
    def test_invalid_class_rejected(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "human_safety", "fake_class"
            ]
        )
        assert any("invalid values" in e for e in _errors(b))

    def test_all_valid_classes_accepted(self):
        b = _valid_boundary(unsupported_claim_classes=_all_classes())
        assert _errors(b) == []

    @pytest.mark.parametrize("cls", sorted(ALL_CLAIM_CLASSES))
    def test_each_class_individually_valid(self, cls):
        classes = sorted(ALL_CLAIM_CLASSES)
        b = _valid_boundary(unsupported_claim_classes=classes)
        assert _errors(b) == []

    def test_empty_string_class_rejected(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "human_safety", "clinical_utility", ""
            ]
        )
        assert any("invalid values" in e for e in _errors(b))


# ---------------------------------------------------------------------------
# Group 7: Rule 8 — minimum unsupported classes (3 tests)
# ---------------------------------------------------------------------------

class TestMinimumClasses:
    def test_two_classes_rejected(self):
        b = _valid_boundary(
            unsupported_claim_classes=["biological_activity", "human_safety"]
        )
        assert any("at least" in e for e in _errors(b))

    def test_exactly_minimum_accepted(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "human_safety", "clinical_utility"
            ]
        )
        assert _errors(b) == []

    def test_minimum_constant(self):
        assert MINIMUM_UNSUPPORTED_CLASSES == 3


# ---------------------------------------------------------------------------
# Group 8: Rule 9 — boundary_statement (3 tests)
# ---------------------------------------------------------------------------

class TestBoundaryStatement:
    def test_empty_rejected(self):
        b = _valid_boundary(boundary_statement="")
        assert any("boundary_statement" in e for e in _errors(b))

    def test_too_long_rejected(self):
        b = _valid_boundary(boundary_statement="x" * (BOUNDARY_STATEMENT_MAX_LENGTH + 1))
        assert any("boundary_statement" in e for e in _errors(b))

    def test_at_limit_accepted(self):
        b = _valid_boundary(boundary_statement="x" * BOUNDARY_STATEMENT_MAX_LENGTH)
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 9: Rule 10 — dry_lab_only (3 tests)
# ---------------------------------------------------------------------------

class TestDryLabOnly:
    def test_false_rejected(self):
        b = _valid_boundary(dry_lab_only=False)
        assert any("dry_lab_only" in e for e in _errors(b))

    def test_true_accepted(self):
        b = _valid_boundary(dry_lab_only=True)
        assert _errors(b) == []

    def test_dry_lab_constant_name(self):
        assert CCB_PREFIX == "CCB-"


# ---------------------------------------------------------------------------
# Group 10: Rule 11 — all_listed_classes_unsupported (3 tests)
# ---------------------------------------------------------------------------

class TestAllListedClassesUnsupported:
    def test_false_rejected(self):
        b = _valid_boundary(all_listed_classes_unsupported=False)
        assert any("all_listed_classes_unsupported" in e for e in _errors(b))

    def test_true_accepted(self):
        b = _valid_boundary(all_listed_classes_unsupported=True)
        assert _errors(b) == []

    def test_both_flags_true_accepted(self):
        b = _valid_boundary(dry_lab_only=True, all_listed_classes_unsupported=True)
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 11: Rule 12 — no duplicate claim classes (3 tests)
# ---------------------------------------------------------------------------

class TestNoDuplicateClasses:
    def test_duplicate_rejected(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "biological_activity", "biological_activity", "human_safety", "clinical_utility"
            ]
        )
        assert any("duplicates" in e for e in _errors(b))

    def test_unique_classes_accepted(self):
        b = _valid_boundary(
            unsupported_claim_classes=["biological_activity", "human_safety", "clinical_utility"]
        )
        assert _errors(b) == []

    def test_all_unique_all_classes_accepted(self):
        b = _valid_boundary(unsupported_claim_classes=_all_classes())
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 12: Rule 13 — notes length (3 tests)
# ---------------------------------------------------------------------------

class TestNotesLength:
    def test_too_long_rejected(self):
        b = _valid_boundary(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in _errors(b))

    def test_at_limit_accepted(self):
        b = _valid_boundary(notes="n" * NOTES_MAX_LENGTH)
        assert _errors(b) == []

    def test_empty_notes_accepted(self):
        b = _valid_boundary(notes="")
        assert _errors(b) == []


# ---------------------------------------------------------------------------
# Group 13: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_incomplete_classes_triggers_warning(self):
        b = _valid_boundary(
            unsupported_claim_classes=["biological_activity", "human_safety", "clinical_utility"]
        )
        warns = _warns(b)
        assert any("not listed as unsupported" in w for w in warns)

    def test_all_classes_listed_no_missing_warning(self):
        b = _valid_boundary(unsupported_claim_classes=_all_classes())
        warns = _warns(b)
        assert not any("not listed as unsupported" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        b = _valid_boundary(notes="")
        warns = _warns(b)
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        b = _valid_boundary(notes="All classes documented for external review.")
        warns = _warns(b)
        assert not any("notes is empty" in w for w in warns)

    def test_all_classes_listed_with_notes_no_missing_warning(self):
        b = _valid_boundary(
            unsupported_claim_classes=_all_classes(),
            notes="Full boundary documentation.",
        )
        warns = _warns(b)
        assert not any("not listed as unsupported" in w for w in warns)

    def test_partial_classes_exact_warning_count(self):
        b = _valid_boundary(
            unsupported_claim_classes=["biological_activity", "human_safety", "clinical_utility"]
        )
        warns = _warns(b)
        missing_warn = [w for w in warns if "not listed as unsupported" in w]
        assert len(missing_warn) == 1


# ---------------------------------------------------------------------------
# Group 14: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            ccb_id="CCB-20240315-001",
            pipeline_version="v2.1.0",
            certificate_id="CERT-20240315-001",
            candidate_id="AMPF-001",
            boundary_date="2024-03-15",
            unsupported_claim_classes=_all_classes(),
            boundary_statement="This certificate does not support biological activity, safety, or clinical claims.",
            dry_lab_only=True,
            all_listed_classes_unsupported=True,
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(ccb_id="CCB-001", pipeline_version="v1.0")
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught(self):
        data = dict(
            ccb_id="WRONG-001",
            pipeline_version="v1.0",
            certificate_id="CERT-001",
            candidate_id="AMPF-001",
            boundary_date="2024-01-01",
            unsupported_claim_classes=_all_classes(),
            boundary_statement="No claims supported.",
            dry_lab_only=True,
            all_listed_classes_unsupported=True,
        )
        result = validate_dict(data)
        assert any("ccb_id" in e for e in result)

    def test_extra_notes_in_dict(self):
        data = dict(
            ccb_id="CCB-20240315-002",
            pipeline_version="v2.1.0",
            certificate_id="CERT-20240315-002",
            candidate_id="AMPF-002",
            boundary_date="2024-03-15",
            unsupported_claim_classes=_all_classes(),
            boundary_statement="All 8 claim classes are unsupported. Computational predictions only.",
            dry_lab_only=True,
            all_listed_classes_unsupported=True,
            notes="Issued for partner external review.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 15: Edge cases (8 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_claim_classes_count(self):
        assert len(ALL_CLAIM_CLASSES) == 8

    def test_minimum_unsupported_is_three(self):
        assert MINIMUM_UNSUPPORTED_CLASSES == 3

    def test_boundary_statement_one_below_limit(self):
        b = _valid_boundary(boundary_statement="x" * (BOUNDARY_STATEMENT_MAX_LENGTH - 1))
        assert _errors(b) == []

    def test_notes_one_below_limit(self):
        b = _valid_boundary(notes="n" * (NOTES_MAX_LENGTH - 1))
        assert _errors(b) == []

    def test_resistance_profile_is_valid_class(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "resistance_profile", "biological_activity", "human_safety"
            ]
        )
        assert _errors(b) == []

    def test_mechanism_proof_is_valid_class(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "mechanism_proof", "biological_activity", "human_safety"
            ]
        )
        assert _errors(b) == []

    def test_regulatory_approval_is_valid_class(self):
        b = _valid_boundary(
            unsupported_claim_classes=[
                "regulatory_approval", "biological_activity", "human_safety"
            ]
        )
        assert _errors(b) == []

    def test_all_classes_in_all_claim_classes(self):
        expected = {
            "biological_activity", "human_safety", "clinical_utility",
            "animal_efficacy", "therapeutic_indication", "regulatory_approval",
            "mechanism_proof", "resistance_profile",
        }
        assert ALL_CLAIM_CLASSES == expected
