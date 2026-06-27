from __future__ import annotations

import random

CANONICAL_AA = "ACDEFGHIKLMNPQRSTVWY"


def mutate_sequence(sequence: str, mutations: int = 1, seed: int | None = None) -> str:
    """Toy mutation generator for benchmarking only.

    This is deliberately simple and bounded. It is not a high-capability design model.
    """
    rng = random.Random(seed)
    seq = list(sequence)
    if not seq:
        return sequence
    for _ in range(max(0, mutations)):
        idx = rng.randrange(len(seq))
        seq[idx] = rng.choice(CANONICAL_AA)
    return "".join(seq)
