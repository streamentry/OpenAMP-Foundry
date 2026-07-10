"""Tests for BCR- benchmark challenge registry schema."""

import pytest
from openamp_foundry.evidence.benchmark_challenge_registry import (
    BenchmarkChallengeRegistry,
    ChallengeEntry,
    REQUIRED_CHALLENGE_TYPES,
    VALID_CHALLENGE_VERDICTS,
    VALID_BCR_HARDNESS_GRADES,
    build_benchmark_challenge_registry,
    format_benchmark_challenge_registry,
    validate_benchmark_challenge_registry,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(**kwargs):
    defaults = dict(
        bcr_id="BCR-001",
        batch_id="BATCH-01",
        pipeline_version="v1.0",
        nch_artifact_id="NCH-001",
        nch_raw_verdict="novel_batch",
        cmc_artifact_id="CMC-001",
        cmc_raw_verdict="gap_meaningful",
        sch_artifact_id="SCH-001",
        sch_raw_verdict="selection_adds_value",
        limitations=["dry-lab only"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_benchmark_challenge_registry(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------


def test_required_challenge_types_is_tuple():
    assert isinstance(REQUIRED_CHALLENGE_TYPES, tuple)


def test_required_challenge_types_contains_nch():
    assert "NCH" in REQUIRED_CHALLENGE_TYPES


def test_required_challenge_types_contains_cmc():
    assert "CMC" in REQUIRED_CHALLENGE_TYPES


def test_required_challenge_types_contains_sch():
    assert "SCH" in REQUIRED_CHALLENGE_TYPES


def test_required_challenge_types_count():
    assert len(REQUIRED_CHALLENGE_TYPES) == 3


def test_valid_challenge_verdicts_is_frozenset():
    assert isinstance(VALID_CHALLENGE_VERDICTS, frozenset)


def test_valid_challenge_verdicts_contains_pass():
    assert "pass" in VALID_CHALLENGE_VERDICTS


def test_valid_challenge_verdicts_contains_marginal():
    assert "marginal" in VALID_CHALLENGE_VERDICTS


def test_valid_challenge_verdicts_contains_fail():
    assert "fail" in VALID_CHALLENGE_VERDICTS


def test_valid_challenge_verdicts_contains_not_run():
    assert "not_run" in VALID_CHALLENGE_VERDICTS


def test_valid_bcr_hardness_grades_is_frozenset():
    assert isinstance(VALID_BCR_HARDNESS_GRADES, frozenset)


def test_valid_bcr_hardness_grades_contains_a():
    assert "A" in VALID_BCR_HARDNESS_GRADES


def test_valid_bcr_hardness_grades_contains_b():
    assert "B" in VALID_BCR_HARDNESS_GRADES


def test_valid_bcr_hardness_grades_contains_c():
    assert "C" in VALID_BCR_HARDNESS_GRADES


def test_valid_bcr_hardness_grades_contains_d():
    assert "D" in VALID_BCR_HARDNESS_GRADES


# ---------------------------------------------------------------------------
# 2. build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_benchmark_challenge_registry():
    assert isinstance(_build(), BenchmarkChallengeRegistry)


def test_build_bcr_id_stored():
    assert _build().bcr_id == "BCR-001"


def test_build_batch_id_stored():
    assert _build().batch_id == "BATCH-01"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v1.0"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_challenges_required_is_3():
    assert _build().n_challenges_required == 3


def test_build_all_pass_gives_grade_a():
    assert _build().hardness_grade == "A"


def test_build_all_pass_n_passed_3():
    assert _build().n_challenges_passed == 3


def test_build_all_pass_n_marginal_0():
    assert _build().n_challenges_marginal == 0


def test_build_all_pass_n_failed_0():
    assert _build().n_challenges_failed == 0


def test_build_all_marginal_gives_grade_b():
    r = _build(
        nch_raw_verdict="mixed_novelty",
        cmc_raw_verdict="gap_marginal",
        sch_raw_verdict="marginal_improvement",
    )
    assert r.hardness_grade == "B"


def test_build_all_marginal_n_marginal_3():
    r = _build(
        nch_raw_verdict="mixed_novelty",
        cmc_raw_verdict="gap_marginal",
        sch_raw_verdict="marginal_improvement",
    )
    assert r.n_challenges_marginal == 3


def test_build_mixed_pass_and_marginal_gives_grade_b():
    r = _build(
        nch_raw_verdict="novel_batch",
        cmc_raw_verdict="gap_marginal",
        sch_raw_verdict="marginal_improvement",
    )
    assert r.hardness_grade == "B"


def test_build_one_fail_gives_grade_c():
    r = _build(
        nch_raw_verdict="near_neighbor_dominated",
        cmc_raw_verdict="gap_meaningful",
        sch_raw_verdict="selection_adds_value",
    )
    assert r.hardness_grade == "C"


def test_build_all_fail_gives_grade_d():
    r = _build(
        nch_raw_verdict="near_neighbor_dominated",
        cmc_raw_verdict="gap_absent",
        sch_raw_verdict="proximity_driven",
    )
    assert r.hardness_grade == "D"


def test_build_not_run_verdicts_give_grade_d():
    r = _build()
    r2 = _build(
        nch_raw_verdict="challenge_not_run",
        cmc_raw_verdict="challenge_not_run",
        sch_raw_verdict="challenge_not_run",
    )
    assert r2.hardness_grade == "D"


def test_build_challenge_entries_length():
    assert len(_build().challenge_entries) == 3


def test_build_challenge_entries_are_challenge_entry():
    for e in _build().challenge_entries:
        assert isinstance(e, ChallengeEntry)


def test_build_nch_entry_challenge_verdict_pass():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["NCH"].challenge_verdict == "pass"


def test_build_cmc_entry_challenge_verdict_pass():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["CMC"].challenge_verdict == "pass"


def test_build_sch_entry_challenge_verdict_pass():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["SCH"].challenge_verdict == "pass"


def test_build_nch_artifact_id_stored():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["NCH"].artifact_id == "NCH-001"


def test_build_cmc_artifact_id_stored():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["CMC"].artifact_id == "CMC-001"


def test_build_sch_artifact_id_stored():
    entries = {e.challenge_type: e for e in _build().challenge_entries}
    assert entries["SCH"].artifact_id == "SCH-001"


def test_build_nch_mixed_novelty_maps_to_marginal():
    r = _build(nch_raw_verdict="mixed_novelty")
    entries = {e.challenge_type: e for e in r.challenge_entries}
    assert entries["NCH"].challenge_verdict == "marginal"


def test_build_cmc_gap_marginal_maps_to_marginal():
    r = _build(cmc_raw_verdict="gap_marginal")
    entries = {e.challenge_type: e for e in r.challenge_entries}
    assert entries["CMC"].challenge_verdict == "marginal"


def test_build_sch_marginal_improvement_maps_to_marginal():
    r = _build(sch_raw_verdict="marginal_improvement")
    entries = {e.challenge_type: e for e in r.challenge_entries}
    assert entries["SCH"].challenge_verdict == "marginal"


def test_build_nch_nn_dominated_maps_to_fail():
    r = _build(nch_raw_verdict="near_neighbor_dominated")
    entries = {e.challenge_type: e for e in r.challenge_entries}
    assert entries["NCH"].challenge_verdict == "fail"


def test_build_limitations_stored():
    assert _build().limitations == ["dry-lab only"]


def test_build_created_at_stored():
    assert _build().created_at == "2026-07-10"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_bcr_id_prefix():
    with pytest.raises(ValueError, match="BCR-"):
        _build(bcr_id="BAD-001")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_invalid_hardness_grade():
    bcr = _build()
    bcr.hardness_grade = "X"
    with pytest.raises(ValueError, match="hardness_grade"):
        validate_benchmark_challenge_registry(bcr)


def test_validate_rejects_n_challenges_required_mismatch():
    bcr = _build()
    bcr.n_challenges_required = 5
    with pytest.raises(ValueError, match="n_challenges_required"):
        validate_benchmark_challenge_registry(bcr)


def test_validate_rejects_n_challenges_passed_mismatch():
    bcr = _build()
    bcr.n_challenges_passed = 99
    with pytest.raises(ValueError, match="n_challenges_passed"):
        validate_benchmark_challenge_registry(bcr)


def test_validate_rejects_dry_lab_only_false():
    bcr = _build()
    bcr.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_benchmark_challenge_registry(bcr)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format
# ---------------------------------------------------------------------------


def test_format_contains_bcr_id():
    assert "BCR-001" in format_benchmark_challenge_registry(_build())


def test_format_contains_batch_id():
    assert "BATCH-01" in format_benchmark_challenge_registry(_build())


def test_format_contains_hardness_grade():
    assert "A" in format_benchmark_challenge_registry(_build())


def test_format_contains_nch():
    assert "NCH" in format_benchmark_challenge_registry(_build())


def test_format_contains_cmc():
    assert "CMC" in format_benchmark_challenge_registry(_build())


def test_format_contains_sch():
    assert "SCH" in format_benchmark_challenge_registry(_build())


def test_format_contains_pass_verdict():
    assert "PASS" in format_benchmark_challenge_registry(_build())


def test_format_contains_limitations():
    assert "dry-lab only" in format_benchmark_challenge_registry(_build())


def test_format_contains_dry_lab_only():
    assert "dry_lab_only: True" in format_benchmark_challenge_registry(_build())


def test_format_is_string():
    assert isinstance(format_benchmark_challenge_registry(_build()), str)
