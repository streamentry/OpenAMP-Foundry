from __future__ import annotations

import csv
import hashlib
import random
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


CHARGED_RESIDUES = frozenset("KRDEH")
NEUTRAL_BACKGROUND = "AACCGGILLMNPQSSFSTTVVWWY"


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


def _stable_seed(record_id: str, sequence: str, seed: int) -> int:
    payload = f"{seed}:{record_id}:{sequence}".encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)


def synthesize_charge_balanced_decoy(
    record: SequenceRecord,
    *,
    seed: int = 20260706,
) -> SequenceRecord:
    """Create a deterministic synthetic decoy with matched length and charged residues.

    This is a negative-control stress test, not a biological negative dataset. It
    preserves K/R/D/E/H counts exactly and samples every other residue from a
    neutral background, so charge-density discrimination is forced to chance.
    """

    rng = random.Random(_stable_seed(record.record_id, record.sequence, seed))
    charged = [aa for aa in record.sequence if aa in CHARGED_RESIDUES]
    neutral_count = max(0, len(record.sequence) - len(charged))
    residues = charged + [rng.choice(NEUTRAL_BACKGROUND) for _ in range(neutral_count)]
    rng.shuffle(residues)
    return SequenceRecord(
        record_id=f"SYN-{record.record_id}",
        sequence="".join(residues),
    )


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


def run_charge_balanced_synthetic_benchmark(
    amp_csv: str | Path,
    config_path: str | Path = "configs/pipeline.yaml",
    seed: int = 20260706,
) -> dict:
    positives = load_sequence_records(amp_csv)
    synthetic_decoys = [
        synthesize_charge_balanced_decoy(record, seed=seed) for record in positives
    ]

    pos_pipeline = [pipeline_score(item.sequence, config_path) for item in positives]
    neg_pipeline = [pipeline_score(item.sequence, config_path) for item in synthetic_decoys]
    pos_charge = [charge_density(item.sequence) for item in positives]
    neg_charge = [charge_density(item.sequence) for item in synthetic_decoys]

    deltas = [abs(pos - neg) for pos, neg in zip(pos_charge, neg_charge, strict=True)]
    pipeline_auroc = auroc_from_scores(pos_pipeline, neg_pipeline)
    charge_auroc = auroc_from_scores(pos_charge, neg_charge)
    return {
        "benchmark": "charge_balanced_synthetic_decoys",
        "decoy_policy": (
            "Synthetic control preserving length and K/R/D/E/H counts; neutral "
            "positions resampled from a fixed neutral residue background."
        ),
        "seed": seed,
        "n_positives": len(positives),
        "n_synthetic_decoys": len(synthetic_decoys),
        "mean_abs_charge_density_delta": round(sum(deltas) / len(deltas), 4)
        if deltas
        else 0.0,
        "max_abs_charge_density_delta": round(max(deltas), 4) if deltas else 0.0,
        "pipeline_auroc": round(pipeline_auroc, 4),
        "charge_density_auroc": round(charge_auroc, 4),
        "pipeline_minus_charge_density": round(pipeline_auroc - charge_auroc, 4),
        "interpretation": (
            "Pipeline retains signal against exact charge-balanced synthetic controls."
            if pipeline_auroc > 0.6 and charge_auroc == 0.5
            else "Pipeline does not establish robust non-charge signal against exact charge-balanced synthetic controls."
        ),
        "decoys_preview": [
            {
                "positive_id": positive.record_id,
                "synthetic_decoy_id": decoy.record_id,
                "positive_charge_density": charge_density(positive.sequence),
                "synthetic_charge_density": charge_density(decoy.sequence),
                "synthetic_sequence": decoy.sequence,
            }
            for positive, decoy in zip(positives[:20], synthetic_decoys[:20], strict=True)
        ],
    }
