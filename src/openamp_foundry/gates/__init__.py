"""Pipeline decision gates for OpenAMP Foundry.

Pre-registered gate checks (e.g. Wave 0.5 gate set, top-level
`gate-check`) that block downstream work until scoring and panel
selection satisfy documented minimum standards.
"""

from openamp_foundry.gates.gate_checker import (
    GateResult,
    check_all_gates,
    check_gate_1_auroc,
    check_gate_2_leakage,
    check_gate_3_disagreement,
    check_gate_4_top10_positive_recall,
    check_gate_5_interpretation,
)
from openamp_foundry.gates.wave0_5_gate_checker import (
    W05GateResult,
    check_w05_1_family_diversity,
    check_w05_2_family_redundancy,
    check_w05_3_activity_consensus,
    check_w05_4_safety_annotation,
    check_w05_5_novelty_qualification,
    check_w05_6_control_integrity,
    check_w05_7_claim_safety,
    run_all_gates,
)

__all__ = [
    # top-level gate-check
    "GateResult",
    "check_all_gates",
    "check_gate_1_auroc",
    "check_gate_2_leakage",
    "check_gate_3_disagreement",
    "check_gate_4_top10_positive_recall",
    "check_gate_5_interpretation",
    # Wave 0.5 gate set
    "W05GateResult",
    "check_w05_1_family_diversity",
    "check_w05_2_family_redundancy",
    "check_w05_3_activity_consensus",
    "check_w05_4_safety_annotation",
    "check_w05_5_novelty_qualification",
    "check_w05_6_control_integrity",
    "check_w05_7_claim_safety",
    "run_all_gates",
]
