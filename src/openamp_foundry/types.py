from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PeptideCandidate:
    candidate_id: str
    sequence: str
    source: str = "unknown"


@dataclass
class ScoredCandidate:
    candidate: PeptideCandidate
    features: dict[str, Any]
    scores: dict[str, float]
    references_checked: list[str] = field(default_factory=list)
    nearest_reference: dict[str, Any] | None = None
    selection_reason: list[str] = field(default_factory=list)
    known_failure_modes: list[str] = field(default_factory=list)
