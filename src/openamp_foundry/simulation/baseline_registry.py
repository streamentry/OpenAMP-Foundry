"""Per-module cheapest-baseline declarations for virtual assay modules.

Every simulation module must declare the simplest baseline it must beat,
making it easy to detect simulation theater (modules that don't beat trivial baselines).
Dry-lab only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALID_BASELINE_TYPES: set[str] = {"heuristic", "random", "constant", "length"}


@dataclass
class BaselineDeclaration:
    module_id: str
    module_name: str
    baseline_description: str
    baseline_type: str
    evidence_level_ceiling: int
    notes: str = ""


BASELINE_DECLARATIONS: list[BaselineDeclaration] = [
    BaselineDeclaration(
        module_id="membrane_proxy",
        module_name="Membrane Proxy",
        baseline_description="charge density (net charge at pH 7.4)",
        baseline_type="heuristic",
        evidence_level_ceiling=1,
        notes="Must beat charge density alone on AMP-vs-decoy discrimination before contributing to level-2 evidence.",
    ),
    BaselineDeclaration(
        module_id="structure_proxy",
        module_name="Structure Proxy",
        baseline_description="length alone (no structural signal)",
        baseline_type="length",
        evidence_level_ceiling=1,
        notes="Must beat sequence length alone on helical structure prediction before contributing to level-2 evidence.",
    ),
    BaselineDeclaration(
        module_id="dummy_membrane_proxy",
        module_name="Dummy Membrane Proxy",
        baseline_description="charge density (net charge at pH 7.4)",
        baseline_type="heuristic",
        evidence_level_ceiling=1,
        notes="Stub for testing only. Trivially fails the baseline check; should not be used for scoring.",
    ),
    BaselineDeclaration(
        module_id="external_adapter_placeholder",
        module_name="External Adapter Placeholder",
        baseline_description="constant 0.5 (no signal)",
        baseline_type="constant",
        evidence_level_ceiling=1,
        notes="Placeholder. Any external adapter must declare and beat its own baseline before contributing evidence.",
    ),
]


def get_baseline_declaration(module_id: str) -> BaselineDeclaration | None:
    for decl in BASELINE_DECLARATIONS:
        if decl.module_id == module_id:
            return decl
    return None


def list_baseline_declarations() -> list[BaselineDeclaration]:
    return list(BASELINE_DECLARATIONS)


def check_baseline_requirement(
    module_id: str,
    claimed_evidence_level: int,
    baseline_beaten: bool,
) -> dict[str, Any]:
    """Check whether a module can claim a given evidence level.

    If the module has not beaten its declared baseline, the effective evidence
    level is capped at its evidence_level_ceiling.

    Returns a dict with keys:
        module_id, baseline_beaten, claimed_evidence_level,
        effective_evidence_level, capped, message, dry_lab_only
    """
    decl = get_baseline_declaration(module_id)
    if decl is None:
        return {
            "module_id": module_id,
            "baseline_beaten": baseline_beaten,
            "claimed_evidence_level": claimed_evidence_level,
            "effective_evidence_level": claimed_evidence_level,
            "capped": False,
            "message": f"No baseline declaration found for module '{module_id}'. Proceeding uncapped.",
            "dry_lab_only": True,
        }

    if baseline_beaten or claimed_evidence_level <= decl.evidence_level_ceiling:
        effective = claimed_evidence_level
        capped = False
        if baseline_beaten:
            msg = (
                f"Module '{module_id}' has beaten its baseline "
                f"({decl.baseline_description}). Evidence level {claimed_evidence_level} is permitted."
            )
        else:
            msg = (
                f"Module '{module_id}' has not beaten its baseline "
                f"({decl.baseline_description}), but claimed level {claimed_evidence_level} "
                f"is within the allowed ceiling ({decl.evidence_level_ceiling}). "
                f"Caution: baseline not beaten."
            )
    else:
        effective = decl.evidence_level_ceiling
        capped = True
        msg = (
            f"Module '{module_id}' has NOT beaten its declared baseline "
            f"({decl.baseline_description}). "
            f"Evidence level capped from {claimed_evidence_level} to {effective} "
            f"(ceiling for unbeaten baseline)."
        )

    return {
        "module_id": module_id,
        "baseline_beaten": baseline_beaten,
        "claimed_evidence_level": claimed_evidence_level,
        "effective_evidence_level": effective,
        "capped": capped,
        "message": msg,
        "dry_lab_only": True,
    }


def validate_baseline_declarations() -> list[str]:
    """Validate all entries in BASELINE_DECLARATIONS.

    Returns a list of error strings (empty = valid).
    """
    errors: list[str] = []
    seen_ids: set[str] = set()

    for i, decl in enumerate(BASELINE_DECLARATIONS):
        if not decl.module_id:
            errors.append(f"Entry {i}: module_id is empty")
        if not decl.baseline_description:
            errors.append(f"Entry {i} ({decl.module_id}): baseline_description is empty")
        if decl.baseline_type not in VALID_BASELINE_TYPES:
            errors.append(
                f"Entry {i} ({decl.module_id}): invalid baseline_type '{decl.baseline_type}'. "
                f"Must be one of: {sorted(VALID_BASELINE_TYPES)}"
            )
        if not (1 <= decl.evidence_level_ceiling <= 6):
            errors.append(
                f"Entry {i} ({decl.module_id}): evidence_level_ceiling "
                f"{decl.evidence_level_ceiling} must be 1..6"
            )
        if decl.module_id in seen_ids:
            errors.append(f"Duplicate module_id: '{decl.module_id}'")
        seen_ids.add(decl.module_id)

    return errors
