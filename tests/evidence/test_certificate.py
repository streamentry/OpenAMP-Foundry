"""Tests for evidence/certificate.py — build_certificate content and structure."""
from __future__ import annotations

import re

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate

_CANDIDATE = PeptideCandidate("AMPF-001", "KWKLFKKIGAVLKVL", "test_source")
_FEATURES = compute_features(_CANDIDATE.sequence)
_SCORES = {
    "activity": 0.80,
    "safety": 0.90,
    "synthesis": 0.85,
    "novelty": 0.45,
    "ensemble": 0.82,
}


def _make_scored(
    candidate: PeptideCandidate = _CANDIDATE,
    features: dict | None = None,
    scores: dict | None = None,
    nearest_reference: dict | None = None,
    selection_reason: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=candidate,
        features=features if features is not None else _FEATURES,
        scores=scores if scores is not None else _SCORES,
        nearest_reference=nearest_reference,
        selection_reason=selection_reason or ["high ensemble score"],
        known_failure_modes=known_failure_modes or ["No wet-lab assay has been run."],
    )


class TestBuildCertificateContent:
    def test_candidate_id_correct(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["candidate_id"] == "AMPF-001"

    def test_sequence_correct(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["sequence"] == "KWKLFKKIGAVLKVL"

    def test_source_correct(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["source"] == "test_source"

    def test_source_default_is_unknown(self):
        cand = PeptideCandidate("TEST-001", "KWKLF")
        cert = build_certificate(_make_scored(candidate=cand), {}, [])
        assert cert["source"] == "unknown"

    def test_features_passthrough(self):
        feat = {"length": 5, "net_charge_proxy": 3}
        cert = build_certificate(_make_scored(features=feat), {}, [])
        assert cert["features"] == feat

    def test_scores_passthrough(self):
        scores = {"activity": 0.75, "ensemble": 0.70}
        cert = build_certificate(_make_scored(scores=scores), {}, [])
        assert cert["scores"] == scores

    def test_nearest_reference_none_when_not_set(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["nearest_reference"] is None

    def test_nearest_reference_passthrough(self):
        ref = {"id": "REF-001", "similarity": 0.82}
        cert = build_certificate(_make_scored(nearest_reference=ref), {}, [])
        assert cert["nearest_reference"] == ref

    def test_references_checked_empty_list(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert cert["references_checked"] == []

    def test_references_checked_passthrough(self):
        refs = ["DRAMP0001", "DRAMP0002"]
        cert = build_certificate(_make_scored(), {}, refs)
        assert cert["references_checked"] == refs

    def test_selection_reason_passthrough(self):
        reasons = ["high activity", "good safety"]
        cert = build_certificate(_make_scored(selection_reason=reasons), {}, [])
        assert cert["selection_reason"] == reasons

    def test_known_failure_modes_passthrough(self):
        modes = ["No wet-lab assay.", "Heuristic only."]
        cert = build_certificate(_make_scored(known_failure_modes=modes), {}, [])
        assert cert["known_failure_modes"] == modes

    def test_recommended_next_steps_contains_expert_review(self):
        cert = build_certificate(_make_scored(), {}, [])
        combined = " ".join(cert["recommended_next_steps"]).lower()
        assert "expert" in combined or "review" in combined

    def test_recommended_next_steps_contains_no_claim_disclaimer(self):
        cert = build_certificate(_make_scored(), {}, [])
        combined = " ".join(cert["recommended_next_steps"]).lower()
        assert "do not claim" in combined or "without experimental" in combined

    def test_recommended_next_steps_is_non_empty_list(self):
        cert = build_certificate(_make_scored(), {}, [])
        steps = cert["recommended_next_steps"]
        assert isinstance(steps, list)
        assert len(steps) >= 1

    def test_generated_at_is_iso_timestamp(self):
        cert = build_certificate(_make_scored(), {}, [])
        ts = cert["generated_at"]
        assert isinstance(ts, str)
        assert "T" in ts
        assert re.search(r"(\+00:00|Z)$", ts) is not None

    def test_pipeline_version_is_non_empty_string(self):
        cert = build_certificate(_make_scored(), {}, [])
        v = cert["pipeline_version"]
        assert isinstance(v, str)
        assert len(v) > 0

    def test_config_hash_is_64_char_hex(self):
        cert = build_certificate(_make_scored(), {"weights": {}}, [])
        h = cert["config_hash"]
        assert isinstance(h, str)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_config_hash_stable_for_same_config(self):
        config = {"weights": {"activity": 0.4}, "threshold": 0.7}
        h1 = build_certificate(_make_scored(), config, [])["config_hash"]
        h2 = build_certificate(_make_scored(), config, [])["config_hash"]
        assert h1 == h2

    def test_config_hash_differs_for_different_configs(self):
        h1 = build_certificate(_make_scored(), {"k": 1}, [])["config_hash"]
        h2 = build_certificate(_make_scored(), {"k": 2}, [])["config_hash"]
        assert h1 != h2

    def test_all_required_keys_present(self):
        cert = build_certificate(_make_scored(), {}, [])
        required = {
            "candidate_id", "sequence", "source", "features", "scores",
            "nearest_reference", "references_checked", "selection_reason",
            "known_failure_modes", "recommended_next_steps", "generated_at",
            "pipeline_version", "config_hash",
        }
        assert required <= set(cert.keys())

    def test_returns_dict(self):
        cert = build_certificate(_make_scored(), {}, [])
        assert isinstance(cert, dict)

    def test_empty_selection_reason_passthrough(self):
        # The _make_scored() helper uses `or` so it cannot test selection_reason=[].
        # This test bypasses the helper to verify the production code handles an empty list.
        # The JSON schema allows an empty array (no minItems constraint).
        scored = ScoredCandidate(
            candidate=_CANDIDATE,
            features=_FEATURES,
            scores=_SCORES,
            selection_reason=[],
            known_failure_modes=["No wet-lab assay has been run."],
        )
        cert = build_certificate(scored, {}, [])
        assert cert["selection_reason"] == []
