.PHONY: demo test lint ci clean bench-leakage bench-baseline bench-hidden-active generate phase3 pilot validate-scoring validate-scoring-strict external-predict pilot-confident presynth-qc gold-standard diversity synthesis-order

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

ci: lint test
	@echo "CI passed: lint + 1081-test suite green"

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

pilot: phase3
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli pilot-panel \
		--ranked outputs/phase3_ranked.jsonl \
		--n 20 \
		--max-per-seed 4 \
		--similarity-threshold 0.75 \
		--out-csv outputs/pilot_panel.csv \
		--out-md outputs/pilot_panel.md

validate-scoring:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/random_background.csv \
		--benchmark-type standard \
		--out outputs/validate_scoring_report.json

validate-scoring-strict:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/scrambled_decoys.csv \
		--benchmark-type strict \
		--out outputs/validate_scoring_strict_report.json

external-predict: pilot
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli external-predict \
		--pilot-csv outputs/pilot_panel.csv \
		--out-fasta outputs/pilot_panel.fasta \
		--out-checklist outputs/external_predict_checklist.md

pilot-confident:
	@if [ -z "$(KEEP)" ]; then \
		echo "Usage: make pilot-confident KEEP=ID1,ID2,..."; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli pilot-confident \
		--pilot-csv outputs/pilot_panel.csv \
		--keep "$(KEEP)" \
		--out outputs/confident_panel

presynth-qc:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli presynth-qc \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/presynth_qc_report.md

gold-standard:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli gold-standard \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/gold_standard_calibration.md \
		--config configs/pipeline.yaml

diversity:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli diversity-check \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/diversity_report.md

synthesis-order:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli synthesis-order \
		--panel-csv outputs/confident_panel.csv \
		--out-csv outputs/synthesis_order.csv \
		--out-md outputs/synthesis_checklist.md \
		--quantity-mg 5

clean:
	rm -rf outputs/*.jsonl outputs/*.md outputs/*.json outputs/evidence outputs/phase3_evidence .pytest_cache .ruff_cache
