from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List


VALID_TREND_VERDICTS = frozenset({
    "improving",
    "stable",
    "degrading",
    "insufficient_data",
})

DEFAULT_ROLLING_WINDOW = 5
DEFAULT_ALERT_THRESHOLD = 0.1
MIN_OUTCOMES_FOR_TREND = 2


@dataclass
class WHROutcomeRecord:
    whr_id: str
    batch_id: str
    predicted_score: float
    confirmed_hit: bool
    confirmation_date: str


@dataclass
class PredictionQualityTrendReport:
    pqt_id: str
    pipeline_version: str
    n_outcomes_total: int
    n_confirmed_hits: int
    n_batches_covered: int
    outcome_records: List[WHROutcomeRecord]
    rolling_window_size: int
    rolling_precision_values: List[float]
    overall_precision: float
    trend_verdict: str
    degradation_alert: bool
    score_hit_correlation: float
    dry_lab_only: bool
    limitations: List[str]
    created_at: str
    alert_threshold: float


@dataclass
class PQTValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def _pearson_r(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(a * b for a, b in zip(xs, ys))
    sum_x2 = sum(a * a for a in xs)
    sum_y2 = sum(b * b for b in ys)
    numerator = n * sum_xy - sum_x * sum_y
    denom = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
    if denom == 0.0:
        return 0.0
    return numerator / denom


def _compute_rolling_precision(
    outcome_records: List[WHROutcomeRecord], window_size: int
) -> List[float]:
    n = len(outcome_records)
    if n < window_size:
        return []
    values = []
    for i in range(n - window_size + 1):
        window = outcome_records[i : i + window_size]
        hits = sum(1 for r in window if r.confirmed_hit)
        values.append(hits / window_size)
    return values


def validate_prediction_quality_trend_report(
    report: PredictionQualityTrendReport,
) -> PQTValidationResult:
    violations = []

    if not report.pqt_id.startswith("PQT-"):
        violations.append("pqt_id must start with 'PQT-'")

    if not report.dry_lab_only:
        violations.append("dry_lab_only must be True for PQT- records")

    if report.n_outcomes_total != len(report.outcome_records):
        violations.append(
            f"n_outcomes_total ({report.n_outcomes_total}) must equal len(outcome_records) ({len(report.outcome_records)})"
        )

    expected_n_hits = sum(1 for r in report.outcome_records if r.confirmed_hit)
    if report.n_confirmed_hits != expected_n_hits:
        violations.append(
            f"n_confirmed_hits ({report.n_confirmed_hits}) must equal sum(confirmed_hit) ({expected_n_hits})"
        )

    expected_batches = len(set(r.batch_id for r in report.outcome_records))
    if report.n_batches_covered != expected_batches:
        violations.append(
            f"n_batches_covered ({report.n_batches_covered}) must equal len(unique batch_ids) ({expected_batches})"
        )

    n = report.n_outcomes_total
    expected_overall = (n_conf := report.n_confirmed_hits) / n if n > 0 else 0.0
    if abs(report.overall_precision - expected_overall) > 0.001:
        violations.append(
            f"overall_precision ({report.overall_precision}) inconsistent with {n_conf}/{n} ({expected_overall})"
        )

    if report.rolling_window_size < 2:
        violations.append(
            f"rolling_window_size must be >= 2, got {report.rolling_window_size}"
        )

    k = report.rolling_window_size
    expected_rpv_len = max(0, n - k + 1)
    if len(report.rolling_precision_values) != expected_rpv_len:
        violations.append(
            f"len(rolling_precision_values) ({len(report.rolling_precision_values)}) must equal max(0, n_outcomes_total - rolling_window_size + 1) ({expected_rpv_len})"
        )

    rpv = report.rolling_precision_values
    threshold = report.alert_threshold

    if report.trend_verdict == "insufficient_data":
        if len(rpv) != 0:
            violations.append(
                f"trend_verdict='insufficient_data' requires empty rolling_precision_values, got len={len(rpv)}"
            )
    elif report.trend_verdict == "improving":
        if len(rpv) == 0:
            violations.append("trend_verdict='improving' requires non-empty rolling_precision_values")
        elif not (rpv[-1] > rpv[0] + threshold):
            violations.append(
                f"trend_verdict='improving' requires last rpv ({rpv[-1]}) > first rpv + threshold ({rpv[0]} + {threshold} = {rpv[0] + threshold})"
            )
    elif report.trend_verdict == "degrading":
        if len(rpv) == 0:
            violations.append("trend_verdict='degrading' requires non-empty rolling_precision_values")
        elif not (rpv[-1] < rpv[0] - threshold):
            violations.append(
                f"trend_verdict='degrading' requires last rpv ({rpv[-1]}) < first rpv - threshold ({rpv[0]} - {threshold} = {rpv[0] - threshold})"
            )
    elif report.trend_verdict == "stable":
        if len(rpv) == 0:
            violations.append("trend_verdict='stable' requires non-empty rolling_precision_values")
        elif not (abs(rpv[-1] - rpv[0]) <= threshold):
            violations.append(
                f"trend_verdict='stable' requires |last rpv - first rpv| <= threshold, got |{rpv[-1]} - {rpv[0]}| = {abs(rpv[-1] - rpv[0])} > {threshold}"
            )
    else:
        violations.append(
            f"trend_verdict '{report.trend_verdict}' must be one of {sorted(VALID_TREND_VERDICTS)}"
        )

    expected_degradation = report.trend_verdict == "degrading"
    if report.degradation_alert != expected_degradation:
        violations.append(
            f"degradation_alert ({report.degradation_alert}) must equal (trend_verdict == 'degrading') ({expected_degradation})"
        )

    if not (-1.0 <= report.score_hit_correlation <= 1.0):
        violations.append(
            f"score_hit_correlation ({report.score_hit_correlation}) must be in range [-1.0, 1.0]"
        )

    if not report.limitations:
        violations.append("limitations must be non-empty")

    if not (0 < report.alert_threshold <= 1.0):
        violations.append(
            f"alert_threshold ({report.alert_threshold}) must be > 0 and <= 1.0"
        )

    return PQTValidationResult(valid=len(violations) == 0, violations=violations)


def build_prediction_quality_trend_report(
    pqt_id: str,
    pipeline_version: str,
    outcome_records: List[WHROutcomeRecord],
    limitations: List[str],
    created_at: str,
    rolling_window_size: int = DEFAULT_ROLLING_WINDOW,
    alert_threshold: float = DEFAULT_ALERT_THRESHOLD,
) -> PredictionQualityTrendReport:
    n_outcomes_total = len(outcome_records)
    n_confirmed_hits = sum(1 for r in outcome_records if r.confirmed_hit)
    n_batches_covered = len(set(r.batch_id for r in outcome_records))

    overall_precision = n_confirmed_hits / n_outcomes_total if n_outcomes_total > 0 else 0.0

    rolling_precision_values = _compute_rolling_precision(outcome_records, rolling_window_size)

    if len(rolling_precision_values) == 0:
        trend_verdict = "insufficient_data"
    else:
        first = rolling_precision_values[0]
        last = rolling_precision_values[-1]
        if last > first + alert_threshold:
            trend_verdict = "improving"
        elif last < first - alert_threshold:
            trend_verdict = "degrading"
        else:
            trend_verdict = "stable"

    degradation_alert = trend_verdict == "degrading"

    predicted_scores = [r.predicted_score for r in outcome_records]
    hit_ints = [int(r.confirmed_hit) for r in outcome_records]
    score_hit_correlation = _pearson_r(predicted_scores, hit_ints)

    report = PredictionQualityTrendReport(
        pqt_id=pqt_id,
        pipeline_version=pipeline_version,
        n_outcomes_total=n_outcomes_total,
        n_confirmed_hits=n_confirmed_hits,
        n_batches_covered=n_batches_covered,
        outcome_records=outcome_records,
        rolling_window_size=rolling_window_size,
        rolling_precision_values=rolling_precision_values,
        overall_precision=overall_precision,
        trend_verdict=trend_verdict,
        degradation_alert=degradation_alert,
        score_hit_correlation=score_hit_correlation,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
        alert_threshold=alert_threshold,
    )

    result = validate_prediction_quality_trend_report(report)
    if not result.valid:
        raise ValueError(f"Invalid PQT: {result.violations}")
    return report


def format_prediction_quality_trend_report(report: PredictionQualityTrendReport) -> str:
    lines = [
        f"Prediction Quality Trend Report — {report.pqt_id}",
        f"Pipeline: {report.pipeline_version}  |  Outcomes: {report.n_outcomes_total}  |  Hits: {report.n_confirmed_hits}",
        f"Batches Covered: {report.n_batches_covered}  |  Window: {report.rolling_window_size}",
        f"Overall Precision: {report.overall_precision:.4f}  |  Verdict: {report.trend_verdict}",
        f"Degradation Alert: {report.degradation_alert}  |  Threshold: {report.alert_threshold:.2f}",
        f"Score–Hit Correlation: {report.score_hit_correlation:.4f}",
        f"Rolling Precision Values: {[f'{v:.4f}' for v in report.rolling_precision_values]}",
        f"Created: {report.created_at}",
        f"Limitations: {'; '.join(report.limitations)}",
        "dry_lab_only: True",
    ]
    return "\n".join(lines)
