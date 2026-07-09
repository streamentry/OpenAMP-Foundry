"""Calibration package — wet-lab feedback loop for the OpenAMP foundry.

This package provides the machine-readable policy, intake report,
gate verdict, and weight-update proposal that together form the
pre-registered, human-gated recalibration workflow:

    pilot panel predictions
        + validated lab results
        → calibration-intake report (descriptive only)
        → evaluated against pre-registered policy
        → gate verdict (may_recalibrate? True/False)
        → engine (compute proposed weight deltas)
        → human reviewer inspects proposal + verdict
        → (separate) apply approved weight changes

The engine computes proposals only. It does NOT apply changes.
A human reviewer must sign a dated decision log entry before any
weight update takes effect.
"""

from openamp_foundry.calibration.intake import (
    ACTIVITY_THRESHOLD,
    HEMOLYSIS_HIGH_PCT,
    MIC_ACTIVE_CUTOFF_UG_ML,
    MIN_COHORT_SIZE,
    build_calibration_intake_report,
    write_calibration_intake_json,
    write_calibration_intake_markdown,
)

from openamp_foundry.calibration.policy import (
    LockedChange,
    PolicyLoadError,
    PolicyRule,
    ProhibitedAction,
    RateLimit,
    RecalibrationPolicy,
    ReviewerArtefact,
    canonical_prohibited_action_ids,
    load_recalibration_policy,
)

from openamp_foundry.calibration.engine import (
    BudgetExceededError,
    PolicyViolationError,
    WeightDelta,
    WeightUpdateProposal,
    compute_weight_update,
    write_weight_update_proposal_json,
    write_weight_update_proposal_markdown,
)

from openamp_foundry.calibration.recalibration_gate import (
    GateVerdict,
    ProhibitedActionAudit,
    RateLimitStatus,
    ReviewerArtefactStatus,
    RuleResult,
    evaluate_recalibration_gate,
    write_gate_verdict_json,
    write_gate_verdict_markdown,
)

from openamp_foundry.calibration.overfit_warning import (
    check_cohort_overfit_risk,
    run_overfit_check,
    write_overfit_check_json,
    write_overfit_check_markdown,
)

from openamp_foundry.calibration.policy_version import (
    VersionValidation,
    validate_policy_version,
    auto_increment_version,
)

from openamp_foundry.calibration.result_quality import (
    QUALITY_FLAGS,
    ResultQualityReport,
    assess_result_quality,
    filter_results_for_calibration,
    write_result_quality_json,
    write_result_quality_markdown,
)

__all__ = [
    # Constants
    "MIN_COHORT_SIZE",
    "MIC_ACTIVE_CUTOFF_UG_ML",
    "ACTIVITY_THRESHOLD",
    "HEMOLYSIS_HIGH_PCT",
    # Intake
    "build_calibration_intake_report",
    "write_calibration_intake_json",
    "write_calibration_intake_markdown",
    # Policy
    "load_recalibration_policy",
    "canonical_prohibited_action_ids",
    "RecalibrationPolicy",
    "PolicyRule",
    "ProhibitedAction",
    "RateLimit",
    "ReviewerArtefact",
    "LockedChange",
    "PolicyLoadError",
    # Gate
    "evaluate_recalibration_gate",
    "write_gate_verdict_json",
    "write_gate_verdict_markdown",
    "GateVerdict",
    "RuleResult",
    "ProhibitedActionAudit",
    "RateLimitStatus",
    "ReviewerArtefactStatus",
    # Engine
    "compute_weight_update",
    "write_weight_update_proposal_json",
    "write_weight_update_proposal_markdown",
    "WeightDelta",
    "WeightUpdateProposal",
    "PolicyViolationError",
    "BudgetExceededError",
    # Policy version
    "validate_policy_version",
    "auto_increment_version",
    "VersionValidation",
    # Overfit warning
    "check_cohort_overfit_risk",
    "run_overfit_check",
    "write_overfit_check_json",
    "write_overfit_check_markdown",
    # Result quality
    "QUALITY_FLAGS",
    "ResultQualityReport",
    "assess_result_quality",
    "filter_results_for_calibration",
    "write_result_quality_json",
    "write_result_quality_markdown",
]
