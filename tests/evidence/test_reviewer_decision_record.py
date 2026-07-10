"""Tests for RDR- reviewer decision record schema."""

import pytest
from openamp_foundry.evidence.reviewer_decision_record import (
    DimensionRating,
    ReviewerDecisionRecord,
    VALID_RDR_DIMENSIONS,
    VALID_RDR_RATINGS,
    VALID_RDR_OVERALL_DECISIONS,
    BLOCKING_RATINGS,
    REQUIRED_DIMENSIONS,
    build_reviewer_decision_record,
    format_reviewer_decision_record,
    validate_reviewer_decision_record,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_dimension_ratings():
    return [
        DimensionRating(dimension="novelty", rating="acceptable", notes="Novel fold."),
        DimensionRating(dimension="controls", rating="acceptable", notes="Controls OK."),
        DimensionRating(dimension="safety", rating="acceptable", notes="Safe."),
        DimensionRating(dimension="synthesis", rating="acceptable", notes="Feasible."),
        DimensionRating(dimension="claim_scope", rating="acceptable", notes="Scoped."),
    ]


def _build(**kwargs):
    defaults = dict(
        rdr_id="RDR-001",
        pipeline_version="v1.0",
        artifact_id="fam-001",
        reviewer_role="external_microbiologist",
        dimension_ratings=_default_dimension_ratings(),
        overall_decision="approved",
        decision_notes="Strong family.",
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_reviewer_decision_record(**defaults)


def _make_rdr(**kwargs):
    defaults = dict(
        rdr_id="RDR-001",
        pipeline_version="v1.0",
        artifact_id="fam-001",
        reviewer_role="external_microbiologist",
        dimension_ratings=_default_dimension_ratings(),
        n_dimensions_assessed=5,
        n_blocking=0,
        has_unassessed_required=False,
        overall_decision="approved",
        decision_notes="Strong family.",
        dry_lab_only=True,
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return ReviewerDecisionRecord(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (14 tests)
# ---------------------------------------------------------------------------


def test_valid_rdr_dimensions_is_frozenset():
    assert isinstance(VALID_RDR_DIMENSIONS, frozenset)


def test_valid_rdr_dimensions_has_five():
    assert len(VALID_RDR_DIMENSIONS) == 5


def test_valid_rdr_dimensions_contains_novelty():
    assert "novelty" in VALID_RDR_DIMENSIONS


def test_valid_rdr_dimensions_contains_controls():
    assert "controls" in VALID_RDR_DIMENSIONS


def test_valid_rdr_dimensions_contains_safety():
    assert "safety" in VALID_RDR_DIMENSIONS


def test_valid_rdr_dimensions_contains_synthesis():
    assert "synthesis" in VALID_RDR_DIMENSIONS


def test_valid_rdr_dimensions_contains_claim_scope():
    assert "claim_scope" in VALID_RDR_DIMENSIONS


def test_valid_rdr_ratings_is_frozenset():
    assert isinstance(VALID_RDR_RATINGS, frozenset)


def test_valid_rdr_ratings_has_four():
    assert len(VALID_RDR_RATINGS) == 4


def test_valid_rdr_overall_decisions_is_frozenset():
    assert isinstance(VALID_RDR_OVERALL_DECISIONS, frozenset)


def test_valid_rdr_overall_decisions_has_four():
    assert len(VALID_RDR_OVERALL_DECISIONS) == 4


def test_required_dimensions_is_tuple_with_three():
    assert isinstance(REQUIRED_DIMENSIONS, tuple)
    assert len(REQUIRED_DIMENSIONS) == 3
    assert REQUIRED_DIMENSIONS == ("novelty", "safety", "claim_scope")


def test_blocking_ratings_is_frozenset():
    assert isinstance(BLOCKING_RATINGS, frozenset)


def test_blocking_ratings_has_one():
    assert len(BLOCKING_RATINGS) == 1
    assert "requires_revision" in BLOCKING_RATINGS


# ---------------------------------------------------------------------------
# 2. build – happy paths (18 tests)
# ---------------------------------------------------------------------------


def test_build_returns_reviewer_decision_record():
    assert isinstance(_build(), ReviewerDecisionRecord)


def test_build_approved_no_blocking():
    r = _build(overall_decision="approved")
    assert r.overall_decision == "approved"
    assert r.n_blocking == 0


def test_build_approved_with_conditions():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="requires_revision", notes="Need more data."
    )
    r = _build(
        dimension_ratings=ratings,
        overall_decision="approved_with_conditions",
    )
    assert r.overall_decision == "approved_with_conditions"
    assert r.n_blocking == 1


def test_build_rejected():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="requires_revision", notes="Not novel."
    )
    ratings[2] = DimensionRating(
        dimension="safety", rating="requires_revision", notes="Toxic."
    )
    r = _build(
        dimension_ratings=ratings,
        overall_decision="rejected",
    )
    assert r.overall_decision == "rejected"
    assert r.n_blocking == 2


def test_build_deferred():
    r = _build(overall_decision="deferred")
    assert r.overall_decision == "deferred"


def test_build_n_dimensions_assessed_all_assessed():
    r = _build()
    assert r.n_dimensions_assessed == 5


def test_build_n_dimensions_assessed_some_not_assessed():
    ratings = _default_dimension_ratings()
    ratings[3] = DimensionRating(
        dimension="synthesis", rating="not_assessed", notes=""
    )
    r = _build(dimension_ratings=ratings)
    assert r.n_dimensions_assessed == 4


def test_build_n_blocking_count():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="requires_revision", notes="Not novel."
    )
    ratings[1] = DimensionRating(
        dimension="controls", rating="requires_revision", notes="Bad controls."
    )
    ratings[2] = DimensionRating(
        dimension="safety", rating="requires_revision", notes="Toxic."
    )
    r = _build(
        dimension_ratings=ratings,
        overall_decision="approved_with_conditions",
    )
    assert r.n_blocking == 3


def test_build_n_blocking_zero():
    r = _build()
    assert r.n_blocking == 0


def test_build_has_unassessed_required_true():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="not_assessed", notes=""
    )
    ratings[4] = DimensionRating(
        dimension="claim_scope",
        rating="requires_revision",
        notes="Overclaimed.",
    )
    r = _build(
        dimension_ratings=ratings,
        overall_decision="approved_with_conditions",
    )
    assert r.has_unassessed_required is True


def test_build_has_unassessed_required_false():
    r = _build()
    assert r.has_unassessed_required is False


def test_build_dimension_stored():
    r = _build()
    assert r.dimension_ratings[0].dimension == "novelty"


def test_build_rating_stored():
    r = _build()
    assert r.dimension_ratings[0].rating == "acceptable"


def test_build_notes_stored():
    r = _build()
    assert r.dimension_ratings[0].notes == "Novel fold."


def test_build_no_duplicate_dimensions():
    ratings = [
        DimensionRating(dimension="novelty", rating="acceptable", notes=""),
        DimensionRating(dimension="controls", rating="acceptable", notes=""),
        DimensionRating(dimension="safety", rating="acceptable", notes=""),
        DimensionRating(dimension="synthesis", rating="acceptable", notes=""),
        DimensionRating(dimension="claim_scope", rating="acceptable", notes=""),
    ]
    r = _build(dimension_ratings=ratings)
    assert len(r.dimension_ratings) == 5


def test_build_rdr_id_stored():
    r = _build(rdr_id="RDR-099")
    assert r.rdr_id == "RDR-099"


def test_build_pipeline_version_stored():
    r = _build(pipeline_version="v2.0")
    assert r.pipeline_version == "v2.0"


def test_build_artifact_id_stored():
    r = _build(artifact_id="fam-099")
    assert r.artifact_id == "fam-099"


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_rdr_id_prefix():
    with pytest.raises(ValueError, match="RDR-"):
        _build(rdr_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_artifact_id():
    with pytest.raises(ValueError):
        _build(artifact_id="")


def test_validate_rejects_empty_reviewer_role():
    with pytest.raises(ValueError):
        _build(reviewer_role="")


def test_validate_rejects_invalid_dimension():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="invalid_dim", rating="acceptable", notes=""
    )
    with pytest.raises(ValueError, match="dimension"):
        _build(dimension_ratings=ratings)


def test_validate_rejects_invalid_rating():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="invalid_rating", notes=""
    )
    with pytest.raises(ValueError, match="rating"):
        _build(dimension_ratings=ratings)


def test_validate_rejects_notes_too_long():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty",
        rating="acceptable",
        notes="x" * 301,
    )
    with pytest.raises(ValueError, match="notes"):
        _build(dimension_ratings=ratings)


def test_validate_rejects_duplicate_dimension():
    ratings = _default_dimension_ratings()
    ratings.append(
        DimensionRating(dimension="novelty", rating="acceptable", notes="dup")
    )
    with pytest.raises(ValueError, match="duplicate dimension"):
        _build(dimension_ratings=ratings)


def test_validate_rejects_n_dimensions_assessed_mismatch():
    rdr = _make_rdr()
    rdr.n_dimensions_assessed = 99
    with pytest.raises(ValueError, match="n_dimensions_assessed"):
        validate_reviewer_decision_record(rdr)


def test_validate_rejects_n_blocking_mismatch():
    rdr = _make_rdr()
    rdr.n_blocking = 99
    with pytest.raises(ValueError, match="n_blocking"):
        validate_reviewer_decision_record(rdr)


def test_validate_rejects_has_unassessed_required_mismatch():
    rdr = _make_rdr()
    rdr.has_unassessed_required = True
    with pytest.raises(ValueError, match="has_unassessed_required"):
        validate_reviewer_decision_record(rdr)


def test_validate_rejects_approved_with_blocking():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="requires_revision", notes="Not novel."
    )
    with pytest.raises(ValueError, match="approved"):
        _build(
            dimension_ratings=ratings,
            overall_decision="approved",
        )


def test_validate_rejects_approved_with_unassessed_required():
    ratings = _default_dimension_ratings()
    ratings[0] = DimensionRating(
        dimension="novelty", rating="not_assessed", notes=""
    )
    with pytest.raises(ValueError, match="approved"):
        _build(
            dimension_ratings=ratings,
            overall_decision="approved",
        )


def test_validate_rejects_dry_lab_only_false():
    rdr = _make_rdr()
    rdr.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_reviewer_decision_record(rdr)


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


def test_validate_rejects_invalid_overall_decision():
    with pytest.raises(ValueError, match="overall_decision"):
        _build(overall_decision="invalid_decision")


def test_validate_rejects_approved_with_conditions_no_blocking():
    with pytest.raises(ValueError, match="approved_with_conditions"):
        _build(overall_decision="approved_with_conditions")


def test_validate_rejects_rejected_no_blocking():
    with pytest.raises(ValueError, match="rejected"):
        _build(overall_decision="rejected")


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_rdr_id():
    assert "RDR-001" in format_reviewer_decision_record(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_reviewer_decision_record(_build())


def test_format_contains_artifact_id():
    assert "fam-001" in format_reviewer_decision_record(_build())


def test_format_contains_reviewer_role():
    assert "external_microbiologist" in format_reviewer_decision_record(_build())


def test_format_contains_dimension_ratings():
    output = format_reviewer_decision_record(_build())
    assert "novelty" in output
    assert "acceptable" in output


def test_format_contains_overall_decision():
    assert "approved" in format_reviewer_decision_record(_build())


def test_format_contains_dry_lab_only():
    assert "Dry lab only: True" in format_reviewer_decision_record(_build())


def test_format_is_string():
    assert isinstance(format_reviewer_decision_record(_build()), str)
