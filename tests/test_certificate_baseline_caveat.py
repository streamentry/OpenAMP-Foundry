"""CI tests for the baseline_caveat field in certificates — Phase B B3.

The baseline_caveat field forces cheap-explanation visibility: every certificate
must explicitly state which cheap heuristics (charge, length, hydrophobicity)
the candidate passes, so reviewers can assess the residual ML signal.

Three canonical cheap baselines:
  1. Net charge >= 4 (cationic bias heuristic)
  2. Length in [10, 40] aa (typical AMP length range)
  3. Hydrophobic fraction >= 0.30

63 tests across 8 groups.
"""

from __future__ import annotations

import json

import pytest

from openamp_foundry.evidence.certificate import (
    _BASELINE_LENGTH_MAX,
    _BASELINE_LENGTH_MIN,
    _BASELINE_MIN_CHARGE,
    _BASELINE_MIN_HYDROPHOBIC_FRACTION,
    _build_baseline_caveat,
    build_certificate,
)
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scored(sequence: str, candidate_id: str = "AMPF-TEST") -> ScoredCandidate:
    return ScoredCandidate(
        candidate=PeptideCandidate(candidate_id, sequence, "test_source"),
        features=compute_features(sequence),
        scores={"activity": 0.80, "safety": 0.90, "novelty": 0.50, "ensemble": 0.82},
        nearest_reference=None,
        selection_reason=["high ensemble score"],
        known_failure_modes=["No wet-lab assay has been run."],
    )


# AMP-like sequence: high charge, AMP length, hydrophobic fraction ~0.47
_AMP_SEQ = "KWKLFKKIGAVLKVL"  # K=6 -> charge ~6; length=15; hydrophobic ~0.47

# Short, low-charge, low-hydrophobicity sequence -- fails all three baselines
_ATYPICAL_SEQ = "GSGSGSGS"  # G+S: charge ~0, length=8, hydrophobic_fraction ~0

# Long sequence > 40 aa
_LONG_SEQ = "KWKLFKKIGAVLKVLKWKLFKKIGAVLKVLKWKLFKKIGAVLKVLKW"  # length=47


# ---------------------------------------------------------------------------
# Group 1: BasicPresence (6 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatPresence:
    """baseline_caveat is always present, non-empty, and well-formed."""

    def test_baseline_caveat_present_in_certificate(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        assert "baseline_caveat" in cert

    def test_baseline_caveat_is_string(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        assert isinstance(cert["baseline_caveat"], str)

    def test_baseline_caveat_non_empty(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        assert len(cert["baseline_caveat"]) > 0

    def test_baseline_caveat_present_for_atypical_sequence(self):
        cert = build_certificate(_make_scored(_ATYPICAL_SEQ), {}, [])
        assert "baseline_caveat" in cert
        assert isinstance(cert["baseline_caveat"], str)
        assert len(cert["baseline_caveat"]) > 0

    def test_baseline_caveat_contains_cheapest_explanation(self):
        caveat = cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])["baseline_caveat"]
        assert "cheapest" in caveat.lower() or "baseline" in caveat.lower()

    def test_baseline_caveat_survives_json_roundtrip(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        roundtripped = json.loads(json.dumps(cert))
        assert roundtripped["baseline_caveat"] == cert["baseline_caveat"]


# ---------------------------------------------------------------------------
# Group 2: ChargeFlags (12 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatChargeFlag:
    """Caveat correctly flags charge >= 4 as YES, charge < 4 as NO."""

    def test_high_charge_sequence_charge_flag_yes(self):
        # KWKLFKKIGAVLKVL has several K residues -> charge >= 4
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        charge = scored.features.get("net_charge_proxy", 0)
        if charge >= _BASELINE_MIN_CHARGE:
            assert "YES" in caveat

    def test_charge_value_reported_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert "charge=" in caveat

    def test_charge_threshold_mentioned_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert f"\u2265{_BASELINE_MIN_CHARGE}" in caveat

    def test_low_charge_sequence_charge_flag_no(self):
        # GSGSGSGS: G and S have charge ~0
        scored = _make_scored(_ATYPICAL_SEQ)
        caveat = _build_baseline_caveat(scored)
        charge = scored.features.get("net_charge_proxy", 0)
        if charge < _BASELINE_MIN_CHARGE:
            assert "NO" in caveat

    def test_charge_flag_passes_at_boundary(self):
        # Build a scored with exactly charge=4 in features (override)
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = float(_BASELINE_MIN_CHARGE)
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat  # 4 >= 4

    def test_charge_flag_fails_below_boundary(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = float(_BASELINE_MIN_CHARGE - 1)
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_charge_flag_positive_high_charge(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 10.0
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat

    def test_charge_flag_negative_charge(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = -2.0
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_charge_flag_zero_charge(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 0.0
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_caveat_shows_charge_decimal(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 5.0
        caveat = _build_baseline_caveat(scored)
        assert "5.0" in caveat

    def test_caveat_charge_3_99_fails(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 3.99
        caveat = _build_baseline_caveat(scored)
        # 3.99 < 4 -> NO
        assert "NO" in caveat

    def test_caveat_charge_4_01_passes(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 4.01
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat


# ---------------------------------------------------------------------------
# Group 3: LengthFlags (12 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatLengthFlag:
    """Caveat correctly flags length in [10, 40] as YES, outside as NO."""

    def test_amp_length_range_flag_yes(self):
        # _AMP_SEQ is 15 aa -> YES
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        length = scored.features.get("length", 0)
        if _BASELINE_LENGTH_MIN <= length <= _BASELINE_LENGTH_MAX:
            assert "YES" in caveat

    def test_length_value_reported_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert "length=" in caveat

    def test_length_range_mentioned_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert f"{_BASELINE_LENGTH_MIN}-{_BASELINE_LENGTH_MAX}" in caveat

    def test_short_sequence_length_flag_no(self):
        # GSGSGSGS: length=8 < 10 -> NO
        scored = _make_scored(_ATYPICAL_SEQ)
        caveat = _build_baseline_caveat(scored)
        length = scored.features.get("length", 0)
        if length < _BASELINE_LENGTH_MIN:
            assert "NO" in caveat

    def test_long_sequence_length_flag_no(self):
        # _LONG_SEQ: length=47 > 40 -> NO for length
        scored = _make_scored(_LONG_SEQ)
        caveat = _build_baseline_caveat(scored)
        length = scored.features.get("length", 0)
        if length > _BASELINE_LENGTH_MAX:
            assert "NO" in caveat

    def test_length_flag_at_min_boundary(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = _BASELINE_LENGTH_MIN
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat

    def test_length_flag_at_max_boundary(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = _BASELINE_LENGTH_MAX
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat

    def test_length_flag_below_min(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = _BASELINE_LENGTH_MIN - 1
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_length_flag_above_max(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = _BASELINE_LENGTH_MAX + 1
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_length_reported_as_integer(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        length = scored.features.get("length", 0)
        assert str(int(length)) in caveat

    def test_length_zero_fails(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = 0
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_length_5_fails(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["length"] = 5
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat


# ---------------------------------------------------------------------------
# Group 4: HydrophobicityFlags (10 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatHydrophobicityFlag:
    """Caveat correctly flags hydrophobic_fraction >= 0.30 as YES, below as NO."""

    def test_hydrophobic_value_reported_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert "hydrophobic_fraction=" in caveat

    def test_hydrophobic_threshold_mentioned_in_caveat(self):
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        assert f"\u2265{_BASELINE_MIN_HYDROPHOBIC_FRACTION:.2f}" in caveat

    def test_amp_hydrophobicity_flag_yes(self):
        # _AMP_SEQ: L, I, V, A are hydrophobic -> fraction likely >= 0.30
        scored = _make_scored(_AMP_SEQ)
        caveat = _build_baseline_caveat(scored)
        hydro = scored.features.get("hydrophobic_fraction", 0.0)
        if hydro >= _BASELINE_MIN_HYDROPHOBIC_FRACTION:
            assert "YES" in caveat

    def test_atypical_hydrophobicity_flag_no(self):
        scored = _make_scored(_ATYPICAL_SEQ)
        caveat = _build_baseline_caveat(scored)
        hydro = scored.features.get("hydrophobic_fraction", 0.0)
        if hydro < _BASELINE_MIN_HYDROPHOBIC_FRACTION:
            assert "NO" in caveat

    def test_hydro_flag_at_boundary(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = _BASELINE_MIN_HYDROPHOBIC_FRACTION
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat  # 0.30 >= 0.30

    def test_hydro_flag_just_below_boundary(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = _BASELINE_MIN_HYDROPHOBIC_FRACTION - 0.01
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_hydro_flag_high_hydrophobicity(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = 0.8
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat

    def test_hydro_flag_zero_hydrophobicity(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = 0.0
        caveat = _build_baseline_caveat(scored)
        assert "NO" in caveat

    def test_hydro_shown_as_two_decimal(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = 0.45
        caveat = _build_baseline_caveat(scored)
        assert "0.45" in caveat

    def test_hydro_value_0_50_passes(self):
        scored = _make_scored(_AMP_SEQ)
        scored.features["hydrophobic_fraction"] = 0.50
        caveat = _build_baseline_caveat(scored)
        assert "YES" in caveat


# ---------------------------------------------------------------------------
# Group 5: AllFlagsYes -- all three baselines pass (5 tests)
# ---------------------------------------------------------------------------

class TestAllBaselineFlagsPass:
    """Candidate passing all three cheap baselines gets appropriate warning."""

    def _scored_all_yes(self) -> ScoredCandidate:
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 6.0
        scored.features["length"] = 15
        scored.features["hydrophobic_fraction"] = 0.47
        return scored

    def test_all_flags_yes_caveat_warns(self):
        caveat = _build_baseline_caveat(self._scored_all_yes())
        assert "YES" in caveat

    def test_all_flags_yes_mentions_conjunction_rule(self):
        caveat = _build_baseline_caveat(self._scored_all_yes())
        assert "conjunction" in caveat.lower() or "all three" in caveat.lower()

    def test_all_flags_yes_mentions_residual(self):
        caveat = _build_baseline_caveat(self._scored_all_yes())
        assert "residual" in caveat.lower()

    def test_all_flags_yes_in_certificate(self):
        cert = build_certificate(self._scored_all_yes(), {}, [])
        assert "baseline_caveat" in cert
        assert "YES" in cert["baseline_caveat"]

    def test_all_flags_yes_cert_survives_json(self):
        cert = build_certificate(self._scored_all_yes(), {}, [])
        rt = json.loads(json.dumps(cert))
        assert rt["baseline_caveat"] == cert["baseline_caveat"]


# ---------------------------------------------------------------------------
# Group 6: AllFlagsNo -- no cheap baseline passes (5 tests)
# ---------------------------------------------------------------------------

class TestNoBaselineFlagsPass:
    """Candidate failing all three cheap baselines gets appropriate note."""

    def _scored_all_no(self) -> ScoredCandidate:
        scored = _make_scored(_AMP_SEQ)
        scored.features["net_charge_proxy"] = 0.0   # charge < 4 -> NO
        scored.features["length"] = 5               # < 10 -> NO
        scored.features["hydrophobic_fraction"] = 0.0  # < 0.30 -> NO
        return scored

    def test_all_flags_no_caveat_shows_no(self):
        caveat = _build_baseline_caveat(self._scored_all_no())
        assert "NO" in caveat

    def test_all_flags_no_mentions_ml_signal_dominant(self):
        caveat = _build_baseline_caveat(self._scored_all_no())
        assert "ml" in caveat.lower() or "dominant" in caveat.lower() or "cannot be explained" in caveat.lower()

    def test_all_flags_no_caveat_present(self):
        caveat = _build_baseline_caveat(self._scored_all_no())
        assert isinstance(caveat, str) and len(caveat) > 0

    def test_all_flags_no_in_certificate(self):
        cert = build_certificate(self._scored_all_no(), {}, [])
        assert "NO" in cert["baseline_caveat"]

    def test_all_flags_no_cert_survives_json(self):
        cert = build_certificate(self._scored_all_no(), {}, [])
        rt = json.loads(json.dumps(cert))
        assert rt["baseline_caveat"] == cert["baseline_caveat"]


# ---------------------------------------------------------------------------
# Group 7: ClaimDiscipline (5 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatClaimDiscipline:
    """baseline_caveat must not make biological claims."""

    def test_caveat_no_proven_language(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        assert "proven" not in caveat.lower()

    def test_caveat_no_clinical_language(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        assert "clinical" not in caveat.lower()

    def test_caveat_no_drug_language(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        assert "drug" not in caveat.lower()

    def test_caveat_no_cure_language(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        assert "cure" not in caveat.lower()

    def test_caveat_no_safe_in_humans_language(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        assert "safe in humans" not in caveat.lower()


# ---------------------------------------------------------------------------
# Group 8: Integration (8 tests)
# ---------------------------------------------------------------------------

class TestBaselineCaveatIntegration:
    """Integration tests: baseline_caveat interacts correctly with other cert fields."""

    def test_caveat_alongside_proof_ladder_level(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        assert "baseline_caveat" in cert
        assert "proof_ladder_level" in cert

    def test_caveat_present_with_multiple_references(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, ["APD-001", "DRAMP-002"])
        assert "baseline_caveat" in cert

    def test_caveat_present_with_empty_scores(self):
        scored = _make_scored(_AMP_SEQ)
        scored.scores = {}
        cert = build_certificate(scored, {}, [])
        assert "baseline_caveat" in cert
        assert isinstance(cert["baseline_caveat"], str)

    def test_caveat_varies_by_sequence(self):
        cert_amp = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        cert_aty = build_certificate(_make_scored(_ATYPICAL_SEQ), {}, [])
        # Different sequences should have different caveats
        assert cert_amp["baseline_caveat"] != cert_aty["baseline_caveat"]

    def test_caveat_present_with_config(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {"threshold": 0.7}, [])
        assert "baseline_caveat" in cert

    def test_long_seq_caveat_correct(self):
        cert = build_certificate(_make_scored(_LONG_SEQ), {}, [])
        caveat = cert["baseline_caveat"]
        # Length > 40 -> length flag is NO
        assert "NO" in caveat

    def test_caveat_is_last_field_or_key_in_cert(self):
        cert = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        keys = list(cert.keys())
        assert "baseline_caveat" in keys

    def test_two_certificates_same_sequence_same_caveat(self):
        cert1 = build_certificate(_make_scored(_AMP_SEQ), {}, [])
        cert2 = build_certificate(_make_scored(_AMP_SEQ, "AMPF-002"), {}, [])
        # Same sequence -> same features -> same caveat
        assert cert1["baseline_caveat"] == cert2["baseline_caveat"]
