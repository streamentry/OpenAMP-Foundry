# 15-Minute Quickstart

**Goal:** Go from zero to running the full demo pipeline in 15 minutes.

---

## Prerequisites (2 min)

- Python 3.11+
- git

## Setup (5 min)

```bash
git clone https://github.com/Open-Problem-Lab/OpenAMP-Foundry.git
cd OpenAMP-Foundry
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the Demo (3 min)

```bash
make demo
```

This will rank 10 demo candidates, generate evidence certificates in `outputs/evidence/`, and produce a report at `outputs/demo_report.md`.

## View Results (2 min)

```bash
# View the report
cat outputs/demo_report.md

# View a candidate's evidence certificate
cat outputs/evidence/AMPF-000001.json

# View the run manifest
cat outputs/run_manifest.json
```

## Run with Simulation Scores (2 min)

```bash
PYTHONPATH=src python3 -m openamp_foundry.cli rank \
  --candidates examples/sequences/demo_candidates.csv \
  --references examples/known_reference/demo_known_amps.csv \
  --out outputs/demo_ranked.jsonl \
  --report outputs/demo_report.md \
  --simulation-mode info
```

This adds membrane binding and structure proxy scores to every candidate.

## Run the Full Test Suite (1 min)

```bash
python3 -m pytest -q --tb=short
```

> **Note:** Full suite takes ~80s. Use `-k` to run specific tests.

## Next Steps

- Read [`docs/evidence/LIMITATIONS_OVERVIEW.md`](../evidence/LIMITATIONS_OVERVIEW.md) for honest limitations
- Read [`CONTRIBUTING.md`](../../CONTRIBUTING.md) for contribution guidelines
- Read [`AGENTS.md`](../AGENTS.md) for the agent operating contract
