from __future__ import annotations

from openamp_foundry.types import PeptideCandidate


def deterministic_split(
    candidates: list[PeptideCandidate], holdout_mod: int = 5
) -> tuple[list[PeptideCandidate], list[PeptideCandidate]]:
    train: list[PeptideCandidate] = []
    holdout: list[PeptideCandidate] = []
    for i, cand in enumerate(candidates):
        if i % holdout_mod == 0:
            holdout.append(cand)
        else:
            train.append(cand)
    return train, holdout
