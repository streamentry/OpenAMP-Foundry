"""CandidateRejectionCertificate — Phase B B7.

When a candidate fails any gate, this schema captures the rejection as a
first-class auditable artifact. Makes failures as durable as passes.

ID prefix: CRC-
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

CRC_PREFIX = "CRC-"

VALID_REJECTION_GATES = frozenset({
    "wave0_5_safety_gate",
    "novelty_gate",
    "activity_threshold",
    "diversity_filter",
    "hemolysis_gate",
    "toxicity_gate",
    "synthesis_feasibility_gate",
    "manual_review",
    "claim_boundary_gate",
    "calibration_gate",
})

VALID_REJECTION_REASONS = frozenset({
    "safety_score_below_threshold",
    "activity_score_below_threshold",
    "insufficient_novelty",
    "hemolysis_risk_too_high",
    "toxicity_risk_too_high",
    "synthesis_infeasible",
    "duplicate_of_known",
    "diversity_cluster_full",
    "human_reviewer_rejected",
    "claim_boundary_violation",
    "calibration_refused",
    "overclaiming_language_detected",
})

VALID_PROOF_LADDER_LEVELS = (
    "valid_input",
    "reproducible_dry_lab_features",
    "baseline_triaged",
    "leakage_aware_benchmark",
    "multi_signal_candidate_evidence",
    "expert_reviewed_assay_proposal",
    "initial_qualified_assay_result",
    "safety_adjusted_follow_up_signal",
    "independent_replication",
    "reusable_discovery_loop",
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:.+Z-]+)?$")


@dataclass
class CandidateRejectionCertificate:
    crc_id: str
    pipeline_version: str
    candidate_id: str
    sequence: str
    rejection_date: str
    rejection_gate: str
    rejection_reason: str
    evidence_summary: str
    proof_ladder_level_at_rejection: str
    dry_lab_only: bool
    scores: dict = field(default_factory=dict)
    notes: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        warnings: list[str] = []

        # Rule 1: CRC- prefix
        if not self.crc_id.startswith(CRC_PREFIX):
            errors.append(f"crc_id must start with '{CRC_PREFIX}', got {self.crc_id!r}")

        # Rule 2: pipeline_version non-empty
        if not self.pipeline_version.strip():
            errors.append("pipeline_version must not be empty")

        # Rule 3: candidate_id non-empty
        if not self.candidate_id.strip():
            errors.append("candidate_id must not be empty")

        # Rule 4: sequence non-empty and uppercase amino acids
        if not self.sequence.strip():
            errors.append("sequence must not be empty")
        elif not re.match(r"^[ACDEFGHIKLMNPQRSTVWY]+$", self.sequence.upper()):
            errors.append(
                "sequence must contain only standard amino acid characters"
            )

        # Rule 5: rejection_date ISO format
        if not _ISO_DATE_RE.match(self.rejection_date):
            errors.append(
                f"rejection_date must be ISO 8601 date, got {self.rejection_date!r}"
            )

        # Rule 6: rejection_gate in controlled vocab
        if self.rejection_gate not in VALID_REJECTION_GATES:
            errors.append(
                f"rejection_gate must be one of {sorted(VALID_REJECTION_GATES)}, "
                f"got {self.rejection_gate!r}"
            )

        # Rule 7: rejection_reason in controlled vocab
        if self.rejection_reason not in VALID_REJECTION_REASONS:
            errors.append(
                f"rejection_reason must be one of {sorted(VALID_REJECTION_REASONS)}, "
                f"got {self.rejection_reason!r}"
            )

        # Rule 8: evidence_summary non-empty
        if not self.evidence_summary.strip():
            errors.append("evidence_summary must not be empty")

        # Rule 9: proof_ladder_level_at_rejection in controlled vocab
        if self.proof_ladder_level_at_rejection not in VALID_PROOF_LADDER_LEVELS:
            errors.append(
                f"proof_ladder_level_at_rejection must be one of "
                f"{VALID_PROOF_LADDER_LEVELS}, got {self.proof_ladder_level_at_rejection!r}"
            )

        # Rule 10: dry_lab_only must be True
        if not self.dry_lab_only:
            errors.append(
                "dry_lab_only must be True — rejection certificates are dry-lab artifacts"
            )

        # Rule 11: proof_ladder_level_at_rejection <= multi_signal_candidate_evidence if dry_lab_only
        dry_lab_cap_index = VALID_PROOF_LADDER_LEVELS.index("multi_signal_candidate_evidence")
        if self.proof_ladder_level_at_rejection in VALID_PROOF_LADDER_LEVELS:
            level_index = VALID_PROOF_LADDER_LEVELS.index(self.proof_ladder_level_at_rejection)
            if self.dry_lab_only and level_index > dry_lab_cap_index:
                errors.append(
                    f"dry_lab_only=True caps proof_ladder_level_at_rejection at "
                    f"'multi_signal_candidate_evidence' (level 4), "
                    f"got {self.proof_ladder_level_at_rejection!r} (level {level_index})"
                )

        # Rule 12: scores must be dict if provided
        if not isinstance(self.scores, dict):
            errors.append("scores must be a dict")

        # Rule 13: notes length cap
        if len(self.notes) > 400:
            errors.append(f"notes must be ≤400 characters, got {len(self.notes)}")

        # Warning: evidence_summary short
        if len(self.evidence_summary.strip()) < 20:
            warnings.append(
                "evidence_summary is very short; provide enough context to "
                "reconstruct the rejection decision"
            )

        # Warning: notes empty
        if not self.notes.strip():
            warnings.append(
                "notes is empty; consider adding reviewer context or "
                "follow-up instructions"
            )

        if errors:
            return errors
        return [f"WARNING: {w}" for w in warnings] if warnings else []


def validate_dict(data: dict) -> list[str]:
    """Validate a dict representation of CandidateRejectionCertificate."""
    try:
        record = CandidateRejectionCertificate(
            crc_id=data.get("crc_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            candidate_id=data.get("candidate_id", ""),
            sequence=data.get("sequence", ""),
            rejection_date=data.get("rejection_date", ""),
            rejection_gate=data.get("rejection_gate", ""),
            rejection_reason=data.get("rejection_reason", ""),
            evidence_summary=data.get("evidence_summary", ""),
            proof_ladder_level_at_rejection=data.get("proof_ladder_level_at_rejection", ""),
            dry_lab_only=data.get("dry_lab_only", False),
            scores=data.get("scores", {}),
            notes=data.get("notes", ""),
        )
        return record.validate()
    except Exception as exc:
        return [f"Construction error: {exc}"]
