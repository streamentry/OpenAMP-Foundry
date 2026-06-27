.PHONY: demo test lint clean bench-leakage

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

clean:
	rm -rf outputs/*.jsonl outputs/*.md outputs/*.json outputs/evidence .pytest_cache .ruff_cache
