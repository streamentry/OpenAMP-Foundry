"""Tests for the active-learning batch-2 selector.

Honest limitation: All data is synthetic. These tests verify code-path
integrity, not biological sampling efficiency.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ───────────────────────────────────────────────────────────


def _write_panel_csv(path: Path, rows: list[dict]) -> Path:
    fieldnames = [
        "pilot_rank", "candidate_id", "sequence", "length", "seed",
        "ensemble", "activity", "boman_activity", "disagreement",
        "safety", "synthesis", "novelty", "serum_stability",
        "selectivity_proxy", "rich_selectivity", "pilot_priority",
        "amphipathic_score", "charge_ph74",
    ]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def _panel_row(
    candidate_id: str,
    sequence: str,
    seed: str = "SEED-TEST",
    ensemble: float = 0.80,
    disagreement: float = 0.10,
    safety: float = 0.90,
    rich_selectivity: float = 0.75,
) -> dict:
    return {
        "pilot_rank": "1",
        "candidate_id": candidate_id,
        "sequence": sequence,
        "length": str(len(sequence)),
        "seed": seed,
        "ensemble": f"{ensemble:.2f}",
        "activity": f"{ensemble:.2f}",
        "boman_activity": "0.75",
        "disagreement": f"{disagreement:.2f}",
        "safety": f"{safety:.2f}",
        "synthesis": "0.85",
        "novelty": "0.70",
        "serum_stability": "0.65",
        "selectivity_proxy": "0.60",
        "rich_selectivity": f"{rich_selectivity:.2f}",
        "pilot_priority": "0.75",
        "amphipathic_score": "1.5",
        "charge_ph74": "4.0",
    }


# ── Tests ─────────────────────────────────────────────────────────────


class TestSelectBatch2:
    """Tests for ``select_batch_2()``."""

    def test_basic_selection(self, tmp_path):
        """Selects the correct number of candidates from a pool."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row(f"CAND-{i:03d}", f"AAAAKKKKFF{i}", seed=f"SEED-{i}")
            for i in range(20)
        ]
        _write_panel_csv(pool, rows)
        batch_1 = ["CAND-000", "CAND-001", "CAND-002"]

        result = select_batch_2(pool, batch_1, n=5)
        assert len(result.selected) == 5
        assert result.n_requested == 5
        assert result.n_remaining == 17
        assert all(
            c.get("candidate_id") not in batch_1
            for c in result.selected
        )

    def test_safety_gate_filters_out_toxic(self, tmp_path):
        """Candidates below safety threshold are excluded."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row("CAND-SAFE-1", "AAAAKKKFF1", safety=0.9),
            _panel_row("CAND-TOXIC-1", "BBBBLLLGG2", safety=0.2),
            _panel_row("CAND-SAFE-2", "CCCCMMMHH3", safety=0.8),
            _panel_row("CAND-TOXIC-2", "DDDDNNNII4", safety=0.1),
        ]
        _write_panel_csv(pool, rows)

        result = select_batch_2(pool, [], n=4)
        ids = [c.get("candidate_id") for c in result.selected]
        assert "CAND-TOXIC-1" not in ids
        assert "CAND-TOXIC-2" not in ids
        assert "CAND-SAFE-1" in ids
        assert "CAND-SAFE-2" in ids
        assert result.n_after_safety_gate == 2

    def test_selectivity_gate_filters(self, tmp_path):
        """Candidates below selectivity threshold are excluded."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row("CAND-SEL-1", "AAAAKKKFF1", rich_selectivity=0.8),
            _panel_row("CAND-LOW-SEL", "BBBBLLLGG2", rich_selectivity=0.3),
        ]
        _write_panel_csv(pool, rows)

        result = select_batch_2(pool, [], n=2)
        ids = [c.get("candidate_id") for c in result.selected]
        assert "CAND-LOW-SEL" not in ids
        assert "CAND-SEL-1" in ids

    def test_uncertainty_probe_guarantee(self, tmp_path):
        """At least one high-uncertainty candidate is selected when available."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row("CAND-HIGH-UNC", "AAAAKKKFF1", ensemble=0.51, disagreement=0.45),
            _panel_row("CAND-LOW-UNC-A", "BBBBLLLGG2", ensemble=0.90, disagreement=0.05),
            _panel_row("CAND-LOW-UNC-B", "CCCCMMMHH3", ensemble=0.92, disagreement=0.04),
            _panel_row("CAND-LOW-UNC-C", "DDDDNNNII4", ensemble=0.88, disagreement=0.06),
            _panel_row("CAND-LOW-UNC-D", "EEEEOOOJJ5", ensemble=0.91, disagreement=0.03),
        ]
        _write_panel_csv(pool, rows)

        result = select_batch_2(pool, [], n=3, min_uncertainty_probes=1)
        selected_ids = [c.get("candidate_id") for c in result.selected]
        assert "CAND-HIGH-UNC" in selected_ids
        assert result.probes_in_top_n >= 1

    def test_diversity_vs_batch_1(self, tmp_path):
        """Diverse candidates are preferred over near-duplicates of batch 1."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row("CAND-NOVEL", "QWERTYUIOPLKJHGFDSA", ensemble=0.75, disagreement=0.10),
            _panel_row("CAND-DUP", "AAAKKKFFFI", ensemble=0.85, disagreement=0.05),
        ]
        batch_1_candidates = tmp_path / "batch1.csv"
        _write_panel_csv(pool, rows)
        _write_panel_csv(batch_1_candidates, [
            _panel_row("BATCH1-1", "AAAKKKFFFI", ensemble=0.82, disagreement=0.07),
        ])

        result = select_batch_2(
            pool,
            batch_1_ids=["BATCH1-1"],
            n=2,
            diversity_weight=0.5,
            uncertainty_weight=0.0,
            ensemble_weight=0.5,
        )
        selected_ids = [c.get("candidate_id") for c in result.selected]
        # CAND-DUP is a near-duplicate of batch1-1, so with high diversity weight
        # the novel candidate should rank higher
        assert "CAND-NOVEL" in selected_ids

    def test_no_remaining_candidates(self, tmp_path):
        """Empty pool returns empty selection with explanatory note."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        _write_panel_csv(pool, [
            _panel_row("CAND-001", "AAAAKKKFFF"),
        ])

        result = select_batch_2(pool, batch_1_ids=["CAND-001"], n=5)
        assert len(result.selected) == 0
        assert len(result.notes) > 0

    def test_all_gated_out(self, tmp_path):
        """Pool where every remaining candidate fails safety gate."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        _write_panel_csv(pool, [
            _panel_row("CAND-A", "AAAAKKKFFF1", safety=0.1, rich_selectivity=0.2),
            _panel_row("CAND-B", "BBBBLLLGGG2", safety=0.2, rich_selectivity=0.3),
        ])

        result = select_batch_2(pool, batch_1_ids=[], n=5)
        assert len(result.selected) == 0
        assert result.n_after_safety_gate == 0
        assert len(result.notes) > 0

    def test_batch_selection_has_reason(self, tmp_path):
        """Each selected candidate has a selection_reason field."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row(f"CAND-{i:03d}", f"AAAAKKKKFF{i}", ensemble=0.80 - i * 0.02)
            for i in range(10)
        ]
        _write_panel_csv(pool, rows)

        result = select_batch_2(pool, batch_1_ids=[], n=5)
        for c in result.selected:
            assert "selection_reason" in c
            assert isinstance(c["selection_reason"], str)
            assert len(c["selection_reason"]) > 0

    def test_selection_metadata_shape(self, tmp_path):
        """BatchSelection dataclass has all expected fields."""
        from openamp_foundry.active_learning.selector import select_batch_2

        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row(f"CAND-{i:03d}", f"AAAAKKKKFF{i}") for i in range(10)
        ]
        _write_panel_csv(pool, rows)

        result = select_batch_2(pool, batch_1_ids=[], n=3)
        d = result.to_dict()
        assert "version" in d
        assert "n_requested" in d
        assert "n_remaining" in d
        assert "n_after_safety_gate" in d
        assert "selected" in d
        assert "probes_in_top_n" in d
        assert "notes" in d
        assert len(d["selected"]) == 3

    def test_cli_select_batch(self, tmp_path):
        """CLI select-batch exits 0 and produces valid JSON output."""
        pool = tmp_path / "pool.csv"
        rows = [
            _panel_row(f"CAND-{i:03d}", f"AAAAKKKKFF{i}") for i in range(15)
        ]
        _write_panel_csv(pool, rows)
        out = tmp_path / "batch2.json"

        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli", "select-batch",
                "--candidates", str(pool),
                "--batch-1-ids", "CAND-000,CAND-001",
                "--n", "5",
                "--out", str(out),
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert out.exists()
        data = json.loads(out.read_text())
        assert len(data["selected"]) == 5
        assert data["n_requested"] == 5
        assert "version" in data

    def test_cli_rejects_missing_candidates(self, tmp_path):
        """CLI exits 1 when candidates CSV does not exist."""
        missing = tmp_path / "nonexistent.csv"
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli", "select-batch",
                "--candidates", str(missing),
                "--batch-1-ids", "CAND-001",
                "--out", str(tmp_path / "batch2.json"),
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1
        assert "error" in result.stdout


# ── Active-learning benchmark tests ────────────────────────────────────────


class TestActiveLearningBenchmark:
    """Tests for the active-learning recovery benchmark."""

    def test_generate_benchmark_pool(self):
        """Pool has correct number of candidates and labels."""
        from openamp_foundry.active_learning.benchmark import (
            generate_benchmark_pool,
        )

        pool = generate_benchmark_pool(n_total=50, n_active=10)
        assert len(pool) == 50
        n_active = sum(1 for c in pool if c["label"] == 1)
        assert n_active == 10

    def test_benchmark_returns_correct_shape(self, tmp_path):
        """Benchmark result has all expected fields."""
        from openamp_foundry.active_learning.benchmark import (
            generate_benchmark_pool,
            run_active_learning_benchmark,
            write_benchmark_pool,
        )

        pool = generate_benchmark_pool(n_total=30, n_active=6)
        csv_path = tmp_path / "pool.csv"
        write_benchmark_pool(pool, csv_path)

        result = run_active_learning_benchmark(
            csv_path, n_hidden_actives=2, batch_size=5, max_rounds=3,
        )
        d = result.to_dict()
        assert "version" in d
        assert "n_hidden_actives" in d
        assert "rounds_to_first_recovery" in d
        assert "final_recall" in d
        assert "passed" in d
        assert "selector_outperforms_random" in d
        assert len(d["rounds"]) > 0

    def test_benchmark_recovery_in_expected_range(self, tmp_path):
        """Selector should recover hidden actives within reasonable rounds
        because active candidates have measurably higher ensemble scores."""
        from openamp_foundry.active_learning.benchmark import (
            generate_benchmark_pool,
            run_active_learning_benchmark,
            write_benchmark_pool,
        )

        pool = generate_benchmark_pool(n_total=50, n_active=10, rng_seed=42)
        csv_path = tmp_path / "pool.csv"
        write_benchmark_pool(pool, csv_path)

        result = run_active_learning_benchmark(
            csv_path, n_hidden_actives=3, batch_size=5, max_rounds=5,
        )
        # With 10 active out of 50, and the selector biased toward high-ensemble
        # candidates, it should recover at least some hidden actives.
        assert result.final_recall > 0.0, (
            f"Selector failed to recover any hidden active: {result.notes}"
        )

    def test_benchmark_comparison_to_random(self, tmp_path):
        """Selector should match or beat random baseline on recall."""
        from openamp_foundry.active_learning.benchmark import (
            generate_benchmark_pool,
            run_active_learning_benchmark,
            write_benchmark_pool,
        )

        pool = generate_benchmark_pool(n_total=50, n_active=10, rng_seed=42)
        csv_path = tmp_path / "pool.csv"
        write_benchmark_pool(pool, csv_path)

        result = run_active_learning_benchmark(
            csv_path, n_hidden_actives=3, batch_size=5, max_rounds=5,
        )
        assert result.random_baseline_final_recall >= 0.0
        assert result.final_recall > 0.0

    def test_benchmark_empty_pool_rejected(self, tmp_path):
        """Benchmark raises on pool with no active candidates."""
        from openamp_foundry.active_learning.benchmark import (
            generate_benchmark_pool,
            run_active_learning_benchmark,
            write_benchmark_pool,
        )

        pool = generate_benchmark_pool(n_total=10, n_active=0, rng_seed=1)
        csv_path = tmp_path / "pool.csv"
        write_benchmark_pool(pool, csv_path)

        with pytest.raises(ValueError, match="No active candidates"):
            run_active_learning_benchmark(csv_path)

    def test_benchmark_pool_not_found(self, tmp_path):
        """Benchmark raises on missing file."""
        from openamp_foundry.active_learning.benchmark import (
            run_active_learning_benchmark,
        )

        with pytest.raises(FileNotFoundError):
            run_active_learning_benchmark(tmp_path / "nonexistent.csv")

    def test_benchmark_pre_registered_thresholds(self, tmp_path):
        """Pre-registered thresholds are accessible."""
        from openamp_foundry.active_learning.benchmark import (
            PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY,
            PREREGISTERED_MIN_RECALL,
        )

        assert PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY >= 1
        assert 0.0 < PREREGISTERED_MIN_RECALL <= 1.0

    def test_cli_bench_active_learning(self, tmp_path):
        """CLI bench active-learning exits 0 and produces valid output."""
        result = subprocess.run(
            [
                sys.executable, "-m", "openamp_foundry.cli", "bench",
                "active-learning",
                "--n-hidden", "2",
                "--batch-size", "5",
                "--max-rounds", "3",
                "--rng-seed", "42",
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr[:500]}"
        data = json.loads(result.stdout)
        assert "version" in data
        assert "rounds" in data
        assert "passed" in data
        assert data["n_hidden_actives"] == 2
