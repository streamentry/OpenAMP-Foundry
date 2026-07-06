"""Validation gate for virtual-assay weighted mode.

The gate converts ablation benchmark outputs into an explicit permission
decision.  Weighted simulation must fail closed until both current ablation
views show improvement over existing cheap/pipeline scorers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MIN_WITHIN_AMP_DELTA = 0.03
MIN_AMP_VS_DECOY_DELTA = 0.005


@dataclass(frozen=True)
class SimulationGateVerdict:
    """Machine-readable permission decision for simulation ranking modes."""

    may_use_weighted_mode: bool
    integration_mode: str
    required_mode: str
    checks: dict[str, bool]
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "may_use_weighted_mode": self.may_use_weighted_mode,
            "integration_mode": self.integration_mode,
            "required_mode": self.required_mode,
            "checks": self.checks,
            "reasons": self.reasons,
        }


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"simulation ablation artifact not found: {p}")
    payload = json.loads(p.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"simulation ablation artifact must be a JSON object: {p}")
    return payload


def _result(payload: dict[str, Any], key: str, default: Any = None) -> Any:
    results = payload.get("results", {})
    if not isinstance(results, dict):
        return default
    return results.get(key, default)


def evaluate_simulation_gate(
    *,
    amp_vs_decoy_path: str | Path,
    within_amp_path: str | Path,
    required_mode: str = "weighted",
) -> SimulationGateVerdict:
    """Evaluate whether simulation outputs may affect candidate selection.

    Confirmed policy:
    - `off` and `info` are always allowed because they do not affect ranking.
    - `weighted` requires both ablation artifacts and positive improvement.
    - Missing or malformed artifacts raise, rather than silently passing.
    """

    if required_mode not in {"off", "info", "weighted"}:
        raise ValueError("required_mode must be one of: off, info, weighted")

    if required_mode in {"off", "info"}:
        return SimulationGateVerdict(
            may_use_weighted_mode=False,
            integration_mode=required_mode,
            required_mode=required_mode,
            checks={
                "weighted_requested": False,
                "amp_vs_decoy_improves": False,
                "within_amp_improves": False,
            },
            reasons=[
                f"{required_mode} mode does not affect ranking; ablation permission not required."
            ],
        )

    amp_vs_decoy = _load_json(amp_vs_decoy_path)
    within_amp = _load_json(within_amp_path)

    amp_delta = float(_result(amp_vs_decoy, "delta", 0.0))
    within_delta = float(_result(within_amp, "delta", 0.0))
    amp_verdict = _result(amp_vs_decoy, "verdict", "UNKNOWN")
    within_verdict = _result(within_amp, "verdict", "UNKNOWN")

    checks = {
        "weighted_requested": True,
        "amp_vs_decoy_improves": amp_verdict == "IMPROVEMENT"
        and amp_delta > MIN_AMP_VS_DECOY_DELTA,
        "within_amp_improves": within_verdict == "IMPROVEMENT"
        and within_delta > MIN_WITHIN_AMP_DELTA,
    }

    reasons: list[str] = []
    if not checks["amp_vs_decoy_improves"]:
        reasons.append(
            "AMP-vs-decoy ablation does not improve over ensemble "
            f"(verdict={amp_verdict}, delta={amp_delta:+.4f})."
        )
    if not checks["within_amp_improves"]:
        reasons.append(
            "Within-AMP ablation does not improve over existing scorers "
            f"(verdict={within_verdict}, delta={within_delta:+.4f})."
        )

    may_use_weighted = all(checks.values())
    return SimulationGateVerdict(
        may_use_weighted_mode=may_use_weighted,
        integration_mode="weighted" if may_use_weighted else "info",
        required_mode=required_mode,
        checks=checks,
        reasons=reasons
        if reasons
        else ["Both simulation ablation views clear the weighted-mode bar."],
    )
