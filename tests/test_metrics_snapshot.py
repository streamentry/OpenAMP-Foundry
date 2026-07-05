from __future__ import annotations

import json

from openamp_foundry.benchmark.metrics_snapshot import build_metrics_snapshot


def test_metrics_snapshot_matches_current_benchmark_truth(tmp_path):
    snapshot = build_metrics_snapshot(n_bootstrap=200)

    assert snapshot["schema_version"] == 1
    assert snapshot["standard"]["n_total"] == 191
    assert snapshot["standard"]["n_positives"] == 95
    assert snapshot["standard"]["n_negatives"] == 96
    assert snapshot["standard"]["auroc"] == 0.7832
    assert snapshot["phase3"]["auroc"] == 0.7448
    assert snapshot["cluster_split"]["full_auroc"] == 0.7832
    assert snapshot["expert_ablation"]["expert_auroc"] == 0.7097
    assert snapshot["selectivity"]["n_hemolytic"] == 54
    assert snapshot["triage"]["best_scorer"] == "gate_triage"
    assert "gate_triage" in snapshot["triage"]["per_scorer"]
    assert snapshot["triage"]["per_scorer"]["gate_triage"]["triages_correctly"] is True
    assert snapshot["charge_matched_decoys"]["benchmark"] == "charge_matched_decoys"
    assert snapshot["charge_matched_decoys"]["n_positives"] == 500
    assert "top_20_by_gate_triage" in snapshot["triage"]
    assert "top_20_by_gate_triage" in snapshot["strict_triage"]
    assert "expert_composite" in snapshot["triage"]["per_scorer"]
    assert snapshot["triage"]["per_scorer"]["expert_composite"]["triages_correctly"] is True
    assert snapshot["triage"]["top_20_by_expert_composite"]["DECOY"] > 0

    out = tmp_path / "metrics_snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
    reloaded = json.loads(out.read_text(encoding="utf-8"))
    assert reloaded["standard"]["auroc"] == 0.7832
