# First Run Walkthrough

## Purpose

This walkthrough helps a new human or AI agent complete a first run of OpenAMP Foundry and understand what the outputs do and do not prove.

A good first run should produce clarity, not confidence.

## Prime rule

**The demo proves the workflow can run. It does not prove any candidate is biologically active, safe, or useful.**

## Before you start

Read:

- [`README.md`](../README.md)
- [`SAFETY.md`](../SAFETY.md)
- [`docs/COMMAND_SURFACE.md`](COMMAND_SURFACE.md)
- [`docs/PROOF_LADDER.md`](PROOF_LADDER.md)

## Expected setup

OpenAMP expects Python 3.11 or newer.

Typical setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run the demo

```bash
make demo
```

Expected result:

- demo ranking artifact;
- demo report;
- evidence certificates;
- run manifest.

The exact output paths are defined by the Makefile and command surface docs.

## Inspect the report

After the demo, inspect the generated report first.

Ask:

1. What candidates were ranked?
2. What scoring components were used?
3. What limitations are stated?
4. What evidence level is supported?
5. What claims remain unsupported?

The report should make clear that the output is dry-lab triage only.

## Inspect evidence certificates

Evidence certificates should answer:

- candidate identity or safe reference;
- provenance;
- scores;
- known limitations;
- baseline caveats;
- novelty status;
- safety-risk flags;
- unsupported claims;
- proof-ladder level.

A certificate is review infrastructure.

It is not biological proof.

See [`docs/EVIDENCE_CERTIFICATE.md`](EVIDENCE_CERTIFICATE.md).

## Run basic checks

```bash
make test
make lint
make ci
```

These checks support engineering confidence.

They do not support scientific claims about candidates.

## Run benchmark checks

Benchmark commands are documented in [`docs/BENCHMARKING.md`](BENCHMARKING.md).

Benchmark results should be interpreted through:

- [`docs/BENCHMARK_GOVERNANCE.md`](BENCHMARK_GOVERNANCE.md)
- [`docs/METRICS_CURRENT.md`](METRICS_CURRENT.md)
- [`docs/CLAIM_REVIEW_CHECKLIST.md`](CLAIM_REVIEW_CHECKLIST.md)

A benchmark pass means a specific computational check passed under stated assumptions.

It does not prove real-world biological value.

## Common first-run failures

| Symptom | Likely cause | Next action |
|---|---|---|
| Command not found | Virtual environment not activated or package not installed. | Re-run setup steps. |
| Import error | Package not installed editable or wrong Python environment. | Re-run `pip install -e .[dev]`. |
| Missing output directory | Generated artifacts were not created yet or directory is ignored. | Run demo again and inspect Makefile target. |
| Schema validation fails | Artifact format changed or stale output exists. | Regenerate outputs and inspect schema docs. |
| Benchmark differs from docs | Stale metrics or local change. | Check `docs/METRICS_CURRENT.md` and rerun relevant benchmark. |

## First contribution after first run

Good first contributions:

- improve an error message;
- add a missing test;
- fix a broken doc link;
- add a toy schema example;
- clarify a command’s output;
- improve first-run troubleshooting;
- update project index when adding docs.

Avoid first contributions that touch:

- safety policy;
- release policy;
- non-toy candidates;
- model weights;
- benchmark thresholds;
- external-facing biological claims.

## First-run success criteria

A successful first run means you can answer:

1. What is OpenAMP?
2. What is it not?
3. Which command did you run?
4. Which artifacts were created?
5. Which proof-ladder level is supported?
6. What remains unproven?
7. What safe task could improve the repo next?

## Final standard

The first-run experience should turn curiosity into safe contribution.

It should never turn a demo into a biological claim.
