"""Tests for NCH- novelty challenge harness schema."""

import pytest
from openamp_foundry.evidence.novelty_challenge_harness import (
    NoveltyChallengeHarness,
    NCHCandidateResult,
    VALID_NCH_VERDICTS,
    VALID_REFERENCE_DATABASES,
    NEAR_NEIGHBOR_IDENTITY_THRESHOLD,
    NOVEL_BATCH_CEILING,
    NEAR_NEIGHBOR_DOMINATED_FLOOR,
    build_novelty_challenge_harness,
    format_novelty_challenge_harness,
    validate_novelty_challenge_harness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOVEL_CANDIDATES = [
    {"candidate_id": f"FAM-{i:03d}", "max_identity_to_known": 0.30, "closest_known_amp_id": "AMP-X"}
    for i in range(10)
]

_MIXED_CANDIDATES = [
    {"candidate_id": "FAM-001", "max_identity_to_known": 0.90, "closest_known_amp_id": "AMP-A"},
    {"candidate_id": "FAM-002", "max_identity_to_known": 0.30, "closest_known_amp_id": "AMP-B"},
    {"candidate_id": "FAM-003", "max_identity_to_known": 0.30, "closest_known_amp_id": "AMP-C"},
    {"candidate_id": "FAM-004", "max_identity_to_known": 0.30, "closest_known_amp_id": "AMP-D"},
]

_NN_CANDIDATES = [
    {"candidate_id": f"FAM-{i:03d}", "max_identity_to_known": 0.95, "closest_known_amp_id": "AMP-Z"}
    for i in range(10)
]


def _build(**kwargs):
    defaults = dict(
        nch_id="NCH-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        reference_database="APD3",
        candidate_result_dicts=_NOVEL_CANDIDATES,
        limitations=["dry-lab only", "identity search is approximate"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_novelty_challenge_harness(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_nch_verdicts_is_frozenset():
    assert isinstance(VALID_NCH_VERDICTS, frozenset)


def test_valid_nch_verdicts_contains_novel_batch():
    assert "novel_batch" in VALID_NCH_VERDICTS


def test_valid_nch_verdicts_contains_mixed_novelty():
    assert "mixed_novelty" in VALID_NCH_VERDICTS


def test_valid_nch_verdicts_contains_near_neighbor_dominated():
    assert "near_neighbor_dominated" in VALID_NCH_VERDICTS


def test_valid_nch_verdicts_contains_challenge_not_run():
    assert "challenge_not_run" in VALID_NCH_VERDICTS


def test_valid_reference_databases_is_frozenset():
    assert isinstance(VALID_REFERENCE_DATABASES, frozenset)


def test_valid_reference_databases_contains_apd3():
    assert "APD3" in VALID_REFERENCE_DATABASES


def test_valid_reference_databases_contains_dramp():
    assert "DRAMP" in VALID_REFERENCE_DATABASES


def test_valid_reference_databases_contains_custom():
    assert "custom" in VALID_REFERENCE_DATABASES


def test_near_neighbor_identity_threshold():
    assert NEAR_NEIGHBOR_IDENTITY_THRESHOLD == 0.80


def test_novel_batch_ceiling():
    assert NOVEL_BATCH_CEILING == 0.20


def test_near_neighbor_dominated_floor():
    assert NEAR_NEIGHBOR_DOMINATED_FLOOR == 0.60


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_novelty_challenge_harness():
    assert isinstance(_build(), NoveltyChallengeHarness)


def test_build_nch_id_stored():
    assert _build().nch_id == "NCH-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_reference_database_stored():
    assert _build().reference_database == "APD3"


def test_build_identity_threshold_default():
    assert _build().identity_threshold == NEAR_NEIGHBOR_IDENTITY_THRESHOLD


def test_build_identity_threshold_custom():
    r = _build(identity_threshold=0.70)
    assert r.identity_threshold == 0.70


def test_build_novel_batch_verdict_when_all_novel():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    assert r.nch_verdict == "novel_batch"


def test_build_n_candidates_checked_matches_input():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    assert r.n_candidates_checked == 10


def test_build_n_near_neighbors_zero_when_all_novel():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    assert r.n_near_neighbors == 0


def test_build_near_neighbor_fraction_zero_when_all_novel():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    assert r.near_neighbor_fraction == 0.0


def test_build_mixed_novelty_verdict():
    r = _build(candidate_result_dicts=_MIXED_CANDIDATES)
    assert r.nch_verdict == "mixed_novelty"


def test_build_mixed_n_near_neighbors():
    r = _build(candidate_result_dicts=_MIXED_CANDIDATES)
    assert r.n_near_neighbors == 1


def test_build_mixed_near_neighbor_fraction():
    r = _build(candidate_result_dicts=_MIXED_CANDIDATES)
    assert abs(r.near_neighbor_fraction - 0.25) < 1e-4


def test_build_near_neighbor_dominated_verdict():
    r = _build(candidate_result_dicts=_NN_CANDIDATES)
    assert r.nch_verdict == "near_neighbor_dominated"


def test_build_near_neighbor_dominated_n_nn():
    r = _build(candidate_result_dicts=_NN_CANDIDATES)
    assert r.n_near_neighbors == 10


def test_build_challenge_not_run_verdict_when_empty():
    r = _build(candidate_result_dicts=[])
    assert r.nch_verdict == "challenge_not_run"


def test_build_empty_candidates_fraction_zero():
    r = _build(candidate_result_dicts=[])
    assert r.near_neighbor_fraction == 0.0


def test_build_candidate_results_are_nch_candidate_result():
    for cr in _build().candidate_results:
        assert isinstance(cr, NCHCandidateResult)


def test_build_candidate_result_is_near_neighbor_false_for_novel():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    for cr in r.candidate_results:
        assert cr.is_near_neighbor is False


def test_build_candidate_result_is_near_neighbor_true_for_nn():
    r = _build(candidate_result_dicts=_NN_CANDIDATES)
    for cr in r.candidate_results:
        assert cr.is_near_neighbor is True


def test_build_closest_known_amp_id_stored():
    r = _build(candidate_result_dicts=_NOVEL_CANDIDATES)
    assert r.candidate_results[0].closest_known_amp_id == "AMP-X"


def test_build_closest_known_amp_id_defaults_empty():
    candidates = [{"candidate_id": "FAM-001", "max_identity_to_known": 0.3}]
    r = _build(candidate_result_dicts=candidates)
    assert r.candidate_results[0].closest_known_amp_id == ""


def test_build_limitations_stored():
    r = _build()
    assert "dry-lab only" in r.limitations


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_boundary_novel_batch_at_ceiling():
    candidates = [
        {"candidate_id": f"FAM-{i:03d}", "max_identity_to_known": 0.85 if i == 0 else 0.30}
        for i in range(10)
    ]
    r = _build(candidate_result_dicts=candidates)
    assert r.nch_verdict == "novel_batch"
    assert r.n_near_neighbors == 1
    assert abs(r.near_neighbor_fraction - 0.10) < 1e-4


def test_build_boundary_mixed_above_ceiling():
    candidates = [
        {"candidate_id": f"FAM-{i:03d}", "max_identity_to_known": 0.85 if i < 3 else 0.30}
        for i in range(10)
    ]
    r = _build(candidate_result_dicts=candidates)
    assert r.nch_verdict == "mixed_novelty"


def test_build_dramp_database():
    r = _build(reference_database="DRAMP")
    assert r.reference_database == "DRAMP"


def test_build_custom_database():
    r = _build(reference_database="custom")
    assert r.reference_database == "custom"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_nch_id_prefix():
    with pytest.raises(ValueError, match="NCH-"):
        _build(nch_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_reference_database():
    with pytest.raises(ValueError, match="VALID_REFERENCE_DATABASES"):
        _build(reference_database="UNKNOWN_DB")


def test_validate_rejects_zero_identity_threshold():
    with pytest.raises(ValueError, match="identity_threshold"):
        _build(identity_threshold=0.0)


def test_validate_rejects_identity_threshold_above_one():
    with pytest.raises(ValueError, match="identity_threshold"):
        _build(identity_threshold=1.1)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_invalid_nch_verdict():
    nch = _build()
    nch.nch_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="nch_verdict"):
        validate_novelty_challenge_harness(nch)


def test_validate_rejects_dry_lab_only_false():
    nch = _build()
    nch.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_novelty_challenge_harness(nch)


def test_validate_rejects_n_near_neighbors_exceeds_checked():
    nch = _build()
    nch.n_near_neighbors = nch.n_candidates_checked + 1
    with pytest.raises(ValueError, match="n_near_neighbors"):
        validate_novelty_challenge_harness(nch)


def test_validate_rejects_n_candidates_mismatch():
    nch = _build()
    nch.n_candidates_checked = 999
    with pytest.raises(ValueError, match="n_candidates_checked"):
        validate_novelty_challenge_harness(nch)


def test_validate_rejects_identity_above_one_in_candidate():
    candidates = [{"candidate_id": "FAM-001", "max_identity_to_known": 1.5}]
    with pytest.raises(ValueError, match="max_identity_to_known"):
        _build(candidate_result_dicts=candidates)


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_nch_id():
    assert "NCH-001" in format_novelty_challenge_harness(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_novelty_challenge_harness(_build())


def test_format_contains_reference_database():
    assert "APD3" in format_novelty_challenge_harness(_build())


def test_format_contains_verdict():
    assert "novel_batch" in format_novelty_challenge_harness(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_novelty_challenge_harness(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_novelty_challenge_harness(_build())


def test_format_contains_near_neighbor_label_for_nn():
    r = _build(candidate_result_dicts=_NN_CANDIDATES)
    assert "NEAR-NEIGHBOR" in format_novelty_challenge_harness(r)


def test_format_is_string():
    assert isinstance(format_novelty_challenge_harness(_build()), str)
