"""Tests for CSD- claim strength downgrade schema."""

import pytest
from openamp_foundry.evidence.claim_strength_downgrade import (
    ClaimStrengthDowngrade,
    VALID_CSD_CLAIM_CLASSES,
    VALID_CSD_TRIGGER_TYPES,
    VALID_CSD_DOWNGRADE_LEVELS,
    PROOF_LADDER_LEVELS,
    build_claim_strength_downgrade,
    format_claim_strength_downgrade,
    validate_claim_strength_downgrade,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIMITATIONS = ["Claim strength downgraded due to new evidence."]


def _build(**kwargs):
    defaults = dict(
        csd_id="CSD-001",
        pipeline_version="v1.0",
        artifact_id="cert-run-001",
        claim_class="novelty",
        trigger_type="benchmark_result",
        original_claim_text="This is a strong novel AMP family.",
        downgraded_claim_text="This is a candidate AMP family with moderate evidence.",
        original_proof_ladder_level="multi_signal_candidate_evidence",
        downgraded_proof_ladder_level="plausible_candidate",
        downgrade_level="major",
        trigger_evidence_ref="BMC-0003",
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return build_claim_strength_downgrade(**defaults)


def _make_csd(**kwargs):
    defaults = dict(
        csd_id="CSD-001",
        pipeline_version="v1.0",
        artifact_id="cert-run-001",
        claim_class="novelty",
        trigger_type="benchmark_result",
        original_claim_text="This is a strong novel AMP family.",
        downgraded_claim_text="This is a candidate AMP family with moderate evidence.",
        original_proof_ladder_level="multi_signal_candidate_evidence",
        downgraded_proof_ladder_level="plausible_candidate",
        downgrade_level="major",
        proof_ladder_steps_dropped=1,
        trigger_evidence_ref="BMC-0003",
        is_retracted=False,
        dry_lab_only=True,
        limitations=list(LIMITATIONS),
        created_at="2026-07-10",
    )
    defaults.update(kwargs)
    return ClaimStrengthDowngrade(**defaults)


# ---------------------------------------------------------------------------
# 1. Constants (14 tests)
# ---------------------------------------------------------------------------


def test_valid_csd_claim_classes_is_frozenset():
    assert isinstance(VALID_CSD_CLAIM_CLASSES, frozenset)


def test_valid_csd_claim_classes_has_seven():
    assert len(VALID_CSD_CLAIM_CLASSES) == 7


def test_valid_csd_claim_classes_contains_novelty():
    assert "novelty" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_activity():
    assert "activity" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_selectivity():
    assert "selectivity" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_safety():
    assert "safety" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_reproducibility():
    assert "reproducibility" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_calibration_improvement():
    assert "calibration_improvement" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_claim_classes_contains_cheap_baseline_outperformed():
    assert "cheap_baseline_outperformed" in VALID_CSD_CLAIM_CLASSES


def test_valid_csd_trigger_types_is_frozenset():
    assert isinstance(VALID_CSD_TRIGGER_TYPES, frozenset)


def test_valid_csd_trigger_types_has_six():
    assert len(VALID_CSD_TRIGGER_TYPES) == 6


def test_valid_csd_downgrade_levels_is_frozenset():
    assert isinstance(VALID_CSD_DOWNGRADE_LEVELS, frozenset)


def test_valid_csd_downgrade_levels_has_three():
    assert len(VALID_CSD_DOWNGRADE_LEVELS) == 3


def test_proof_ladder_levels_is_tuple_with_seven():
    assert isinstance(PROOF_LADDER_LEVELS, tuple)
    assert len(PROOF_LADDER_LEVELS) == 7
    assert PROOF_LADDER_LEVELS == (
        "speculative",
        "plausible_candidate",
        "multi_signal_candidate_evidence",
        "expert_reviewed_assay_proposal",
        "confirmed_in_vitro_hit",
        "replicated_independent_hit",
        "in_vivo_validated",
    )


# ---------------------------------------------------------------------------
# 2. build – happy paths (18 tests)
# ---------------------------------------------------------------------------


def test_build_returns_claim_strength_downgrade():
    assert isinstance(_build(), ClaimStrengthDowngrade)


def test_build_minor_downgrade_same_level():
    r = _build(
        downgrade_level="minor",
        original_proof_ladder_level="plausible_candidate",
        downgraded_proof_ladder_level="plausible_candidate",
        original_claim_text="Strong novel AMP family.",
        downgraded_claim_text="Likely novel AMP family.",
    )
    assert r.downgrade_level == "minor"
    assert r.proof_ladder_steps_dropped == 0


def test_build_major_downgrade_two_steps():
    r = _build(
        downgrade_level="major",
        original_proof_ladder_level="expert_reviewed_assay_proposal",
        downgraded_proof_ladder_level="plausible_candidate",
    )
    assert r.downgrade_level == "major"
    assert r.proof_ladder_steps_dropped == 2



def test_build_retracted():
    r = _build(
        downgrade_level="retracted",
        original_proof_ladder_level="confirmed_in_vitro_hit",
        downgraded_proof_ladder_level="speculative",
        downgraded_claim_text="RETRACTED",
    )
    assert r.downgrade_level == "retracted"
    assert r.is_retracted is True


def test_build_proof_ladder_steps_dropped_auto_computed():
    r = _build(
        original_proof_ladder_level="multi_signal_candidate_evidence",
        downgraded_proof_ladder_level="speculative",
    )
    orig_idx = PROOF_LADDER_LEVELS.index("multi_signal_candidate_evidence")
    down_idx = PROOF_LADDER_LEVELS.index("speculative")
    assert r.proof_ladder_steps_dropped == orig_idx - down_idx


def test_build_proof_ladder_steps_dropped_zero_for_retracted():
    r = _build(
        downgrade_level="retracted",
        original_proof_ladder_level="confirmed_in_vitro_hit",
        downgraded_proof_ladder_level="speculative",
        downgraded_claim_text="RETRACTED",
    )
    assert r.proof_ladder_steps_dropped == 0


def test_build_is_retracted_true_when_retracted():
    r = _build(
        downgrade_level="retracted",
        original_proof_ladder_level="multi_signal_candidate_evidence",
        downgraded_proof_ladder_level="speculative",
        downgraded_claim_text="RETRACTED",
    )
    assert r.is_retracted is True


def test_build_is_retracted_false_when_not_retracted():
    r = _build()
    assert r.is_retracted is False


def test_build_enforces_retracted_text():
    r = _build(
        downgrade_level="retracted",
        original_proof_ladder_level="confirmed_in_vitro_hit",
        downgraded_proof_ladder_level="speculative",
        downgraded_claim_text="RETRACTED",
    )
    assert r.downgraded_claim_text == "RETRACTED"


def test_build_claim_class_stored():
    r = _build(claim_class="selectivity")
    assert r.claim_class == "selectivity"


def test_build_trigger_type_stored():
    r = _build(trigger_type="reviewer_challenge")
    assert r.trigger_type == "reviewer_challenge"


def test_build_original_claim_text_stored():
    r = _build(original_claim_text="Original strong claim.")
    assert r.original_claim_text == "Original strong claim."


def test_build_downgraded_claim_text_stored():
    r = _build(downgraded_claim_text="Weaker claim text.")
    assert r.downgraded_claim_text == "Weaker claim text."


def test_build_csd_id_stored():
    r = _build(csd_id="CSD-099")
    assert r.csd_id == "CSD-099"


def test_build_pipeline_version_stored():
    r = _build(pipeline_version="v2.0")
    assert r.pipeline_version == "v2.0"


def test_build_artifact_id_stored():
    r = _build(artifact_id="run-099")
    assert r.artifact_id == "run-099"


def test_build_dry_lab_only_true():
    assert _build().dry_lab_only is True


def test_build_limitations_stored():
    r = _build(limitations=["lim1", "lim2"])
    assert r.limitations == ["lim1", "lim2"]


# ---------------------------------------------------------------------------
# 3. validate – rejection cases (18 tests)
# ---------------------------------------------------------------------------


def test_validate_rejects_bad_csd_id_prefix():
    with pytest.raises(ValueError, match="CSD-"):
        _build(csd_id="BAD-001")


def test_validate_rejects_empty_pipeline_version():
    with pytest.raises(ValueError):
        _build(pipeline_version="")


def test_validate_rejects_empty_artifact_id():
    with pytest.raises(ValueError):
        _build(artifact_id="")


def test_validate_rejects_empty_original_claim_text():
    with pytest.raises(ValueError):
        _build(original_claim_text="")


def test_validate_rejects_empty_downgraded_claim_text():
    with pytest.raises(ValueError):
        _build(downgraded_claim_text="")


def test_validate_rejects_invalid_claim_class():
    with pytest.raises(ValueError, match="claim_class"):
        _build(claim_class="invalid_claim_class")


def test_validate_rejects_invalid_trigger_type():
    with pytest.raises(ValueError, match="trigger_type"):
        _build(trigger_type="invalid_trigger")


def test_validate_rejects_invalid_downgrade_level():
    with pytest.raises(ValueError, match="downgrade_level"):
        _build(downgrade_level="invalid_level")


def test_validate_rejects_invalid_original_proof_ladder_level():
    csd = _make_csd()
    csd.original_proof_ladder_level = "not_a_level"
    with pytest.raises(ValueError, match="original_proof_ladder_level"):
        validate_claim_strength_downgrade(csd)


def test_validate_rejects_invalid_downgraded_proof_ladder_level():
    csd = _make_csd()
    csd.downgraded_proof_ladder_level = "not_a_level"
    with pytest.raises(ValueError, match="downgraded_proof_ladder_level"):
        validate_claim_strength_downgrade(csd)


def test_validate_rejects_upgrade():
    with pytest.raises(ValueError, match="upgrade not allowed"):
        _build(
            original_proof_ladder_level="plausible_candidate",
            downgraded_proof_ladder_level="multi_signal_candidate_evidence",
        )


def test_validate_rejects_retracted_but_text_not_retracted():
    with pytest.raises(ValueError, match="RETRACTED"):
        _build(
            downgrade_level="retracted",
            original_proof_ladder_level="multi_signal_candidate_evidence",
            downgraded_proof_ladder_level="speculative",
            downgraded_claim_text="not actually retracted",
        )


def test_validate_rejects_steps_dropped_mismatch():
    csd = _make_csd()
    csd.proof_ladder_steps_dropped = 99
    with pytest.raises(ValueError, match="proof_ladder_steps_dropped"):
        validate_claim_strength_downgrade(csd)


def test_validate_rejects_is_retracted_mismatch():
    csd = _make_csd()
    csd.is_retracted = True
    with pytest.raises(ValueError, match="is_retracted"):
        validate_claim_strength_downgrade(csd)


def test_validate_rejects_dry_lab_only_false():
    csd = _make_csd()
    csd.dry_lab_only = False
    with pytest.raises(ValueError, match="dry_lab_only"):
        validate_claim_strength_downgrade(csd)


def test_validate_rejects_empty_limitations():
    with pytest.raises(ValueError):
        _build(limitations=[])


def test_validate_rejects_empty_trigger_evidence_ref():
    with pytest.raises(ValueError):
        _build(trigger_evidence_ref="")


def test_validate_rejects_empty_created_at():
    with pytest.raises(ValueError):
        _build(created_at="")


# ---------------------------------------------------------------------------
# 4. format (8 tests)
# ---------------------------------------------------------------------------


def test_format_contains_csd_id():
    assert "CSD-001" in format_claim_strength_downgrade(_build())


def test_format_contains_pipeline_version():
    assert "v1.0" in format_claim_strength_downgrade(_build())


def test_format_contains_artifact_id():
    assert "cert-run-001" in format_claim_strength_downgrade(_build())


def test_format_contains_claim_class():
    assert "novelty" in format_claim_strength_downgrade(_build())


def test_format_contains_original_and_downgraded_claim_text():
    output = format_claim_strength_downgrade(_build())
    assert "strong novel AMP family" in output
    assert "candidate AMP family" in output


def test_format_contains_proof_ladder_levels():
    output = format_claim_strength_downgrade(_build())
    assert "multi_signal_candidate_evidence" in output
    assert "plausible_candidate" in output


def test_format_contains_dry_lab_only():
    assert "Dry lab only: True" in format_claim_strength_downgrade(_build())


def test_format_is_string():
    assert isinstance(format_claim_strength_downgrade(_build()), str)
