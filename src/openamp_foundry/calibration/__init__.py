"""Calibration package — wet-lab feedback loop for the OpenAMP foundry.

This package provides the machine-readable policy, intake report, and
gate verdict that together form the pre-registered, human-gated
recalibration workflow:

    pilot panel predictions
        + validated lab results
        → calibration-intake report (descriptive only)
        → evaluated against pre-registered policy
        → gate verdict (may_recalibrate? True/False)
        → human reviewer inspects verdict before any weight change

The recalibration ENGINE (actual weight-update code) does NOT live here
yet. It is the next loop's job once wet-lab data exists. The current
package provides the permission layer that must exist BEFORE any
recalibration engine can be safely applied.
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
]
