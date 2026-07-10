"""Tests for CBF- cheap baseline flag schema."""

import pytest
from openamp_foundry.evidence.cheap_baseline_flag import (
    CheapBaselineFlag,
    VALID_CBF_VERDICTS,
    VALID_CBF_BASELINE_TYPES,
    VALID_CBF_SCORER_CLASSES,
    MINIMUM_MEANINGFUL_DELTA,
    BLOCKS_RANKING,
    build_cheap_baseline_flag,
    format_cheap_baseline_flag,
    validate_cheap_baseline_flag,
)


def _build(**kwargs):
    defaults = dict(
        cbf_id="CBF-001",
        scorer_id="ARG-scorer-001",
        scorer_class="sequence_scorer",
        pipeline_version="v3.0",
        baseline_type="charge_only_rank",
        baseline_auroc=0.55,
        scorer_auroc=0.72,
        cbr_ref="CBR-001",
        limitations=["Test limitation"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_cheap_baseline_flag(**defaults)


# ---------------------------------------------------------------------------
# Section 1: Constants
# ---------------------------------------------------------------------------


def test_valid_cbf_verdicts_is_frozenset():
    assert isinstance(VALID_CBF_VERDICTS, frozenset)


def test_valid_cbf_verdicts_contains_baseline_declared():
    assert "baseline_declared" in VALID_CBF_VERDICTS


def test_valid_cbf_verdicts_contains_baseline_missing():
    assert "baseline_missing" in VALID_CBF_VERDICTS


def test_valid_cbf_verdicts_size():
    assert len(VALID_CBF_VERDICTS) == 3


def test_valid_cbf_baseline_types_is_frozenset():
    assert isinstance(VALID_CBF_BASELINE_TYPES, frozenset)


def test_valid_cbf_baseline_types_contains_charge_only_rank():
    assert "charge_only_rank" in VALID_CBF_BASELINE_TYPES


def test_valid_cbf_baseline_types_size():
    assert len(VALID_CBF_BASELINE_TYPES) == 6


def test_valid_cbf_scorer_classes_is_frozenset():
    assert isinstance(VALID_CBF_SCORER_CLASSES, frozenset)


def test_valid_cbf_scorer_classes_contains_sequence_scorer():
    assert "sequence_scorer" in VALID_CBF_SCORER_CLASSES


def test_valid_cbf_scorer_classes_size():
    assert len(VALID_CBF_SCORER_CLASSES) == 6


def test_minimum_meaningful_delta_value():
    assert MINIMUM_MEANINGFUL_DELTA == 0.05


def test_blocks_ranking_constant():
    assert BLOCKS_RANKING is True


# ---------------------------------------------------------------------------
# Section 2: build — happy paths
# ---------------------------------------------------------------------------


def test_build_returns_cheap_baseline_flag():
    assert isinstance(_build(), CheapBaselineFlag)


def test_build_baseline_declared_verdict():
    assert _build().verdict == "baseline_declared"


def test_build_baseline_declared_delta_meaningful():
    cbf = _build()
    assert cbf.auroc_delta == pytest.approx(0.17)
    assert cbf.delta_is_meaningful is True


def test_build_baseline_declared_blocks_ranking_false():
    assert _build().blocks_ranking is False


def test_build_baseline_missing_empty_type():
    cbf = _build(baseline_type="")
    assert cbf.verdict == "baseline_missing"
    assert cbf.blocks_ranking is True


def test_build_baseline_missing_sentinel_baseline_auroc():
    cbf = _build(baseline_auroc=-1.0)
    assert cbf.verdict == "baseline_missing"
    assert cbf.auroc_delta == 0.0


def test_build_baseline_missing_sentinel_scorer_auroc():
    cbf = _build(scorer_auroc=-1.0)
    assert cbf.verdict == "baseline_missing"
    assert cbf.auroc_delta == 0.0


def test_build_baseline_insufficient_small_delta():
    cbf = _build(
        baseline_auroc=0.70, scorer_auroc=0.71, baseline_type="length_only_rank"
    )
    assert cbf.auroc_delta == pytest.approx(0.01)
    assert cbf.verdict == "baseline_insufficient"
    assert cbf.delta_is_meaningful is False
    assert cbf.blocks_ranking is True


def test_build_auto_computed_delta():
    cbf = _build(baseline_auroc=0.50, scorer_auroc=0.80)
    assert cbf.auroc_delta == pytest.approx(0.30)


def test_build_delta_is_meaningful_true():
    assert _build(baseline_auroc=0.40, scorer_auroc=0.90).delta_is_meaningful is True


def test_build_delta_is_meaningful_false():
    cbf = _build(baseline_auroc=0.78, scorer_auroc=0.80)
    assert cbf.delta_is_meaningful is False


def test_build_blocks_ranking_true_missing():
    assert _build(baseline_type="").blocks_ranking is True


def test_build_blocks_ranking_true_insufficient():
    cbf = _build(
        baseline_auroc=0.60, scorer_auroc=0.61, baseline_type="random_selection"
    )
    assert cbf.blocks_ranking is True


def test_build_cbr_ref_stored_when_declared():
    assert _build(cbr_ref="SEG-002").cbr_ref == "SEG-002"


def test_build_cbr_ref_empty():
    assert _build(cbr_ref="").cbr_ref == ""


def test_build_scorer_class_stored():
    assert _build(scorer_class="toxicity_filter").scorer_class == "toxicity_filter"


def test_build_cbf_id_stored():
    assert _build(cbf_id="CBF-042").cbf_id == "CBF-042"


def test_build_scorer_id_stored():
    assert _build(scorer_id="ARG-hello-001").scorer_id == "ARG-hello-001"


# ---------------------------------------------------------------------------
# Section 3: validate — rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_cbf_id_prefix():
    with pytest.raises(ValueError, match="CBF-"):
        _build(cbf_id="BAD-001")


def test_validate_rejects_empty_scorer_id():
    with pytest.raises(ValueError, match="scorer_id"):
        _build(scorer_id="")


def test_validate_rejects_invalid_scorer_class():
    with pytest.raises(ValueError, match="VALID_CBF_SCORER_CLASSES"):
        _build(scorer_class="invalid_class")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError, match="pipeline_version"):
        _build(pipeline_version="")


def test_validate_rejects_invalid_baseline_type():
    with pytest.raises(ValueError, match="VALID_CBF_BASELINE_TYPES"):
        _build(baseline_type="invalid_baseline")


def test_validate_rejects_baseline_auroc_out_of_range_low():
    with pytest.raises(ValueError, match="baseline_auroc"):
        _build(baseline_auroc=-2.0)


def test_validate_rejects_baseline_auroc_out_of_range_high():
    with pytest.raises(ValueError, match="baseline_auroc"):
        _build(baseline_auroc=1.5)


def test_validate_rejects_scorer_auroc_out_of_range():
    with pytest.raises(ValueError, match="scorer_auroc"):
        _build(scorer_auroc=-2.0)


def test_validate_rejects_delta_mismatch():
    cbf = _build()
    cbf.auroc_delta = 0.99
    with pytest.raises(ValueError, match="auroc_delta"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_delta_not_zero_when_sentinel():
    cbf = _build(baseline_auroc=-1.0)
    cbf.auroc_delta = 0.05
    with pytest.raises(ValueError, match="auroc_delta"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_delta_is_meaningful_mismatch():
    cbf = _build()
    cbf.delta_is_meaningful = False
    with pytest.raises(ValueError, match="delta_is_meaningful"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_verdict_mismatch():
    cbf = _build()
    cbf.verdict = "baseline_missing"
    with pytest.raises(ValueError, match="verdict"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_blocks_ranking_mismatch():
    cbf = _build()
    cbf.blocks_ranking = True
    with pytest.raises(ValueError, match="blocks_ranking"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_bad_cbr_ref_prefix():
    with pytest.raises(ValueError, match="CBR-"):
        _build(cbr_ref="XXX-001")


def test_validate_rejects_dry_lab_only_false():
    cbf = _build()
    cbf.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_cheap_baseline_flag(cbf)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError, match="created_at"):
        _build(created_at="")


def test_validate_allows_empty_cbr_ref_when_declared():
    cbf = _build(cbr_ref="")
    assert cbf.cbr_ref == ""
    assert cbf.verdict == "baseline_declared"


# ---------------------------------------------------------------------------
# Section 4: format
# ---------------------------------------------------------------------------


def test_format_contains_cbf_id():
    assert "CBF-001" in format_cheap_baseline_flag(_build())


def test_format_contains_scorer_id():
    text = format_cheap_baseline_flag(_build())
    assert "ARG-scorer-001" in text


def test_format_contains_verdict():
    text = format_cheap_baseline_flag(_build())
    assert "baseline_declared" in text


def test_format_contains_baseline_type():
    text = format_cheap_baseline_flag(_build())
    assert "charge_only_rank" in text


def test_format_contains_delta():
    text = format_cheap_baseline_flag(_build())
    assert "Delta" in text


def test_format_baseline_missing_format():
    cbf = _build(baseline_type="")
    text = format_cheap_baseline_flag(cbf)
    assert "not declared" in text
    assert "baseline_missing" in text


def test_format_contains_blocks_ranking():
    text = format_cheap_baseline_flag(_build())
    assert "Blocks ranking" in text


def test_format_is_string():
    assert isinstance(format_cheap_baseline_flag(_build()), str)
