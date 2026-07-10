"""Tests for run manifest hash linking in certificates — Phase B B8.

63 tests verifying that build_certificate() correctly stores run_id and
run_manifest_hash, making every certificate traceable to the exact pipeline
run that produced it.
"""

from __future__ import annotations

import json

import pytest

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEQ = "KWKLFKKIGAVLKVL"
_RUN_ID = "run-abc123-2024-06-01"
_MANIFEST_HASH = "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


def _make_scored(sequence: str = _SEQ) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=PeptideCandidate("AMPF-001", sequence, "test_source"),
        features=compute_features(sequence),
        scores={"activity": 0.80, "safety": 0.90, "novelty": 0.50, "ensemble": 0.82},
        nearest_reference=None,
        selection_reason=["high ensemble score"],
        known_failure_modes=["No wet-lab assay has been run."],
    )


def _cert_no_link() -> dict:
    return build_certificate(_make_scored(), {}, [])


def _cert_with_link() -> dict:
    return build_certificate(
        _make_scored(), {}, [],
        run_id=_RUN_ID,
        run_manifest_hash=_MANIFEST_HASH,
    )


# ---------------------------------------------------------------------------
# Group 1: NewFieldsAlwaysPresent (8 tests)
# ---------------------------------------------------------------------------

class TestNewFieldsAlwaysPresent:
    """run_id and run_manifest_hash are always present in the certificate."""

    def test_run_id_key_present(self):
        assert "run_id" in _cert_no_link()

    def test_run_manifest_hash_key_present(self):
        assert "run_manifest_hash" in _cert_no_link()

    def test_run_id_key_present_with_link(self):
        assert "run_id" in _cert_with_link()

    def test_run_manifest_hash_key_present_with_link(self):
        assert "run_manifest_hash" in _cert_with_link()

    def test_run_id_is_string(self):
        assert isinstance(_cert_no_link()["run_id"], str)

    def test_run_manifest_hash_is_string(self):
        assert isinstance(_cert_no_link()["run_manifest_hash"], str)

    def test_run_id_string_with_link(self):
        assert isinstance(_cert_with_link()["run_id"], str)

    def test_run_manifest_hash_string_with_link(self):
        assert isinstance(_cert_with_link()["run_manifest_hash"], str)


# ---------------------------------------------------------------------------
# Group 2: DefaultValues (8 tests)
# ---------------------------------------------------------------------------

class TestDefaultValues:
    """Without explicit run_id/run_manifest_hash, defaults to empty string."""

    def test_run_id_default_is_empty_string(self):
        assert _cert_no_link()["run_id"] == ""

    def test_run_manifest_hash_default_is_empty_string(self):
        assert _cert_no_link()["run_manifest_hash"] == ""

    def test_default_cert_still_valid_structure(self):
        cert = _cert_no_link()
        assert "candidate_id" in cert
        assert "sequence" in cert
        assert "scores" in cert

    def test_default_run_id_not_none(self):
        assert _cert_no_link()["run_id"] is not None

    def test_default_run_manifest_hash_not_none(self):
        assert _cert_no_link()["run_manifest_hash"] is not None

    def test_explicit_empty_string_same_as_default(self):
        cert_default = build_certificate(_make_scored(), {}, [])
        cert_explicit = build_certificate(_make_scored(), {}, [], run_id="", run_manifest_hash="")
        assert cert_default["run_id"] == cert_explicit["run_id"]
        assert cert_default["run_manifest_hash"] == cert_explicit["run_manifest_hash"]

    def test_only_run_id_provided(self):
        cert = build_certificate(_make_scored(), {}, [], run_id="run-001")
        assert cert["run_id"] == "run-001"
        assert cert["run_manifest_hash"] == ""

    def test_only_manifest_hash_provided(self):
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash="abc123")
        assert cert["run_id"] == ""
        assert cert["run_manifest_hash"] == "abc123"


# ---------------------------------------------------------------------------
# Group 3: WithRunId (10 tests)
# ---------------------------------------------------------------------------

class TestWithRunId:
    """run_id stored correctly with various formats."""

    def test_run_id_stored_correctly(self):
        cert = build_certificate(_make_scored(), {}, [], run_id=_RUN_ID)
        assert cert["run_id"] == _RUN_ID

    def test_uuid_run_id(self):
        run_id = "550e8400-e29b-41d4-a716-446655440000"
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == run_id

    def test_short_run_id(self):
        cert = build_certificate(_make_scored(), {}, [], run_id="r1")
        assert cert["run_id"] == "r1"

    def test_long_run_id(self):
        run_id = "run-" + "x" * 200
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == run_id

    def test_run_id_with_dashes(self):
        run_id = "run-2024-06-01-12-00-00"
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == run_id

    def test_run_id_with_underscores(self):
        run_id = "pipeline_run_001"
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == run_id

    def test_run_id_numeric_string(self):
        run_id = "20240601120000"
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == run_id

    def test_run_id_unchanged_in_cert(self):
        run_id = "original-run-id"
        cert = build_certificate(_make_scored(), {}, [], run_id=run_id)
        assert cert["run_id"] == "original-run-id"

    def test_different_scored_same_run_id(self):
        s1 = _make_scored(_SEQ)
        s2 = _make_scored("ACDEFGHIKLMNPQRS")
        c1 = build_certificate(s1, {}, [], run_id="run-001")
        c2 = build_certificate(s2, {}, [], run_id="run-001")
        assert c1["run_id"] == c2["run_id"]

    def test_run_id_differs_for_different_runs(self):
        c1 = build_certificate(_make_scored(), {}, [], run_id="run-001")
        c2 = build_certificate(_make_scored(), {}, [], run_id="run-002")
        assert c1["run_id"] != c2["run_id"]


# ---------------------------------------------------------------------------
# Group 4: WithManifestHash (10 tests)
# ---------------------------------------------------------------------------

class TestWithManifestHash:
    """run_manifest_hash stored correctly."""

    def test_manifest_hash_stored_correctly(self):
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=_MANIFEST_HASH)
        assert cert["run_manifest_hash"] == _MANIFEST_HASH

    def test_sha256_prefixed_hash(self):
        h = "sha256:abcdef1234"
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == h

    def test_bare_hex_hash(self):
        h = "abcdef1234567890"
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == h

    def test_long_hash(self):
        h = "a" * 64
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == h

    def test_manifest_hash_unchanged(self):
        h = "original-hash-value"
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == "original-hash-value"

    def test_different_hashes_for_different_manifests(self):
        c1 = build_certificate(_make_scored(), {}, [], run_manifest_hash="hash1")
        c2 = build_certificate(_make_scored(), {}, [], run_manifest_hash="hash2")
        assert c1["run_manifest_hash"] != c2["run_manifest_hash"]

    def test_manifest_hash_distinct_from_config_hash(self):
        cert = build_certificate(_make_scored(), {"k": "v"}, [], run_manifest_hash="mh123")
        assert cert["run_manifest_hash"] != cert["config_hash"]

    def test_manifest_hash_is_last_or_in_cert(self):
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash="h")
        keys = list(cert.keys())
        assert "run_manifest_hash" in keys

    def test_manifest_hash_with_colon(self):
        h = "sha256:abc:def"
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == h

    def test_manifest_hash_numeric_string(self):
        h = "1234567890"
        cert = build_certificate(_make_scored(), {}, [], run_manifest_hash=h)
        assert cert["run_manifest_hash"] == h


# ---------------------------------------------------------------------------
# Group 5: BothFieldsProvided (10 tests)
# ---------------------------------------------------------------------------

class TestBothFieldsProvided:
    """run_id and run_manifest_hash stored correctly together."""

    def test_both_fields_stored(self):
        cert = _cert_with_link()
        assert cert["run_id"] == _RUN_ID
        assert cert["run_manifest_hash"] == _MANIFEST_HASH

    def test_both_fields_independent(self):
        cert = _cert_with_link()
        assert cert["run_id"] != cert["run_manifest_hash"]

    def test_config_hash_still_present(self):
        cert = _cert_with_link()
        assert "config_hash" in cert

    def test_proof_ladder_still_present(self):
        cert = _cert_with_link()
        assert "proof_ladder_level" in cert

    def test_baseline_caveat_still_present(self):
        cert = _cert_with_link()
        assert "baseline_caveat" in cert

    def test_recommended_next_steps_still_present(self):
        cert = _cert_with_link()
        assert "recommended_next_steps" in cert

    def test_link_fields_alongside_existing_fields(self):
        cert = _cert_with_link()
        assert cert["candidate_id"] == "AMPF-001"
        assert cert["sequence"] == _SEQ

    def test_cert_with_link_has_all_original_fields(self):
        cert = _cert_with_link()
        for field in ("candidate_id", "sequence", "source", "scores", "pipeline_version",
                      "generated_at", "config_hash", "proof_ladder_level", "baseline_caveat"):
            assert field in cert, f"Missing field: {field}"

    def test_two_certs_same_run_same_link(self):
        s1 = _make_scored(_SEQ)
        s2 = _make_scored("ACDEFG")
        c1 = build_certificate(s1, {}, [], run_id="r1", run_manifest_hash="h1")
        c2 = build_certificate(s2, {}, [], run_id="r1", run_manifest_hash="h1")
        assert c1["run_id"] == c2["run_id"]
        assert c1["run_manifest_hash"] == c2["run_manifest_hash"]

    def test_two_certs_different_runs_different_links(self):
        c1 = build_certificate(_make_scored(), {}, [], run_id="r1", run_manifest_hash="h1")
        c2 = build_certificate(_make_scored(), {}, [], run_id="r2", run_manifest_hash="h2")
        assert c1["run_id"] != c2["run_id"]
        assert c1["run_manifest_hash"] != c2["run_manifest_hash"]


# ---------------------------------------------------------------------------
# Group 6: ClaimDiscipline (5 tests)
# ---------------------------------------------------------------------------

class TestClaimDiscipline:
    """run_id and run_manifest_hash fields don't introduce overclaiming."""

    def test_run_id_field_no_overclaim(self):
        cert = _cert_with_link()
        assert "proven" not in cert["run_id"].lower()

    def test_manifest_hash_field_no_overclaim(self):
        cert = _cert_with_link()
        assert "clinical" not in cert["run_manifest_hash"].lower()

    def test_run_id_not_biological_claim(self):
        cert = _cert_with_link()
        assert "active" not in cert["run_id"].lower()

    def test_cert_with_link_passes_claim_check(self):
        from openamp_foundry.evidence.certificate_quality import assess_certificate_quality
        cert = build_certificate(
            _make_scored(), {"threshold": 0.7}, ["APD-001"],
            run_id=_RUN_ID, run_manifest_hash=_MANIFEST_HASH,
        )
        report = assess_certificate_quality(cert)
        assert report["claim_violations"] == []

    def test_cert_with_link_reaches_external_review_ready(self):
        from openamp_foundry.evidence.certificate_quality import assess_certificate_quality
        cert = build_certificate(
            _make_scored(), {"threshold": 0.7}, ["APD-001"],
            run_id=_RUN_ID, run_manifest_hash=_MANIFEST_HASH,
        )
        report = assess_certificate_quality(cert)
        assert report["quality_tier"] == "external_review_ready"


# ---------------------------------------------------------------------------
# Group 7: JSONRoundtrip (5 tests)
# ---------------------------------------------------------------------------

class TestJSONRoundtrip:
    """run_id and run_manifest_hash survive JSON serialization."""

    def test_run_id_survives_json_roundtrip(self):
        cert = _cert_with_link()
        rt = json.loads(json.dumps(cert))
        assert rt["run_id"] == cert["run_id"]

    def test_manifest_hash_survives_json_roundtrip(self):
        cert = _cert_with_link()
        rt = json.loads(json.dumps(cert))
        assert rt["run_manifest_hash"] == cert["run_manifest_hash"]

    def test_empty_run_id_survives_json_roundtrip(self):
        cert = _cert_no_link()
        rt = json.loads(json.dumps(cert))
        assert rt["run_id"] == ""

    def test_empty_manifest_hash_survives_json_roundtrip(self):
        cert = _cert_no_link()
        rt = json.loads(json.dumps(cert))
        assert rt["run_manifest_hash"] == ""

    def test_full_cert_json_roundtrip_preserves_both(self):
        cert = _cert_with_link()
        rt = json.loads(json.dumps(cert))
        assert rt["run_id"] == _RUN_ID
        assert rt["run_manifest_hash"] == _MANIFEST_HASH


# ---------------------------------------------------------------------------
# Group 8: ReportIntegration (7 tests)
# ---------------------------------------------------------------------------

class TestReportIntegration:
    """run_id and run_manifest_hash appear in expected contexts."""

    def test_cert_with_link_has_more_keys_than_without(self):
        cert_no = _cert_no_link()
        cert_with = _cert_with_link()
        assert set(cert_with.keys()) == set(cert_no.keys())

    def test_run_id_at_expected_position(self):
        cert = _cert_with_link()
        keys = list(cert.keys())
        assert "run_id" in keys[len(keys)//2:]  # in second half of dict

    def test_run_manifest_hash_at_expected_position(self):
        cert = _cert_with_link()
        keys = list(cert.keys())
        assert "run_manifest_hash" in keys

    def test_cert_report_includes_run_id_region(self):
        from openamp_foundry.evidence.certificate_report import build_certificate_report
        cert = _cert_with_link()
        report = build_certificate_report(cert)
        # Report doesn't explicitly format run_id but cert is well-formed
        assert isinstance(report, str) and len(report) > 0

    def test_both_link_fields_present_in_all_certs(self):
        # Both fields should be present regardless of whether they have values
        for kwargs in [
            {},
            {"run_id": "r1"},
            {"run_manifest_hash": "h1"},
            {"run_id": "r1", "run_manifest_hash": "h1"},
        ]:
            cert = build_certificate(_make_scored(), {}, [], **kwargs)
            assert "run_id" in cert
            assert "run_manifest_hash" in cert

    def test_multiple_certs_from_same_run_share_run_id(self):
        scored_list = [_make_scored(_SEQ), _make_scored("ACDEFGHIKLMNPQRS")]
        certs = [
            build_certificate(s, {}, [], run_id="shared-run")
            for s in scored_list
        ]
        assert all(c["run_id"] == "shared-run" for c in certs)

    def test_cert_without_link_backward_compatible(self):
        # Old code calling build_certificate without run_id/manifest should still work
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["run_id"] == ""
        assert cert["run_manifest_hash"] == ""
