"""Tests for recalibration refusal record schema — Phase P P2."""

import pytest
from openamp_foundry.evidence.recalibration_refusal_record import (
    RecalibrationRefusalEntry,
    validate_recalibration_refusal,
    validate_recalibration_refusal_dict,
    RRF_PREFIX,
    VALID_TRIGGER_PREFIXES,
    VALID_REFUSAL_REASONS,
    REFUSAL_NOTES_MAX_LENGTH,
    MIN_BATCHES_FLOOR,
)


def _valid_entry(**kwargs) -> RecalibrationRefusalEntry:
    defaults = dict(
        rrf_id="RRF-001",
        pipeline_version="v1.0.0",
        trigger_id="CPS-001",
        recalibration_refused=True,
        refusal_reason="insufficient_data",
        minimum_batches_required=5,
        batches_evaluated=2,
        refusal_notes="Only 2 batches available; minimum is 5.",
        reviewer="reviewer@example.com",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return RecalibrationRefusalEntry(**defaults)


class TestValidEntry:
    def test_valid_passes(self):
        r = validate_recalibration_refusal(_valid_entry())
        assert r.passed
        assert r.errors == []

    def test_result_fields(self):
        r = validate_recalibration_refusal(_valid_entry())
        assert r.rrf_id == "RRF-001"
        assert r.pipeline_version == "v1.0.0"
        assert r.trigger_id == "CPS-001"
        assert r.recalibration_refused is True
        assert r.refusal_reason == "insufficient_data"
        assert r.dry_lab_only is True

    def test_drm_trigger_passes(self):
        r = validate_recalibration_refusal(_valid_entry(trigger_id="DRM-001"))
        assert r.passed

    def test_effect_within_noise_reason(self):
        r = validate_recalibration_refusal(
            _valid_entry(refusal_reason="effect_within_noise")
        )
        assert r.passed

    def test_recent_recalibration_reason(self):
        r = validate_recalibration_refusal(
            _valid_entry(refusal_reason="recent_recalibration")
        )
        assert r.passed

    def test_conflicting_signals_reason(self):
        r = validate_recalibration_refusal(
            _valid_entry(refusal_reason="conflicting_signals")
        )
        assert r.passed

    def test_reviewer_override_reason_passes_with_warning(self):
        r = validate_recalibration_refusal(
            _valid_entry(refusal_reason="reviewer_override")
        )
        assert r.passed
        assert any("reviewer_override" in w for w in r.warnings)

    def test_no_warnings_for_standard_insufficient_data(self):
        r = validate_recalibration_refusal(_valid_entry())
        assert r.warnings == []

    def test_insufficient_data_but_meets_minimum_warns(self):
        r = validate_recalibration_refusal(
            _valid_entry(
                refusal_reason="insufficient_data",
                minimum_batches_required=3,
                batches_evaluated=5,
            )
        )
        assert r.passed
        assert any("batches_evaluated" in w or "meets minimum" in w for w in r.warnings)

    def test_empty_refusal_notes(self):
        r = validate_recalibration_refusal(_valid_entry(refusal_notes=""))
        assert r.passed

    def test_max_length_notes(self):
        notes = "z" * REFUSAL_NOTES_MAX_LENGTH
        r = validate_recalibration_refusal(_valid_entry(refusal_notes=notes))
        assert r.passed

    def test_zero_batches_evaluated(self):
        r = validate_recalibration_refusal(_valid_entry(batches_evaluated=0))
        assert r.passed

    def test_batches_evaluated_equals_minimum(self):
        r = validate_recalibration_refusal(
            _valid_entry(
                minimum_batches_required=3,
                batches_evaluated=3,
                refusal_reason="effect_within_noise",
            )
        )
        assert r.passed

    def test_minimum_batches_floor(self):
        r = validate_recalibration_refusal(_valid_entry(minimum_batches_required=1))
        assert r.passed

    def test_dry_lab_only_false_allowed(self):
        r = validate_recalibration_refusal(_valid_entry(dry_lab_only=False))
        assert r.passed


class TestRrfIdValidation:
    def test_missing_prefix_fails(self):
        r = validate_recalibration_refusal(_valid_entry(rrf_id="001"))
        assert not r.passed
        assert any("rrf_id" in e for e in r.errors)

    def test_wrong_prefix_fails(self):
        r = validate_recalibration_refusal(_valid_entry(rrf_id="CPS-001"))
        assert not r.passed

    def test_lowercase_prefix_fails(self):
        r = validate_recalibration_refusal(_valid_entry(rrf_id="rrf-001"))
        assert not r.passed

    def test_prefix_only_passes(self):
        r = validate_recalibration_refusal(_valid_entry(rrf_id="RRF-"))
        assert r.passed


class TestTriggerIdValidation:
    def test_no_valid_prefix_fails(self):
        r = validate_recalibration_refusal(_valid_entry(trigger_id="RRF-001"))
        assert not r.passed
        assert any("trigger_id" in e for e in r.errors)

    def test_bare_id_fails(self):
        r = validate_recalibration_refusal(_valid_entry(trigger_id="001"))
        assert not r.passed

    def test_cps_prefix_passes(self):
        r = validate_recalibration_refusal(_valid_entry(trigger_id="CPS-999"))
        assert r.passed

    def test_drm_prefix_passes(self):
        r = validate_recalibration_refusal(_valid_entry(trigger_id="DRM-999"))
        assert r.passed

    @pytest.mark.parametrize("prefix", sorted(VALID_TRIGGER_PREFIXES))
    def test_all_valid_prefixes_pass(self, prefix):
        r = validate_recalibration_refusal(_valid_entry(trigger_id=f"{prefix}001"))
        assert r.passed


class TestRecalibrationRefusedValidation:
    def test_refused_false_fails(self):
        r = validate_recalibration_refusal(_valid_entry(recalibration_refused=False))
        assert not r.passed
        assert any("recalibration_refused" in e for e in r.errors)

    def test_refused_true_required(self):
        entry = _valid_entry(recalibration_refused=False)
        r = validate_recalibration_refusal(entry)
        assert not r.passed
        assert any("CalibrationImprovementRecord" in e or "approved" in e for e in r.errors)


class TestRefusalReasonValidation:
    def test_invalid_reason_fails(self):
        r = validate_recalibration_refusal(_valid_entry(refusal_reason="random_noise"))
        assert not r.passed
        assert any("refusal_reason" in e for e in r.errors)

    def test_empty_reason_fails(self):
        r = validate_recalibration_refusal(_valid_entry(refusal_reason=""))
        assert not r.passed

    @pytest.mark.parametrize("reason", sorted(VALID_REFUSAL_REASONS))
    def test_all_valid_reasons_pass(self, reason):
        r = validate_recalibration_refusal(_valid_entry(refusal_reason=reason))
        assert r.passed or all("refusal_reason" not in e for e in r.errors)


class TestMinimumBatchesValidation:
    def test_below_floor_fails(self):
        r = validate_recalibration_refusal(
            _valid_entry(minimum_batches_required=0)
        )
        assert not r.passed
        assert any("minimum_batches_required" in e for e in r.errors)

    def test_negative_minimum_fails(self):
        r = validate_recalibration_refusal(
            _valid_entry(minimum_batches_required=-1)
        )
        assert not r.passed

    def test_at_floor_passes(self):
        r = validate_recalibration_refusal(
            _valid_entry(minimum_batches_required=MIN_BATCHES_FLOOR)
        )
        assert r.passed


class TestBatchesEvaluatedValidation:
    def test_negative_evaluated_fails(self):
        r = validate_recalibration_refusal(_valid_entry(batches_evaluated=-1))
        assert not r.passed
        assert any("batches_evaluated" in e for e in r.errors)

    def test_zero_passes(self):
        r = validate_recalibration_refusal(_valid_entry(batches_evaluated=0))
        assert r.passed

    def test_large_count_passes(self):
        r = validate_recalibration_refusal(_valid_entry(batches_evaluated=100))
        assert r.passed


class TestRefusalNotesValidation:
    def test_notes_too_long_fails(self):
        notes = "n" * (REFUSAL_NOTES_MAX_LENGTH + 1)
        r = validate_recalibration_refusal(_valid_entry(refusal_notes=notes))
        assert not r.passed
        assert any("refusal_notes" in e for e in r.errors)

    def test_notes_at_limit_passes(self):
        notes = "n" * REFUSAL_NOTES_MAX_LENGTH
        r = validate_recalibration_refusal(_valid_entry(refusal_notes=notes))
        assert r.passed


class TestDictValidation:
    def _valid_dict(self, **kwargs):
        d = dict(
            rrf_id="RRF-001",
            pipeline_version="v1.0.0",
            trigger_id="CPS-001",
            recalibration_refused=True,
            refusal_reason="insufficient_data",
            minimum_batches_required=5,
            batches_evaluated=2,
            refusal_notes="note",
            reviewer="r@example.com",
            dry_lab_only=True,
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_recalibration_refusal_dict(self._valid_dict())
        assert r.passed

    def test_missing_field_fails(self):
        d = self._valid_dict()
        del d["trigger_id"]
        r = validate_recalibration_refusal_dict(d)
        assert not r.passed
        assert any("missing" in e for e in r.errors)

    def test_missing_multiple_fields_fails(self):
        d = self._valid_dict()
        del d["trigger_id"]
        del d["refusal_reason"]
        r = validate_recalibration_refusal_dict(d)
        assert not r.passed

    def test_dry_lab_only_defaults_to_true(self):
        d = self._valid_dict()
        del d["dry_lab_only"]
        r = validate_recalibration_refusal_dict(d)
        assert r.passed
        assert r.dry_lab_only is True

    def test_refused_false_in_dict_fails(self):
        r = validate_recalibration_refusal_dict(
            self._valid_dict(recalibration_refused=False)
        )
        assert not r.passed

    def test_invalid_reason_in_dict_fails(self):
        r = validate_recalibration_refusal_dict(
            self._valid_dict(refusal_reason="bogus")
        )
        assert not r.passed


class TestMultipleErrors:
    def test_multiple_errors_accumulated(self):
        r = validate_recalibration_refusal(
            _valid_entry(
                rrf_id="bad-id",
                trigger_id="bad-trigger",
                recalibration_refused=False,
                refusal_reason="not_valid",
                minimum_batches_required=0,
            )
        )
        assert not r.passed
        assert len(r.errors) >= 5


class TestConstants:
    def test_rrf_prefix(self):
        assert RRF_PREFIX == "RRF-"

    def test_valid_trigger_prefixes(self):
        assert "CPS-" in VALID_TRIGGER_PREFIXES
        assert "DRM-" in VALID_TRIGGER_PREFIXES

    def test_valid_refusal_reasons_count(self):
        assert len(VALID_REFUSAL_REASONS) == 5

    def test_notes_max_length(self):
        assert REFUSAL_NOTES_MAX_LENGTH == 400

    def test_min_batches_floor(self):
        assert MIN_BATCHES_FLOOR == 1
