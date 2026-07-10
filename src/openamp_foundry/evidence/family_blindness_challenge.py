"""FBH- family blindness challenge harness schema.

Per-family benchmark performance record: flags when the pipeline
underperforms on specific AMP families. Prevents aggregate-metric
hiding of family-blind spots.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_FBH_VERDICTS: frozenset[str] = frozenset({
    "all_families_represented",
    "weak_family_excluded",
    "insufficient_data",
})

VALID_AUROC_GRADES: frozenset[str] = frozenset({
    "strong",
    "adequate",
    "weak",
    "not_evaluated",
})

WEAK_FAMILY_AUROC_THRESHOLD: float = 0.55
WEAK_FAMILY_PANEL_FLOOR: float = 0.10


@dataclass
class FamilyPerformanceEntry:
    family_name: str
    auroc: float
    n_candidates: int
    panel_count: int
    panel_fraction: float
    auroc_grade: str
    is_weak_class: bool


@dataclass
class FamilyBlingnessChallenge:
    fbh_id: str
    pipeline_version: str
    family_entries: list[FamilyPerformanceEntry]
    n_families_total: int
    n_weak_families: int
    n_excluded_weak_families: int
    excluded_weak_family_names: list[str]
    verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_auroc_grade(auroc: float) -> str:
    if auroc == -1.0:
        return "not_evaluated"
    if auroc >= 0.70:
        return "strong"
    if auroc >= 0.55:
        return "adequate"
    return "weak"


def _compute_is_weak_class(auroc: float, n_candidates: int) -> bool:
    return auroc < WEAK_FAMILY_AUROC_THRESHOLD and n_candidates >= 3


def _compute_verdict(family_entries: list[FamilyPerformanceEntry]) -> str:
    if len(family_entries) == 0:
        return "insufficient_data"
    for entry in family_entries:
        if entry.is_weak_class and entry.panel_fraction < WEAK_FAMILY_PANEL_FLOOR:
            return "weak_family_excluded"
    return "all_families_represented"


def validate_family_blindness_challenge(fbh: FamilyBlingnessChallenge) -> None:
    if not fbh.fbh_id.startswith("FBH-"):
        raise ValueError(f"fbh_id must start with 'FBH-': {fbh.fbh_id!r}")
    if not fbh.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for entry in fbh.family_entries:
        if not (-1.0 <= entry.auroc <= 1.0):
            raise ValueError(f"auroc must be in [-1.0, 1.0]: {entry.auroc}")
        if entry.n_candidates < 1:
            raise ValueError(f"n_candidates must be >= 1: {entry.n_candidates}")
        if entry.panel_count < 0:
            raise ValueError(f"panel_count must be >= 0: {entry.panel_count}")
        if entry.panel_count > entry.n_candidates:
            raise ValueError(
                f"panel_count ({entry.panel_count}) cannot exceed "
                f"n_candidates ({entry.n_candidates})"
            )
    if fbh.n_families_total != len(fbh.family_entries):
        raise ValueError(
            f"n_families_total {fbh.n_families_total} != "
            f"len(family_entries) {len(fbh.family_entries)}"
        )
    expected_n_weak = sum(1 for e in fbh.family_entries if e.is_weak_class)
    if fbh.n_weak_families != expected_n_weak:
        raise ValueError(
            f"n_weak_families {fbh.n_weak_families} != computed {expected_n_weak}"
        )
    expected_excluded = [
        e.family_name
        for e in fbh.family_entries
        if e.is_weak_class and e.panel_fraction < WEAK_FAMILY_PANEL_FLOOR
    ]
    if fbh.n_excluded_weak_families != len(expected_excluded):
        raise ValueError(
            f"n_excluded_weak_families {fbh.n_excluded_weak_families} != "
            f"computed {len(expected_excluded)}"
        )
    if fbh.excluded_weak_family_names != expected_excluded:
        raise ValueError("excluded_weak_family_names mismatch")
    if fbh.verdict not in VALID_FBH_VERDICTS:
        raise ValueError(f"verdict {fbh.verdict!r} not in VALID_FBH_VERDICTS")
    if fbh.verdict == "weak_family_excluded" and fbh.n_excluded_weak_families < 1:
        raise ValueError(
            "verdict weak_family_excluded but n_excluded_weak_families < 1"
        )
    if fbh.verdict == "all_families_represented" and fbh.n_excluded_weak_families != 0:
        raise ValueError(
            "verdict all_families_represented but n_excluded_weak_families != 0"
        )
    if not fbh.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not fbh.limitations:
        raise ValueError("limitations must be non-empty")
    if not fbh.created_at:
        raise ValueError("created_at must be non-empty")


def build_family_blindness_challenge(
    *,
    fbh_id: str,
    pipeline_version: str,
    family_entry_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> FamilyBlingnessChallenge:
    """Build a FamilyBlingnessChallenge.

    family_entry_dicts: list of dicts with keys:
        family_name (str), auroc (float),
        n_candidates (int), panel_count (int)
    """
    family_entries = []
    for d in family_entry_dicts:
        auroc = float(d["auroc"])
        n_candidates = int(d["n_candidates"])
        panel_count = int(d["panel_count"])
        panel_fraction = round(panel_count / n_candidates, 6) if n_candidates > 0 else 0.0
        auroc_grade = _compute_auroc_grade(auroc)
        is_weak_class = _compute_is_weak_class(auroc, n_candidates)
        family_entries.append(
            FamilyPerformanceEntry(
                family_name=d["family_name"],
                auroc=auroc,
                n_candidates=n_candidates,
                panel_count=panel_count,
                panel_fraction=panel_fraction,
                auroc_grade=auroc_grade,
                is_weak_class=is_weak_class,
            )
        )
    n_families_total = len(family_entries)
    n_weak_families = sum(1 for e in family_entries if e.is_weak_class)
    excluded_names = [
        e.family_name
        for e in family_entries
        if e.is_weak_class and e.panel_fraction < WEAK_FAMILY_PANEL_FLOOR
    ]
    n_excluded_weak_families = len(excluded_names)
    verdict = _compute_verdict(family_entries)
    fbh = FamilyBlingnessChallenge(
        fbh_id=fbh_id,
        pipeline_version=pipeline_version,
        family_entries=family_entries,
        n_families_total=n_families_total,
        n_weak_families=n_weak_families,
        n_excluded_weak_families=n_excluded_weak_families,
        excluded_weak_family_names=excluded_names,
        verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_family_blindness_challenge(fbh)
    return fbh


def format_family_blindness_challenge(fbh: FamilyBlingnessChallenge) -> str:
    lines = [
        f"Family Blindness Challenge — {fbh.fbh_id}",
        f"Pipeline: {fbh.pipeline_version}",
        f"Verdict: {fbh.verdict}",
        f"Families: {fbh.n_families_total} total, {fbh.n_weak_families} weak, "
        f"{fbh.n_excluded_weak_families} excluded",
    ]
    if fbh.excluded_weak_family_names:
        lines.append(
            "Excluded weak families: "
            f"{', '.join(fbh.excluded_weak_family_names)}"
        )
    if fbh.family_entries:
        lines.append("Per-family performance:")
        for entry in fbh.family_entries:
            lines.append(
                f"  {entry.family_name}: AUROC={entry.auroc:.3f} "
                f"(grade={entry.auroc_grade}), "
                f"panel={entry.panel_count}/{entry.n_candidates} "
                f"({entry.panel_fraction:.1%}), weak={entry.is_weak_class}"
            )
    lines.append(f"Created: {fbh.created_at}")
    lines.append(f"Limitations: {'; '.join(fbh.limitations)}")
    lines.append(f"dry_lab_only: {fbh.dry_lab_only}")
    return "\n".join(lines)
