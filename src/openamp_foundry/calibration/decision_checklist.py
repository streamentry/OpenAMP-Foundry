"""Calibration decision review checklist — structured human-review before recalibration updates.

Each recalibration decision should be reviewed against a structured checklist
before being applied. This module provides the checklist items, a dataclass
for a completed checklist, and JSON/Markdown writers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

CHECKLIST_ITEMS: list[dict[str, Any]] = [
    {
        "id": "G9-01",
        "category": "data_quality",
        "question": "Was the calibration cohort size adequate (≥30 candidates per model parameter)?",
        "rationale": "Small cohorts produce unreliable calibration signals and risk false learning.",
        "required": True,
    },
    {
        "id": "G9-02",
        "category": "data_quality",
        "question": "Were all lab-result quality flags reviewed and low-quality results excluded?",
        "rationale": "Contaminated, interfered, or otherwise flagged results must not drive calibration updates.",
        "required": True,
    },
    {
        "id": "G9-03",
        "category": "statistical_validity",
        "question": "Did the AUROC or primary calibration metric meet the pre-registered threshold?",
        "rationale": "Calibration should only update weights when performance meets the minimum bar.",
        "required": True,
    },
    {
        "id": "G9-04",
        "category": "statistical_validity",
        "question": "Were confidence intervals reported and did the lower bound exceed the minimum threshold?",
        "rationale": "A point estimate above threshold may not be meaningful if uncertainty is high.",
        "required": True,
    },
    {
        "id": "G9-05",
        "category": "safety_consistency",
        "question": "Were all novelty, toxicity, and hemolysis safety filters unchanged by the calibration?",
        "rationale": "Calibration must not silently bypass safety constraints on candidate selection.",
        "required": True,
    },
    {
        "id": "G9-06",
        "category": "safety_consistency",
        "question": "Were synthetic or simulation results prevented from raising the proof-ladder level?",
        "rationale": "Synthetic outputs are anti-overclaim and must not inflate evidence levels.",
        "required": True,
    },
    {
        "id": "G9-07",
        "category": "safety_consistency",
        "question": "Was the overfit risk assessed and no critical-level warning present?",
        "rationale": "Under-powered calibration cohorts produce unreliable weight updates.",
        "required": True,
    },
    {
        "id": "G9-08",
        "category": "approval",
        "question": "Was the calibration decision reviewed and signed by a qualified human reviewer?",
        "rationale": "Automated calibration updates without human review bypass governance.",
        "required": True,
    },
    {
        "id": "G9-09",
        "category": "approval",
        "question": "Was the recalibration gate verdict evaluated and did it permit recalibration?",
        "rationale": "The gate verdict encodes pre-registered conditions that must all be satisfied.",
        "required": True,
    },
    {
        "id": "G9-10",
        "category": "documentation",
        "question": "Was the recalibration decision log updated with the review date, reviewer, and outcome?",
        "rationale": "Auditability requires a dated, signed record of every recalibration decision.",
        "required": True,
    },
    {
        "id": "G9-11",
        "category": "documentation",
        "question": "Were the proposed weight deltas reviewed and the rationale documented?",
        "rationale": "Each weight change must have a traceable justification for future reviewers.",
        "required": True,
    },
    {
        "id": "G9-12",
        "category": "statistical_validity",
        "question": "Was the calibration cohort drawn from the same distribution as the intended scoring population?",
        "rationale": "Cohort distribution shift can produce misleading calibration signals.",
        "required": False,
    },
]


@dataclass
class CalibrationDecisionChecklist:
    checklist_id: str
    date: str
    reviewer: str
    responses: dict[str, bool]
    notes: dict[str, str]
    overall_pass: bool
    missing_required: list[str]
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_checklist(
    checklist_id: str,
    date: str,
    reviewer: str,
    responses: dict[str, bool],
    notes: dict[str, str] | None = None,
) -> CalibrationDecisionChecklist:
    """Build a CalibrationDecisionChecklist, validating responses against CHECKLIST_ITEMS.

    Raises ValueError if any response key is not a known checklist item id.
    """
    known_ids = {item["id"] for item in CHECKLIST_ITEMS}
    unknown = set(responses) - known_ids
    if unknown:
        raise ValueError(
            f"Unknown checklist item id(s): {sorted(unknown)}. "
            f"Valid ids: {sorted(known_ids)}"
        )

    missing_required = [
        item["id"]
        for item in CHECKLIST_ITEMS
        if item["required"] and item["id"] not in responses
    ]
    missing_required += [
        item["id"]
        for item in CHECKLIST_ITEMS
        if item["required"] and item["id"] in responses and not responses[item["id"]]
    ]

    all_required_present_and_true = len(missing_required) == 0

    return CalibrationDecisionChecklist(
        checklist_id=checklist_id,
        date=date,
        reviewer=reviewer,
        responses=responses,
        notes=notes or {},
        overall_pass=all_required_present_and_true,
        missing_required=sorted(set(missing_required)) if missing_required else [],
        dry_lab_only=True,
    )


def write_checklist_json(checklist: CalibrationDecisionChecklist, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checklist.to_dict(), indent=2) + "\n", encoding="utf-8")


def write_checklist_markdown(checklist: CalibrationDecisionChecklist, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Calibration Decision Review Checklist",
        "",
        f"**Checklist ID:** {checklist.checklist_id}",
        f"**Date:** {checklist.date}",
        f"**Reviewer:** {checklist.reviewer}",
        f"**Overall Pass:** {'✅' if checklist.overall_pass else '❌'}",
        f"**Dry-lab only:** {checklist.dry_lab_only}",
        "",
    ]

    if checklist.missing_required:
        lines.append("### Missing Required Items")
        lines.append("")
        for mid in checklist.missing_required:
            lines.append(f"- ❌ **{mid}** — see checklist item below")
        lines.append("")

    lines.append("## Checklist Items")
    lines.append("")
    lines.append("| ID | Category | Question | Response |")
    lines.append("|---|---|---|:---:|")

    for item in CHECKLIST_ITEMS:
        item_id = item["id"]
        if item_id in checklist.responses:
            chosen = checklist.responses[item_id]
            icon = "✅" if chosen else "❌"
        else:
            icon = "—"
        lines.append(f"| {item_id} | {item['category']} | {item['question']} | {icon} |")

    lines.append("")

    if checklist.notes:
        lines.append("## Notes")
        lines.append("")
        for note_id, note_text in sorted(checklist.notes.items()):
            lines.append(f"**{note_id}:** {note_text}")
            lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "This checklist is a structured human-review aid. It does "
        "not confirm biological activity, safety, or real-world "
        "performance. All calibration decisions require qualified "
        "human review regardless of checklist results."
    )
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
