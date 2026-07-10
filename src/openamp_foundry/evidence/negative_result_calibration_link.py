"""
Calibration link schema connecting negative-result entries to calibration intake records.

F7: Closes the learning loop. Every batch of rejected/failed candidates
should feed back into the calibration pipeline. This schema records the
explicit link between NRR- negative result records and CAL- calibration
intake records, making the learning loop auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LINK_ID_PREFIX: str = "NCL-"
NRR_ID_PREFIX: str = "NRR-"
CAL_ID_PREFIX: str = "CAL-"
MIN_NRR_IDS: int = 1
MIN_LINK_RATIONALE_LENGTH: int = 10

VALID_LINK_STATUSES: frozenset[str] = frozenset({
    "pending",
    "submitted",
    "accepted",
    "rejected",
    "superseded",
})

VALID_LINK_TYPES: frozenset[str] = frozenset({
    "batch_failure_feedback",
    "single_candidate_rejection",
    "systematic_failure_pattern",
    "assay_protocol_failure",
    "data_quality_rejection",
})


@dataclass
class NegativeResultCalibrationLink:
    """
    Auditable link between a set of NRR- negative result records
    and a CAL- calibration intake record.

    Ensures that failures inform the next calibration cycle and
    prevents silent discard of negative evidence.
    """

    link_id: str
    nrr_ids: list[str]
    intake_id: str
    linked_at: str
    link_type: str
    link_rationale: str
    batch_coverage_fraction: float
    all_nrrs_linked: bool
    link_status: str
    notes: str


@dataclass
class LinkValidationResult:
    """Result of validating a NegativeResultCalibrationLink."""

    is_valid: bool
    violations: list[str]
    warnings: list[str]
    link_id: str
    validation_summary: str


def validate_negative_result_calibration_link(
    link: NegativeResultCalibrationLink,
) -> LinkValidationResult:
    """
    Validate a NegativeResultCalibrationLink against all integrity rules.

    Rules:
      1. link_id must start with 'NCL-'
      2. link_id must have content after the prefix
      3. intake_id must start with 'CAL-'
      4. nrr_ids must have at least MIN_NRR_IDS entries
      5. all nrr_ids must start with 'NRR-'
      6. nrr_ids must not contain duplicates
      7. linked_at must not be empty
      8. link_type must be in VALID_LINK_TYPES
      9. link_rationale must be at least MIN_LINK_RATIONALE_LENGTH characters
      10. batch_coverage_fraction must be in [0.0, 1.0]
      11. link_status must be in VALID_LINK_STATUSES
      12. if all_nrrs_linked is True, batch_coverage_fraction must equal 1.0
      13. if batch_coverage_fraction == 1.0, all_nrrs_linked must be True
      14. notes must be a string (may be empty)
    """
    violations: list[str] = []
    warnings: list[str] = []

    if not link.link_id.startswith(LINK_ID_PREFIX):
        violations.append(
            f"link_id must start with '{LINK_ID_PREFIX}', got: {link.link_id!r}"
        )

    if len(link.link_id) <= len(LINK_ID_PREFIX):
        violations.append("link_id must have content after the prefix.")

    if not link.intake_id.startswith(CAL_ID_PREFIX):
        violations.append(
            f"intake_id must start with '{CAL_ID_PREFIX}', got: {link.intake_id!r}"
        )

    if len(link.nrr_ids) < MIN_NRR_IDS:
        violations.append(
            f"nrr_ids must have at least {MIN_NRR_IDS} entry, "
            f"got {len(link.nrr_ids)}."
        )

    for nrr_id in link.nrr_ids:
        if not nrr_id.startswith(NRR_ID_PREFIX):
            violations.append(
                f"All nrr_ids must start with '{NRR_ID_PREFIX}', got: {nrr_id!r}"
            )

    if len(link.nrr_ids) != len(set(link.nrr_ids)):
        violations.append("nrr_ids must not contain duplicates.")

    if not link.linked_at.strip():
        violations.append("linked_at must not be empty.")

    if link.link_type not in VALID_LINK_TYPES:
        violations.append(
            f"link_type must be one of {sorted(VALID_LINK_TYPES)}, "
            f"got: {link.link_type!r}"
        )

    if len(link.link_rationale.strip()) < MIN_LINK_RATIONALE_LENGTH:
        violations.append(
            f"link_rationale must be at least {MIN_LINK_RATIONALE_LENGTH} characters, "
            f"got length {len(link.link_rationale.strip())}."
        )

    if not (0.0 <= link.batch_coverage_fraction <= 1.0):
        violations.append(
            f"batch_coverage_fraction must be in [0.0, 1.0], "
            f"got: {link.batch_coverage_fraction}"
        )

    if link.link_status not in VALID_LINK_STATUSES:
        violations.append(
            f"link_status must be one of {sorted(VALID_LINK_STATUSES)}, "
            f"got: {link.link_status!r}"
        )

    if link.all_nrrs_linked and link.batch_coverage_fraction != 1.0:
        violations.append(
            "If all_nrrs_linked is True, batch_coverage_fraction must be 1.0, "
            f"got: {link.batch_coverage_fraction}"
        )

    if link.batch_coverage_fraction == 1.0 and not link.all_nrrs_linked:
        violations.append(
            "If batch_coverage_fraction is 1.0, all_nrrs_linked must be True."
        )

    if not link.notes and link.link_status == "rejected":
        warnings.append(
            "Link status is 'rejected' but notes are empty. "
            "Consider documenting why the link was rejected."
        )

    is_valid = len(violations) == 0
    if is_valid:
        summary = (
            f"NegativeResultCalibrationLink {link.link_id} is valid: "
            f"{len(link.nrr_ids)} NRR record(s) linked to {link.intake_id}, "
            f"coverage={link.batch_coverage_fraction:.0%}."
        )
    else:
        summary = (
            f"NegativeResultCalibrationLink {link.link_id} has "
            f"{len(violations)} violation(s): "
            + "; ".join(violations[:2])
            + ("..." if len(violations) > 2 else "")
        )

    return LinkValidationResult(
        is_valid=is_valid,
        violations=violations,
        warnings=warnings,
        link_id=link.link_id,
        validation_summary=summary,
    )


def format_negative_result_calibration_link(link: NegativeResultCalibrationLink) -> str:
    """Return a human-readable summary of a NegativeResultCalibrationLink."""
    lines: list[str] = [
        f"Negative Result Calibration Link: {link.link_id}",
        f"  Type:             {link.link_type}",
        f"  Status:           {link.link_status}",
        f"  Linked at:        {link.linked_at}",
        f"  Intake record:    {link.intake_id}",
        f"  NRR records ({len(link.nrr_ids)}):",
    ]
    for nrr_id in link.nrr_ids:
        lines.append(f"    - {nrr_id}")
    lines.append(f"  Batch coverage:   {link.batch_coverage_fraction:.0%}")
    lines.append(f"  All NRRs linked:  {link.all_nrrs_linked}")
    lines.append(f"  Rationale:        {link.link_rationale}")
    if link.notes:
        lines.append(f"  Notes:            {link.notes}")
    return "\n".join(lines)
