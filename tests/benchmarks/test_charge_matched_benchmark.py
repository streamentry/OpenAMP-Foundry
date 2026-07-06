from __future__ import annotations

import csv

from openamp_foundry.benchmark.charge_matched import (
    SequenceRecord,
    auroc_from_scores,
    charge_density,
    greedy_charge_matched_decoys,
    run_charge_balanced_synthetic_benchmark,
    run_charge_matched_benchmark,
    synthesize_charge_balanced_decoy,
)


def test_auroc_from_scores_handles_ties():
    assert auroc_from_scores([0.8, 0.5], [0.5, 0.2]) == 0.875


def test_charge_density_uses_ph74_side_chain_charge():
    assert charge_density("KKAA") == 0.5
    assert charge_density("AAAA") == 0.0


def test_greedy_charge_matched_decoys_uses_each_decoy_once():
    positives = [
        SequenceRecord("P1", "KKAA"),
        SequenceRecord("P2", "KAAA"),
    ]
    decoys = [
        SequenceRecord("D1", "KKGG"),
        SequenceRecord("D2", "KGGG"),
    ]

    matches = greedy_charge_matched_decoys(positives, decoys)

    assert [match["decoy_id"] for match in matches] == ["D1", "D2"]
    assert len({match["decoy_id"] for match in matches}) == 2


def test_synthetic_charge_balanced_decoy_preserves_charge_density():
    record = SequenceRecord("AMP-1", "KRDHAAAILL")

    decoy = synthesize_charge_balanced_decoy(record)

    assert decoy.record_id == "SYN-AMP-1"
    assert len(decoy.sequence) == len(record.sequence)
    assert charge_density(decoy.sequence) == charge_density(record.sequence)


def test_synthetic_charge_balanced_decoy_is_deterministic():
    record = SequenceRecord("AMP-1", "KRDHAAAILL")

    first = synthesize_charge_balanced_decoy(record, seed=7)
    second = synthesize_charge_balanced_decoy(record, seed=7)

    assert first == second


def test_run_charge_matched_benchmark_reports_adversarial_metrics(tmp_path):
    amp_csv = tmp_path / "amps.csv"
    decoy_csv = tmp_path / "decoys.csv"
    with amp_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "sequence"])
        writer.writeheader()
        writer.writerow({"id": "A1", "sequence": "KWKLFKKIGAVLKVL"})
        writer.writerow({"id": "A2", "sequence": "RLLRLLRLLR"})
    with decoy_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "sequence"])
        writer.writeheader()
        writer.writerow({"id": "D1", "sequence": "KAGAKAGAAG"})
        writer.writerow({"id": "D2", "sequence": "RAGARAGAAG"})

    result = run_charge_matched_benchmark(amp_csv, decoy_csv)

    assert result["benchmark"] == "charge_matched_decoys"
    assert result["n_positives"] == 2
    assert result["n_matched_decoys"] == 2
    assert "pipeline_auroc" in result
    assert "charge_density_auroc" in result
    assert result["matches_preview"]


def test_run_charge_balanced_synthetic_benchmark_reports_exact_charge_control(tmp_path):
    amp_csv = tmp_path / "amps.csv"
    with amp_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "sequence"])
        writer.writeheader()
        writer.writerow({"id": "A1", "sequence": "KWKLFKKIGAVLKVL"})
        writer.writerow({"id": "A2", "sequence": "RLLRLLRLLR"})

    result = run_charge_balanced_synthetic_benchmark(amp_csv)

    assert result["benchmark"] == "charge_balanced_synthetic_decoys"
    assert result["n_positives"] == 2
    assert result["n_synthetic_decoys"] == 2
    assert result["max_abs_charge_density_delta"] == 0.0
    assert result["charge_density_auroc"] == 0.5
    assert result["decoys_preview"]
