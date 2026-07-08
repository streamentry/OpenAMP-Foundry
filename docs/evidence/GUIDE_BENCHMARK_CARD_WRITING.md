# Benchmark Card Writing Guide

How to write a benchmark card.

## Required Sections
- **Purpose**: What the benchmark measures
- **Dataset**: What data is used and its source
- **Metrics**: What metrics are reported
- **Caveats**: What the benchmark does NOT prove
- **Reproduction**: How to run the benchmark

## Format
```markdown
# Benchmark: [Name]

## Purpose
One paragraph describing what this benchmark measures.

## Dataset
- Positives: N sequences from [source]
- Negatives: N sequences from [source]
- Split method: [method]

## Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|

## Caveats
- Known limitations of this benchmark.
- What this benchmark does not test.

## Reproduction
```bash
make bench-500
```
```
