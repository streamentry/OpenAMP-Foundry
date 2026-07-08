# Fixture Design Guide

How to design test fixtures for the pipeline.

## Principles
- Fixtures should be minimal — only include what's needed for the test.
- Fixtures should be deterministic — same input always produces same output.
- Fixtures should be labeled as synthetic or demo, not real data.
- Fixtures should be small enough to be reviewed manually.

## Location
- Test fixtures go in `tests/fixtures/`.
- Demo fixtures go in `examples/`.
- Never use real candidate data as test fixtures.

## Required Fields
- `candidate_id` — clearly identifies the fixture
- `sequence` — valid amino acid sequence
- `source` — indicates it's a fixture (e.g., `test_fixture`, `demo`)
