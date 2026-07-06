# Data Directory

## Purpose

This directory is for data-related structure, not for unrestricted biological dataset storage.

OpenAMP Foundry ships toy/demo data by default. Non-toy data requires governance, licensing review, safety review where relevant, and dataset cards.

See:

- [`../DATA_LICENSE_NOTICE.md`](../DATA_LICENSE_NOTICE.md)
- [`../docs/DATA_GOVERNANCE.md`](../docs/DATA_GOVERNANCE.md)
- [`../docs/BENCHMARK_GOVERNANCE.md`](../docs/BENCHMARK_GOVERNANCE.md)

## Default rule

Do not commit third-party AMP databases, partner data, restricted data, result summaries, or generated candidate panels here unless release status is clear and review requirements are satisfied.

## Recommended layout

```text
data/
  README.md
  raw/                 # local-only or ignored external data
  processed/           # generated normalized data, usually ignored unless toy/open
  cards/               # dataset cards
  toy/                 # small demo/test datasets safe to ship
  manifests/           # data manifests and hashes
```

## What may be committed

Usually safe to commit:

- toy/demo data;
- dataset cards;
- metadata-only records;
- fetch scripts where licenses permit;
- small schema examples;
- manifests without restricted content;
- generated outputs explicitly marked safe to publish.

Requires review before commit:

- non-toy biological data;
- public datasets with unclear redistribution status;
- generated candidate panels;
- partner-derived result summaries;
- benchmark datasets with nontrivial label or release implications;
- any data containing sensitive or restricted material.

## Dataset card requirement

For every external or non-toy dataset, create a dataset card with:

- dataset ID;
- source;
- access date;
- license;
- redistribution status;
- citation requirement;
- intended use;
- label definitions;
- preprocessing steps;
- known biases;
- leakage risks;
- safety-release status;
- reviewer and review date.

## Data quality rules

Data used for benchmarks should document:

- positive-label definition;
- negative-label construction;
- sequence deduplication;
- near-duplicate policy;
- charge/length/composition distributions;
- split strategy;
- known shortcut risks;
- whether the benchmark is exploratory, informational, gate, or deprecated.

## Generated candidate data

Generated candidate data is not automatically safe to commit or publish.

Before committing generated candidates, confirm:

- release status;
- safety review requirement;
- novelty and similarity review;
- proof-ladder level;
- whether metadata-only release is safer;
- whether candidate identities or sequences should be withheld.

## Result-summary data

Qualified external result summaries should enter through structured schemas and release review.

Do not commit operational laboratory details or private partner information.

## Final standard

The data directory should make data provenance and release status clearer, not become a dumping ground for raw biological artifacts.
