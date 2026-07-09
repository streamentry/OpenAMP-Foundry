"""Recalibration rollback plan — documented procedure for safer recalibration updates.

If a recalibration degrades performance, there must be a documented rollback
procedure. This module provides rollback triggers, a standard rollback plan
with ordered steps, and JSON/Markdown writers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROLLBACK_TRIGGERS: list[dict[str, str]] = [
    {
        "id": "RT-01",
        "name": "AUROC regression",
        "description": "Primary calibration metric drops significantly from baseline after recalibration.",
        "threshold": "AUROC drops > 0.02 from baseline",
        "severity": "critical",
    },
    {
        "id": "RT-02",
        "name": "Calibration metric below minimum threshold",
        "description": "Calibration metric falls below the pre-registered minimum acceptable threshold.",
        "threshold": "Calibration metric < 0.65 AUROC or equivalent",
        "severity": "critical",
    },
    {
        "id": "RT-03",
        "name": "Novel safety filter bypass",
        "description": "Recalibration introduces a path for candidates to bypass hemolysis, toxicity, or novelty safety filters.",
        "threshold": "Any safety filter bypass detected",
        "severity": "critical",
    },
    {
        "id": "RT-04",
        "name": "Cohort distribution shift detected",
        "description": "The calibration cohort distribution differs significantly from the intended scoring population.",
        "threshold": "KS-test p < 0.05 on any key feature distribution",
        "severity": "warning",
    },
    {
        "id": "RT-05",
        "name": "Unexplained weight delta magnitude",
        "description": "The L1 weight delta exceeds the pre-registered budget without documented rationale.",
        "threshold": "L1 delta > 0.10 without documented rationale",
        "severity": "warning",
    },
]


@dataclass
class RollbackStep:
    step_number: int
    action: str
    responsible: str
    detail: str
    dry_lab_only: bool = True


DEFAULT_ROLLBACK_STEPS: list[RollbackStep] = [
    RollbackStep(
        step_number=1,
        action="Halt any pending calibration updates",
        responsible="pipeline",
        detail="Immediately stop any in-progress calibration engine proposals or weight updates. Prevent new proposals from entering the review queue until regression is resolved.",
    ),
    RollbackStep(
        step_number=2,
        action="Document the regression event with timestamps",
        responsible="human-reviewer",
        detail="Record the date, time, affected calibration version, triggering metric values, and the specific benchmark or gate that detected the regression. Include links to the pre-recalibration and post-recalibration metrics snapshots.",
    ),
    RollbackStep(
        step_number=3,
        action="Restore previous weight vector from version control",
        responsible="pipeline",
        detail="Check out the previous committed weight configuration from version control. Verify the restored weights match the pre-recalibration benchmark snapshot. Run a dry-run proposal to confirm no unexpected delta remains.",
    ),
    RollbackStep(
        step_number=4,
        action="Re-run benchmark gate to confirm restoration",
        responsible="both",
        detail="Re-run the benchmark regression gate and the primary AUROC benchmark. Confirm the AUROC returns to within 0.01 of the pre-recalibration baseline. If not, investigate and re-restore.",
    ),
    RollbackStep(
        step_number=5,
        action="Review root cause and update calibration policy if needed",
        responsible="human-reviewer",
        detail="Analyze why the recalibration degraded performance. Was the cohort under-powered? Was there a distribution shift? Was an overfit warning missed? Update the calibration policy to prevent recurrence if a systemic gap is identified.",
    ),
    RollbackStep(
        step_number=6,
        action="Log rollback decision in calibration decision log",
        responsible="human-reviewer",
        detail="Write a dated decision log entry documenting the rollback event: version rolled back, triggering metrics, steps taken, root cause analysis, and any policy changes. The log must be signed by the human reviewer.",
    ),
]


@dataclass
class RollbackPlan:
    plan_id: str
    version: str
    triggered_by: list[str]
    steps: list[RollbackStep]
    notes: str
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "version": self.version,
            "triggered_by": self.triggered_by,
            "steps": [asdict(step) for step in self.steps],
            "notes": self.notes,
            "dry_lab_only": self.dry_lab_only,
        }


def build_rollback_plan(
    plan_id: str,
    version: str,
    triggered_by: list[str],
    notes: str = "",
    extra_steps: list[RollbackStep] | None = None,
) -> RollbackPlan:
    """Build a RollbackPlan, validating triggered_by against ROLLBACK_TRIGGERS ids.

    Raises ValueError if any trigger id is unknown.
    """
    known_ids = {t["id"] for t in ROLLBACK_TRIGGERS}
    unknown = set(triggered_by) - known_ids
    if unknown:
        raise ValueError(
            f"Unknown rollback trigger id(s): {sorted(unknown)}. "
            f"Valid ids: {sorted(known_ids)}"
        )

    steps = list(DEFAULT_ROLLBACK_STEPS)
    if extra_steps:
        offset = max(s.step_number for s in steps)
        for i, step in enumerate(extra_steps, start=offset + 1):
            step.step_number = i
        steps.extend(extra_steps)

    return RollbackPlan(
        plan_id=plan_id,
        version=version,
        triggered_by=sorted(triggered_by),
        steps=steps,
        notes=notes,
        dry_lab_only=True,
    )


def write_rollback_plan_json(plan: RollbackPlan, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_dict(), indent=2) + "\n", encoding="utf-8")


def write_rollback_plan_markdown(plan: RollbackPlan, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    severity_labels = {
        "critical": "**CRITICAL**",
        "warning": "**WARNING**",
    }

    trigger_rows = "\n".join(
        f"| {t['id']} | {t['name']} | {t['description']} "
        f"| `{t['threshold']}` | {severity_labels.get(t['severity'], t['severity'])} |"
        for t in ROLLBACK_TRIGGERS
    )

    step_list = "\n".join(
        f"{s.step_number}. **{s.action}** (responsible: {s.responsible})\n"
        f"   {s.detail}"
        for s in plan.steps
    )

    trigger_ids = ", ".join(plan.triggered_by)

    lines = [
        "# Recalibration Rollback Plan",
        "",
        f"**Plan ID:** {plan.plan_id}",
        f"**Calibration Version:** {plan.version}",
        f"**Triggered By:** {trigger_ids}",
        f"**Dry-lab only:** {plan.dry_lab_only}",
        "",
    ]

    if plan.notes:
        lines.append(f"**Notes:** {plan.notes}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Rollback Triggers",
        "",
        "The following conditions can trigger a recalibration rollback:",
        "",
        "| ID | Name | Description | Threshold | Severity |",
        "|---|---|---|:---|---|",
        trigger_rows,
        "",
        "---",
        "",
        "## Rollback Steps",
        "",
        "Upon triggering, the following steps must be followed in order:",
        "",
        step_list,
        "",
        "---",
        "",
        "## Caveats",
        "",
        "- This rollback plan restores previous weight configurations, not previous",
        "  pipeline code or benchmark results. Code-level regressions require a",
        "  separate rollback procedure.",
        "- Rollback restores the weight vector only. It does not undo any candidate",
        "  selections or synthesis decisions that were made using the degraded weights.",
        "- The rollback does not guarantee that the restored configuration will pass",
        "  future benchmark regression gates — benchmark drift from unrelated changes",
        "  may affect the restored configuration.",
        "- All rollback actions are dry-lab operations. They affect computational",
        "  scoring only, not biological activity or safety.",
        "- A rollback is a procedural response to a detected regression. It is not",
        "  evidence that the original recalibration was invalid — only that its",
        "  outcome was unacceptable.",
        "- Human review is required for steps 2, 5, and 6. Automated rollback is",
        "  not permitted without documented human oversight.",
        "",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
