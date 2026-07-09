import pytest
from openamp_foundry.evidence.experiment_priority_justification import (
    ExperimentPriorityEntry,
    ExperimentPriorityResult,
    validate_experiment_priority,
    validate_experiment_priority_dict,
    MINIMUM_SELECTION_CRITERIA,
    MAXIMUM_SELECTION_CRITERIA_WARNING,
    MAX_REJECTION_RATIONALE_LENGTH,
    MAX_RESOURCE_CONSTRAINT_LENGTH,
)


def _valid_entry(**overrides) -> ExperimentPriorityEntry:
    base = dict(
        justification_id="EPJ-001",
        batch_id="BATCH-002",
        pipeline_version="0.9.8",
        decision_date="2026-07-10",
        selection_criteria=[
            "Highest predicted hit rate vs. random baseline",
            "All candidates passed novelty and safety filters",
            "Sequence diversity covers three distinct structural families",
        ],
        rejected_alternatives=["BATCH-001", "BATCH-003"],
        rejection_rationale=(
            "BATCH-001 showed lower predicted hit rate and higher predicted toxicity. "
            "BATCH-003 lacked sufficient structural diversity for meaningful family coverage."
        ),
        resource_constraint="Synthesis capacity limited to 10 candidates per wave.",
        safety_reviewed=True,
        pre_specified=True,
        decided_by="pipeline@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return ExperimentPriorityEntry(**base)


def _valid_dict(**overrides) -> dict:
    base = dict(
        justification_id="EPJ-001",
        batch_id="BATCH-002",
        pipeline_version="0.9.8",
        decision_date="2026-07-10",
        selection_criteria=[
            "Highest predicted hit rate vs. random baseline",
            "All candidates passed novelty and safety filters",
        ],
        rejected_alternatives=["BATCH-001"],
        rejection_rationale="BATCH-001 showed lower predicted hit rate and higher toxicity.",
        resource_constraint="Synthesis capacity limited to 10 candidates per wave.",
        safety_reviewed=True,
        pre_specified=True,
        decided_by="pipeline@example.com",
        dry_lab_only=True,
    )
    base.update(overrides)
    return base


# --- Happy path ---

def test_valid_entry_passes():
    result = validate_experiment_priority(_valid_entry())
    assert result.passed
    assert result.errors == []
    assert result.warnings == []


def test_result_dry_lab_only_always_true():
    result = validate_experiment_priority(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_populated():
    result = validate_experiment_priority(_valid_entry())
    assert result.justification_id == "EPJ-001"
    assert result.batch_id == "BATCH-002"
    assert result.criteria_count == 3
    assert result.rejected_alternative_count == 2
    assert result.safety_reviewed is True


def test_exactly_minimum_criteria_passes_with_warning():
    result = validate_experiment_priority(
        _valid_entry(
            selection_criteria=["criterion_one", "criterion_two"]
        )
    )
    assert result.passed
    assert any("minimum" in w.lower() or str(MINIMUM_SELECTION_CRITERIA) in w for w in result.warnings)


def test_single_rejected_alternative_passes():
    result = validate_experiment_priority(_valid_entry(rejected_alternatives=["BATCH-001"]))
    assert result.passed


def test_empty_resource_constraint_warns():
    result = validate_experiment_priority(_valid_entry(resource_constraint=""))
    assert result.passed
    assert any("resource_constraint" in w.lower() or "constraint" in w.lower() for w in result.warnings)


def test_resource_constraint_documented_no_warn():
    result = validate_experiment_priority(
        _valid_entry(resource_constraint="Limited to 10 candidates per synthesis wave.")
    )
    assert not any("resource_constraint" in w.lower() and "empty" in w.lower() for w in result.warnings)


# --- justification_id ---

def test_justification_id_must_start_with_epj():
    result = validate_experiment_priority(_valid_entry(justification_id="PRI-001"))
    assert not result.passed
    assert any("EPJ-" in e for e in result.errors)


def test_justification_id_empty_fails():
    result = validate_experiment_priority(_valid_entry(justification_id=""))
    assert not result.passed


def test_justification_id_epj_prefix_valid():
    result = validate_experiment_priority(_valid_entry(justification_id="EPJ-999"))
    assert result.passed


# --- selection_criteria ---

def test_empty_selection_criteria_fails():
    result = validate_experiment_priority(_valid_entry(selection_criteria=[]))
    assert not result.passed
    assert any("selection_criteria" in e for e in result.errors)


def test_single_criterion_fails():
    result = validate_experiment_priority(_valid_entry(selection_criteria=["only_one"]))
    assert not result.passed
    assert any("selection_criteria" in e for e in result.errors)


def test_many_criteria_warns():
    criteria = [f"criterion_{i}" for i in range(MAXIMUM_SELECTION_CRITERIA_WARNING + 1)]
    result = validate_experiment_priority(_valid_entry(selection_criteria=criteria))
    assert result.passed
    assert any("over-fit" in w.lower() or "many criteria" in w.lower() or str(MAXIMUM_SELECTION_CRITERIA_WARNING) in w for w in result.warnings)


def test_criteria_at_max_warning_no_warn():
    criteria = [f"criterion_{i}" for i in range(MAXIMUM_SELECTION_CRITERIA_WARNING)]
    result = validate_experiment_priority(_valid_entry(selection_criteria=criteria))
    assert not any("over-fit" in w.lower() for w in result.warnings)


# --- rejected_alternatives ---

def test_empty_rejected_alternatives_fails():
    result = validate_experiment_priority(_valid_entry(rejected_alternatives=[]))
    assert not result.passed
    assert any("rejected_alternatives" in e for e in result.errors)


def test_multiple_alternatives_passes():
    result = validate_experiment_priority(
        _valid_entry(rejected_alternatives=["BATCH-001", "BATCH-003", "BATCH-004"])
    )
    assert result.passed
    assert result.rejected_alternative_count == 3


# --- rejection_rationale ---

def test_empty_rejection_rationale_fails():
    result = validate_experiment_priority(_valid_entry(rejection_rationale=""))
    assert not result.passed
    assert any("rejection_rationale" in e for e in result.errors)


def test_rejection_rationale_at_max_passes():
    result = validate_experiment_priority(
        _valid_entry(rejection_rationale="A" * MAX_REJECTION_RATIONALE_LENGTH)
    )
    assert result.passed


def test_rejection_rationale_over_max_fails():
    result = validate_experiment_priority(
        _valid_entry(rejection_rationale="A" * (MAX_REJECTION_RATIONALE_LENGTH + 1))
    )
    assert not result.passed


# --- resource_constraint ---

def test_resource_constraint_at_max_passes():
    result = validate_experiment_priority(
        _valid_entry(resource_constraint="A" * MAX_RESOURCE_CONSTRAINT_LENGTH)
    )
    assert result.passed


def test_resource_constraint_over_max_fails():
    result = validate_experiment_priority(
        _valid_entry(resource_constraint="A" * (MAX_RESOURCE_CONSTRAINT_LENGTH + 1))
    )
    assert not result.passed
    assert any("resource_constraint" in e for e in result.errors)


# --- safety_reviewed ---

def test_safety_not_reviewed_fails():
    result = validate_experiment_priority(_valid_entry(safety_reviewed=False))
    assert not result.passed
    assert any("safety_reviewed" in e for e in result.errors)


def test_safety_reviewed_true_passes():
    result = validate_experiment_priority(_valid_entry(safety_reviewed=True))
    assert result.passed


# --- decided_by ---

def test_empty_decided_by_fails():
    result = validate_experiment_priority(_valid_entry(decided_by=""))
    assert not result.passed
    assert any("decided_by" in e for e in result.errors)


# --- dry_lab_only ---

def test_dry_lab_only_false_fails():
    result = validate_experiment_priority(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# --- pre_specified warning ---

def test_post_hoc_selection_warns():
    result = validate_experiment_priority(_valid_entry(pre_specified=False))
    assert result.passed
    assert any("pre_specified" in w or "post-hoc" in w.lower() for w in result.warnings)


def test_pre_specified_true_no_posthoc_warn():
    result = validate_experiment_priority(_valid_entry(pre_specified=True))
    assert not any("post-hoc" in w.lower() for w in result.warnings)


# --- dict interface ---

def test_valid_dict_passes():
    result = validate_experiment_priority_dict(_valid_dict())
    assert result.passed


def test_missing_justification_id_fails():
    d = _valid_dict()
    del d["justification_id"]
    result = validate_experiment_priority_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_missing_selection_criteria_fails():
    d = _valid_dict()
    del d["selection_criteria"]
    result = validate_experiment_priority_dict(d)
    assert not result.passed


def test_missing_safety_reviewed_fails():
    d = _valid_dict()
    del d["safety_reviewed"]
    result = validate_experiment_priority_dict(d)
    assert not result.passed


def test_dict_dry_lab_only_defaults_true():
    d = _valid_dict()
    del d["dry_lab_only"]
    result = validate_experiment_priority_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_dict_criteria_count_populated():
    result = validate_experiment_priority_dict(_valid_dict())
    assert result.criteria_count == 2


def test_dict_rejected_count_populated():
    result = validate_experiment_priority_dict(_valid_dict())
    assert result.rejected_alternative_count == 1


def test_multiple_missing_fields():
    d = {}
    result = validate_experiment_priority_dict(d)
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


# --- constants ---

def test_minimum_selection_criteria_value():
    assert MINIMUM_SELECTION_CRITERIA == 2


def test_maximum_selection_criteria_warning_value():
    assert MAXIMUM_SELECTION_CRITERIA_WARNING == 6


def test_max_rejection_rationale_length_value():
    assert MAX_REJECTION_RATIONALE_LENGTH == 500


def test_max_resource_constraint_length_value():
    assert MAX_RESOURCE_CONSTRAINT_LENGTH == 200
