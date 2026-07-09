from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class BenchmarkCard:
    benchmark_id: str
    benchmark_name: str
    version: str
    date: str
    metric: str
    metric_value: float
    baseline_name: str
    baseline_value: float
    delta: float
    beats_baseline: bool
    dataset: str
    dataset_size: int
    scope: list[str]
    caveats: list[str]
    dry_lab_only: bool = True


def make_benchmark_card(
    benchmark_id: str,
    benchmark_name: str,
    metric: str,
    metric_value: float,
    baseline_name: str,
    baseline_value: float,
    dataset: str,
    dataset_size: int,
    *,
    version: str = "1.0.0",
    date: str = "",
    scope: list[str] | None = None,
    caveats: list[str] | None = None,
) -> BenchmarkCard:
    delta = metric_value - baseline_value
    beats_baseline = delta > 0
    return BenchmarkCard(
        benchmark_id=benchmark_id,
        benchmark_name=benchmark_name,
        version=version,
        date=date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        metric=metric,
        metric_value=metric_value,
        baseline_name=baseline_name,
        baseline_value=baseline_value,
        delta=delta,
        beats_baseline=beats_baseline,
        dataset=dataset,
        dataset_size=dataset_size,
        scope=scope or [],
        caveats=caveats or [],
    )


def validate_benchmark_card(card: BenchmarkCard) -> list[str]:
    errors: list[str] = []
    if not card.benchmark_id:
        errors.append("benchmark_id must be non-empty")
    if not card.benchmark_name:
        errors.append("benchmark_name must be non-empty")
    if not card.metric:
        errors.append("metric must be non-empty")
    if not card.dataset:
        errors.append("dataset must be non-empty")
    if not card.baseline_name:
        errors.append("baseline_name must be non-empty")
    if card.dataset_size < 1:
        errors.append(f"dataset_size must be >= 1, got {card.dataset_size}")
    expected_delta = card.metric_value - card.baseline_value
    if abs(card.delta - expected_delta) > 1e-9:
        errors.append(
            f"delta {card.delta} does not match metric_value - baseline_value "
            f"({expected_delta})"
        )
    expected_beats = expected_delta > 0
    if card.beats_baseline != expected_beats:
        errors.append(
            f"beats_baseline={card.beats_baseline} does not match delta > 0 "
            f"({expected_beats})"
        )
    if not card.dry_lab_only:
        errors.append("dry_lab_only must be True")
    return errors


def benchmark_card_summary(cards: list[BenchmarkCard]) -> dict:
    beats_count = sum(1 for c in cards if c.beats_baseline)
    fails_count = sum(1 for c in cards if not c.beats_baseline)
    return {
        "total": len(cards),
        "beats_baseline_count": beats_count,
        "fails_baseline_count": fails_count,
        "dry_lab_only": True,
    }
