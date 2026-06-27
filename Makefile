.PHONY: demo test lint clean

demo:
	PYTHONPATH=src python -m openamp_foundry.cli rank --candidates examples/sequences/demo_candidates.csv --references examples/known_reference/demo_known_amps.csv --out outputs/demo_ranked.jsonl --report outputs/demo_report.md --cert-dir outputs/evidence

test:
	pytest -q

lint:
	ruff check src tests scripts

clean:
	rm -rf outputs/*.jsonl outputs/*.md outputs/evidence .pytest_cache .ruff_cache
