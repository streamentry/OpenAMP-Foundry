from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RankingPolicy:
    mode: str
    recommended_for: str
    evidence_basis: list[str]
    caution: str
    not_a_claim: str


def get_ranking_policy(mode: str) -> RankingPolicy:
    if mode == "expert":
        return RankingPolicy(
            mode="expert",
            recommended_for=(
                "Use only as an explicit safety-aware alternative when triaging among "
                "AMP-like candidates where hemolysis/selectivity trade-offs matter."
            ),
            evidence_basis=[
                "Within-AMP selectivity benchmark: expert composite trends better than ensemble on hemolysis-aware ranking, but the signal is not yet statistically secure.",
                "Multi-class triage benchmark: ensemble shows anti-selective bias; selectivity_proxy is the only scorer that clearly triages selective > hemolytic > decoy.",
            ],
            caution=(
                "Do not treat expert ranking as the default synthesis gate. On the broader "
                "AMP vs decoy benchmark, expert composite underperforms the simple ensemble."
            ),
            not_a_claim=(
                "Expert mode is not a validated safety predictor and does not establish low "
                "hemolysis risk. Experimental hemolysis assay is still required."
            ),
        )

    return RankingPolicy(
        mode="ensemble",
        recommended_for=(
            "Default synthesis gate for broad AMP-vs-decoy ranking until a stronger "
            "selectivity-aware replacement beats it across honest benchmarks."
        ),
        evidence_basis=[
            "Retrospective AMP vs decoy benchmark: ensemble AUROC remains higher than expert composite.",
            "Cluster-split benchmark: ensemble still carries the repo's strongest leakage-aware broad ranking signal.",
        ],
        caution=(
            "Do not mistake the default for safety-awareness. The ensemble shows anti-selective "
            "bias on the multi-class triage benchmark and should be checked against safety-specific views."
        ),
        not_a_claim=(
            "Ensemble mode does not prove antimicrobial activity, safety, or wet-lab readiness."
        ),
    )


def ranking_policy_payload(mode: str) -> dict[str, object]:
    return asdict(get_ranking_policy(mode))
