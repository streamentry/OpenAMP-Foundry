# Data License Notice

## Purpose

This notice defines the repository’s default data posture.

OpenAMP Foundry ships only toy/demo data by default.

External biological databases, benchmarks, reference sets, partner data, and result summaries may have licenses, access rules, citation requirements, redistribution limits, or safety constraints.

Do not assume data can be committed merely because it is accessible.

## Prime rule

**No non-toy dataset should enter the repo without license status, redistribution status, intended use, and known biases documented.**

## Default policy

1. Ship toy/demo data for tests and tutorials.
2. Do not commit raw third-party data unless redistribution is clearly allowed.
3. Prefer metadata, dataset cards, and fetch instructions where raw redistribution is unclear.
4. Store access dates and citation requirements.
5. Separate raw, processed, generated, benchmark, and result-summary data.
6. Mark restricted or partner-derived data clearly.
7. Do not publish sensitive candidate or result data without release review.

## Dataset card requirement

Every non-toy data source should have a dataset card.

Dataset cards should include:

- dataset ID;
- source name;
- source URL or private reference;
- access date;
- license or terms;
- redistribution status;
- citation requirements;
- label definitions;
- intended use;
- prohibited use;
- known biases;
- leakage risks;
- preprocessing steps;
- safety-release status;
- reviewer and review date.

Use `docs/DATA_GOVERNANCE.md` for the full standard.

## Data classes

| Class | Examples | Release posture |
|---|---|---|
| Toy/demo data | tiny examples for tests and docs | Open. |
| Public redistributable data | data with clear compatible license | Open with attribution. |
| Public reference-only data | accessible but not redistributable | Metadata/fetch instructions only. |
| Restricted data | partner, sensitive, or access-limited data | Do not commit raw data. |
| Generated candidate data | candidate panels and rankings | Review before release. |
| Result-summary data | qualified partner result summaries | Review before release. |

## Data contribution checklist

A data contribution must include:

- dataset card;
- license or terms summary;
- citation requirements;
- intended use;
- preprocessing record;
- label definitions;
- known biases;
- leakage risks;
- safety-release status;
- tests or validation where applicable.

## Benchmark data warning

Benchmark datasets can create false progress if labels, negatives, or splits are weak.

Before using data for a benchmark, review:

- negative-set construction;
- near-duplicate leakage;
- charge/length/composition shortcut risks;
- split method;
- confidence intervals;
- claim being gated.

See `docs/BENCHMARK_GOVERNANCE.md`.

## Final standard

A serious outsider should be able to tell where every dataset came from, whether it can be reused, what it means, and what it cannot prove.
