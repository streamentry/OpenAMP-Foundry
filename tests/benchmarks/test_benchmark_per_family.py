from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "benchmarks"
_spec = importlib.util.spec_from_file_location(
    "_scripts_benchmark_per_family", _SCRIPTS_DIR / "benchmark_per_family.py"
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
main = _mod.main
classify_amp = _mod.classify_amp

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")


def _make_features(length=15, net_charge=2.0, proline_fraction=0.0):
    return {
        "length": length,
        "net_charge_ph74": net_charge,
        "proline_fraction": proline_fraction,
    }


class TestClassifyAmp:
    def test_cysteine_rich_two_cys(self):
        assert classify_amp("CACDEFGHIKLAC", _make_features()) == "cysteine_rich"

    def test_cysteine_rich_four_cys(self):
        assert classify_amp("CCACDEFGHCC", _make_features()) == "cysteine_rich"

    def test_short_max_12aa(self):
        assert classify_amp("ACDEFGHIKLMN", _make_features(length=12)) == "short"

    def test_short_under_over_12(self):
        ch = "ACDEFGHIKLMNP"
        assert classify_amp(ch, _make_features(length=13)) != "short"

    def test_proline_rich(self):
        seq = "PPPPPPP" + "A" * 10
        assert classify_amp(seq, _make_features(proline_fraction=0.40)) == "proline_rich"

    def test_proline_rich_respects_cys_priority(self):
        seq = "CPCPCPCPCPCPCPCPCPCP"
        assert classify_amp(seq, _make_features(proline_fraction=0.40)) == "cysteine_rich"

    def test_highly_cationic(self):
        assert classify_amp("AAAAA", _make_features(net_charge=5.0)) == "highly_cationic"

    def test_highly_cationic_respects_cys_priority(self):
        assert classify_amp("CAAAAAC", _make_features(net_charge=5.0)) == "cysteine_rich"

    def test_highly_cationic_respects_short_priority(self):
        assert classify_amp("AAAAA", _make_features(length=5, net_charge=5.0)) == "short"

    def test_moderately_cationic(self):
        assert classify_amp("AAAAA", _make_features(net_charge=3.0)) == "moderately_cationic"

    def test_low_charge(self):
        assert classify_amp("AAAAA", _make_features(net_charge=1.0)) == "low_charge"

    def test_priority_order_cys_first(self):
        ch = "CACDEFGHIKLAC"
        assert classify_amp(ch, _make_features(length=11, net_charge=5.0, proline_fraction=0.30)) == "cysteine_rich"

    def test_priority_order_short_second(self):
        assert classify_amp("A" * 10, _make_features(length=10, net_charge=5.0, proline_fraction=0.30)) == "short"

    def test_priority_order_proline_third(self):
        assert classify_amp("APAPAPAPAPAP", _make_features(length=13, net_charge=5.0, proline_fraction=0.30)) == "proline_rich"


class TestMainAndStructure:
    def test_main_returns_zero(self):
        rc = main(["--out", "/tmp/test_per_family.json"])
        assert rc == 0

    def test_output_json_has_all_classes(self):
        expected = {"cysteine_rich", "proline_rich", "short", "highly_cationic", "moderately_cationic", "low_charge", "all_amps"}
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert set(report["results"]) == expected

    def test_all_amps_auroc_matches_expanded_benchmark(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        auroc = report["results"]["all_amps"]["auroc"]
        assert 0.77 <= auroc <= 0.79

    def test_highly_cationic_auroc_above_09(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        auroc = report["results"]["highly_cationic"]["auroc"]
        assert auroc >= 0.90

    def test_proline_rich_auroc_below_07(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        auroc = report["results"]["proline_rich"]["auroc"]
        assert auroc < 0.70

    def test_low_charge_auroc_below_075(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        auroc = report["results"]["low_charge"]["auroc"]
        assert auroc < 0.75

    def test_n_amps_total_500(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert report["n_amps_total"] == 500

    def test_min_class_size_5(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert report["min_class_size"] == 5

    def test_class_distribution_matches_results(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        total = sum(report["class_distribution"].values())
        assert total == 500

    def test_interpretation_does_not_claim_all_above_70(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert "all AMP structural classes" not in report["interpretation"]

    def test_interpretation_mentions_weak_classes(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert "Potential blind spots" in report["interpretation"]

    def test_best_class_highly_cationic(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert report["best_class"] == "highly_cationic"

    def test_worst_class_proline_rich(self):
        with open("/tmp/test_per_family.json") as f:
            report = json.load(f)
        assert report["worst_class"] == "proline_rich"
