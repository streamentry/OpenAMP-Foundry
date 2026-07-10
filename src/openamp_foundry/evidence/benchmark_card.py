"""BenchmarkCard schema — Phase C C2.

Machine-readable documentation for each benchmark in the pipeline.
Prevents incomplete benchmark docs by requiring: measurement target,
split strategy, at least one cheap enemy baseline (must be beaten before
an advanced scorer gets ranking authority), at least one known limitation.

ID prefix: BMC-
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

BMC_PREFIX = "BMC-"

VALID_SPLIT_STRATEGIES = frozenset({
    "random_80_20",
    "random_70_30",
    "family_stratified",
    "charge_stratified",
    "length_stratified",
    "temporal_split",
    "scaffold_split",
    "leakage_aware_split",
    "cross_validation_5fold",
    "cross_validation_10fold",
})

VALID_MEASUREMENT_TARGETS = frozenset({
    "antimicrobial_activity_prediction",
    "hemolysis_risk_prediction",
    "toxicity_prediction",
    "novelty_scoring",
    "synthesis_feasibility",
    "diversity_selection",
    "ensemble_ranking",
    "safety_scoring",
    "selectivity_prediction",
    "calibration_accuracy",
})

VALID_EVALUATION_METRICS = frozenset({
    "precision_at_k",
    "recall_at_k",
    "auc_roc",
    "auc_pr",
    "mcc",
    "f1",
    "accuracy",
    "spearman_rho",
    "pearson_r",
    "enrichment_factor",
    "calibration_error",
    "brier_score",
})

_MIN_CHEAP_ENEMIES = 1
_MIN_KNOWN_LIMITATIONS = 1
_NOTES_MAX_LENGTH = 500
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:.+Z-]+)?$")


@dataclass
class BenchmarkCard:
    bmc_id: str
    pipeline_version: str
    benchmark_name: str
    measurement_target: str
    split_strategy: str
    cheap_enemy_baselines: List[str]
    evaluation_metrics: List[str]
    known_limitations: List[str]
    deprecated: bool
    created_date: str
    last_updated_date: str
    notes: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        warnings: list[str] = []

        # Rule 1: BMC- prefix
        if not self.bmc_id.startswith(BMC_PREFIX):
            errors.append(f"bmc_id must start with '{BMC_PREFIX}', got {self.bmc_id!r}")

        # Rule 2: pipeline_version non-empty
        if not self.pipeline_version.strip():
            errors.append("pipeline_version must not be empty")

        # Rule 3: benchmark_name non-empty
        if not self.benchmark_name.strip():
            errors.append("benchmark_name must not be empty")

        # Rule 4: measurement_target in controlled vocab
        if self.measurement_target not in VALID_MEASUREMENT_TARGETS:
            errors.append(
                f"measurement_target must be one of {sorted(VALID_MEASUREMENT_TARGETS)}, "
                f"got {self.measurement_target!r}"
            )

        # Rule 5: split_strategy in controlled vocab
        if self.split_strategy not in VALID_SPLIT_STRATEGIES:
            errors.append(
                f"split_strategy must be one of {sorted(VALID_SPLIT_STRATEGIES)}, "
                f"got {self.split_strategy!r}"
            )

        # Rule 6: cheap_enemy_baselines non-empty
        if not self.cheap_enemy_baselines or len(self.cheap_enemy_baselines) < _MIN_CHEAP_ENEMIES:
            errors.append(
                f"cheap_enemy_baselines must have at least {_MIN_CHEAP_ENEMIES} entry — "
                "a benchmark with no declared cheap enemies cannot prove the method beats "
                "trivial baselines"
            )

        # Rule 7: all cheap enemy names non-empty strings
        for i, enemy in enumerate(self.cheap_enemy_baselines):
            if not isinstance(enemy, str) or not enemy.strip():
                errors.append(f"cheap_enemy_baselines[{i}] must be a non-empty string")

        # Rule 8: evaluation_metrics non-empty and in vocab
        if not self.evaluation_metrics:
            errors.append("evaluation_metrics must have at least one entry")
        else:
            for metric in self.evaluation_metrics:
                if metric not in VALID_EVALUATION_METRICS:
                    errors.append(
                        f"evaluation_metrics entry {metric!r} must be one of "
                        f"{sorted(VALID_EVALUATION_METRICS)}"
                    )

        # Rule 9: known_limitations non-empty
        if not self.known_limitations or len(self.known_limitations) < _MIN_KNOWN_LIMITATIONS:
            errors.append(
                f"known_limitations must have at least {_MIN_KNOWN_LIMITATIONS} entry — "
                "every benchmark has limitations; document them or do not ship the benchmark"
            )

        # Rule 10: all known_limitations non-empty strings
        for i, lim in enumerate(self.known_limitations):
            if not isinstance(lim, str) or not lim.strip():
                errors.append(f"known_limitations[{i}] must be a non-empty string")

        # Rule 11: created_date ISO format
        if not _ISO_DATE_RE.match(self.created_date):
            errors.append(
                f"created_date must be ISO 8601 date, got {self.created_date!r}"
            )

        # Rule 12: last_updated_date ISO format
        if not _ISO_DATE_RE.match(self.last_updated_date):
            errors.append(
                f"last_updated_date must be ISO 8601 date, got {self.last_updated_date!r}"
            )

        # Rule 13: if deprecated, notes must explain why
        if self.deprecated and not self.notes.strip():
            errors.append(
                "notes must explain why the benchmark is deprecated when deprecated=True"
            )

        # Rule 14: notes length cap
        if len(self.notes) > _NOTES_MAX_LENGTH:
            errors.append(
                f"notes must be ≤{_NOTES_MAX_LENGTH} characters, got {len(self.notes)}"
            )

        # Warning: only one cheap enemy (weak — two or more preferred)
        if len(self.cheap_enemy_baselines) < 2:
            warnings.append(
                "cheap_enemy_baselines has only one entry; two or more cheap enemies "
                "provide stronger anti-hype evidence"
            )

        # Warning: only one known limitation (probably incomplete)
        if len(self.known_limitations) < 2:
            warnings.append(
                "known_limitations has only one entry; document at least two limitations "
                "for a complete benchmark card"
            )

        if errors:
            return errors
        return [f"WARNING: {w}" for w in warnings] if warnings else []


def validate_dict(data: dict) -> list[str]:
    """Validate a dict representation of BenchmarkCard."""
    try:
        record = BenchmarkCard(
            bmc_id=data.get("bmc_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            benchmark_name=data.get("benchmark_name", ""),
            measurement_target=data.get("measurement_target", ""),
            split_strategy=data.get("split_strategy", ""),
            cheap_enemy_baselines=data.get("cheap_enemy_baselines", []),
            evaluation_metrics=data.get("evaluation_metrics", []),
            known_limitations=data.get("known_limitations", []),
            deprecated=data.get("deprecated", False),
            created_date=data.get("created_date", ""),
            last_updated_date=data.get("last_updated_date", ""),
            notes=data.get("notes", ""),
        )
        return record.validate()
    except Exception as exc:
        return [f"Construction error: {exc}"]
