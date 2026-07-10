"""NRC- negative-result citation policy schema.

Enforces that any public positive claim references all known relevant negative
results.  Cherry-picking — highlighting successes while silently omitting
failures — is the most common way an AI pipeline overstates its case.

Every public claim about pipeline outputs must be paired with an NRC- record
that lists relevant NRR- records and confirms they are cited.  A claim with
uncited negatives is machine-flagged as non_compliant.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_NRC_VERDICTS: frozenset[str] = frozenset({
    "compliant",
    "non_compliant",
    "no_relevant_negatives",
})


@dataclass
class NegativeResultCitationPolicy:
    nrc_id: str
    claim_id: str
    pipeline_version: str
    relevant_nrr_ids: list[str]
    cited_nrr_ids: list[str]
    uncited_nrr_ids: list[str]
    uncited_count: int
    all_relevant_cited: bool
    policy_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_negative_result_citation_policy(nrc: NegativeResultCitationPolicy) -> None:
    if not nrc.nrc_id.startswith("NRC-"):
        raise ValueError(f"nrc_id must start with 'NRC-': {nrc.nrc_id!r}")
    if not nrc.claim_id:
        raise ValueError("claim_id must be non-empty")
    if not nrc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for nrr_id in nrc.relevant_nrr_ids:
        if not nrr_id.startswith("NRR-"):
            raise ValueError(f"relevant_nrr_id must start with 'NRR-': {nrr_id!r}")
    for nrr_id in nrc.cited_nrr_ids:
        if not nrr_id.startswith("NRR-"):
            raise ValueError(f"cited_nrr_id must start with 'NRR-': {nrr_id!r}")
    relevant_set = set(nrc.relevant_nrr_ids)
    for nrr_id in nrc.cited_nrr_ids:
        if nrr_id not in relevant_set:
            raise ValueError(
                f"cited_nrr_id {nrr_id!r} not in relevant_nrr_ids"
            )
    expected_uncited = [r for r in nrc.relevant_nrr_ids if r not in set(nrc.cited_nrr_ids)]
    if sorted(nrc.uncited_nrr_ids) != sorted(expected_uncited):
        raise ValueError("uncited_nrr_ids inconsistent with relevant_nrr_ids and cited_nrr_ids")
    if nrc.uncited_count != len(nrc.uncited_nrr_ids):
        raise ValueError("uncited_count must equal len(uncited_nrr_ids)")
    expected_all_cited = nrc.uncited_count == 0
    if nrc.all_relevant_cited != expected_all_cited:
        raise ValueError("all_relevant_cited inconsistent with uncited_count")
    if nrc.policy_verdict not in VALID_NRC_VERDICTS:
        raise ValueError(
            f"policy_verdict {nrc.policy_verdict!r} not in VALID_NRC_VERDICTS"
        )
    if not nrc.relevant_nrr_ids and nrc.policy_verdict != "no_relevant_negatives":
        raise ValueError(
            "policy_verdict must be 'no_relevant_negatives' when relevant_nrr_ids is empty"
        )
    if nrc.relevant_nrr_ids and nrc.all_relevant_cited and nrc.policy_verdict != "compliant":
        raise ValueError(
            "policy_verdict must be 'compliant' when all relevant negatives are cited"
        )
    if nrc.relevant_nrr_ids and not nrc.all_relevant_cited and nrc.policy_verdict != "non_compliant":
        raise ValueError(
            "policy_verdict must be 'non_compliant' when relevant negatives are uncited"
        )
    if not nrc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not nrc.limitations:
        raise ValueError("limitations must be non-empty")
    if not nrc.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(relevant: list[str], cited_set: set[str]) -> str:
    if not relevant:
        return "no_relevant_negatives"
    if all(r in cited_set for r in relevant):
        return "compliant"
    return "non_compliant"


def build_negative_result_citation_policy(
    *,
    nrc_id: str,
    claim_id: str,
    pipeline_version: str,
    relevant_nrr_ids: list[str],
    cited_nrr_ids: list[str],
    limitations: list[str],
    created_at: str,
) -> NegativeResultCitationPolicy:
    """Build a NegativeResultCitationPolicy.

    uncited_nrr_ids, uncited_count, all_relevant_cited, and policy_verdict
    are all auto-computed from relevant_nrr_ids and cited_nrr_ids.
    """
    relevant = list(relevant_nrr_ids)
    cited = list(cited_nrr_ids)
    cited_set = set(cited)
    uncited = [r for r in relevant if r not in cited_set]
    uncited_count = len(uncited)
    all_cited = uncited_count == 0
    verdict = _compute_verdict(relevant, cited_set)
    nrc = NegativeResultCitationPolicy(
        nrc_id=nrc_id,
        claim_id=claim_id,
        pipeline_version=pipeline_version,
        relevant_nrr_ids=relevant,
        cited_nrr_ids=cited,
        uncited_nrr_ids=uncited,
        uncited_count=uncited_count,
        all_relevant_cited=all_cited,
        policy_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_negative_result_citation_policy(nrc)
    return nrc


def format_negative_result_citation_policy(nrc: NegativeResultCitationPolicy) -> str:
    lines = [
        f"Negative-Result Citation Policy — {nrc.nrc_id}",
        f"Claim: {nrc.claim_id}  |  Pipeline: {nrc.pipeline_version}",
        f"Verdict: {nrc.policy_verdict}",
        f"Relevant negatives: {len(nrc.relevant_nrr_ids)}  "
        f"Cited: {len(nrc.cited_nrr_ids)}  "
        f"Uncited: {nrc.uncited_count}",
    ]
    if nrc.uncited_nrr_ids:
        lines.append(f"Uncited negatives: {', '.join(nrc.uncited_nrr_ids)}")
    lines.append(f"All relevant cited: {nrc.all_relevant_cited}")
    lines.append(f"Limitations: {'; '.join(nrc.limitations)}")
    lines.append(f"Created: {nrc.created_at}")
    lines.append(f"dry_lab_only: {nrc.dry_lab_only}")
    return "\n".join(lines)
