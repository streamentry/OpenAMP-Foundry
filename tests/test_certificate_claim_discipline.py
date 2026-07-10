"""CI test that dry-lab certificates cannot include forbidden claims — Phase B B9.

This is a discipline gate: if build_certificate() ever emits text that matches
a forbidden pattern, this test fails in CI. It makes claim discipline machine-
verifiable, not just reviewer-dependent.

Two sets of forbidden patterns are enforced:
  1. RISKY_PATTERNS from scripts/safety/check_claims.py — overclaiming language
  2. FORBIDDEN_CLAIM_PATTERNS from gates/wave0_5_gate_checker.py — therapeutic/clinical claims

All text fields of the certificate are scanned: candidate_id, sequence, source,
selection_reason, known_failure_modes, recommended_next_steps, proof_ladder_level.
"""

from __future__ import annotations

import json
import re

import pytest

from openamp_foundry.evidence.certificate import build_certificate
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.gates.wave0_5_gate_checker import FORBIDDEN_CLAIM_PATTERNS
from openamp_foundry.types import PeptideCandidate, ScoredCandidate
from scripts.safety.check_claims import RISKY_PATTERNS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SEQUENCE = "KWKLFKKIGAVLKVL"
_CANDIDATE = PeptideCandidate("AMPF-001", _SEQUENCE, "test_source")
_FEATURES = compute_features(_SEQUENCE)
_SCORES = {
    "activity": 0.80,
    "safety": 0.90,
    "synthesis": 0.85,
    "novelty": 0.45,
    "ensemble": 0.82,
}


def _make_scored(
    candidate: PeptideCandidate | None = None,
    scores: dict | None = None,
    selection_reason: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=candidate or _CANDIDATE,
        features=_FEATURES,
        scores=scores or _SCORES,
        nearest_reference=None,
        selection_reason=selection_reason or ["high ensemble score"],
        known_failure_modes=known_failure_modes or ["No wet-lab assay has been run."],
    )


def _collect_cert_text_fields(cert: dict) -> list[str]:
    """Extract all text content from certificate fields that could hold claims."""
    texts: list[str] = []
    for key, val in cert.items():
        if isinstance(val, str):
            texts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    texts.append(item)
    return texts


def _check_risky_patterns(texts: list[str]) -> list[str]:
    """Return list of violations against RISKY_PATTERNS."""
    violations: list[str] = []
    for pattern, msg in RISKY_PATTERNS:
        for text in texts:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"Pattern {pattern!r}: {msg!r} — found in: {text[:80]!r}")
    return violations


def _check_forbidden_patterns(texts: list[str]) -> list[str]:
    """Return list of violations against FORBIDDEN_CLAIM_PATTERNS."""
    violations: list[str] = []
    for pat in FORBIDDEN_CLAIM_PATTERNS:
        for text in texts:
            if pat.search(text):
                violations.append(
                    f"ForbiddenPattern {pat.pattern!r} — found in: {text[:80]!r}"
                )
    return violations


# ---------------------------------------------------------------------------
# Group 1: Default certificate has no forbidden claims (6 tests)
# ---------------------------------------------------------------------------

class TestDefaultCertificateCleanClaims:
    """The certificate produced by build_certificate() must be claim-clean."""

    def test_default_cert_passes_risky_patterns(self):
        cert = build_certificate(_make_scored(), {}, [])
        texts = _collect_cert_text_fields(cert)
        violations = _check_risky_patterns(texts)
        assert violations == [], (
            "Default certificate contains risky claim language:\n"
            + "\n".join(violations)
        )

    def test_default_cert_passes_forbidden_patterns(self):
        cert = build_certificate(_make_scored(), {}, [])
        texts = _collect_cert_text_fields(cert)
        violations = _check_forbidden_patterns(texts)
        assert violations == [], (
            "Default certificate contains forbidden claim language:\n"
            + "\n".join(violations)
        )

    def test_recommended_next_steps_clean(self):
        cert = build_certificate(_make_scored(), {}, [])
        steps = cert.get("recommended_next_steps", [])
        assert isinstance(steps, list)
        violations = _check_risky_patterns(steps)
        assert violations == [], (
            "recommended_next_steps contains risky language:\n"
            + "\n".join(violations)
        )

    def test_known_failure_modes_clean(self):
        cert = build_certificate(_make_scored(), {}, [])
        modes = cert.get("known_failure_modes", [])
        # known_failure_modes may not always be present in cert
        # but if it is, it must be clean
        if not isinstance(modes, list):
            modes = []
        violations = _check_risky_patterns(modes)
        assert violations == [], (
            "known_failure_modes contains risky language:\n"
            + "\n".join(violations)
        )

    def test_proof_ladder_level_is_string_not_overclaim(self):
        cert = build_certificate(_make_scored(), {}, [])
        level = cert.get("proof_ladder_level", "")
        assert isinstance(level, str)
        # Must not use clinical/therapeutic language
        assert "clinical" not in level.lower()
        assert "proven" not in level.lower()
        assert "validated" not in level.lower()

    def test_cert_has_no_prohibited_keys(self):
        cert = build_certificate(_make_scored(), {}, [])
        prohibited_keys = {"clinical_evidence", "wet_lab_result", "proven_active"}
        overlap = prohibited_keys & set(cert.keys())
        assert overlap == set(), f"Certificate has prohibited keys: {overlap}"


# ---------------------------------------------------------------------------
# Group 2: Known risky patterns are caught by the scanner (12 tests)
# ---------------------------------------------------------------------------

class TestRiskyPatternDetection:
    """Verify the scanner catches forbidden language if it were injected."""

    @pytest.mark.parametrize("phrase,should_match", [
        ("This candidate is proven to be active", True),
        ("safe in humans based on our analysis", True),
        ("clinically useful for treating infections", True),
        ("This is a drug candidate ready for trials", True),
        ("This candidate is a cure for MRSA", True),
        ("computationally nominated candidate", False),
        ("dry-lab candidate evidence only", False),
        ("No wet-lab assay has been run", False),
        ("independent domain expert review required", False),
        ("This is computationally nominated evidence only", False),
        ("high ensemble score supports selection", False),
        ("activity score 0.80 — no biological proof", False),
    ])
    def test_phrase_detection(self, phrase, should_match):
        violations = _check_risky_patterns([phrase])
        if should_match:
            assert violations, f"Expected risky phrase to be caught: {phrase!r}"
        else:
            assert not violations, (
                f"Safe phrase incorrectly flagged: {phrase!r}\n"
                + "\n".join(violations)
            )


# ---------------------------------------------------------------------------
# Group 3: Forbidden patterns from wave0_5_gate_checker are caught (8 tests)
# ---------------------------------------------------------------------------

class TestForbiddenPatternDetection:
    """Verify wave0_5 FORBIDDEN_CLAIM_PATTERNS catch prohibited language."""

    @pytest.mark.parametrize("phrase,should_match", [
        ("antibiotic for treatment of MRSA", True),
        ("clinical therapy for gram-negative infections", True),
        ("wet-lab evidence confirm antimicrobial activity", True),
        ("demonstrated antimicrobial activity in mice", True),
        ("computationally nominated dry-lab candidate", False),
        ("activity score from in-silico prediction", False),
        ("no biological validation performed", False),
        ("review required before any assay decision", False),
    ])
    def test_forbidden_pattern_detection(self, phrase, should_match):
        violations = _check_forbidden_patterns([phrase])
        if should_match:
            assert violations, (
                f"Expected forbidden phrase to be caught: {phrase!r}"
            )
        else:
            assert not violations, (
                f"Safe phrase incorrectly flagged by forbidden patterns: {phrase!r}\n"
                + "\n".join(violations)
            )


# ---------------------------------------------------------------------------
# Group 4: Scanner covers all text fields in a real certificate (5 tests)
# ---------------------------------------------------------------------------

class TestScannerCoverage:
    """The _collect_cert_text_fields function covers all relevant cert fields."""

    def test_collector_extracts_string_fields(self):
        cert = {"a": "text A", "b": 123, "c": "text C"}
        texts = _collect_cert_text_fields(cert)
        assert "text A" in texts
        assert "text C" in texts

    def test_collector_extracts_list_string_fields(self):
        cert = {"steps": ["step one", "step two"], "score": 0.8}
        texts = _collect_cert_text_fields(cert)
        assert "step one" in texts
        assert "step two" in texts

    def test_collector_skips_non_string_list_items(self):
        cert = {"items": [1, 2, "text", None]}
        texts = _collect_cert_text_fields(cert)
        assert "text" in texts
        assert len([t for t in texts if not isinstance(t, str)]) == 0

    def test_real_cert_text_fields_collected(self):
        cert = build_certificate(_make_scored(), {}, [])
        texts = _collect_cert_text_fields(cert)
        assert len(texts) >= 3, "Expected at least 3 text fields in certificate"

    def test_recommended_next_steps_are_collected(self):
        cert = build_certificate(_make_scored(), {}, [])
        texts = _collect_cert_text_fields(cert)
        steps = cert.get("recommended_next_steps", [])
        for step in steps:
            if isinstance(step, str):
                assert step in texts


# ---------------------------------------------------------------------------
# Group 5: Certificates with custom fields stay clean (4 tests)
# ---------------------------------------------------------------------------

class TestCustomSelectionReasonClean:
    """Even with custom selection_reason, certificates must stay claim-clean."""

    def test_safe_selection_reason_passes(self):
        scored = _make_scored(selection_reason=["high ensemble score", "diverse scaffold"])
        cert = build_certificate(scored, {}, [])
        texts = _collect_cert_text_fields(cert)
        assert _check_risky_patterns(texts) == []

    def test_cert_with_multiple_references_passes(self):
        scored = _make_scored()
        cert = build_certificate(scored, {}, ["APD-001", "DRAMP-002"])
        texts = _collect_cert_text_fields(cert)
        assert _check_risky_patterns(texts) == []

    def test_low_score_candidate_stays_clean(self):
        scored = _make_scored(scores={"activity": 0.3, "safety": 0.4, "novelty": 0.2})
        cert = build_certificate(scored, {}, [])
        texts = _collect_cert_text_fields(cert)
        assert _check_risky_patterns(texts) == []
        assert _check_forbidden_patterns(texts) == []

    def test_claim_discipline_survives_json_roundtrip(self):
        cert = build_certificate(_make_scored(), {}, [])
        roundtripped = json.loads(json.dumps(cert))
        texts = _collect_cert_text_fields(roundtripped)
        assert _check_risky_patterns(texts) == []
        assert _check_forbidden_patterns(texts) == []
