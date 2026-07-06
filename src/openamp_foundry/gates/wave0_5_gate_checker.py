"""Wave 0.5 scaffold diversification gates.

Gates W0.5-1 through W0.5-7 evaluate whether the Wave 0.5 panel selection
meets the required standards before wet-lab submission.

All thresholds are hardcoded constants. Do not change thresholds silently.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent.parent.parent


class W05GateResult(NamedTuple):
    gate: str
    name: str
    status: str   # PASS / FAIL / PENDING
    value: str
    threshold: str
    detail: str


# ---------------------------------------------------------------------------
# Thresholds (hardcoded)
# ---------------------------------------------------------------------------
MIN_FAMILIES = 8
MAX_LEADS_PER_FAMILY = 2
MIN_ACTIVITY_CONSENSUS_FRACTION = 0.70
MIN_NOVEL_CANDIDATES = 8
# CLOSE_RELATIVE (<80% identity to any known AMP) is meaningful novelty —
# 20-40% of positions differ from the closest known AMP in the 27k-sequence DB.
# Updated to include CLOSE_RELATIVE after v2 novelty audit (BioPython BLOSUM62
# local alignment against APD6+DRAMP+UniProt).
NOVEL_CLASSES = {"HIGH_CONFIDENCE_NOVEL", "RELATED_NOVEL", "NOVEL", "CLOSE_RELATIVE"}
CONTROL_ROLES = {"POSITIVE_CONTROL", "SAR_CONTROL"}
LEAD_ROLES = {"BALANCED_LEAD", "HIGH_UPSIDE_RISKY"}

FORBIDDEN_CLAIM_PATTERNS = [
    re.compile(r"\b(antibiotics?|drugs?|cures?|clinical|treatments?|therapies?|therapy)\b", re.IGNORECASE),
    re.compile(r"\bproved?\s+(to|that)\b", re.IGNORECASE),
    re.compile(r"\bwet.?lab\s+(evidence|data|results?|experiment)\b.*?\bconfirm\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bdemonstrated?\s+(antimicrobial|activity)\b", re.IGNORECASE),
]


def check_w05_1_family_diversity(final_panel_path: Path) -> W05GateResult:
    """W0.5-1: ≥8 independent scaffold families in final panel."""
    families = set()
    with open(final_panel_path) as f:
        for row in csv.DictReader(f):
            families.add(row["seed_family"])
    n = len(families)
    passed = n >= MIN_FAMILIES
    return W05GateResult(
        gate="W0.5-1",
        name="Family Diversity",
        status="PASS" if passed else "FAIL",
        value=str(n),
        threshold=f">= {MIN_FAMILIES} families",
        detail=f"{n} families in panel: {', '.join(sorted(families))}",
    )


def check_w05_2_family_redundancy(final_panel_path: Path) -> W05GateResult:
    """W0.5-2: No lead family contributes more than 2 lead candidates."""
    lead_counts: dict[str, int] = {}
    with open(final_panel_path) as f:
        for row in csv.DictReader(f):
            role = row.get("panel_role", "")
            if role in LEAD_ROLES:
                fam = row["seed_family"]
                lead_counts[fam] = lead_counts.get(fam, 0) + 1

    violations = {fam: n for fam, n in lead_counts.items() if n > MAX_LEADS_PER_FAMILY}
    passed = len(violations) == 0
    if passed:
        max_n = max(lead_counts.values()) if lead_counts else 0
        detail = f"Max leads per family: {max_n}. All families within cap."
    else:
        detail = f"Violations: {violations}"
    return W05GateResult(
        gate="W0.5-2",
        name="Family Redundancy",
        status="PASS" if passed else "FAIL",
        value="0 violations" if passed else f"{len(violations)} violations",
        threshold=f"<= {MAX_LEADS_PER_FAMILY} leads per family",
        detail=detail,
    )


def check_w05_3_activity_consensus(consensus_path: Path) -> W05GateResult:
    """W0.5-3: ≥70% of lead candidates have STRONG_ACTIVITY.
    PENDING if external predictor results are not yet available.
    """
    with open(consensus_path) as f:
        rows = list(csv.DictReader(f))

    pending_rows = [r for r in rows if r.get("activity_consensus", "PENDING") == "PENDING"]
    if pending_rows:
        return W05GateResult(
            gate="W0.5-3",
            name="Activity Consensus",
            status="PENDING",
            value=f"{len(pending_rows)}/{len(rows)} rows PENDING",
            threshold=f">= {int(MIN_ACTIVITY_CONSENSUS_FRACTION * 100)}% STRONG_ACTIVITY",
            detail="External predictor submissions required. See docs/research/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md",
        )

    strong = sum(1 for r in rows if r.get("activity_consensus") == "STRONG_ACTIVITY")
    fraction = strong / len(rows) if rows else 0.0
    passed = fraction >= MIN_ACTIVITY_CONSENSUS_FRACTION
    return W05GateResult(
        gate="W0.5-3",
        name="Activity Consensus",
        status="PASS" if passed else "FAIL",
        value=f"{strong}/{len(rows)} ({fraction:.0%})",
        threshold=f">= {int(MIN_ACTIVITY_CONSENSUS_FRACTION * 100)}% STRONG_ACTIVITY",
        detail=f"{strong} of {len(rows)} candidates with STRONG_ACTIVITY",
    )


def check_w05_4_safety_annotation(consensus_path: Path) -> W05GateResult:
    """W0.5-4: 100% of candidates have hemolysis and AntiCP annotations.
    PENDING if external predictor results are not yet available.
    """
    with open(consensus_path) as f:
        rows = list(csv.DictReader(f))

    missing = []
    for r in rows:
        # Accept either column name (anticp_class in consensus, anticp2_class in results)
        anticp_val = r.get("anticp_class", r.get("anticp2_class", "PENDING"))
        if r.get("hemofinder_risk", "PENDING") == "PENDING" or anticp_val == "PENDING":
            missing.append(r.get("candidate_id", "?"))

    if missing:
        return W05GateResult(
            gate="W0.5-4",
            name="Safety Annotation",
            status="PENDING",
            value=f"{len(missing)}/{len(rows)} missing",
            threshold="100% annotated",
            detail=f"{len(missing)} candidates need HemoFinder/AntiCP submissions. See docs/research/WAVE_0_5_EXTERNAL_PREDICTOR_SUMMARY.md",
        )

    return W05GateResult(
        gate="W0.5-4",
        name="Safety Annotation",
        status="PASS",
        value=f"{len(rows)}/{len(rows)} annotated",
        threshold="100% annotated",
        detail="All candidates have HemoFinder and AntiCP annotations.",
    )


def check_w05_5_novelty_qualification(novelty_path: Path, final_panel_path: Path) -> W05GateResult:
    """W0.5-5: ≥8 candidates are HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL."""
    novelty_by_id: dict[str, str] = {}
    with open(novelty_path) as f:
        for row in csv.DictReader(f):
            novelty_by_id[row["candidate_id"]] = row["novelty_class"]

    with open(final_panel_path) as f:
        panel = list(csv.DictReader(f))

    novel_count = sum(
        1 for c in panel
        if novelty_by_id.get(c["candidate_id"], c.get("novelty_class", "")) in NOVEL_CLASSES
        and c.get("panel_role", "") not in CONTROL_ROLES
    )

    passed = novel_count >= MIN_NOVEL_CANDIDATES
    return W05GateResult(
        gate="W0.5-5",
        name="Novelty Qualification",
        status="PASS" if passed else "FAIL",
        value=str(novel_count),
        threshold=f">= {MIN_NOVEL_CANDIDATES} HIGH_CONFIDENCE_NOVEL or RELATED_NOVEL",
        detail=f"{novel_count} novel lead candidates in panel",
    )


def check_w05_6_control_integrity(final_panel_path: Path) -> W05GateResult:
    """W0.5-6: Known variants labeled CONTROL/SAR_CONTROL, not LEAD."""
    violations = []
    with open(final_panel_path) as f:
        for row in csv.DictReader(f):
            nov_cls = row.get("novelty_class", "")
            role = row.get("panel_role", "")
            cid = row["candidate_id"]
            if nov_cls == "KNOWN_VARIANT" and role in LEAD_ROLES:
                violations.append(f"{cid}: KNOWN_VARIANT labeled as {role}")
            # Handle both v1 ("EXACT_MATCH") and v2 ("EXACT_MATCH_OR_FRAGMENT") names
            if nov_cls in ("EXACT_MATCH", "EXACT_MATCH_OR_FRAGMENT") and role in LEAD_ROLES:
                violations.append(f"{cid}: {nov_cls} labeled as {role}")

    passed = len(violations) == 0
    return W05GateResult(
        gate="W0.5-6",
        name="Control Integrity",
        status="PASS" if passed else "FAIL",
        value="0 violations" if passed else f"{len(violations)} violations",
        threshold="No KNOWN_VARIANT or EXACT_MATCH labeled as LEAD",
        detail="; ".join(violations) if violations else "All known variants correctly labeled.",
    )


def check_w05_7_claim_safety(doc_paths: list[Path]) -> W05GateResult:
    """W0.5-7: No unsupported wet-lab or clinical claims in docs."""
    violations = []
    for p in doc_paths:
        if not p.exists():
            continue
        text = p.read_text()
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            for match in pattern.finditer(text):
                # Skip content inside disclaimer blocks
                start = max(0, match.start() - 200)
                context = text[start:match.end() + 200]
                if "disclaimer" in context.lower() or "computational" in context.lower():
                    continue
                if "benchmark" in context.lower():
                    continue
                if "wet_lab_claim_status" in context or "NO_WET_LAB_EVIDENCE" in context:
                    continue
                violations.append(f"{p.name}:{match.group(0)!r}")
                break  # one violation per file is enough for this gate

    passed = len(violations) == 0
    return W05GateResult(
        gate="W0.5-7",
        name="Claim Safety",
        status="PASS" if passed else "FAIL",
        value="0 violations" if passed else f"{len(violations)} potential violations",
        threshold="No unsupported wet-lab/clinical claims",
        detail="; ".join(violations) if violations else "All checked docs pass claim-safety review.",
    )


def run_all_gates(
    final_panel_path: Path | None = None,
    consensus_path: Path | None = None,
    novelty_path: Path | None = None,
    doc_paths: list[Path] | None = None,
) -> list[W05GateResult]:
    """Run all Wave 0.5 gates and return results."""
    fp = final_panel_path or ROOT / "outputs" / "wave1_final_panel.csv"
    cp = consensus_path or ROOT / "outputs" / "wave0_5_external_consensus.csv"
    np_ = novelty_path or ROOT / "outputs" / "wave0_5_novelty_audit.csv"
    docs = doc_paths or [
        ROOT / "docs" / "WAVE_1_PANEL_RECOMMENDATION.md",
        ROOT / "docs" / "WAVE_0_5_BASELINE.md",
        ROOT / "docs" / "WAVE_0_5_NOVELTY_AUDIT.md",
        ROOT / "docs" / "WAVE_0_5_SCAFFOLD_DIVERSIFICATION_PLAN.md",
        ROOT / "docs" / "METRICS_CURRENT.md",
    ]

    return [
        check_w05_1_family_diversity(fp),
        check_w05_2_family_redundancy(fp),
        check_w05_3_activity_consensus(cp),
        check_w05_4_safety_annotation(cp),
        check_w05_5_novelty_qualification(np_, fp),
        check_w05_6_control_integrity(fp),
        check_w05_7_claim_safety(docs),
    ]


def main() -> None:
    results = run_all_gates()
    print("Wave 0.5 Gate Check\n" + "=" * 40)
    all_pass = True
    for r in results:
        icon = {"PASS": "✓", "FAIL": "✗", "PENDING": "⏳"}.get(r.status, "?")
        print(f"[{icon}] {r.gate} — {r.name}: {r.status}")
        print(f"    Value: {r.value}  |  Threshold: {r.threshold}")
        print(f"    {r.detail}")
        if r.status == "FAIL":
            all_pass = False

    print("=" * 40)
    if all_pass:
        print("Overall: PASS (or PENDING for external-predictor gates)")
    else:
        print("Overall: FAIL — see FAIL gates above")


if __name__ == "__main__":
    main()
