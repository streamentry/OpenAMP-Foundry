from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "benchmarks"
_spec = importlib.util.spec_from_file_location(
    "_scripts_benchmark_multi_negatives", _SCRIPTS_DIR / "benchmark_multi_negatives.py"
)
_multi = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_multi)
main = _multi.main
load_amp_sequences = _multi.load_amp_sequences
generate_uniform_decoys = _multi.generate_uniform_decoys
generate_reverse_decoys = _multi.generate_reverse_decoys
generate_shuffled_decoys = _multi.generate_shuffled_decoys
write_decoy_csv = _multi.write_decoy_csv


class TestAmpLoading:
    def test_loads_known_amps(self):
        amps = load_amp_sequences("examples/validation/known_amps.csv")
        assert len(amps) == 95
        assert all("sequence" in a for a in amps)

    def test_all_sequences_upper(self):
        amps = load_amp_sequences("examples/validation/known_amps.csv")
        for a in amps:
            assert a["sequence"] == a["sequence"].strip().upper()


class TestDecoyGeneration:
    def test_uniform_decoys_same_length(self):
        amps = [{"sequence": "ACDEF"}, {"sequence": "ACDEFGHIKL"}]
        import random
        rng = random.Random(42)
        decoys = generate_uniform_decoys(amps, rng)
        assert len(decoys) == 2
        assert len(decoys[0]["sequence"]) == 5
        assert len(decoys[1]["sequence"]) == 10

    def test_uniform_decoys_only_standard_aas(self):
        amps = [{"sequence": "ACDEF"}]
        import random
        rng = random.Random(42)
        decoys = generate_uniform_decoys(amps, rng)
        seq = decoys[0]["sequence"]
        assert all(aa in "ACDEFGHIKLMNPQRSTVWY" for aa in seq)

    def test_reverse_decoys_are_reversed(self):
        amps = [{"sequence": "ACDEFGHIK"}, {"sequence": "KIHGFEDCA"}]
        decoys = generate_reverse_decoys(amps)
        assert decoys[0]["sequence"] == "KIHGFEDCA"
        assert decoys[1]["sequence"] == "ACDEFGHIK"

    def test_reverse_decoys_have_deterministic_ids(self):
        amps = [{"sequence": "ACD"}, {"sequence": "EFG"}]
        decoys = generate_reverse_decoys(amps)
        assert decoys[0]["id"] == "REVERSE-DECOY-0001"
        assert decoys[1]["id"] == "REVERSE-DECOY-0002"

    def test_shuffled_decoys_preserve_composition(self):
        amps = [{"sequence": "AAAAABBBBBCCCCCDDDDD"}]
        import random
        rng = random.Random(42)
        decoys = generate_shuffled_decoys(amps, rng)
        shuffled = decoys[0]["sequence"]
        assert sorted(shuffled) == sorted(amps[0]["sequence"])

    def test_shuffled_decoys_often_differ(self):
        seq = "ACDEFGHIKLMNPQRSTVWY"
        amps = [{"sequence": seq}]
        import random
        diff_count = 0
        for seed in range(10):
            rng = random.Random(seed)
            decoys = generate_shuffled_decoys(amps, rng)
            if decoys[0]["sequence"] != seq:
                diff_count += 1
        assert diff_count >= 9


class TestWriteDecoyCsv:
    def test_writes_valid_csv(self, tmp_path):
        rows = [
            {"id": "D1", "sequence": "AAAAA", "family": "test", "reference": "R1", "label": "0"},
        ]
        p = write_decoy_csv(rows, tmp_path / "decoys.csv")
        assert p.exists()
        text = p.read_text(encoding="utf-8")
        assert "id,sequence,family,reference,label" in text
        assert "D1,AAAAA" in text


def _parse_stdout(stdout: str) -> dict:
    """Parse JSON from multiline stdout, which may have trailing status lines."""
    lines = stdout.strip().split("\n")
    depth = 0
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "{" and depth == 0:
            start = i
            depth = 1
        elif start is not None:
            depth += stripped.count("{") - stripped.count("}")
            if depth == 0:
                chunk = "\n".join(lines[start:i+1])
                return json.loads(chunk)
    msg = f"No complete JSON object found in stdout:\n{stdout}"
    raise ValueError(msg)


class TestMultiNegativeBenchmarkCLI:
    def test_exit_0_with_known_amps(self):
        result = subprocess.run(
            [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py",
             "--amp-csv", "examples/validation/known_amps.csv"],
            capture_output=True, text=True,
            cwd=_REPO_ROOT,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        assert result.returncode == 0

    def test_reports_all_four_sets(self):
        result = subprocess.run(
            [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py",
             "--amp-csv", "examples/validation/known_amps.csv"],
            capture_output=True, text=True,
            cwd=_REPO_ROOT,
        )
        data = _parse_stdout(result.stdout)
        assert data["n_sets"] == 4
        sets = {r["negative_set"] for r in data["results"]}
        assert sets == {"swissprot_background", "uniform_random", "reverse", "shuffled"}

    def test_independent_sets_above_07(self):
        result = subprocess.run(
            [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py",
             "--amp-csv", "examples/validation/known_amps.csv"],
            capture_output=True, text=True,
            cwd=_REPO_ROOT,
        )
        data = _parse_stdout(result.stdout)
        assert data["all_independent_sets_above_0_70"] is True

    def test_writes_report_file(self, tmp_path):
        report = tmp_path / "report.json"
        result = subprocess.run(
            [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py",
             "--amp-csv", "examples/validation/known_amps.csv",
             "--out", str(report)],
            capture_output=True, text=True,
            cwd=_REPO_ROOT,
        )
        assert result.returncode == 0
        assert report.exists()
        data = json.loads(report.read_text(encoding="utf-8"))
        assert data["n_sets"] == 4

    def test_fails_on_synthetic_weak_amps(self, tmp_path):
        """If all AMPs are weak (non-AMP-like), the independent sets should fail < 0.70."""
        weak_amps = tmp_path / "weak_amps.csv"
        weak_amps.write_text(
            "id,sequence,family,reference,is_amp\n"
            "W1,DDDDDDDDDD,synthetic,test,1\n"
            "W2,EEEEEEEEEE,synthetic,test,1\n"
            "W3,KKKKKKKKKK,synthetic,test,1\n"
            "W4,RRRRRRRRRR,synthetic,test,1\n"
            "W5,SSSSSSSSSS,synthetic,test,1\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, "scripts/benchmarks/benchmark_multi_negatives.py",
             "--amp-csv", str(weak_amps)],
            capture_output=True, text=True,
            cwd=_REPO_ROOT,
        )
        assert result.returncode == 1
