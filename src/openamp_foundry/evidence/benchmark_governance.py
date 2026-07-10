"""Benchmark governance — Phase C C10.

CI check that rejects missing benchmark cards for governed benchmark scripts.
Prevents benchmark sprawl by requiring every governed script to have a
corresponding BMC- card in BENCHMARK_REGISTRY.

Usage:
    report = check_governance(scripts_dir, registry_by_id)
    if not report.is_compliant:
        raise BenchmarkGovernanceError(report.violation_summary)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Mapping from script filename to required BMC ID.
# Add a new entry here BEFORE adding a new benchmark script.
SCRIPT_TO_BMC_ID: dict[str, str] = {
    "benchmark_precision_at_k.py": "BMC-0001",
    "benchmark_charge_matched.py": "BMC-0002",
    "benchmark_calibration.py": "BMC-0003",
    "benchmark_per_family.py": "BMC-0004",
    "benchmark_cheap_enemy_comparison.py": "BMC-0005",
}

# Frozenset of scripts that must have a registered BMC card.
# Scripts outside this set are ungoverned (warning only, not a CI failure).
GOVERNED_SCRIPTS: frozenset[str] = frozenset(SCRIPT_TO_BMC_ID.keys())


class BenchmarkGovernanceError(Exception):
    """Raised when a governed benchmark script lacks a valid BMC card."""


@dataclass
class GovernanceReport:
    total_scripts: int
    governed_scripts: list[str] = field(default_factory=list)
    ungoverned_scripts: list[str] = field(default_factory=list)
    compliant_scripts: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    is_compliant: bool = True
    violation_summary: str = ""


def _discover_scripts(scripts_dir: str | Path) -> list[str]:
    """Return sorted list of benchmark_*.py filenames in scripts_dir."""
    p = Path(scripts_dir)
    if not p.is_dir():
        return []
    return sorted(
        f.name
        for f in p.iterdir()
        if f.is_file() and f.name.startswith("benchmark_") and f.name.endswith(".py")
    )


def check_governance(
    scripts_dir: str | Path,
    registry_by_id: dict[str, Any],
    governed_scripts: frozenset[str] = GOVERNED_SCRIPTS,
    script_to_bmc_id: dict[str, str] = SCRIPT_TO_BMC_ID,
) -> GovernanceReport:
    """Check that all governed benchmark scripts have registered BMC cards.

    Args:
        scripts_dir: Directory to scan for benchmark_*.py files.
        registry_by_id: Dict mapping BMC ID to BenchmarkCard (e.g. BENCHMARK_REGISTRY_BY_ID).
        governed_scripts: Set of script filenames that must have cards.
        script_to_bmc_id: Mapping from script filename to expected BMC ID.

    Returns:
        GovernanceReport with compliance status and violation details.
    """
    discovered = _discover_scripts(scripts_dir)
    total = len(discovered)

    governed: list[str] = []
    ungoverned: list[str] = []
    compliant: list[str] = []
    violations: list[str] = []

    for script in discovered:
        if script in governed_scripts:
            governed.append(script)
            bmc_id = script_to_bmc_id.get(script)
            if bmc_id is None:
                violations.append(
                    f"{script}: in GOVERNED_SCRIPTS but has no entry in SCRIPT_TO_BMC_ID"
                )
            elif bmc_id not in registry_by_id:
                violations.append(
                    f"{script}: requires {bmc_id} but that card is not in the registry"
                )
            else:
                compliant.append(script)
        else:
            ungoverned.append(script)

    # Also flag governed scripts in the mapping but absent from the scanned directory.
    # These are not violations (scripts may be in different locations) — they are noted.
    # Only scripts that were discovered AND governed trigger violations.

    is_compliant = len(violations) == 0

    if is_compliant:
        summary = (
            f"Governance OK: {len(compliant)}/{len(governed)} governed scripts "
            f"have valid BMC cards. {len(ungoverned)} ungoverned scripts (no card required)."
        )
    else:
        lines = [f"Governance FAILED: {len(violations)} violation(s):"]
        for v in violations:
            lines.append(f"  - {v}")
        lines.append(
            f"Add a BMC- card to BENCHMARK_REGISTRY and update SCRIPT_TO_BMC_ID "
            f"in benchmark_governance.py before adding this benchmark script."
        )
        summary = "\n".join(lines)

    return GovernanceReport(
        total_scripts=total,
        governed_scripts=governed,
        ungoverned_scripts=ungoverned,
        compliant_scripts=compliant,
        violations=violations,
        is_compliant=is_compliant,
        violation_summary=summary,
    )


def format_governance_report(report: GovernanceReport) -> str:
    """Format a GovernanceReport as a human-readable string."""
    lines = [
        "=== BENCHMARK GOVERNANCE REPORT ===",
        f"Scripts discovered: {report.total_scripts}",
        f"  Governed (require BMC card): {len(report.governed_scripts)}",
        f"  Ungoverned (no card required): {len(report.ungoverned_scripts)}",
        "",
        f"COMPLIANT scripts: {len(report.compliant_scripts)}",
    ]
    for s in sorted(report.compliant_scripts):
        lines.append(f"  [OK] {s}")
    if report.ungoverned_scripts:
        lines.append(f"\nUNGOVERNED scripts (warnings only): {len(report.ungoverned_scripts)}")
        for s in sorted(report.ungoverned_scripts):
            lines.append(f"  [?] {s}")
    if report.violations:
        lines.append(f"\nVIOLATIONS: {len(report.violations)}")
        for v in report.violations:
            lines.append(f"  [FAIL] {v}")
    lines.append(f"\nCOMPLIANCE: {'PASS' if report.is_compliant else 'FAIL'}")
    lines.append("")
    lines.append(report.violation_summary)
    return "\n".join(lines)
