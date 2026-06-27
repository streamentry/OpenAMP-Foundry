.PHONY: demo test lint clean bench-leakage bench-baseline bench-hidden-active generate phase3

PYTHON := $(shell [ -f .venv/bin/python ] && echo .venv/bin/python || echo python3)
PYTEST  := $(shell [ -f .venv/bin/pytest ] && echo .venv/bin/pytest || echo pytest)
RUFF    := $(shell [ -f .venv/bin/ruff ] && echo .venv/bin/ruff || echo ruff)

demo:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli rank \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--out outputs/demo_ranked.jsonl \
		--report outputs/demo_report.md \
		--cert-dir outputs/evidence \
		--manifest outputs/run_manifest.json

test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests scripts

bench-leakage:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench leakage \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--out outputs/leakage_report.json

bench-baseline:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench baseline \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--positives examples/known_reference/demo_known_amps.csv \
		--out outputs/bench_baseline_report.json

bench-hidden-active:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench baseline \
		--candidates examples/benchmark/mixed_candidates.csv \
		--positives examples/benchmark/active_labels.csv \
		--k 5 10 20 \
		--out outputs/bench_hidden_active_report.json

generate:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli generate-batch \
		--seeds examples/sequences/amp_seeds.csv \
		--out examples/sequences/phase3_pool.csv \
		--n-double 25 \
		--n-charge 12 \
		--rng-seed 2024

phase3: generate
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli rank \
		--candidates examples/sequences/phase3_pool.csv \
		--references examples/known_reference/amp_curated_references.csv \
		--out outputs/phase3_ranked.jsonl \
		--report outputs/phase3_report.md \
		--cert-dir outputs/phase3_evidence \
		--manifest outputs/phase3_manifest.json \
		--config configs/phase3.yaml
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli batch-pack \
		--ranked outputs/phase3_ranked.jsonl \
		--out-json outputs/phase3_batch_pack.json \
		--out-md outputs/phase3_batch_pack.md

clean:
	rm -rf outputs/*.jsonl outputs/*.md outputs/*.json outputs/evidence outputs/phase3_evidence .pytest_cache .ruff_cache
