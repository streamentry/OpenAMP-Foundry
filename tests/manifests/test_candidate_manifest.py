"""Tests for candidate manifest module."""
from pathlib import Path

import pytest

from openamp_foundry.manifests.candidate_manifest import (
    CandidateManifest,
    make_candidate_manifest,
    validate_candidate_manifest,
    manifest_to_dict,
    manifest_summary,
)


def _valid_manifest() -> CandidateManifest:
    return make_candidate_manifest(
        candidate_id="AMP-001",
        sequence="AKLWKR",
        evidence_level=2,
        scopes=["bacterial_binding"],
        scores={"binding_energy": 0.75},
        uncertainty=0.1,
        source_modules=["membrane_proxy"],
    )


class TestMakeCandidateManifest:
    def test_returns_candidate_manifest(self):
        m = make_candidate_manifest(
            candidate_id="AMP-001",
            sequence="AKLWKR",
            evidence_level=2,
            scopes=["bacterial_binding"],
            scores={"binding_energy": 0.75},
            uncertainty=0.1,
            source_modules=["membrane_proxy"],
        )
        assert isinstance(m, CandidateManifest)

    def test_dry_lab_only_always_true(self):
        m = _valid_manifest()
        assert m.dry_lab_only is True

        m2 = make_candidate_manifest(
            candidate_id="AMP-002",
            sequence="GIGKFLHSAKK",
            evidence_level=1,
            scopes=["anti_fungal"],
            scores={"charge": 3.0},
            uncertainty=0.2,
            source_modules=["charge_scorer"],
        )
        assert m2.dry_lab_only is True


class TestValidateCandidateManifest:
    def test_valid_manifest_returns_empty_list(self):
        m = _valid_manifest()
        errors = validate_candidate_manifest(m)
        assert errors == []

    def test_empty_candidate_id(self):
        m = _valid_manifest()
        m.candidate_id = ""
        errors = validate_candidate_manifest(m)
        assert any("candidate_id" in e for e in errors)

    def test_empty_sequence(self):
        m = _valid_manifest()
        m.sequence = ""
        errors = validate_candidate_manifest(m)
        assert any("sequence" in e for e in errors)

    def test_evidence_level_below_range(self):
        m = _valid_manifest()
        m.evidence_level = 0
        errors = validate_candidate_manifest(m)
        assert any("evidence_level" in e for e in errors)

    def test_evidence_level_above_range(self):
        m = _valid_manifest()
        m.evidence_level = 7
        errors = validate_candidate_manifest(m)
        assert any("evidence_level" in e for e in errors)

    def test_empty_scopes(self):
        m = _valid_manifest()
        m.scopes = []
        errors = validate_candidate_manifest(m)
        assert any("scopes" in e for e in errors)

    def test_uncertainty_below_range(self):
        m = _valid_manifest()
        m.uncertainty = -0.1
        errors = validate_candidate_manifest(m)
        assert any("uncertainty" in e for e in errors)

    def test_uncertainty_above_range(self):
        m = _valid_manifest()
        m.uncertainty = 1.1
        errors = validate_candidate_manifest(m)
        assert any("uncertainty" in e for e in errors)

    def test_empty_source_modules(self):
        m = _valid_manifest()
        m.source_modules = []
        errors = validate_candidate_manifest(m)
        assert any("source_modules" in e for e in errors)

    def test_dry_lab_only_false(self):
        m = _valid_manifest()
        m.dry_lab_only = False
        errors = validate_candidate_manifest(m)
        assert any("dry_lab_only" in e for e in errors)

    def test_invalid_version_format(self):
        m = _valid_manifest()
        m.version = "1.0"
        errors = validate_candidate_manifest(m)
        assert any("version" in e for e in errors)


class TestManifestToDict:
    def test_returns_dict_with_all_fields(self):
        m = _valid_manifest()
        d = manifest_to_dict(m)
        assert isinstance(d, dict)
        assert d["candidate_id"] == "AMP-001"
        assert d["sequence"] == "AKLWKR"
        assert d["evidence_level"] == 2
        assert d["scopes"] == ["bacterial_binding"]
        assert d["scores"] == {"binding_energy": 0.75}
        assert d["uncertainty"] == 0.1
        assert d["source_modules"] == ["membrane_proxy"]
        assert d["calibration_set"] is None
        assert d["safety_flags"] == []
        assert d["provenance_run_id"] is None
        assert d["dry_lab_only"] is True
        assert "version" in d
        assert "created_at" in d
        assert d["notes"] == []


class TestManifestSummary:
    def test_total_correct(self):
        m1 = _valid_manifest()
        m2 = _valid_manifest()
        m2.candidate_id = "AMP-002"
        m2.evidence_level = 3
        summary = manifest_summary([m1, m2])
        assert summary["total"] == 2

    def test_with_safety_flags_correct(self):
        m1 = _valid_manifest()
        m2 = _valid_manifest()
        m2.candidate_id = "AMP-002"
        m2.safety_flags = ["hemolytic_risk"]
        summary = manifest_summary([m1, m2])
        assert summary["with_safety_flags"] == 1

    def test_dry_lab_only_true(self):
        m = _valid_manifest()
        summary = manifest_summary([m])
        assert summary["dry_lab_only"] is True

    def test_by_evidence_level(self):
        m1 = _valid_manifest()
        m2 = _valid_manifest()
        m2.candidate_id = "AMP-002"
        m2.evidence_level = 3
        m3 = _valid_manifest()
        m3.candidate_id = "AMP-003"
        m3.evidence_level = 2
        summary = manifest_summary([m1, m2, m3])
        assert summary["by_evidence_level"]["2"] == 2
        assert summary["by_evidence_level"]["3"] == 1


class TestSchemaFileExists:
    def test_schema_file_exists(self):
        schema_path = Path("schemas/candidate_manifest.schema.json")
        assert schema_path.exists(), (
            f"Schema file not found at {schema_path}"
        )
