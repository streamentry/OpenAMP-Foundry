import pytest
from src.openamp_foundry.evidence.hit_confirmation_report import (
    VALID_CONFIRMATION_VERDICTS,
    VALID_DIVERGENCE_TYPES,
    VALID_PREDICTION_QUALITY_GRADES,
    HitConfirmationReport,
    HCRValidationResult,
    validate_hit_confirmation_report,
    build_hit_confirmation_report,
    format_hit_confirmation_report,
)


def _valid_report(**kwargs):
    defaults = dict(
        hcr_id="HCR-0001",
        candidate_id="AMPF-0001",
        sequence="KWKLFKKIEK",
        whr_ids=["WHR-0001"],
        pre_registration_id="PRE-0001",
        dry_lab_score=0.85,
        confirmation_verdict="confirmed_hit",
        divergence_types=["no_divergence"],
        prediction_quality_grade="A",
        n_experiments=3,
        n_confirmed=2,
        n_inactive=1,
        n_inconclusive=0,
        dry_lab_only=False,
        limitations="Single lab, single strain, not generalizable.",
        notes="",
    )
    defaults.update(kwargs)
    return HitConfirmationReport(**defaults)


# ── Constants ──────────────────────────────────────────────────────────────────

class TestConstants:
    def test_valid_confirmation_verdicts_is_frozenset(self):
        assert isinstance(VALID_CONFIRMATION_VERDICTS, frozenset)

    def test_valid_confirmation_verdicts_count(self):
        assert len(VALID_CONFIRMATION_VERDICTS) == 4

    def test_confirmed_hit_in_verdicts(self):
        assert "confirmed_hit" in VALID_CONFIRMATION_VERDICTS

    def test_partial_hit_in_verdicts(self):
        assert "partial_hit" in VALID_CONFIRMATION_VERDICTS

    def test_not_confirmed_in_verdicts(self):
        assert "not_confirmed" in VALID_CONFIRMATION_VERDICTS

    def test_inconclusive_in_verdicts(self):
        assert "inconclusive" in VALID_CONFIRMATION_VERDICTS

    def test_valid_divergence_types_is_frozenset(self):
        assert isinstance(VALID_DIVERGENCE_TYPES, frozenset)

    def test_valid_divergence_types_count(self):
        assert len(VALID_DIVERGENCE_TYPES) == 7

    def test_no_divergence_in_divergence_types(self):
        assert "no_divergence" in VALID_DIVERGENCE_TYPES

    def test_mic_above_predicted_range_in_divergence_types(self):
        assert "mic_above_predicted_range" in VALID_DIVERGENCE_TYPES

    def test_multiple_divergences_in_divergence_types(self):
        assert "multiple_divergences" in VALID_DIVERGENCE_TYPES

    def test_valid_prediction_quality_grades_is_frozenset(self):
        assert isinstance(VALID_PREDICTION_QUALITY_GRADES, frozenset)

    def test_prediction_quality_grades_count(self):
        assert len(VALID_PREDICTION_QUALITY_GRADES) == 5

    def test_grade_a_in_quality_grades(self):
        assert "A" in VALID_PREDICTION_QUALITY_GRADES

    def test_grade_na_in_quality_grades(self):
        assert "N/A" in VALID_PREDICTION_QUALITY_GRADES


# ── Dataclass ──────────────────────────────────────────────────────────────────

class TestHitConfirmationReportDataclass:
    def test_instantiation(self):
        r = _valid_report()
        assert r.hcr_id == "HCR-0001"

    def test_whr_ids_list(self):
        r = _valid_report(whr_ids=["WHR-0001", "WHR-0002"])
        assert len(r.whr_ids) == 2

    def test_dry_lab_only_false(self):
        r = _valid_report()
        assert r.dry_lab_only is False

    def test_pre_registration_id_optional(self):
        r = _valid_report(pre_registration_id=None)
        assert r.pre_registration_id is None

    def test_notes_default_empty(self):
        r = _valid_report(notes="")
        assert r.notes == ""

    def test_divergence_types_list(self):
        r = _valid_report(divergence_types=["mic_above_predicted_range"])
        assert "mic_above_predicted_range" in r.divergence_types


# ── Validation ─────────────────────────────────────────────────────────────────

class TestValidateHitConfirmationReport:
    def test_valid_report_passes(self):
        r = _valid_report()
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_invalid_hcr_id_prefix(self):
        r = _valid_report(hcr_id="BAD-0001")
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("hcr_id" in v for v in result.violations)

    def test_empty_candidate_id_blocked(self):
        r = _valid_report(candidate_id="")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_toy_candidate_id_blocked(self):
        r = _valid_report(candidate_id="TOY-0001")
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("TOY-" in v for v in result.violations)

    def test_short_sequence_blocked(self):
        r = _valid_report(sequence="KWK")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_empty_whr_ids_blocked(self):
        r = _valid_report(whr_ids=[])
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("whr_id" in v for v in result.violations)

    def test_invalid_whr_id_prefix_blocked(self):
        r = _valid_report(whr_ids=["BAD-0001"])
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_dry_lab_score_above_1_blocked(self):
        r = _valid_report(dry_lab_score=1.5)
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_dry_lab_score_negative_blocked(self):
        r = _valid_report(dry_lab_score=-0.1)
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_invalid_confirmation_verdict_blocked(self):
        r = _valid_report(confirmation_verdict="definitely_active")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_invalid_divergence_type_blocked(self):
        r = _valid_report(divergence_types=["unknown_divergence"])
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_invalid_prediction_quality_grade_blocked(self):
        r = _valid_report(prediction_quality_grade="E")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_n_experiments_zero_blocked(self):
        r = _valid_report(n_experiments=0)
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_n_confirmed_negative_blocked(self):
        r = _valid_report(n_confirmed=-1)
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_counts_exceed_n_experiments_blocked(self):
        r = _valid_report(n_experiments=2, n_confirmed=2, n_inactive=1, n_inconclusive=0)
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_dry_lab_only_true_blocked(self):
        r = _valid_report(dry_lab_only=True)
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("dry_lab_only" in v for v in result.violations)

    def test_empty_limitations_blocked(self):
        r = _valid_report(limitations="")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_short_limitations_blocked(self):
        r = _valid_report(limitations="Too short")
        result = validate_hit_confirmation_report(r)
        assert not result.valid

    def test_confirmed_hit_requires_n_confirmed_ge_1(self):
        r = _valid_report(confirmation_verdict="confirmed_hit", n_confirmed=0, n_inactive=2, n_inconclusive=1)
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("n_confirmed" in v for v in result.violations)

    def test_not_confirmed_requires_n_inactive_ge_1(self):
        r = _valid_report(confirmation_verdict="not_confirmed", n_confirmed=0, n_inactive=0, n_inconclusive=3)
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("n_inactive" in v for v in result.violations)

    def test_no_divergence_cannot_coexist_with_other_types(self):
        r = _valid_report(divergence_types=["no_divergence", "mic_above_predicted_range"])
        result = validate_hit_confirmation_report(r)
        assert not result.valid
        assert any("no_divergence" in v for v in result.violations)

    def test_multiple_whr_ids_valid(self):
        r = _valid_report(whr_ids=["WHR-0001", "WHR-0002", "WHR-0003"])
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_dry_lab_score_boundary_0(self):
        r = _valid_report(dry_lab_score=0.0)
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_dry_lab_score_boundary_1(self):
        r = _valid_report(dry_lab_score=1.0)
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_partial_hit_verdict_valid(self):
        r = _valid_report(confirmation_verdict="partial_hit", n_confirmed=1, n_inactive=1, n_inconclusive=1)
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_inconclusive_verdict_valid(self):
        r = _valid_report(confirmation_verdict="inconclusive", n_confirmed=0, n_inactive=0, n_inconclusive=3)
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_multiple_divergence_types_valid(self):
        r = _valid_report(divergence_types=["mic_above_predicted_range", "selectivity_mismatch"])
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_grade_b_valid(self):
        r = _valid_report(prediction_quality_grade="B")
        result = validate_hit_confirmation_report(r)
        assert result.valid

    def test_grade_na_valid(self):
        r = _valid_report(prediction_quality_grade="N/A")
        result = validate_hit_confirmation_report(r)
        assert result.valid


# ── Build ──────────────────────────────────────────────────────────────────────

class TestBuildHitConfirmationReport:
    def test_build_valid(self):
        r = build_hit_confirmation_report(
            hcr_id="HCR-0001",
            candidate_id="AMPF-0001",
            sequence="KWKLFKKIEK",
            whr_ids=["WHR-0001"],
            dry_lab_score=0.85,
            confirmation_verdict="confirmed_hit",
            divergence_types=["no_divergence"],
            prediction_quality_grade="A",
            n_experiments=3,
            n_confirmed=2,
            n_inactive=1,
            n_inconclusive=0,
            limitations="Single lab, single strain, not generalizable.",
        )
        assert r.hcr_id == "HCR-0001"
        assert r.dry_lab_only is False

    def test_build_enforces_dry_lab_only_false(self):
        r = build_hit_confirmation_report(
            hcr_id="HCR-0002",
            candidate_id="AMPF-0002",
            sequence="FLPKLKKLLK",
            whr_ids=["WHR-0002"],
            dry_lab_score=0.72,
            confirmation_verdict="partial_hit",
            divergence_types=["mic_above_predicted_range"],
            prediction_quality_grade="C",
            n_experiments=2,
            n_confirmed=1,
            n_inactive=1,
            n_inconclusive=0,
            limitations="Limited to E. coli K-12, results not extrapolatable.",
        )
        assert r.dry_lab_only is False

    def test_build_raises_on_toy_id(self):
        with pytest.raises(ValueError):
            build_hit_confirmation_report(
                hcr_id="HCR-0003",
                candidate_id="TOY-0001",
                sequence="KWKLFKKIEK",
                whr_ids=["WHR-0001"],
                dry_lab_score=0.85,
                confirmation_verdict="confirmed_hit",
                divergence_types=["no_divergence"],
                prediction_quality_grade="A",
                n_experiments=1,
                n_confirmed=1,
                n_inactive=0,
                n_inconclusive=0,
                limitations="Single lab, single strain.",
            )

    def test_build_raises_on_invalid_verdict(self):
        with pytest.raises(ValueError):
            build_hit_confirmation_report(
                hcr_id="HCR-0004",
                candidate_id="AMPF-0001",
                sequence="KWKLFKKIEK",
                whr_ids=["WHR-0001"],
                dry_lab_score=0.85,
                confirmation_verdict="probably_active",
                divergence_types=["no_divergence"],
                prediction_quality_grade="A",
                n_experiments=1,
                n_confirmed=1,
                n_inactive=0,
                n_inconclusive=0,
                limitations="Single lab, single strain.",
            )

    def test_build_with_pre_registration_id(self):
        r = build_hit_confirmation_report(
            hcr_id="HCR-0005",
            candidate_id="AMPF-0005",
            sequence="GIKCKILKKLR",
            whr_ids=["WHR-0005"],
            dry_lab_score=0.91,
            confirmation_verdict="confirmed_hit",
            divergence_types=["no_divergence"],
            prediction_quality_grade="A",
            n_experiments=4,
            n_confirmed=4,
            n_inactive=0,
            n_inconclusive=0,
            limitations="Single lab, reproducibility not independently verified.",
            pre_registration_id="PRE-0001",
        )
        assert r.pre_registration_id == "PRE-0001"

    def test_build_raises_on_empty_whr_ids(self):
        with pytest.raises(ValueError):
            build_hit_confirmation_report(
                hcr_id="HCR-0006",
                candidate_id="AMPF-0006",
                sequence="KWKLFKKIEK",
                whr_ids=[],
                dry_lab_score=0.85,
                confirmation_verdict="confirmed_hit",
                divergence_types=["no_divergence"],
                prediction_quality_grade="A",
                n_experiments=1,
                n_confirmed=1,
                n_inactive=0,
                n_inconclusive=0,
                limitations="Single lab, single strain.",
            )

    def test_build_not_confirmed_verdict(self):
        r = build_hit_confirmation_report(
            hcr_id="HCR-0007",
            candidate_id="AMPF-0007",
            sequence="KWKLFKKIEK",
            whr_ids=["WHR-0007"],
            dry_lab_score=0.60,
            confirmation_verdict="not_confirmed",
            divergence_types=["mic_above_predicted_range"],
            prediction_quality_grade="D",
            n_experiments=3,
            n_confirmed=0,
            n_inactive=3,
            n_inconclusive=0,
            limitations="Multiple labs, consistent result, generalizability unknown.",
        )
        assert r.confirmation_verdict == "not_confirmed"


# ── Format ─────────────────────────────────────────────────────────────────────

class TestFormatHitConfirmationReport:
    def _build(self, **kwargs):
        defaults = dict(
            hcr_id="HCR-0001",
            candidate_id="AMPF-0001",
            sequence="KWKLFKKIEK",
            whr_ids=["WHR-0001"],
            dry_lab_score=0.85,
            confirmation_verdict="confirmed_hit",
            divergence_types=["no_divergence"],
            prediction_quality_grade="A",
            n_experiments=3,
            n_confirmed=2,
            n_inactive=1,
            n_inconclusive=0,
            limitations="Single lab, single strain, not generalizable.",
        )
        defaults.update(kwargs)
        return build_hit_confirmation_report(**defaults)

    def test_format_returns_string(self):
        r = self._build()
        assert isinstance(format_hit_confirmation_report(r), str)

    def test_format_contains_hcr_id(self):
        r = self._build()
        assert "HCR-0001" in format_hit_confirmation_report(r)

    def test_format_contains_candidate_id(self):
        r = self._build()
        assert "AMPF-0001" in format_hit_confirmation_report(r)

    def test_format_contains_verdict(self):
        r = self._build()
        assert "confirmed_hit" in format_hit_confirmation_report(r)

    def test_format_contains_dry_lab_score(self):
        r = self._build()
        assert "0.850" in format_hit_confirmation_report(r)

    def test_format_contains_dry_lab_only_false(self):
        r = self._build()
        assert "dry_lab_only: False" in format_hit_confirmation_report(r)

    def test_format_contains_prediction_quality(self):
        r = self._build()
        assert "A" in format_hit_confirmation_report(r)

    def test_format_contains_limitations(self):
        r = self._build()
        assert "Single lab" in format_hit_confirmation_report(r)

    def test_format_contains_whr_ids(self):
        r = self._build()
        assert "WHR-0001" in format_hit_confirmation_report(r)

    def test_format_contains_pre_registration_id(self):
        r = self._build(pre_registration_id="PRE-0001")
        assert "PRE-0001" in format_hit_confirmation_report(r)

    def test_format_omits_pre_registration_when_none(self):
        r = self._build()
        out = format_hit_confirmation_report(r)
        assert "Pre-Registration" not in out

    def test_format_multiline(self):
        r = self._build()
        lines = format_hit_confirmation_report(r).split("\n")
        assert len(lines) >= 7

    def test_format_not_confirmed_verdict(self):
        r = self._build(
            hcr_id="HCR-0007",
            candidate_id="AMPF-0007",
            sequence="KWKLFKKIEK",
            whr_ids=["WHR-0007"],
            dry_lab_score=0.60,
            confirmation_verdict="not_confirmed",
            divergence_types=["mic_above_predicted_range"],
            prediction_quality_grade="D",
            n_experiments=3,
            n_confirmed=0,
            n_inactive=3,
            n_inconclusive=0,
            limitations="Multiple labs, consistent result, generalizability unknown.",
        )
        assert "not_confirmed" in format_hit_confirmation_report(r)
