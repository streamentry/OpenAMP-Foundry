# New Contributor Curriculum

A staged path from first reading to a useful first pull request.

---

## Prerequisites

- Python 3.11+
- Basic familiarity with command line and git
- Read [CONTRIBUTING.md](../../CONTRIBUTING.md)

## Stage 1: Orientation (30 min)

Read these in order:

1. `README.md` — project overview and quickstart
2. [`docs/evidence/LIMITATIONS_OVERVIEW.md`](../evidence/LIMITATIONS_OVERVIEW.md) — honest limitations
3. `docs/getting-started/QUICKSTART.md` — run the demo
4. `AGENTS.md` — operating principles (useful even for humans)
5. `AGENT_TASKS.json` — safe task categories

## Stage 2: Core Concepts (1-2 hours)

1. `docs/engineering/ARCHITECTURE.md` — system architecture
2. `docs/evidence/EVIDENCE_CERTIFICATE.md` — evidence schema
3. `docs/evidence/BENCHMARK_GOVERNANCE.md` — benchmark policies
4. `docs/evidence/PROOF_LADDER.md` — evidence levels
5. `docs/evidence/SYNTHETIC_DATA_POLICY.md` — data labeling rules

## Stage 3: Practice Tasks

Choose a task type based on your comfort level.

### Docs-only (no Python needed)

- Fix a broken doc link: `python scripts/check_doc_links.py`
- Improve a section in any docs/ file
- Add a test for an existing doc (see existing test_*.py files for patterns)

### Tests

- Add a missing-file error test (see `tests/test_missing_file_errors.py`)
- Add a metric polarity test (see `tests/test_metric_polarity_registry.py`)
- Improve coverage on an existing test file

### Schemas

- Review a schema in `schemas/` for completeness
- Add a validation test for a schema

### Local checks (scripts/)

- Improve `scripts/check_claims.py` pattern list
- Add a pattern to `scripts/check_doc_links.py`
- Improve `scripts/check_pyproject.py`

## Stage 4: First Pull Request

1. Pick an issue from the open issues list
2. Comment on the issue that you're working on it
3. Create a branch, make your change, add tests
4. Run `python3 -m pytest -q` to verify nothing is broken
5. Run `python scripts/check_doc_links.py` to check links
6. Create a PR that references the issue number

## Task Types Requiring Maintainer Discussion

- Changes to scoring weights (`configs/pipeline.yaml`)
- Changes to the calibration pipeline
- Changes to safety policy or review templates
- Adding new dependencies to `pyproject.toml`
- Any change that modifies benchmark thresholds
