"""NSN- no-silent-network policy schema for simulation adapters.

Sequence data is sensitive.  An adapter that silently sends candidate
sequences to an external endpoint could expose proprietary sequences
without any audit trail.

This policy requires that:
  1. Every external network call an adapter can make is declared upfront.
  2. Any call NOT in the declared list is flagged as undeclared.
  3. Any call that could transmit sequence data is flagged as a
     sequence-exposure risk regardless of declaration.

In dry-lab mode the expected network call count is zero.
A compliant adapter either makes no network calls or makes only
explicitly declared calls with no sequence-bearing endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_NSN_VERDICTS: frozenset[str] = frozenset({
    "compliant",
    "undeclared_calls_detected",
    "sequence_exposure_risk",
})

SEQUENCE_EXPOSURE_KEYWORDS: tuple[str, ...] = (
    "sequence",
    "seq",
    "fasta",
    "peptide",
    "protein",
    "amino",
    "residue",
)


@dataclass
class NoSilentNetworkPolicy:
    nsn_id: str
    adapter_id: str
    pipeline_version: str
    declared_network_calls: list[str]
    observed_network_calls: list[str]
    undeclared_calls: list[str]
    undeclared_calls_detected: bool
    sequence_exposure_risk: bool
    policy_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _has_sequence_exposure_risk(calls: list[str]) -> bool:
    for call in calls:
        call_lower = call.lower()
        if any(kw in call_lower for kw in SEQUENCE_EXPOSURE_KEYWORDS):
            return True
    return False


def validate_no_silent_network_policy(nsn: NoSilentNetworkPolicy) -> None:
    if not nsn.nsn_id.startswith("NSN-"):
        raise ValueError(f"nsn_id must start with 'NSN-': {nsn.nsn_id!r}")
    if not nsn.adapter_id:
        raise ValueError("adapter_id must be non-empty")
    if not nsn.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if nsn.policy_verdict not in VALID_NSN_VERDICTS:
        raise ValueError(
            f"policy_verdict {nsn.policy_verdict!r} not in VALID_NSN_VERDICTS"
        )
    declared_set = set(nsn.declared_network_calls)
    expected_undeclared = [c for c in nsn.observed_network_calls if c not in declared_set]
    if sorted(nsn.undeclared_calls) != sorted(expected_undeclared):
        raise ValueError("undeclared_calls inconsistent with observed/declared network calls")
    expected_undeclared_flag = len(nsn.undeclared_calls) > 0
    if nsn.undeclared_calls_detected != expected_undeclared_flag:
        raise ValueError(
            "undeclared_calls_detected inconsistent with undeclared_calls"
        )
    all_calls = nsn.declared_network_calls + nsn.observed_network_calls
    expected_exposure = _has_sequence_exposure_risk(all_calls)
    if nsn.sequence_exposure_risk != expected_exposure:
        raise ValueError(
            "sequence_exposure_risk inconsistent with network call endpoints"
        )
    if nsn.undeclared_calls_detected and nsn.policy_verdict != "undeclared_calls_detected":
        raise ValueError(
            "policy_verdict must be 'undeclared_calls_detected' when undeclared calls present"
        )
    if (
        nsn.sequence_exposure_risk
        and not nsn.undeclared_calls_detected
        and nsn.policy_verdict != "sequence_exposure_risk"
    ):
        raise ValueError(
            "policy_verdict must be 'sequence_exposure_risk' when sequence exposure risk present"
        )
    if (
        not nsn.undeclared_calls_detected
        and not nsn.sequence_exposure_risk
        and nsn.policy_verdict != "compliant"
    ):
        raise ValueError(
            "policy_verdict must be 'compliant' when no undeclared calls and no exposure risk"
        )
    if not nsn.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not nsn.limitations:
        raise ValueError("limitations must be non-empty")
    if not nsn.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    undeclared_calls_detected: bool,
    sequence_exposure_risk: bool,
) -> str:
    if undeclared_calls_detected:
        return "undeclared_calls_detected"
    if sequence_exposure_risk:
        return "sequence_exposure_risk"
    return "compliant"


def build_no_silent_network_policy(
    *,
    nsn_id: str,
    adapter_id: str,
    pipeline_version: str,
    declared_network_calls: list[str] | None = None,
    observed_network_calls: list[str] | None = None,
    limitations: list[str],
    created_at: str,
) -> NoSilentNetworkPolicy:
    """Build a NoSilentNetworkPolicy.

    undeclared_calls, undeclared_calls_detected, sequence_exposure_risk,
    and policy_verdict are all auto-computed.
    """
    declared = list(declared_network_calls) if declared_network_calls else []
    observed = list(observed_network_calls) if observed_network_calls else []
    declared_set = set(declared)
    undeclared = [c for c in observed if c not in declared_set]
    undeclared_detected = len(undeclared) > 0
    all_calls = declared + observed
    exposure_risk = _has_sequence_exposure_risk(all_calls)
    verdict = _compute_verdict(undeclared_detected, exposure_risk)
    nsn = NoSilentNetworkPolicy(
        nsn_id=nsn_id,
        adapter_id=adapter_id,
        pipeline_version=pipeline_version,
        declared_network_calls=declared,
        observed_network_calls=observed,
        undeclared_calls=undeclared,
        undeclared_calls_detected=undeclared_detected,
        sequence_exposure_risk=exposure_risk,
        policy_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_no_silent_network_policy(nsn)
    return nsn


def format_no_silent_network_policy(nsn: NoSilentNetworkPolicy) -> str:
    lines = [
        f"No-Silent-Network Policy — {nsn.nsn_id}",
        f"Adapter: {nsn.adapter_id}  |  Pipeline: {nsn.pipeline_version}",
        f"Verdict: {nsn.policy_verdict}",
        f"Declared calls: {len(nsn.declared_network_calls)}",
        f"Observed calls: {len(nsn.observed_network_calls)}",
        f"Undeclared calls detected: {nsn.undeclared_calls_detected}",
        f"Sequence exposure risk: {nsn.sequence_exposure_risk}",
    ]
    if nsn.undeclared_calls:
        lines.append(f"Undeclared calls: {', '.join(nsn.undeclared_calls)}")
    lines.append(f"Limitations: {'; '.join(nsn.limitations)}")
    lines.append(f"Created: {nsn.created_at}")
    lines.append(f"dry_lab_only: {nsn.dry_lab_only}")
    return "\n".join(lines)
