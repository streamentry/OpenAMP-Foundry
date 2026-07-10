"""Tests for ProofLadderLevelCertificate schema — Phase B B1.

Exactly 63 tests: valid baseline + each validation rule + edge cases + warnings.
"""

from __future__ import annotations

import pytest

from openamp_foundry.evidence.proof_ladder_level_certificate import (
    DRY_LAB_MAX_LEVEL,
    NOTES_MAX_LENGTH,
    PLC_PREFIX,
    UNSUPPORTED_CLAIMS_MAX_LENGTH,
    VALID_EVIDENCE_TYPES,
    VALID_PROOF_LADDER_LEVELS,
    VALID_VERIFIER_TYPES,
    ProofLadderLevelCertificate,
    validate,
    validate_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_plc(**overrides) -> ProofLadderLevelCertificate:
    defaults = dict(
        plc_id="PLC-20240315-001",
        pipeline_version="v2.1.0",
        candidate_id="AMPF-001",
        certificate_id="CERT-20240315-001",
        claimed_level="multi_signal_candidate_evidence",
        evidence_type="dry_lab_only",
        verifier_type="automated_pipeline",
        verification_date="2024-03-15",
        supporting_artifact_ids=["CCS-20240314-001", "BSP-20240314-001"],
        unsupported_claims=(
            "Does not support any claim of biological activity, antimicrobial "
            "efficacy, safety in humans, or clinical utility. No wet-lab data exists."
        ),
        human_review_required=False,
        human_review_completed=False,
        dry_lab_only=True,
        notes="",
    )
    defaults.update(overrides)
    return ProofLadderLevelCertificate(**defaults)


def _valid() -> ProofLadderLevelCertificate:
    return _valid_plc()


def _errors(p):
    return [e for e in validate(p) if not e.startswith("WARNING:")]


def _warns(p):
    return [e for e in validate(p) if e.startswith("WARNING:")]


# ---------------------------------------------------------------------------
# Group 1: Valid baseline (3 tests)
# ---------------------------------------------------------------------------

class TestValidBaseline:
    def test_valid_returns_no_errors(self):
        assert _errors(_valid()) == []

    def test_valid_with_notes(self):
        plc = _valid_plc(notes="Reviewed by pipeline owner.")
        assert _errors(plc) == []

    def test_valid_baseline_triaged_level(self):
        plc = _valid_plc(claimed_level="baseline_triaged")
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 2: Rule 1 — plc_id prefix (4 tests)
# ---------------------------------------------------------------------------

class TestPlcIdPrefix:
    def test_wrong_prefix_rejected(self):
        plc = _valid_plc(plc_id="CIR-001")
        assert any("plc_id" in e for e in _errors(plc))

    def test_lowercase_prefix_rejected(self):
        plc = _valid_plc(plc_id="plc-001")
        assert any("plc_id" in e for e in _errors(plc))

    def test_no_prefix_rejected(self):
        plc = _valid_plc(plc_id="001")
        assert any("plc_id" in e for e in _errors(plc))

    def test_correct_prefix_accepted(self):
        plc = _valid_plc(plc_id="PLC-2024-001")
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 3: Rules 2-4 — pipeline_version, candidate_id, certificate_id (4 tests)
# ---------------------------------------------------------------------------

class TestIdentifierFields:
    def test_empty_pipeline_version_rejected(self):
        plc = _valid_plc(pipeline_version="")
        assert any("pipeline_version" in e for e in _errors(plc))

    def test_empty_candidate_id_rejected(self):
        plc = _valid_plc(candidate_id="")
        assert any("candidate_id" in e for e in _errors(plc))

    def test_empty_certificate_id_rejected(self):
        plc = _valid_plc(certificate_id="")
        assert any("certificate_id" in e for e in _errors(plc))

    def test_all_identifiers_valid(self):
        plc = _valid_plc(
            pipeline_version="v3.0.0",
            candidate_id="AMPF-999",
            certificate_id="CERT-FINAL-001",
        )
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 4: Rule 5 — claimed_level vocabulary (5 tests)
# ---------------------------------------------------------------------------

class TestClaimedLevel:
    def test_invalid_level_rejected(self):
        plc = _valid_plc(claimed_level="biological_proof")
        assert any("claimed_level" in e for e in _errors(plc))

    def test_empty_level_rejected(self):
        plc = _valid_plc(claimed_level="")
        assert any("claimed_level" in e for e in _errors(plc))

    def test_all_dry_lab_levels_accepted(self):
        dry_lab_levels = [
            "valid_input", "reproducible_dry_lab_features",
            "baseline_triaged", "leakage_aware_benchmark",
            "multi_signal_candidate_evidence",
        ]
        for level in dry_lab_levels:
            plc = _valid_plc(claimed_level=level)
            assert _errors(plc) == [], f"Level {level} should be valid for dry_lab_only"

    def test_plc_prefix_constant(self):
        assert PLC_PREFIX == "PLC-"

    def test_dry_lab_max_level_constant(self):
        assert DRY_LAB_MAX_LEVEL == "multi_signal_candidate_evidence"


# ---------------------------------------------------------------------------
# Group 5: Rule 6 — evidence_type vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestEvidenceType:
    def test_invalid_type_rejected(self):
        plc = _valid_plc(evidence_type="magic_evidence")
        assert any("evidence_type" in e for e in _errors(plc))

    def test_empty_rejected(self):
        plc = _valid_plc(evidence_type="")
        assert any("evidence_type" in e for e in _errors(plc))

    @pytest.mark.parametrize("etype", sorted(VALID_EVIDENCE_TYPES))
    def test_all_valid_types_accepted(self, etype):
        extra = {}
        if etype in ("wet_lab_preliminary", "wet_lab_replicated"):
            extra["dry_lab_only"] = False
            extra["claimed_level"] = "baseline_triaged"
        plc = _valid_plc(evidence_type=etype, **extra)
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 6: Rule 7 — verifier_type vocabulary (4 tests)
# ---------------------------------------------------------------------------

class TestVerifierType:
    def test_invalid_verifier_rejected(self):
        plc = _valid_plc(verifier_type="unknown_entity")
        assert any("verifier_type" in e for e in _errors(plc))

    def test_empty_rejected(self):
        plc = _valid_plc(verifier_type="")
        assert any("verifier_type" in e for e in _errors(plc))

    @pytest.mark.parametrize("vtype", sorted(VALID_VERIFIER_TYPES))
    def test_all_valid_verifier_types_accepted(self, vtype):
        plc = _valid_plc(verifier_type=vtype)
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 7: Rule 8 — verification_date ISO format (3 tests)
# ---------------------------------------------------------------------------

class TestVerificationDate:
    def test_invalid_format_rejected(self):
        plc = _valid_plc(verification_date="March 15, 2024")
        assert any("verification_date" in e for e in _errors(plc))

    def test_wrong_separator_rejected(self):
        plc = _valid_plc(verification_date="2024/03/15")
        assert any("verification_date" in e for e in _errors(plc))

    def test_valid_iso_date(self):
        plc = _valid_plc(verification_date="2025-01-01")
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 8: Rule 9 — supporting_artifact_ids non-empty (3 tests)
# ---------------------------------------------------------------------------

class TestSupportingArtifacts:
    def test_empty_list_rejected(self):
        plc = _valid_plc(supporting_artifact_ids=[])
        assert any("supporting_artifact_ids" in e for e in _errors(plc))

    def test_single_artifact_accepted_with_warning(self):
        plc = _valid_plc(supporting_artifact_ids=["CCS-001"])
        assert _errors(plc) == []
        warns = _warns(plc)
        assert any("supporting artifact" in w for w in warns)

    def test_multiple_artifacts_accepted(self):
        plc = _valid_plc(supporting_artifact_ids=["CCS-001", "BSP-001", "CIR-001"])
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 9: Rule 10 — unsupported_claims (4 tests)
# ---------------------------------------------------------------------------

class TestUnsupportedClaims:
    def test_empty_rejected(self):
        plc = _valid_plc(unsupported_claims="")
        assert any("unsupported_claims" in e for e in _errors(plc))

    def test_whitespace_only_rejected(self):
        plc = _valid_plc(unsupported_claims="   ")
        assert any("unsupported_claims" in e for e in _errors(plc))

    def test_too_long_rejected(self):
        plc = _valid_plc(unsupported_claims="x" * (UNSUPPORTED_CLAIMS_MAX_LENGTH + 1))
        assert any("unsupported_claims" in e for e in _errors(plc))

    def test_at_limit_accepted(self):
        plc = _valid_plc(unsupported_claims="x" * UNSUPPORTED_CLAIMS_MAX_LENGTH)
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 10: Rule 11 — dry_lab_only caps level (4 tests)
# ---------------------------------------------------------------------------

class TestDryLabLevelCap:
    def test_dry_lab_only_cannot_claim_expert_review_level(self):
        plc = _valid_plc(
            dry_lab_only=True,
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
        )
        assert any("caps claimed_level" in e for e in _errors(plc))

    def test_dry_lab_only_cannot_claim_wet_lab_level(self):
        plc = _valid_plc(
            dry_lab_only=True,
            claimed_level="initial_qualified_assay_result",
            human_review_required=True,
        )
        assert any("caps claimed_level" in e for e in _errors(plc))

    def test_dry_lab_only_at_max_level_accepted(self):
        plc = _valid_plc(
            dry_lab_only=True,
            claimed_level="multi_signal_candidate_evidence",
        )
        assert _errors(plc) == []

    def test_not_dry_lab_only_can_claim_higher_level(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="wet_lab_preliminary",
            claimed_level="initial_qualified_assay_result",
            human_review_required=True,
            human_review_completed=True,
        )
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 11: Rule 12 — wet_lab levels require human_review_required=True (4 tests)
# ---------------------------------------------------------------------------

class TestHumanReviewRequired:
    def test_expert_review_level_requires_human_review(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=False,
        )
        assert any("human_review_required" in e for e in _errors(plc))

    def test_wet_lab_level_requires_human_review(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="wet_lab_preliminary",
            claimed_level="initial_qualified_assay_result",
            human_review_required=False,
        )
        assert any("human_review_required" in e for e in _errors(plc))

    def test_dry_lab_level_does_not_require_human_review(self):
        plc = _valid_plc(
            claimed_level="multi_signal_candidate_evidence",
            human_review_required=False,
        )
        assert _errors(plc) == []

    def test_expert_review_level_with_human_review_accepted(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
            human_review_completed=True,
        )
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 12: Rule 13 — human_review pending warning (3 tests)
# ---------------------------------------------------------------------------

class TestHumanReviewPending:
    def test_required_but_not_completed_warns(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
            human_review_completed=False,
        )
        warns = _warns(plc)
        assert any("pending human review" in w for w in warns)

    def test_required_and_completed_no_pending_warning(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
            human_review_completed=True,
        )
        warns = _warns(plc)
        assert not any("pending human review" in w for w in warns)

    def test_not_required_and_not_completed_no_warning(self):
        plc = _valid_plc(
            human_review_required=False,
            human_review_completed=False,
        )
        warns = _warns(plc)
        assert not any("pending human review" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 13: Rule 14 — notes length (3 tests)
# ---------------------------------------------------------------------------

class TestNotesLength:
    def test_too_long_rejected(self):
        plc = _valid_plc(notes="n" * (NOTES_MAX_LENGTH + 1))
        assert any("notes" in e for e in _errors(plc))

    def test_at_limit_accepted(self):
        plc = _valid_plc(notes="n" * NOTES_MAX_LENGTH)
        assert _errors(plc) == []

    def test_empty_notes_accepted(self):
        plc = _valid_plc(notes="")
        assert _errors(plc) == []


# ---------------------------------------------------------------------------
# Group 14: Warnings (6 tests)
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_single_artifact_triggers_warning(self):
        plc = _valid_plc(supporting_artifact_ids=["CCS-001"])
        warns = _warns(plc)
        assert any("supporting artifact" in w for w in warns)

    def test_multiple_artifacts_suppresses_warning(self):
        plc = _valid_plc(supporting_artifact_ids=["CCS-001", "BSP-001"])
        warns = _warns(plc)
        assert not any("supporting artifact" in w for w in warns)

    def test_empty_notes_triggers_warning(self):
        plc = _valid_plc(notes="")
        warns = _warns(plc)
        assert any("notes" in w.lower() for w in warns)

    def test_notes_present_suppresses_notes_warning(self):
        plc = _valid_plc(notes="Pipeline automated check on batch 3.")
        warns = _warns(plc)
        assert not any("notes is empty" in w for w in warns)

    def test_pending_human_review_warning(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
            human_review_completed=False,
        )
        warns = _warns(plc)
        assert any("pending human review" in w for w in warns)

    def test_completed_human_review_no_pending_warning(self):
        plc = _valid_plc(
            dry_lab_only=False,
            evidence_type="dry_lab_plus_expert_review",
            claimed_level="expert_reviewed_assay_proposal",
            human_review_required=True,
            human_review_completed=True,
        )
        warns = _warns(plc)
        assert not any("pending human review" in w for w in warns)


# ---------------------------------------------------------------------------
# Group 15: validate_dict (4 tests)
# ---------------------------------------------------------------------------

class TestValidateDict:
    def test_valid_dict_returns_no_errors(self):
        data = dict(
            plc_id="PLC-20240315-001",
            pipeline_version="v2.1.0",
            candidate_id="AMPF-001",
            certificate_id="CERT-20240315-001",
            claimed_level="multi_signal_candidate_evidence",
            evidence_type="dry_lab_only",
            verifier_type="automated_pipeline",
            verification_date="2024-03-15",
            supporting_artifact_ids=["CCS-001", "BSP-001"],
            unsupported_claims="No biological activity claim. No clinical utility.",
            human_review_required=False,
            human_review_completed=False,
            dry_lab_only=True,
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []

    def test_missing_required_field_returns_error(self):
        data = dict(plc_id="PLC-001", pipeline_version="v1.0")
        result = validate_dict(data)
        assert any("Schema construction error" in e for e in result)

    def test_invalid_field_caught_by_dict_validator(self):
        data = dict(
            plc_id="WRONG-001",
            pipeline_version="v1.0",
            candidate_id="AMPF-001",
            certificate_id="CERT-001",
            claimed_level="baseline_triaged",
            evidence_type="dry_lab_only",
            verifier_type="automated_pipeline",
            verification_date="2024-01-01",
            supporting_artifact_ids=["CCS-001", "BSP-001"],
            unsupported_claims="No biological claim.",
            human_review_required=False,
            human_review_completed=False,
            dry_lab_only=True,
        )
        result = validate_dict(data)
        assert any("plc_id" in e for e in result)

    def test_dict_with_notes(self):
        data = dict(
            plc_id="PLC-20240315-002",
            pipeline_version="v2.1.0",
            candidate_id="AMPF-002",
            certificate_id="CERT-20240315-002",
            claimed_level="leakage_aware_benchmark",
            evidence_type="dry_lab_only",
            verifier_type="pipeline_owner",
            verification_date="2024-03-15",
            supporting_artifact_ids=["CCS-001", "CIR-001"],
            unsupported_claims="No wet-lab data. No human safety data.",
            human_review_required=False,
            human_review_completed=False,
            dry_lab_only=True,
            notes="Leakage-aware benchmark confirmed by pipeline owner.",
        )
        errs = [e for e in validate_dict(data) if not e.startswith("WARNING:")]
        assert errs == []


# ---------------------------------------------------------------------------
# Group 16: Edge cases (7 tests)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_dry_lab_levels_are_valid(self):
        for level in VALID_PROOF_LADDER_LEVELS[:5]:
            plc = _valid_plc(claimed_level=level)
            assert _errors(plc) == [], f"Level {level} should be valid"

    def test_all_verifier_types_valid(self):
        for vtype in sorted(VALID_VERIFIER_TYPES):
            plc = _valid_plc(verifier_type=vtype)
            assert _errors(plc) == [], f"Verifier type {vtype} should be valid"

    def test_unsupported_claims_one_below_limit(self):
        plc = _valid_plc(unsupported_claims="u" * (UNSUPPORTED_CLAIMS_MAX_LENGTH - 1))
        assert _errors(plc) == []

    def test_notes_one_below_limit(self):
        plc = _valid_plc(notes="n" * (NOTES_MAX_LENGTH - 1))
        assert _errors(plc) == []

    def test_valid_input_level_accepted(self):
        plc = _valid_plc(claimed_level="valid_input")
        assert _errors(plc) == []

    def test_independent_replication_not_dry_lab(self):
        plc = _valid_plc(
            dry_lab_only=True,
            claimed_level="independent_replication",
            human_review_required=True,
        )
        assert any("caps claimed_level" in e for e in _errors(plc))

    def test_multiple_supporting_artifacts_no_warning(self):
        plc = _valid_plc(
            supporting_artifact_ids=["CCS-001", "BSP-001", "CIR-001", "PCI-001"]
        )
        warns = _warns(plc)
        assert not any("supporting artifact" in w for w in warns)
