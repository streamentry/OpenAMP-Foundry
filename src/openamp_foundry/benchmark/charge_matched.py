from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from openamp_foundry.config import load_config
from openamp_foundry.features.physchem import compute_features, net_charge_at_ph74
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.ensemble import ensemble_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


@dataclass(frozen=True)
class SequenceRecord:
    record_id: str
    sequence: str


def auroc_from_scores(positive_scores: Iterable[float], negative_scores: Iterable[float]) -> float:
    pos = list(positive_scores)
    neg = list(negative_scores)
    if not pos or not neg:
        return 0.5

    better = 0.0
    total = 0
    for p_score in pos:
        for n_score in neg:
            if p_score > n_score:
                better += 1.0
            elif p_score == n_score:
                better += 0.5
            total += 1
    return better / total if total else 0.5


def load_sequence_records(path: str | Path) -> list[SequenceRecord]:
    records: list[SequenceRecord] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if "sequence" not in (reader.fieldnames or []):
            raise ValueError(f"{path} is missing required 'sequence' column")
        for idx, row in enumerate(reader, start=1):
            records.append(
                SequenceRecord(
                    record_id=row.get("id") or f"row-{idx:06d}",
                    sequence="".join(row["sequence"].strip().upper().split()),
                )
            )
    return records


def charge_density(sequence: str) -> float:
    return round(net_charge_at_ph74(sequence) / len(sequence), 4) if sequence else 0.0


def pipeline_score(sequence: str, config_path: str | Path = "configs/pipeline.yaml") -> float:
    config = load_config(config_path)
    features = compute_features(sequence)
    scores = {
        "activity": activity_likeness_score(features),
        "safety": safety_score(features),
        "synthesis": synthesis_feasibility_score(features, valid_sequence=True),
        "novelty": 1.0,
    }
    return ensemble_score(scores, config["weights"])


def greedy_charge_matched_decoys(
    positives: list[SequenceRecord],
    decoys: list[SequenceRecord],
) -> list[dict]:
    unused = {item.record_id: item for item in decoys}
    matches: list[dict] = []
    for positive in sorted(positives, key=lambda item: item.record_id):
        pos_density = charge_density(positive.sequence)
        best = min(
            unused.values(),
            key=lambda decoy: (
                abs(charge_density(decoy.sequence) - pos_density),
                decoy.record_id,
            ),
        )
        del unused[best.record_id]
        decoy_density = charge_density(best.sequence)
        matches.append(
            {
                "positive_id": positive.record_id,
                "decoy_id": best.record_id,
                "positive_charge_density": pos_density,
                "decoy_charge_density": decoy_density,
                "abs_charge_density_delta": round(abs(pos_density - decoy_density), 4),
            }
        )
    return matches


def run_charge_matched_benchmark(
    amp_csv: str | Path,
    decoy_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
) -> dict:
    positives = load_sequence_records(amp_csv)
    decoys = load_sequence_records(decoy_csv)
    if len(decoys) < len(positives):
        raise ValueError("charge-matched benchmark requires at least as many decoys as positives")

    matches = greedy_charge_matched_decoys(positives, decoys)
    decoy_by_id = {item.record_id: item for item in decoys}
    matched_decoys = [decoy_by_id[match["decoy_id"]] for match in matches]

    pos_pipeline = [pipeline_score(item.sequence, config_path) for item in positives]
    neg_pipeline = [pipeline_score(item.sequence, config_path) for item in matched_decoys]
    pos_charge = [charge_density(item.sequence) for item in positives]
    neg_charge = [charge_density(item.sequence) for item in matched_decoys]

    mean_abs_delta = (
        sum(match["abs_charge_density_delta"] for match in matches) / len(matches)
        if matches
        else 0.0
    )

    pipeline_auroc = auroc_from_scores(pos_pipeline, neg_pipeline)
    charge_auroc = auroc_from_scores(pos_charge, neg_charge)
    return {
        "benchmark": "charge_matched_decoys",
        "n_positives": len(positives),
        "n_decoys_available": len(decoys),
        "n_matched_decoys": len(matched_decoys),
        "mean_abs_charge_density_delta": round(mean_abs_delta, 4),
        "pipeline_auroc": round(pipeline_auroc, 4),
        "charge_density_auroc": round(charge_auroc, 4),
        "pipeline_minus_charge_density": round(pipeline_auroc - charge_auroc, 4),
        "interpretation": (
            "Pipeline signal remains after charge matching."
            if pipeline_auroc > 0.6 and pipeline_auroc > charge_auroc
            else "Pipeline signal is weak once charge density is matched; treat raw AMP-vs-decoy AUROC as charge-inflated."
        ),
        "matches_preview": matches[:20],
    }
