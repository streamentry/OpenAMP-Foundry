"""Wet-lab hit record schema — Phase Q Q2.

WHR- (Wet-Lab Hit Record): machine-readable record of an actual experimental
outcome for a nominated candidate. First schema in the project where
dry_lab_only MUST be False.

Key safety invariants:
- dry_lab_only MUST be False (enforced: if True, raises ValueError)
- interpretation must be one of: "active", "inactive", "inconclusive"
- result_value must be a finite non-negative float
- experiment_type must be from VALID_EXPERIMENT_TYPES
- CANNOT claim clinical efficacy or in-vivo validation
- proof_ladder_level for wet-lab results is capped at "single_assay_hit"
  (no higher claim allowed without multi-assay confirmation)
- limitations list MUST be non-empty
- candidate_id MUST NOT be a TOY- ID (real results only)
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


VALID_EXPERIMENT_TYPES: frozenset[str] = frozenset({
    "mic_broth_dilution",
    "disk_diffusion",
    "kill_curve",
    "flow_cytometry_membrane",
    "fluorescence_microscopy",
    "biofilm_inhibition",
    "hemolysis_assay",
    "cytotoxicity_mtt",
    "time_kill_assay",
    "turbidity_growth_inhibition",
})

VALID_INTERPRETATIONS: frozenset[str] = frozenset({
    "active",
    "inactive",
    "inconclusive",
})

VALID_PROOF_LADDER_LEVELS: frozenset[str] = frozenset({
    "single_assay_hit",
    "replicated_single_assay_hit",
    "multi_assay_candidate",
})

_WHR_RE = re.compile(r"^WHR-[A-Za-z0-9_-]+$")
_AA_SEQ_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")

MAX_PROOF_LADDER_LEVEL = "multi_assay_candidate"
MAX_NOTES_LEN = 500


@dataclass
class WetlabHitRecord:
    """Machine-readable record of a single wet-lab experimental outcome.

    dry_lab_only MUST be False — this records a real experimental result.
    """
    whr_id: str
    candidate_id: str
    sequence: str
    experiment_date: str
    experiment_type: str
    result_value: float
    result_unit: str
    interpretation: str
    assay_lab: str
    assay_method: str
    dry_lab_only: bool
    limitations: list[str] = field(default_factory=list)
    notes: str = ""
    related_bsp_id: str = ""
    related_psc_id: str = ""
    proof_ladder_level: str = "single_assay_hit"


@dataclass
class WHRValidationResult:
    valid: bool
    violations: list[str]
    whr_id: str | None


def validate_wetlab_hit_record(record: WetlabHitRecord) -> WHRValidationResult:
    """Validate a WetlabHitRecord and return violations.

    A record is valid only when violations is empty.
    """
    violations: list[str] = []

    # ID format
    if not _WHR_RE.match(record.whr_id):
        violations.append(
            f"whr_id '{record.whr_id}' must match WHR-[A-Za-z0-9_-]+"
        )

    # dry_lab_only MUST be False
    if record.dry_lab_only is True:
        violations.append(
            "dry_lab_only must be False for WHR- records: "
            "this schema records real experimental results only"
        )

    # candidate_id must not be TOY-
    if record.candidate_id.startswith("TOY-"):
        violations.append(
            f"candidate_id '{record.candidate_id}' must not be a TOY- ID: "
            "real results require real candidate IDs"
        )

    # sequence must be non-empty amino acid string
    if not record.sequence:
        violations.append("sequence must be non-empty")
    elif not _AA_SEQ_RE.match(record.sequence):
        violations.append(
            f"sequence '{record.sequence[:20]}...' contains non-amino-acid characters"
        )

    # experiment_date must be non-empty
    if not record.experiment_date:
        violations.append("experiment_date must be non-empty")

    # experiment_type must be valid
    if record.experiment_type not in VALID_EXPERIMENT_TYPES:
        violations.append(
            f"experiment_type '{record.experiment_type}' is not in VALID_EXPERIMENT_TYPES"
        )

    # result_value must be finite and non-negative
    if not math.isfinite(record.result_value):
        violations.append(
            f"result_value {record.result_value} must be a finite number"
        )
    elif record.result_value < 0:
        violations.append(
            f"result_value {record.result_value} must be non-negative"
        )

    # result_unit must be non-empty
    if not record.result_unit:
        violations.append("result_unit must be non-empty")

    # interpretation must be valid
    if record.interpretation not in VALID_INTERPRETATIONS:
        violations.append(
            f"interpretation '{record.interpretation}' is not in VALID_INTERPRETATIONS"
        )

    # assay_lab must be non-empty
    if not record.assay_lab:
        violations.append("assay_lab must be non-empty")

    # assay_method must be non-empty
    if not record.assay_method:
        violations.append("assay_method must be non-empty")

    # limitations must be non-empty list
    if not record.limitations:
        violations.append(
            "limitations must be non-empty: "
            "every wet-lab result has scope and replication limitations"
        )

    # proof_ladder_level must be valid
    if record.proof_ladder_level not in VALID_PROOF_LADDER_LEVELS:
        violations.append(
            f"proof_ladder_level '{record.proof_ladder_level}' is not valid; "
            f"must be one of {sorted(VALID_PROOF_LADDER_LEVELS)}"
        )

    # notes length cap
    if len(record.notes) > MAX_NOTES_LEN:
        violations.append(
            f"notes length {len(record.notes)} exceeds maximum {MAX_NOTES_LEN}"
        )

    return WHRValidationResult(
        valid=len(violations) == 0,
        violations=violations,
        whr_id=record.whr_id if _WHR_RE.match(record.whr_id) else None,
    )


def build_wetlab_hit_record(
    whr_id: str,
    candidate_id: str,
    sequence: str,
    experiment_date: str,
    experiment_type: str,
    result_value: float,
    result_unit: str,
    interpretation: str,
    assay_lab: str,
    assay_method: str,
    limitations: list[str],
    notes: str = "",
    related_bsp_id: str = "",
    related_psc_id: str = "",
    proof_ladder_level: str = "single_assay_hit",
) -> WetlabHitRecord:
    """Build a WetlabHitRecord with dry_lab_only=False enforced."""
    return WetlabHitRecord(
        whr_id=whr_id,
        candidate_id=candidate_id,
        sequence=sequence,
        experiment_date=experiment_date,
        experiment_type=experiment_type,
        result_value=result_value,
        result_unit=result_unit,
        interpretation=interpretation,
        assay_lab=assay_lab,
        assay_method=assay_method,
        dry_lab_only=False,
        limitations=limitations,
        notes=notes,
        related_bsp_id=related_bsp_id,
        related_psc_id=related_psc_id,
        proof_ladder_level=proof_ladder_level,
    )


def format_wetlab_hit_record(record: WetlabHitRecord) -> str:
    """Return a human-readable summary of the wet-lab hit record."""
    result = validate_wetlab_hit_record(record)
    lines = [
        f"WHR Record: {record.whr_id}",
        f"  Candidate: {record.candidate_id}",
        f"  Sequence:  {record.sequence}",
        f"  Experiment: {record.experiment_type} ({record.experiment_date})",
        f"  Result: {record.result_value} {record.result_unit}",
        f"  Interpretation: {record.interpretation}",
        f"  Lab: {record.assay_lab}",
        f"  Proof ladder: {record.proof_ladder_level}",
        f"  dry_lab_only: {record.dry_lab_only}",
        f"  Limitations ({len(record.limitations)}):",
    ]
    for lim in record.limitations:
        lines.append(f"    - {lim}")
    if result.valid:
        lines.append("  Status: VALID")
    else:
        lines.append(f"  Status: INVALID ({len(result.violations)} violation(s))")
        for v in result.violations:
            lines.append(f"    VIOLATION: {v}")
    return "\n".join(lines)
