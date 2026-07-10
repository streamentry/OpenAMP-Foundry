import pytest
from src.openamp_foundry.evidence.preprint_evidence_bundle import (
    VALID_BUNDLE_STATUSES,
    VALID_PREPRINT_SERVERS,
    VALID_CLAIM_STRENGTH_TIERS,
    DRY_LAB_ONLY_DISCLAIMER,
    PreprintEvidenceBundle,
    PEBValidationResult,
    validate_preprint_evidence_bundle,
    build_preprint_evidence_bundle,
    format_preprint_evidence_bundle,
)


def _valid_bundle(**kwargs):
    defaults = dict(
        peb_id="PEB-0001",
        run_id="RUN-2026-001",
        candidate_family_id="AMPF-FAM-001",
        srg_id="SRG-0001",
        atr_id="ATR-0001",
        cfc_id="CFC-0001",
        fnr_id="FNR-0001",
        pqg_id="PQG-0001",
        bundle_status="approved",
        preprint_server="bioRxiv",
        claim_strength_tier="preliminary_wet_lab",
        n_candidates_included=10,
        n_confirmed_hits=2,
        artifact_ids=["SRG-0001", "ATR-0001", "CFC-0001", "FNR-0001", "PQG-0001"],
        dry_lab_only_disclaimer=DRY_LAB_ONLY_DISCLAIMER,
        dry_lab_only=True,
        limitations="Single lab, single strain; results not independently replicated.",
        notes="",
        preprint_doi=None,
    )
    defaults.update(kwargs)
    return PreprintEvidenceBundle(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_bundle_statuses_is_frozenset(self):
        assert isinstance(VALID_BUNDLE_STATUSES, frozenset)

    def test_bundle_statuses_count(self):
        assert len(VALID_BUNDLE_STATUSES) == 5

    def test_draft_in_statuses(self):
        assert "draft" in VALID_BUNDLE_STATUSES

    def test_published_in_statuses(self):
        assert "published" in VALID_BUNDLE_STATUSES

    def test_preprint_servers_is_frozenset(self):
        assert isinstance(VALID_PREPRINT_SERVERS, frozenset)

    def test_biorxiv_in_servers(self):
        assert "bioRxiv" in VALID_PREPRINT_SERVERS

    def test_not_submitted_in_servers(self):
        assert "not_submitted" in VALID_PREPRINT_SERVERS

    def test_claim_strength_tiers_is_frozenset(self):
        assert isinstance(VALID_CLAIM_STRENGTH_TIERS, frozenset)

    def test_claim_strength_tiers_count(self):
        assert len(VALID_CLAIM_STRENGTH_TIERS) == 4

    def test_computational_nomination_in_tiers(self):
        assert "computational_nomination" in VALID_CLAIM_STRENGTH_TIERS

    def test_replicated_wet_lab_in_tiers(self):
        assert "replicated_wet_lab" in VALID_CLAIM_STRENGTH_TIERS

    def test_dry_lab_only_disclaimer_is_string(self):
        assert isinstance(DRY_LAB_ONLY_DISCLAIMER, str)

    def test_dry_lab_only_disclaimer_contains_computational(self):
        assert "computational" in DRY_LAB_ONLY_DISCLAIMER

    def test_dry_lab_only_disclaimer_contains_no_biological_proof(self):
        assert "biological proof" in DRY_LAB_ONLY_DISCLAIMER


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestPreprintEvidenceBundleDataclass:
    def test_instantiation(self):
        b = _valid_bundle()
        assert b.peb_id == "PEB-0001"

    def test_dry_lab_only_true(self):
        b = _valid_bundle()
        assert b.dry_lab_only is True

    def test_artifact_ids_list(self):
        b = _valid_bundle()
        assert len(b.artifact_ids) == 5

    def test_preprint_doi_optional(self):
        b = _valid_bundle(preprint_doi=None)
        assert b.preprint_doi is None

    def test_notes_default_empty(self):
        b = _valid_bundle(notes="")
        assert b.notes == ""


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidatePreprintEvidenceBundle:
    def test_valid_bundle_passes(self):
        b = _valid_bundle()
        result = validate_preprint_evidence_bundle(b)
        assert result.valid

    def test_invalid_peb_id_prefix(self):
        b = _valid_bundle(peb_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("peb_id" in v for v in result.violations)

    def test_empty_run_id_blocked(self):
        b = _valid_bundle(run_id="")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_toy_candidate_family_id_blocked(self):
        b = _valid_bundle(candidate_family_id="TOY-FAM-001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_invalid_srg_id_prefix(self):
        b = _valid_bundle(srg_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_atr_id_prefix(self):
        b = _valid_bundle(atr_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_cfc_id_prefix(self):
        b = _valid_bundle(cfc_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_fnr_id_prefix(self):
        b = _valid_bundle(fnr_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_pqg_id_prefix(self):
        b = _valid_bundle(pqg_id="BAD-0001")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_bundle_status_blocked(self):
        b = _valid_bundle(bundle_status="ready")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_preprint_server_blocked(self):
        b = _valid_bundle(preprint_server="Twitter")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_invalid_claim_tier_blocked(self):
        b = _valid_bundle(claim_strength_tier="proven_cure")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_n_candidates_zero_blocked(self):
        b = _valid_bundle(n_candidates_included=0)
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_n_confirmed_hits_negative_blocked(self):
        b = _valid_bundle(n_confirmed_hits=-1)
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_n_confirmed_hits_exceeds_candidates_blocked(self):
        b = _valid_bundle(n_confirmed_hits=11, n_candidates_included=10)
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_empty_artifact_ids_blocked(self):
        b = _valid_bundle(artifact_ids=[])
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_submitted_requires_real_server(self):
        b = _valid_bundle(bundle_status="submitted", preprint_server="not_submitted")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("not_submitted" in v for v in result.violations)

    def test_published_requires_real_server(self):
        b = _valid_bundle(bundle_status="published", preprint_server="not_submitted", preprint_doi="10.1234/test")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_draft_blocks_preprint_doi(self):
        b = _valid_bundle(bundle_status="draft", preprint_doi="10.1234/test")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("draft" in v for v in result.violations)

    def test_published_requires_doi(self):
        b = _valid_bundle(bundle_status="published", preprint_doi=None, preprint_server="bioRxiv")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("preprint_doi" in v for v in result.violations)

    def test_replicated_wet_lab_requires_2_confirmed_hits(self):
        b = _valid_bundle(claim_strength_tier="replicated_wet_lab", n_confirmed_hits=1)
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("replicated_wet_lab" in v for v in result.violations)

    def test_wrong_disclaimer_blocked(self):
        b = _valid_bundle(dry_lab_only_disclaimer="Different disclaimer text here.")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid
        assert any("disclaimer" in v for v in result.violations)

    def test_dry_lab_only_false_blocked(self):
        b = _valid_bundle(dry_lab_only=False)
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_empty_limitations_blocked(self):
        b = _valid_bundle(limitations="")
        result = validate_preprint_evidence_bundle(b)
        assert not result.valid

    def test_published_with_doi_valid(self):
        b = _valid_bundle(
            bundle_status="published",
            preprint_server="bioRxiv",
            preprint_doi="10.1101/2026.07.10.123456",
        )
        result = validate_preprint_evidence_bundle(b)
        assert result.valid

    def test_submitted_with_server_valid(self):
        b = _valid_bundle(bundle_status="submitted", preprint_server="chemRxiv")
        result = validate_preprint_evidence_bundle(b)
        assert result.valid

    def test_replicated_wet_lab_with_2_hits_valid(self):
        b = _valid_bundle(claim_strength_tier="replicated_wet_lab", n_confirmed_hits=2)
        result = validate_preprint_evidence_bundle(b)
        assert result.valid

    def test_computational_nomination_with_0_hits_valid(self):
        b = _valid_bundle(claim_strength_tier="computational_nomination", n_confirmed_hits=0)
        result = validate_preprint_evidence_bundle(b)
        assert result.valid

    def test_draft_without_doi_valid(self):
        b = _valid_bundle(bundle_status="draft", preprint_server="not_submitted", preprint_doi=None)
        result = validate_preprint_evidence_bundle(b)
        assert result.valid


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildPreprintEvidenceBundle:
    def test_build_valid(self):
        b = build_preprint_evidence_bundle(
            peb_id="PEB-0001",
            run_id="RUN-2026-001",
            candidate_family_id="AMPF-FAM-001",
            srg_id="SRG-0001",
            atr_id="ATR-0001",
            cfc_id="CFC-0001",
            fnr_id="FNR-0001",
            pqg_id="PQG-0001",
            bundle_status="approved",
            preprint_server="bioRxiv",
            claim_strength_tier="preliminary_wet_lab",
            n_candidates_included=10,
            n_confirmed_hits=2,
            artifact_ids=["SRG-0001", "ATR-0001"],
            limitations="Single lab, single strain; not independently replicated.",
        )
        assert b.peb_id == "PEB-0001"
        assert b.dry_lab_only is True
        assert b.dry_lab_only_disclaimer == DRY_LAB_ONLY_DISCLAIMER

    def test_build_enforces_canonical_disclaimer(self):
        b = build_preprint_evidence_bundle(
            peb_id="PEB-0002",
            run_id="RUN-2026-002",
            candidate_family_id="AMPF-FAM-002",
            srg_id="SRG-0002",
            atr_id="ATR-0002",
            cfc_id="CFC-0002",
            fnr_id="FNR-0002",
            pqg_id="PQG-0002",
            bundle_status="draft",
            preprint_server="not_submitted",
            claim_strength_tier="computational_nomination",
            n_candidates_included=5,
            n_confirmed_hits=0,
            artifact_ids=["CFC-0002"],
            limitations="Draft bundle; not yet reviewed.",
        )
        assert b.dry_lab_only_disclaimer == DRY_LAB_ONLY_DISCLAIMER

    def test_build_raises_on_toy_family(self):
        with pytest.raises(ValueError):
            build_preprint_evidence_bundle(
                peb_id="PEB-0003",
                run_id="RUN-2026-003",
                candidate_family_id="TOY-FAM-001",
                srg_id="SRG-0003",
                atr_id="ATR-0003",
                cfc_id="CFC-0003",
                fnr_id="FNR-0003",
                pqg_id="PQG-0003",
                bundle_status="draft",
                preprint_server="not_submitted",
                claim_strength_tier="computational_nomination",
                n_candidates_included=5,
                n_confirmed_hits=0,
                artifact_ids=["CFC-0003"],
                limitations="Should fail on TOY- family.",
            )

    def test_build_raises_on_wrong_claim_tier_for_hits(self):
        with pytest.raises(ValueError):
            build_preprint_evidence_bundle(
                peb_id="PEB-0004",
                run_id="RUN-2026-004",
                candidate_family_id="AMPF-FAM-004",
                srg_id="SRG-0004",
                atr_id="ATR-0004",
                cfc_id="CFC-0004",
                fnr_id="FNR-0004",
                pqg_id="PQG-0004",
                bundle_status="approved",
                preprint_server="bioRxiv",
                claim_strength_tier="replicated_wet_lab",
                n_candidates_included=10,
                n_confirmed_hits=1,
                artifact_ids=["SRG-0004"],
                limitations="One hit is not enough for replicated tier.",
            )

    def test_build_published_with_doi(self):
        b = build_preprint_evidence_bundle(
            peb_id="PEB-0005",
            run_id="RUN-2026-005",
            candidate_family_id="AMPF-FAM-005",
            srg_id="SRG-0005",
            atr_id="ATR-0005",
            cfc_id="CFC-0005",
            fnr_id="FNR-0005",
            pqg_id="PQG-0005",
            bundle_status="published",
            preprint_server="bioRxiv",
            claim_strength_tier="replicated_wet_lab",
            n_candidates_included=8,
            n_confirmed_hits=3,
            artifact_ids=["SRG-0005", "ATR-0005", "CFC-0005"],
            limitations="Published preprint; independent replication pending.",
            preprint_doi="10.1101/2026.07.10.123456",
        )
        assert b.bundle_status == "published"
        assert b.preprint_doi == "10.1101/2026.07.10.123456"


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatPreprintEvidenceBundle:
    def _build(self, **kwargs):
        defaults = dict(
            peb_id="PEB-0001",
            run_id="RUN-2026-001",
            candidate_family_id="AMPF-FAM-001",
            srg_id="SRG-0001",
            atr_id="ATR-0001",
            cfc_id="CFC-0001",
            fnr_id="FNR-0001",
            pqg_id="PQG-0001",
            bundle_status="approved",
            preprint_server="bioRxiv",
            claim_strength_tier="preliminary_wet_lab",
            n_candidates_included=10,
            n_confirmed_hits=2,
            artifact_ids=["SRG-0001", "ATR-0001"],
            limitations="Single lab, single strain; not independently replicated.",
        )
        defaults.update(kwargs)
        return build_preprint_evidence_bundle(**defaults)

    def test_format_returns_string(self):
        b = self._build()
        assert isinstance(format_preprint_evidence_bundle(b), str)

    def test_format_contains_peb_id(self):
        b = self._build()
        assert "PEB-0001" in format_preprint_evidence_bundle(b)

    def test_format_contains_run_id(self):
        b = self._build()
        assert "RUN-2026-001" in format_preprint_evidence_bundle(b)

    def test_format_contains_bundle_status(self):
        b = self._build()
        assert "approved" in format_preprint_evidence_bundle(b)

    def test_format_contains_preprint_server(self):
        b = self._build()
        assert "bioRxiv" in format_preprint_evidence_bundle(b)

    def test_format_contains_claim_tier(self):
        b = self._build()
        assert "preliminary_wet_lab" in format_preprint_evidence_bundle(b)

    def test_format_contains_artifact_ids(self):
        b = self._build()
        out = format_preprint_evidence_bundle(b)
        assert "SRG-0001" in out
        assert "ATR-0001" in out
        assert "CFC-0001" in out

    def test_format_contains_disclaimer(self):
        b = self._build()
        assert "computational" in format_preprint_evidence_bundle(b)

    def test_format_contains_dry_lab_only_true(self):
        b = self._build()
        assert "dry_lab_only: True" in format_preprint_evidence_bundle(b)

    def test_format_contains_limitations(self):
        b = self._build()
        assert "Single lab" in format_preprint_evidence_bundle(b)

    def test_format_contains_doi_when_present(self):
        b = self._build(
            bundle_status="published",
            preprint_doi="10.1101/2026.07.10.123456",
        )
        assert "10.1101" in format_preprint_evidence_bundle(b)

    def test_format_omits_doi_when_none(self):
        b = self._build()
        assert "DOI" not in format_preprint_evidence_bundle(b)

    def test_format_multiline(self):
        b = self._build()
        lines = format_preprint_evidence_bundle(b).split("\n")
        assert len(lines) >= 10
