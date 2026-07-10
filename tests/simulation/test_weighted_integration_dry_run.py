"""Tests for weighted integration dry-run report schema (Phase H H8).

5 test classes, 63 tests total.
"""

import pytest

from openamp_foundry.simulation.weighted_integration_dry_run import (
    FRACTION_TOLERANCE,
    GATE_CLOSED_DISCLAIMER,
    MAJOR_RANK_CHANGE_THRESHOLD,
    SIGNIFICANT_FRACTION_THRESHOLD,
    VALID_DRY_RUN_OUTCOMES,
    VALID_INTEGRATION_GATE_STATUSES,
    VALID_RANK_CHANGE_MAGNITUDES,
    WEIGHTED_INTEGRATION_DRY_RUN_ID_PREFIX,
    WeightedIntegrationDryRunReport,
    format_weighted_integration_dry_run_report,
    validate_weighted_integration_dry_run_report,
)


def _valid_report(**kwargs) -> WeightedIntegrationDryRunReport:
    defaults = dict(
        report_id="WDR-001",
        batch_id="BATCH-001",
        integration_gate_status="closed",
        n_candidates_evaluated=50,
        n_candidates_would_change_rank=10,
        fraction_would_change_rank=0.20,
        max_rank_delta=3,
        rank_change_magnitude="minor",
        dry_run_outcome="reordering_only",
        integration_gate_currently_closed=True,
        results_applied_to_ranking=False,
        dry_lab_only=True,
        gate_closed_disclaimer=GATE_CLOSED_DISCLAIMER,
        notes="Routine dry-run check",
        created_at="2026-01-01",
    )
    defaults.update(kwargs)
    return WeightedIntegrationDryRunReport(**defaults)


# ---------------------------------------------------------------------------
# Class 1: Constants (10 tests)
# ---------------------------------------------------------------------------

class TestWeightedIntegrationDryRunConstants:
    def test_prefix_value(self):
        assert WEIGHTED_INTEGRATION_DRY_RUN_ID_PREFIX == "WDR-"

    def test_major_rank_change_threshold_positive(self):
        assert MAJOR_RANK_CHANGE_THRESHOLD > 0

    def test_significant_fraction_threshold_in_range(self):
        assert 0.0 < SIGNIFICANT_FRACTION_THRESHOLD < 1.0

    def test_fraction_tolerance_small(self):
        assert FRACTION_TOLERANCE < 0.1

    def test_gate_closed_disclaimer_nonempty(self):
        assert len(GATE_CLOSED_DISCLAIMER) > 20

    def test_gate_closed_disclaimer_mentions_dry_run(self):
        assert "dry-run" in GATE_CLOSED_DISCLAIMER.lower() or \
               "dry run" in GATE_CLOSED_DISCLAIMER.lower() or \
               "counterfactual" in GATE_CLOSED_DISCLAIMER.lower()

    def test_valid_gate_statuses_nonempty(self):
        assert len(VALID_INTEGRATION_GATE_STATUSES) >= 3

    def test_valid_rank_change_magnitudes_nonempty(self):
        assert len(VALID_RANK_CHANGE_MAGNITUDES) >= 4

    def test_valid_dry_run_outcomes_nonempty(self):
        assert len(VALID_DRY_RUN_OUTCOMES) >= 4

    def test_closed_in_gate_statuses(self):
        assert "closed" in VALID_INTEGRATION_GATE_STATUSES


# ---------------------------------------------------------------------------
# Class 2: Validation happy and sad paths (20 tests)
# ---------------------------------------------------------------------------

class TestValidateWeightedIntegrationDryRunReport:
    def test_valid_report_has_no_errors(self):
        r = _valid_report()
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_bad_prefix_rejected(self):
        r = _valid_report(report_id="BAD-001")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("report_id" in e for e in errs)

    def test_invalid_gate_status_rejected(self):
        r = _valid_report(integration_gate_status="unknown")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("integration_gate_status" in e for e in errs)

    def test_invalid_rank_change_magnitude_rejected(self):
        r = _valid_report(rank_change_magnitude="huge")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("rank_change_magnitude" in e for e in errs)

    def test_invalid_dry_run_outcome_rejected(self):
        r = _valid_report(dry_run_outcome="everything_changed")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("dry_run_outcome" in e for e in errs)

    def test_fraction_above_one_rejected(self):
        r = _valid_report(fraction_would_change_rank=1.1,
                          n_candidates_would_change_rank=55)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("fraction_would_change_rank" in e for e in errs)

    def test_fraction_inconsistency_rejected(self):
        r = _valid_report(
            n_candidates_evaluated=50,
            n_candidates_would_change_rank=10,
            fraction_would_change_rank=0.99,
        )
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("fraction_would_change_rank" in e for e in errs)

    def test_n_would_change_exceeds_evaluated_rejected(self):
        r = _valid_report(n_candidates_evaluated=10,
                          n_candidates_would_change_rank=15,
                          fraction_would_change_rank=0.20)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("exceed" in e for e in errs)

    def test_dry_lab_only_false_rejected(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("dry_lab_only" in e for e in errs)

    def test_results_applied_true_rejected(self):
        r = _valid_report(results_applied_to_ranking=True)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("results_applied_to_ranking" in e for e in errs)

    def test_gate_closed_status_with_not_closed_flag_rejected(self):
        r = _valid_report(
            integration_gate_status="closed",
            integration_gate_currently_closed=False,
        )
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("integration_gate_currently_closed" in e for e in errs)

    def test_disclaimer_without_dry_run_or_counterfactual_rejected(self):
        r = _valid_report(gate_closed_disclaimer="This is just a report.")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("disclaimer" in e.lower() for e in errs)

    def test_blank_batch_id_rejected(self):
        r = _valid_report(batch_id="   ")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("batch_id" in e for e in errs)

    def test_blank_created_at_rejected(self):
        r = _valid_report(created_at="")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("created_at" in e for e in errs)

    def test_all_gate_statuses_valid(self):
        for gs in VALID_INTEGRATION_GATE_STATUSES:
            extra = {}
            if gs == "closed":
                extra["integration_gate_currently_closed"] = True
            else:
                extra["integration_gate_currently_closed"] = False
            r = _valid_report(integration_gate_status=gs, **extra)
            errs = validate_weighted_integration_dry_run_report(r)
            assert not any("integration_gate_status" in e for e in errs), gs

    def test_all_rank_change_magnitudes_valid(self):
        for mag in VALID_RANK_CHANGE_MAGNITUDES:
            r = _valid_report(rank_change_magnitude=mag)
            errs = validate_weighted_integration_dry_run_report(r)
            assert not any("rank_change_magnitude" in e for e in errs), mag

    def test_all_dry_run_outcomes_valid(self):
        for outcome in VALID_DRY_RUN_OUTCOMES:
            r = _valid_report(dry_run_outcome=outcome)
            errs = validate_weighted_integration_dry_run_report(r)
            assert not any("dry_run_outcome" in e for e in errs), outcome

    def test_fraction_consistency_passes(self):
        r = _valid_report(
            n_candidates_evaluated=50,
            n_candidates_would_change_rank=10,
            fraction_would_change_rank=0.20,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_open_for_review_gate_status_ok(self):
        r = _valid_report(
            integration_gate_status="open_for_review",
            integration_gate_currently_closed=False,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_disclaimer_with_counterfactual_passes(self):
        r = _valid_report(gate_closed_disclaimer="Counterfactual only. Gate still closed.")
        assert validate_weighted_integration_dry_run_report(r) == []


# ---------------------------------------------------------------------------
# Class 3: Edge cases (13 tests)
# ---------------------------------------------------------------------------

class TestWeightedIntegrationDryRunEdgeCases:
    def test_zero_candidates_ok(self):
        r = _valid_report(
            n_candidates_evaluated=0,
            n_candidates_would_change_rank=0,
            fraction_would_change_rank=0.0,
            dry_run_outcome="insufficient_data",
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_all_candidates_would_change(self):
        r = _valid_report(
            n_candidates_evaluated=20,
            n_candidates_would_change_rank=20,
            fraction_would_change_rank=1.0,
            rank_change_magnitude="major",
            dry_run_outcome="reordering_only",
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_no_candidates_would_change(self):
        r = _valid_report(
            n_candidates_evaluated=20,
            n_candidates_would_change_rank=0,
            fraction_would_change_rank=0.0,
            rank_change_magnitude="none",
            dry_run_outcome="no_change",
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_fraction_within_tolerance_passes(self):
        r = _valid_report(
            n_candidates_evaluated=7,
            n_candidates_would_change_rank=2,
            fraction_would_change_rank=0.2857,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_results_applied_false_is_required(self):
        r = _valid_report(results_applied_to_ranking=True)
        errs = validate_weighted_integration_dry_run_report(r)
        assert len(errs) >= 1

    def test_prefix_case_sensitive(self):
        r = _valid_report(report_id="wdr-001")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("report_id" in e for e in errs)

    def test_empty_notes_ok(self):
        r = _valid_report(notes="")
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_max_rank_delta_zero_ok(self):
        r = _valid_report(max_rank_delta=0, rank_change_magnitude="none",
                          dry_run_outcome="no_change",
                          n_candidates_would_change_rank=0,
                          fraction_would_change_rank=0.0)
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_max_rank_delta_large_ok(self):
        r = _valid_report(max_rank_delta=100, rank_change_magnitude="major")
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_approved_gate_status_ok(self):
        r = _valid_report(
            integration_gate_status="approved",
            integration_gate_currently_closed=False,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_rejected_gate_status_ok(self):
        r = _valid_report(
            integration_gate_status="rejected",
            integration_gate_currently_closed=False,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_disclaimer_mentions_computational_passes(self):
        r = _valid_report(
            gate_closed_disclaimer="Counterfactual report. Computational dry-lab only."
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_mixed_changes_outcome_ok(self):
        r = _valid_report(dry_run_outcome="mixed_changes")
        assert validate_weighted_integration_dry_run_report(r) == []


# ---------------------------------------------------------------------------
# Class 4: Format output (10 tests)
# ---------------------------------------------------------------------------

class TestFormatWeightedIntegrationDryRunReport:
    def test_format_contains_report_id(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "WDR-001" in out

    def test_format_contains_counterfactual_notice(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "COUNTERFACTUAL" in out or "counterfactual" in out.lower()

    def test_format_contains_gate_status(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "closed" in out

    def test_format_contains_batch_id(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "BATCH-001" in out

    def test_format_contains_fraction(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "20.0%" in out or "20%" in out

    def test_format_contains_outcome(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "reordering_only" in out

    def test_format_results_applied_false(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "False" in out

    def test_format_contains_disclaimer(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "dry-run" in out.lower() or "counterfactual" in out.lower()

    def test_format_dry_lab_only_true(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert "True" in out

    def test_format_is_string(self):
        r = _valid_report()
        out = format_weighted_integration_dry_run_report(r)
        assert isinstance(out, str)
        assert len(out) > 50


# ---------------------------------------------------------------------------
# Class 5: Dry-lab and gate enforcement (10 tests)
# ---------------------------------------------------------------------------

class TestWeightedIntegrationDryRunEnforcement:
    def test_dry_lab_only_true_required(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("dry_lab_only" in e for e in errs)

    def test_results_applied_must_be_false(self):
        r = _valid_report(results_applied_to_ranking=True)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("results_applied_to_ranking" in e for e in errs)

    def test_error_message_mentions_dry_run(self):
        r = _valid_report(results_applied_to_ranking=True)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("dry-run" in e.lower() or "applied" in e.lower() for e in errs)

    def test_wdr_prefix_is_mandatory(self):
        r = _valid_report(report_id="WIR-001")
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("WDR-" in e for e in errs)

    def test_disclaimer_must_label_as_counterfactual_or_dry_run(self):
        r = _valid_report(gate_closed_disclaimer="Nothing special about this report.")
        errs = validate_weighted_integration_dry_run_report(r)
        assert len(errs) >= 1

    def test_default_gate_closed_disclaimer_passes(self):
        r = _valid_report(gate_closed_disclaimer=GATE_CLOSED_DISCLAIMER)
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_large_batch_ok(self):
        r = _valid_report(
            n_candidates_evaluated=1000,
            n_candidates_would_change_rank=200,
            fraction_would_change_rank=0.20,
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_dry_lab_error_mentions_dry_lab(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_weighted_integration_dry_run_report(r)
        assert any("dry_lab" in e for e in errs)

    def test_no_change_outcome_zero_fraction_ok(self):
        r = _valid_report(
            n_candidates_evaluated=30,
            n_candidates_would_change_rank=0,
            fraction_would_change_rank=0.0,
            rank_change_magnitude="none",
            dry_run_outcome="no_change",
        )
        assert validate_weighted_integration_dry_run_report(r) == []

    def test_candidates_added_outcome_ok(self):
        r = _valid_report(dry_run_outcome="candidates_added")
        assert validate_weighted_integration_dry_run_report(r) == []
