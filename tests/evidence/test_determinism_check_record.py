"""Tests for DCR- determinism check record schema."""

import pytest
from openamp_foundry.evidence.determinism_check_record import (
    DeterminismCheckRecord,
    VALID_DCR_VERDICTS,
    VALID_DCR_STEP_TYPES,
    VALID_DCR_COMPARISON_METHODS,
    build_determinism_check_record,
    format_determinism_check_record,
    validate_determinism_check_record,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


LIMITATIONS = ["Dry-lab only, not biological validation."]


def _build(**kwargs):
    defaults = dict(
        dcr_id="DCR-001",
        pipeline_version="v1.0",
        step_type="scoring",
        step_id="scorer_abc_v2",
        random_seed="42",
        run1_output_hash="abc123",
        run2_output_hash="abc123",
        comparison_method="exact_match",
        n_runs=2,
        similarity_score=1.0,
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_determinism_check_record(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (12 tests)
# ---------------------------------------------------------------------------


def test_valid_dcr_verdicts_is_frozenset():
    assert isinstance(VALID_DCR_VERDICTS, frozenset)


def test_valid_dcr_verdicts_has_four():
    assert len(VALID_DCR_VERDICTS) == 4


def test_valid_dcr_verdicts_contains_deterministic():
    assert "deterministic" in VALID_DCR_VERDICTS


def test_valid_dcr_verdicts_contains_nondeterministic():
    assert "nondeterministic" in VALID_DCR_VERDICTS


def test_valid_dcr_verdicts_contains_single_run_only():
    assert "single_run_only" in VALID_DCR_VERDICTS


def test_valid_dcr_verdicts_contains_seed_dependent():
    assert "seed_dependent" in VALID_DCR_VERDICTS


def test_valid_dcr_step_types_is_frozenset():
    assert isinstance(VALID_DCR_STEP_TYPES, frozenset)


def test_valid_dcr_step_types_has_seven():
    assert len(VALID_DCR_STEP_TYPES) == 7


def test_valid_dcr_step_types_contains_scoring():
    assert "scoring" in VALID_DCR_STEP_TYPES


def test_valid_dcr_comparison_methods_is_frozenset():
    assert isinstance(VALID_DCR_COMPARISON_METHODS, frozenset)


def test_valid_dcr_comparison_methods_has_four():
    assert len(VALID_DCR_COMPARISON_METHODS) == 4


def test_valid_dcr_comparison_methods_contains_exact_match():
    assert "exact_match" in VALID_DCR_COMPARISON_METHODS


# ---------------------------------------------------------------------------
# 2. build – happy paths (20 tests)
# ---------------------------------------------------------------------------


def test_build_returns_determinism_check_record():
    assert isinstance(_build(), DeterminismCheckRecord)


def test_build_deterministic_matching_hashes():
    assert _build().verdict == "deterministic"


def test_build_nondeterministic_differing_hashes():
    r = _build(run2_output_hash="xyz789")
    assert r.verdict == "nondeterministic"


def test_build_single_run_only_n_runs_1():
    r = _build(n_runs=1, run2_output_hash="", similarity_score=-1.0)
    assert r.verdict == "single_run_only"


def test_build_seed_dependent_override():
    r = _build(run2_output_hash="xyz789", verdict="seed_dependent")
    assert r.verdict == "seed_dependent"


def test_build_outputs_match_true_deterministic():
    r = _build()
    assert r.outputs_match is True
    assert r.verdict == "deterministic"


def test_build_outputs_match_false():
    r = _build(run2_output_hash="xyz789")
    assert r.outputs_match is False


def test_build_n_runs_1_empty_run2():
    r = _build(n_runs=1, run2_output_hash="", similarity_score=-1.0)
    assert r.run2_output_hash == ""


def test_build_n_runs_2_stores_both_hashes():
    r = _build(run1_output_hash="abc123", run2_output_hash="def456")
    assert r.run1_output_hash == "abc123"
    assert r.run2_output_hash == "def456"


def test_build_similarity_score_stored():
    assert _build(similarity_score=0.85).similarity_score == 0.85


def test_build_step_type_stored():
    assert _build(step_type="ranking").step_type == "ranking"


def test_build_step_id_stored():
    assert _build(step_id="step_v3").step_id == "step_v3"


def test_build_random_seed_stored():
    assert _build(random_seed="12345").random_seed == "12345"


def test_build_comparison_method_stored():
    assert _build(comparison_method="rank_correlation").comparison_method == "rank_correlation"


def test_build_dcr_id_stored():
    assert _build(dcr_id="DCR-099").dcr_id == "DCR-099"


def test_build_pipeline_version_stored():
    assert _build(pipeline_version="v2.0").pipeline_version == "v2.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_limitations_stored():
    r = _build(limitations=["lim1", "lim2"])
    assert r.limitations == ["lim1", "lim2"]


def test_build_created_at_stored():
    assert _build(created_at="2026-07-11").created_at == "2026-07-11"


def test_build_similarity_score_minus_one_sentinel():
    r = _build(n_runs=1, run2_output_hash="", similarity_score=-1.0)
    assert r.similarity_score == -1.0


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_dcr_id_prefix():
    with pytest.raises(ValueError, match="DCR-"):
        _build(dcr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_step_type():
    with pytest.raises(ValueError, match="step_type"):
        _build(step_type="invalid_step")


def test_validate_rejects_empty_step_id():
    with pytest.raises(ValueError):
        _build(step_id="")


def test_validate_rejects_empty_random_seed():
    with pytest.raises(ValueError):
        _build(random_seed="")


def test_validate_rejects_empty_run1_output_hash():
    with pytest.raises(ValueError):
        _build(run1_output_hash="")


def test_validate_rejects_invalid_comparison_method():
    with pytest.raises(ValueError, match="comparison_method"):
        _build(comparison_method="bad_method")


def test_validate_rejects_n_runs_3_invalid():
    with pytest.raises(ValueError, match="n_runs"):
        _build(n_runs=3)


def test_validate_rejects_n_runs_2_with_empty_run2_hash():
    with pytest.raises(ValueError):
        _build(n_runs=2, run2_output_hash="")


def test_validate_rejects_n_runs_1_with_non_empty_run2_hash():
    with pytest.raises(ValueError):
        _build(n_runs=1, run2_output_hash="abc")


def test_validate_rejects_outputs_match_mismatch():
    r = _build()
    r.outputs_match = not r.outputs_match
    with pytest.raises(ValueError, match="outputs_match"):
        validate_determinism_check_record(r)


def test_validate_rejects_invalid_verdict():
    r = _build()
    r.verdict = "bogus"
    with pytest.raises(ValueError, match="verdict"):
        validate_determinism_check_record(r)


def test_validate_rejects_verdict_deterministic_when_hashes_differ():
    with pytest.raises(ValueError):
        _build(run2_output_hash="xyz789", verdict="deterministic")


def test_validate_rejects_verdict_nondeterministic_when_hashes_match():
    with pytest.raises(ValueError):
        _build(verdict="nondeterministic")


def test_validate_rejects_similarity_out_of_range():
    with pytest.raises(ValueError, match="similarity_score"):
        _build(similarity_score=1.5)


def test_validate_rejects_dry_lab_only_false():
    r = _build()
    r.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_determinism_check_record(r)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_dcr_id():
    assert "DCR-001" in format_determinism_check_record(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_determinism_check_record(_build())


def test_format_contains_step():
    output = format_determinism_check_record(_build())
    assert "scoring" in output
    assert "scorer_abc_v2" in output


def test_format_contains_seed():
    assert "42" in format_determinism_check_record(_build())


def test_format_contains_comparison():
    assert "exact_match" in format_determinism_check_record(_build())


def test_format_contains_runs():
    assert "2" in format_determinism_check_record(_build())


def test_format_contains_verdict():
    assert "deterministic" in format_determinism_check_record(_build())


def test_format_is_string():
    assert isinstance(format_determinism_check_record(_build()), str)
