"""Synthetic result policy — enforces that synthetic/simulation outputs
cannot raise the proof-ladder level of a candidate.

Dry-lab only. This is a computational policy check, not biological validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

PROOF_LADDER_LEVELS: dict[int, str] = {
    1: "computational nomination",
    2: "virtual-assay support",
    3: "in-silico ensemble agreement",
    4: "ex-vivo preliminary",
    5: "in-vivo preliminary",
    6: "clinical evidence",
}


@dataclass
class SyntheticResultPolicyCheck:
    candidate_id: str
    current_level: int
    proposed_level: int
    evidence_source: str
    policy_pass: bool
    violation: str = ""
    recommendation: str = ""
    dry_lab_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_synthetic_result_policy(
    candidate_id: str,
    current_level: int,
    proposed_level: int,
    evidence_source: str,
) -> SyntheticResultPolicyCheck:
    if current_level not in PROOF_LADDER_LEVELS:
        raise ValueError(
            f"current_level must be 1..6, got {current_level}"
        )
    if proposed_level not in PROOF_LADDER_LEVELS:
        raise ValueError(
            f"proposed_level must be 1..6, got {proposed_level}"
        )

    valid_sources = {"synthetic", "lab", "literature", "unknown"}
    if evidence_source not in valid_sources:
        evidence_source = "unknown"

    violation = ""
    policy_pass = True
    recommendation = ""

    if evidence_source == "synthetic":
        if proposed_level > current_level:
            policy_pass = False
            violation = "Synthetic evidence cannot raise proof-ladder level"
            recommendation = (
                f"Candidate {candidate_id} proposed at proof-ladder level "
                f"{proposed_level} ({PROOF_LADDER_LEVELS[proposed_level]}) "
                f"supported only by synthetic evidence. "
                f"Level {current_level} ({PROOF_LADDER_LEVELS[current_level]}) "
                f"is the maximum allowed without wet-lab evidence."
            )
        elif proposed_level < current_level:
            policy_pass = False
            violation = (
                "Synthetic evidence cannot lower proof-ladder level either; "
                "use lab evidence to reassess"
            )
            recommendation = (
                f"Candidate {candidate_id} synthetic evidence suggests level "
                f"{proposed_level} but non-synthetic evidence supports level "
                f"{current_level}. Review lab and literature evidence to "
                f"determine the correct level."
            )
        else:
            recommendation = (
                f"Candidate {candidate_id} maintained at proof-ladder level "
                f"{current_level} ({PROOF_LADDER_LEVELS[current_level]}) "
                f"with synthetic evidence. This is acceptable."
            )
    else:
        recommendation = (
            f"Candidate {candidate_id} evidence source '{evidence_source}' "
            f"is not restricted by synthetic result policy."
        )

    if proposed_level > 3 and evidence_source in ("synthetic", "unknown"):
        policy_pass = False
        violation = (
            "Levels 4+ require wet-lab evidence; "
            "synthetic/unknown source is insufficient"
        )
        recommendation = (
            f"Candidate {candidate_id} proposed at level {proposed_level} "
            f"({PROOF_LADDER_LEVELS[proposed_level]}) which requires "
            f"wet-lab evidence. Source '{evidence_source}' is insufficient. "
            f"Provide lab or literature evidence."
        )

    return SyntheticResultPolicyCheck(
        candidate_id=candidate_id,
        current_level=current_level,
        proposed_level=proposed_level,
        evidence_source=evidence_source,
        policy_pass=policy_pass,
        violation=violation,
        recommendation=recommendation,
        dry_lab_only=True,
    )


def run_policy_batch(proposals: list[dict]) -> dict:
    checks: list[SyntheticResultPolicyCheck] = []
    for prop in proposals:
        check = check_synthetic_result_policy(
            candidate_id=prop["candidate_id"],
            current_level=prop["current_level"],
            proposed_level=prop["proposed_level"],
            evidence_source=prop["evidence_source"],
        )
        checks.append(check)

    passed = sum(1 for c in checks if c.policy_pass)
    failed = sum(1 for c in checks if not c.policy_pass)

    return {
        "checks": [c.to_dict() for c in checks],
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
        },
        "any_violation": failed > 0,
        "dry_lab_only": True,
    }


def write_policy_check_json(
    result: dict | SyntheticResultPolicyCheck,
    path: str | Path,
) -> None:
    path = Path(path)
    if isinstance(result, SyntheticResultPolicyCheck):
        data = result.to_dict()
    else:
        data = result
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_policy_check_markdown(
    result: dict | SyntheticResultPolicyCheck,
    path: str | Path,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(result, SyntheticResultPolicyCheck):
        data = result.to_dict()
        lines = _single_check_to_markdown(data)
    else:
        lines = _batch_report_to_markdown(result)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _single_check_to_markdown(data: dict) -> list[str]:
    status = "✅ PASS" if data["policy_pass"] else "❌ FAIL"
    lines = [
        "# Synthetic Result Policy Check",
        "",
        f"**Candidate:** {data['candidate_id']}",
        f"**Status:** {status}",
        f"**Current level:** {data['current_level']}",
        f"**Proposed level:** {data['proposed_level']}",
        f"**Evidence source:** {data['evidence_source']}",
        "",
    ]
    if data["violation"]:
        lines.append(f"**Violation:** {data['violation']}")
        lines.append("")
    if data["recommendation"]:
        lines.append(f"**Recommendation:** {data['recommendation']}")
        lines.append("")
    lines.append("---")
    lines.append(
        "_This is a computational policy check and does not measure "
        "biological activity._"
    )
    return lines


def _batch_report_to_markdown(data: dict) -> list[str]:
    summary = data.get("summary", {})
    n_total = summary.get("total", 0)
    n_passed = summary.get("passed", 0)
    n_failed = summary.get("failed", 0)

    lines = [
        "# Synthetic Result Policy Check — Batch Report",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total checks | {n_total} |",
        f"| Passed | {n_passed} |",
        f"| Failed | {n_failed} |",
        f"| Any violation | {data.get('any_violation', False)} |",
        f"| Dry-lab only | {data.get('dry_lab_only', True)} |",
        "",
        "## Per-Candidate Results",
        "",
        "| Candidate | Current | Proposed | Source | Pass | Violation |",
        "|-----------|:-------:|:--------:|:------:|:---:|-----------|",
    ]

    for c in data.get("checks", []):
        status_icon = "✅" if c["policy_pass"] else "❌"
        violation = c.get("violation", "") or "—"
        lines.append(
            f"| {c['candidate_id']} | {c['current_level']} "
            f"| {c['proposed_level']} | {c['evidence_source']} "
            f"| {status_icon} | {violation} |"
        )

    lines.extend([
        "",
        "---",
        "_This is a computational policy check and does not measure "
        "biological activity._",
    ])
    return lines
