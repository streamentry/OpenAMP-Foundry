"""Tests for CMC- charge-matched challenge schema."""

import pytest
from openamp_foundry.evidence.charge_matched_challenge import (
    ChargeMatchedChallenge,
    VALID_CMC_VERDICTS,
    VALID_CHARGE_BASELINE_METHODS,
    MEANINGFUL_GAP_THRESHOLD,
    MARGINAL_GAP_LOWER,
    build_charge_matched_challenge,
    format_charge_matched_challenge,
    validate_charge_matched_challenge,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        cmc_id="CMC-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        baseline_method="charge_only_rank",
        pipeline_auroc=0.82,
        baseline_auroc=0.71,
        n_candidates=100,
        mean_charge_pipeline=4.2,
        mean_charge_baseline=4.1,
        charge_distribution_matched=True,
        limitations=["dry-lab only", "AUROC is approximate"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_charge_matched_challenge(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_valid_cmc_verdicts_is_frozenset():
    assert isinstance(VALID_CMC_VERDICTS, frozenset)


def test_valid_cmc_verdicts_contains_gap_meaningful():
    assert "gap_meaningful" in VALID_CMC_VERDICTS


def test_valid_cmc_verdicts_contains_gap_marginal():
    assert "gap_marginal" in VALID_CMC_VERDICTS


def test_valid_cmc_verdicts_contains_gap_absent():
    assert "gap_absent" in VALID_CMC_VERDICTS


def test_valid_cmc_verdicts_contains_challenge_not_run():
    assert "challenge_not_run" in VALID_CMC_VERDICTS


def test_valid_charge_baseline_methods_is_frozenset():
    assert isinstance(VALID_CHARGE_BASELINE_METHODS, frozenset)


def test_valid_charge_baseline_methods_contains_charge_only():
    assert "charge_only_rank" in VALID_CHARGE_BASELINE_METHODS


def test_valid_charge_baseline_methods_contains_charge_length():
    assert "charge_length_rank" in VALID_CHARGE_BASELINE_METHODS


def test_valid_charge_baseline_methods_contains_logistic():
    assert "logistic_charge_only" in VALID_CHARGE_BASELINE_METHODS


def test_meaningful_gap_threshold():
    assert MEANINGFUL_GAP_THRESHOLD == 0.05


def test_marginal_gap_lower():
    assert MARGINAL_GAP_LOWER == 0.02


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_charge_matched_challenge():
    assert isinstance(_build(), ChargeMatchedChallenge)


def test_build_cmc_id_stored():
    assert _build().cmc_id == "CMC-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_baseline_method_stored():
    assert _build().baseline_method == "charge_only_rank"


def test_build_pipeline_auroc_stored():
    assert abs(_build().pipeline_auroc - 0.82) < 1e-9


def test_build_baseline_auroc_stored():
    assert abs(_build().baseline_auroc - 0.71) < 1e-9


def test_build_auroc_gap_computed():
    r = _build()
    assert abs(r.auroc_gap - (0.82 - 0.71)) < 1e-4


def test_build_gap_meaningful_verdict():
    r = _build(pipeline_auroc=0.82, baseline_auroc=0.71)
    assert r.cmc_verdict == "gap_meaningful"


def test_build_gap_marginal_verdict():
    r = _build(pipeline_auroc=0.73, baseline_auroc=0.71)
    assert r.cmc_verdict == "gap_marginal"


def test_build_gap_absent_verdict():
    r = _build(pipeline_auroc=0.71, baseline_auroc=0.71)
    assert r.cmc_verdict == "gap_absent"


def test_build_challenge_not_run_when_n_candidates_zero():
    r = _build(n_candidates=0)
    assert r.cmc_verdict == "challenge_not_run"


def test_build_gap_absent_when_baseline_higher():
    r = _build(pipeline_auroc=0.70, baseline_auroc=0.75)
    assert r.cmc_verdict == "gap_absent"
    assert r.auroc_gap < 0


def test_build_n_candidates_stored():
    assert _build().n_candidates == 100


def test_build_mean_charge_pipeline_stored():
    assert abs(_build().mean_charge_pipeline - 4.2) < 1e-9


def test_build_mean_charge_baseline_stored():
    assert abs(_build().mean_charge_baseline - 4.1) < 1e-9


def test_build_charge_distribution_matched_stored():
    assert _build().charge_distribution_matched is True


def test_build_charge_distribution_not_matched():
    r = _build(charge_distribution_matched=False)
    assert r.charge_distribution_matched is False


def test_build_charge_length_rank_method():
    r = _build(baseline_method="charge_length_rank")
    assert r.baseline_method == "charge_length_rank"


def test_build_charge_hydrophobicity_method():
    r = _build(baseline_method="charge_hydrophobicity_rank")
    assert r.baseline_method == "charge_hydrophobicity_rank"


def test_build_logistic_charge_only_method():
    r = _build(baseline_method="logistic_charge_only")
    assert r.baseline_method == "logistic_charge_only"


def test_build_limitations_stored():
    assert "dry-lab only" in _build().limitations


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


def test_build_auroc_gap_boundary_meaningful():
    r = _build(pipeline_auroc=0.76, baseline_auroc=0.71)
    assert r.cmc_verdict == "gap_meaningful"


def test_build_auroc_gap_boundary_marginal_at_lower():
    r = _build(pipeline_auroc=0.73, baseline_auroc=0.71)
    assert r.cmc_verdict == "gap_marginal"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_cmc_id_prefix():
    with pytest.raises(ValueError, match="CMC-"):
        _build(cmc_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_baseline_method():
    with pytest.raises(ValueError, match="VALID_CHARGE_BASELINE_METHODS"):
        _build(baseline_method="UNKNOWN_METHOD")


def test_validate_rejects_pipeline_auroc_below_zero():
    with pytest.raises(ValueError, match="pipeline_auroc"):
        _build(pipeline_auroc=-0.01)


def test_validate_rejects_pipeline_auroc_above_one():
    with pytest.raises(ValueError, match="pipeline_auroc"):
        _build(pipeline_auroc=1.01)


def test_validate_rejects_baseline_auroc_below_zero():
    with pytest.raises(ValueError, match="baseline_auroc"):
        _build(baseline_auroc=-0.01)


def test_validate_rejects_baseline_auroc_above_one():
    with pytest.raises(ValueError, match="baseline_auroc"):
        _build(baseline_auroc=1.01)


def test_validate_rejects_auroc_gap_mismatch():
    cmc = _build()
    cmc.auroc_gap = 0.99
    with pytest.raises(ValueError, match="auroc_gap"):
        validate_charge_matched_challenge(cmc)


def test_validate_rejects_negative_n_candidates():
    with pytest.raises(ValueError, match="n_candidates"):
        cmc = _build()
        cmc.n_candidates = -1
        validate_charge_matched_challenge(cmc)


def test_validate_rejects_invalid_verdict():
    cmc = _build()
    cmc.cmc_verdict = "UNKNOWN"
    with pytest.raises(ValueError, match="cmc_verdict"):
        validate_charge_matched_challenge(cmc)


def test_validate_rejects_dry_lab_only_false():
    cmc = _build()
    cmc.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_charge_matched_challenge(cmc)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_cmc_id():
    assert "CMC-001" in format_charge_matched_challenge(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_charge_matched_challenge(_build())


def test_format_contains_baseline_method():
    assert "charge_only_rank" in format_charge_matched_challenge(_build())


def test_format_contains_verdict():
    assert "gap_meaningful" in format_charge_matched_challenge(_build())


def test_format_contains_pipeline_auroc():
    assert "0.8200" in format_charge_matched_challenge(_build())


def test_format_contains_baseline_auroc():
    assert "0.7100" in format_charge_matched_challenge(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_charge_matched_challenge(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_charge_matched_challenge(_build())


def test_format_is_string():
    assert isinstance(format_charge_matched_challenge(_build()), str)
