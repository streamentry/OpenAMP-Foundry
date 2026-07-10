"""Tests for BXR- batch explanation report schema."""

import pytest
from openamp_foundry.evidence.batch_explanation_report import (
    BatchExplanationReport,
    CandidateExplanationEntry,
    VALID_BXR_VERDICTS,
    VALID_SELECTION_REASON_CATEGORIES,
    VALID_CONFIDENCE_LEVELS,
    EXPLAINED_FRACTION_THRESHOLD,
    PARTIAL_FRACTION_THRESHOLD,
    build_batch_explanation_report,
    format_batch_explanation_report,
    validate_batch_explanation_report,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

_ALL_EXPLAINED = [
    {
        "candidate_id": "CAND-001",
        "selection_reason": "winner_exploit",
        "confidence_level": "high",
        "predicted_score": 0.85,
        "uncertainty_score": 0.10,
        "safety_cleared": True,
        "reason_notes": "Strong predicted activity and low uncertainty",
    },
    {
        "candidate_id": "CAND-002",
        "selection_reason": "uncertainty_probe",
        "confidence_level": "low",
        "predicted_score": 0.45,
        "uncertainty_score": 0.80,
        "safety_cleared": True,
        "reason_notes": "High uncertainty; exploration pick",
    },
    {
        "candidate_id": "CAND-003",
        "selection_reason": "diversity_anchor",
        "confidence_level": "moderate",
        "predicted_score": 0.60,
        "uncertainty_score": 0.35,
        "safety_cleared": True,
        "reason_notes": "",
    },
]

_PARTIALLY_EXPLAINED = [
    {
        "candidate_id": "CAND-001",
        "selection_reason": "winner_exploit",
        "confidence_level": "high",
        "predicted_score": 0.82,
        "uncertainty_score": 0.15,
        "safety_cleared": True,
        "reason_notes": "",
    },
    {
        "candidate_id": "CAND-002",
        "selection_reason": "uncertainty_probe",
        "confidence_level": "low",
        "predicted_score": 0.40,
        "uncertainty_score": 0.75,
        "safety_cleared": False,
        "reason_notes": "Safety gate not yet run",
    },
    {
        "candidate_id": "CAND-003",
        "selection_reason": "safety_retest",
        "confidence_level": "moderate",
        "predicted_score": 0.70,
        "uncertainty_score": 0.25,
        "safety_cleared": True,
        "reason_notes": "",
    },
    {
        "candidate_id": "CAND-004",
        "selection_reason": "winner_exploit",
        "confidence_level": "high",
        "predicted_score": 0.90,
        "uncertainty_score": 0.05,
        "safety_cleared": False,
        "reason_notes": "Awaiting safety review",
    },
]

_ALL_EXPLOIT = [
    {
        "candidate_id": "CAND-001",
        "selection_reason": "winner_exploit",
        "confidence_level": "high",
        "predicted_score": 0.90,
        "uncertainty_score": 0.05,
        "safety_cleared": True,
        "reason_notes": "",
    },
]

_ALL_PROBE = [
    {
        "candidate_id": "CAND-001",
        "selection_reason": "uncertainty_probe",
        "confidence_level": "low",
        "predicted_score": 0.30,
        "uncertainty_score": 0.85,
        "safety_cleared": True,
        "reason_notes": "",
    },
]


def _build(**kwargs):
    defaults = dict(
        bxr_id="BXR-001",
        pipeline_version="v2.1",
        batch_id="BSP-001",
        candidate_explanations=_ALL_EXPLAINED,
        limitations=["dry-lab only", "predicted scores are estimates"],
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_batch_explanation_report(**defaults)


# ---------------------------------------------------------------------------
# Section 1: Constants
# ---------------------------------------------------------------------------


def test_valid_bxr_verdicts_is_frozenset():
    assert isinstance(VALID_BXR_VERDICTS, frozenset)


def test_valid_bxr_verdicts_contains_explained():
    assert "explained" in VALID_BXR_VERDICTS


def test_valid_bxr_verdicts_contains_partially_explained():
    assert "partially_explained" in VALID_BXR_VERDICTS


def test_valid_bxr_verdicts_contains_unexplained():
    assert "unexplained" in VALID_BXR_VERDICTS


def test_valid_selection_reason_categories_is_frozenset():
    assert isinstance(VALID_SELECTION_REASON_CATEGORIES, frozenset)


def test_valid_selection_reason_categories_contains_winner_exploit():
    assert "winner_exploit" in VALID_SELECTION_REASON_CATEGORIES


def test_valid_selection_reason_categories_contains_uncertainty_probe():
    assert "uncertainty_probe" in VALID_SELECTION_REASON_CATEGORIES


def test_valid_selection_reason_categories_contains_diversity_anchor():
    assert "diversity_anchor" in VALID_SELECTION_REASON_CATEGORIES


def test_valid_selection_reason_categories_contains_safety_retest():
    assert "safety_retest" in VALID_SELECTION_REASON_CATEGORIES


def test_valid_selection_reason_categories_contains_negative_control():
    assert "negative_control" in VALID_SELECTION_REASON_CATEGORIES


def test_explained_fraction_threshold():
    assert EXPLAINED_FRACTION_THRESHOLD == 0.80


def test_partial_fraction_threshold():
    assert PARTIAL_FRACTION_THRESHOLD == 0.50


# ---------------------------------------------------------------------------
# Section 2: build – happy paths
# ---------------------------------------------------------------------------


def test_build_returns_batch_explanation_report():
    assert isinstance(_build(), BatchExplanationReport)


def test_build_bxr_id_stored():
    assert _build().bxr_id == "BXR-001"


def test_build_pipeline_version_stored():
    assert _build().pipeline_version == "v2.1"


def test_build_batch_id_stored():
    assert _build().batch_id == "BSP-001"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_n_candidates_auto_computed():
    r = _build()
    assert r.n_candidates == 3


def test_build_n_safety_cleared_auto_computed():
    r = _build()
    assert r.n_safety_cleared == 3


def test_build_n_explained_equals_safety_cleared():
    r = _build()
    assert r.n_explained == r.n_safety_cleared


def test_build_explained_verdict_when_all_safety_cleared():
    r = _build()
    assert r.verdict == "explained"


def test_build_explanation_fraction_one_when_all_cleared():
    r = _build()
    assert r.explanation_fraction == 1.0


def test_build_partially_explained_verdict():
    r = _build(candidate_explanations=_PARTIALLY_EXPLAINED)
    assert r.verdict == "partially_explained"


def test_build_partially_explained_n_safety_cleared():
    r = _build(candidate_explanations=_PARTIALLY_EXPLAINED)
    assert r.n_safety_cleared == 2


def test_build_partially_explained_explanation_fraction():
    r = _build(candidate_explanations=_PARTIALLY_EXPLAINED)
    assert abs(r.explanation_fraction - 0.50) < 1e-4


def test_build_exploit_fraction_all_exploit():
    r = _build(candidate_explanations=_ALL_EXPLOIT)
    assert r.exploit_fraction == 1.0


def test_build_probe_fraction_all_probe():
    r = _build(candidate_explanations=_ALL_PROBE)
    assert r.probe_fraction == 1.0


def test_build_unexplained_verdict_when_empty():
    r = _build(candidate_explanations=[])
    assert r.verdict == "unexplained"


def test_build_empty_n_candidates_zero():
    r = _build(candidate_explanations=[])
    assert r.n_candidates == 0


def test_build_empty_fractions_zero():
    r = _build(candidate_explanations=[])
    assert r.explanation_fraction == 0.0
    assert r.exploit_fraction == 0.0
    assert r.probe_fraction == 0.0


# ---------------------------------------------------------------------------
# Section 3: validate – rejection cases
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_bxr_id_prefix():
    with pytest.raises(ValueError, match="BXR-"):
        _build(bxr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        _build(batch_id="")


def test_validate_rejects_invalid_selection_reason():
    entries = [{"candidate_id": "X", "selection_reason": "unknown_reason",
                "confidence_level": "high", "predicted_score": 0.5,
                "uncertainty_score": 0.1, "safety_cleared": True}]
    with pytest.raises(ValueError, match="VALID_SELECTION_REASON_CATEGORIES"):
        _build(candidate_explanations=entries)


def test_validate_rejects_invalid_confidence_level():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "unknown_conf", "predicted_score": 0.5,
                "uncertainty_score": 0.1, "safety_cleared": True}]
    with pytest.raises(ValueError, match="VALID_CONFIDENCE_LEVELS"):
        _build(candidate_explanations=entries)


def test_validate_rejects_predicted_score_below_negative_one():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": -1.5,
                "uncertainty_score": 0.1, "safety_cleared": True}]
    with pytest.raises(ValueError, match="predicted_score"):
        _build(candidate_explanations=entries)


def test_validate_rejects_predicted_score_above_one():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": 1.5,
                "uncertainty_score": 0.1, "safety_cleared": True}]
    with pytest.raises(ValueError, match="predicted_score"):
        _build(candidate_explanations=entries)


def test_validate_rejects_uncertainty_score_below_negative_one():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": 0.5,
                "uncertainty_score": -1.5, "safety_cleared": True}]
    with pytest.raises(ValueError, match="uncertainty_score"):
        _build(candidate_explanations=entries)


def test_validate_rejects_uncertainty_score_above_one():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": 0.5,
                "uncertainty_score": 1.5, "safety_cleared": True}]
    with pytest.raises(ValueError, match="uncertainty_score"):
        _build(candidate_explanations=entries)


def test_validate_rejects_reason_notes_too_long():
    entries = [{"candidate_id": "X", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": 0.5,
                "uncertainty_score": 0.1, "safety_cleared": True,
                "reason_notes": "x" * 201}]
    with pytest.raises(ValueError, match="reason_notes"):
        _build(candidate_explanations=entries)


def test_validate_rejects_empty_candidate_id():
    entries = [{"candidate_id": "", "selection_reason": "winner_exploit",
                "confidence_level": "high", "predicted_score": 0.5,
                "uncertainty_score": 0.1, "safety_cleared": True}]
    with pytest.raises(ValueError, match="candidate_id"):
        _build(candidate_explanations=entries)


def test_validate_rejects_n_candidates_mismatch():
    r = _build()
    r.n_candidates = 999
    with pytest.raises(ValueError, match="n_candidates"):
        validate_batch_explanation_report(r)


def test_validate_rejects_n_safety_cleared_mismatch():
    r = _build()
    r.n_safety_cleared = 999
    with pytest.raises(ValueError, match="n_safety_cleared"):
        validate_batch_explanation_report(r)


def test_validate_rejects_n_explained_not_equal_safety():
    r = _build()
    r.n_explained = 0
    with pytest.raises(ValueError, match="n_explained"):
        validate_batch_explanation_report(r)


def test_validate_rejects_explanation_fraction_mismatch():
    r = _build()
    r.explanation_fraction = 0.99
    with pytest.raises(ValueError, match="explanation_fraction"):
        validate_batch_explanation_report(r)


def test_validate_rejects_dry_lab_only_false():
    r = _build()
    r.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_batch_explanation_report(r)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError, match="limitations"):
        _build(limitations=[])


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# Section 4: format
# ---------------------------------------------------------------------------


def test_format_contains_bxr_id():
    assert "BXR-001" in format_batch_explanation_report(_build())


def test_format_contains_batch_id():
    assert "BSP-001" in format_batch_explanation_report(_build())


def test_format_contains_verdict():
    assert "explained" in format_batch_explanation_report(_build())


def test_format_contains_candidate_id():
    text = format_batch_explanation_report(_build())
    assert "CAND-001" in text


def test_format_contains_selection_reason():
    text = format_batch_explanation_report(_build())
    assert "winner_exploit" in text


def test_format_contains_safety_flag():
    text = format_batch_explanation_report(_build())
    assert "CLEARED" in text


def test_format_contains_limitations():
    assert "dry-lab only" in format_batch_explanation_report(_build())


def test_format_is_string():
    assert isinstance(format_batch_explanation_report(_build()), str)
